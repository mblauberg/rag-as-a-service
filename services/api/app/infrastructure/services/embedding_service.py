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
    """HTTP adapter for embedding generation service."""

    def __init__(self, embedder_url: str):
        """Initialize HTTP embedding service.

        Args:
            embedder_url: Base URL of the embedder service
        """
        self.embedder_url = embedder_url.rstrip("/")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ServiceUnavailableError),
    )
    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings via embedder microservice with retry logic.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors, one per input text

        Raises:
            ServiceUnavailableError: Retried up to 3 times with exponential backoff
            ValidationError: Response validation failed, no retry
            EmbeddingServiceError: Base exception for other errors
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.embedder_url}/api/v1/generate-embeddings",
                    json={"texts": texts},
                    timeout=30.0,
                )
                response.raise_for_status()

                try:
                    data = response.json()
                except ValueError as e:
                    raise ValidationError(
                        "Failed to parse embedding service response", original_error=e
                    ) from e

                if "embeddings" not in data:
                    raise ValidationError(
                        "Invalid response format: missing 'embeddings' key"
                    )

                embeddings = data["embeddings"]

                if len(embeddings) != len(texts):
                    raise ValidationError(
                        f"Expected {len(texts)} embeddings but got {len(embeddings)}"
                    )

                return embeddings  # type: ignore[no-any-return]

        except httpx.ConnectError as e:
            raise ServiceUnavailableError(
                "Failed to connect to embedding service", original_error=e
            ) from e
        except httpx.TimeoutException as e:
            raise ServiceUnavailableError(
                "Embedding service request timed out", original_error=e
            ) from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                raise ServiceUnavailableError(
                    "Embedding service temporarily unavailable", original_error=e
                ) from e
            raise ValidationError(
                f"Embedding service returned error: {e.response.status_code}",
                original_error=e,
            ) from e
        except (EmbeddingServiceError, ServiceUnavailableError, ValidationError):
            raise
        except Exception as e:
            raise ValidationError(
                f"Unexpected error during embedding generation: {type(e).__name__}",
                original_error=e,
            ) from e
