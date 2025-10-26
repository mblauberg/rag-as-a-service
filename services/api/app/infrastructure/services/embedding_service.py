"""HTTP-based embedding service adapter implementation."""

import httpx

from app.core.exceptions import EmbeddingServiceError
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

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for texts via HTTP.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (one per input text)

        Raises:
            EmbeddingServiceError: If embedding generation fails
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
                    raise EmbeddingServiceError(
                        "Failed to parse embedding service response", original_error=e
                    )

                # Validate response structure
                if "embeddings" not in data:
                    raise EmbeddingServiceError(
                        "Invalid response format: missing 'embeddings' key"
                    )

                embeddings = data["embeddings"]

                # Validate embedding count matches input count
                if len(embeddings) != len(texts):
                    raise EmbeddingServiceError(
                        f"Expected {len(texts)} embeddings but got {len(embeddings)}"
                    )

                return embeddings  # type: ignore[no-any-return]

        except httpx.ConnectError as e:
            raise EmbeddingServiceError(
                "Failed to connect to embedding service", original_error=e
            )
        except httpx.TimeoutException as e:
            raise EmbeddingServiceError(
                "Embedding service request timed out", original_error=e
            )
        except httpx.HTTPStatusError as e:
            raise EmbeddingServiceError(
                f"Embedding service returned error: {e.response.status_code}",
                original_error=e,
            )
        except EmbeddingServiceError:
            # Re-raise our own exceptions
            raise
        except Exception as e:
            # Catch any other unexpected errors
            raise EmbeddingServiceError(
                f"Unexpected error during embedding generation: {type(e).__name__}",
                original_error=e,
            )
