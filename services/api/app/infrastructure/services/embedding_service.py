"""HTTP-based embedding service adapter implementation."""

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import EmbeddingServiceError, ServiceUnavailableError, ValidationError
from app.ports.services import EmbeddingService


class HTTPEmbeddingService(EmbeddingService):
    """HTTP adapter for embedding generation service.

    This adapter communicates with the embedder microservice via HTTP
    to generate vector embeddings for text chunks.
    """

    def __init__(self, embedder_url: str):
        """Initialize HTTP embedding service.

        Args:
            embedder_url: Base URL of the embedder service (e.g., "http://localhost:8001")
        """
        self.embedder_url = embedder_url.rstrip("/")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ServiceUnavailableError),
    )
    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for texts via HTTP with retry logic.

        Retries up to 3 times with exponential backoff (2-10s) on service unavailability.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (one per input text)

        Raises:
            ServiceUnavailableError: If embedding service is unavailable (will retry)
            EmbeddingServiceError: If embedding generation fails for other reasons
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.embedder_url}/api/v1/generate-embeddings",
                    json={"texts": texts},
                    timeout=30.0,
                )
                response.raise_for_status()

                # Parse response
                try:
                    data = response.json()
                except ValueError as e:
                    raise ValidationError(
                        "Failed to parse embedding service response", original_error=e
                    )

                # Validate response structure
                if "embeddings" not in data:
                    raise ValidationError(
                        "Invalid response format: missing 'embeddings' key"
                    )

                embeddings = data["embeddings"]

                # Validate embedding count matches input count
                if len(embeddings) != len(texts):
                    raise ValidationError(
                        f"Expected {len(texts)} embeddings but got {len(embeddings)}"
                    )

                return embeddings  # type: ignore[no-any-return]

        except httpx.ConnectError as e:
            raise ServiceUnavailableError(
                "Failed to connect to embedding service", original_error=e
            )
        except httpx.TimeoutException as e:
            raise ServiceUnavailableError(
                "Embedding service request timed out", original_error=e
            )
        except httpx.HTTPStatusError as e:
            # Raise ServiceUnavailableError for 503 to trigger retry
            if e.response.status_code == 503:
                raise ServiceUnavailableError(
                    "Embedding service temporarily unavailable", original_error=e
                )
            # Other HTTP errors don't retry (use ValidationError to prevent retry)
            raise ValidationError(
                f"Embedding service returned error: {e.response.status_code}",
                original_error=e,
            )
        except (EmbeddingServiceError, ServiceUnavailableError, ValidationError):
            # Re-raise our own exceptions
            raise
        except Exception as e:
            # Catch any other unexpected errors (wrap as ValidationError so no retry)
            raise ValidationError(
                f"Unexpected error during embedding generation: {type(e).__name__}",
                original_error=e,
            )
