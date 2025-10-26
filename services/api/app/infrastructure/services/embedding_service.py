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
        """Generate vector embeddings via embedder microservice with retry logic.

        Calls the embedder service to generate dense vector representations
        of text using sentence-transformers models (e.g., all-MiniLM-L6-v2).

        Implements resilient retry logic with exponential backoff:
        - Retries up to 3 times on service unavailability (503 errors)
        - Exponential backoff: 2s, 4s, 8s (max 10s between retries)
        - Immediate failure for validation errors (no retry)

        The embedder service uses CPU-optimized sentence-transformers for
        batch embedding generation, supporting various model architectures
        (MiniLM, BERT, RoBERTa, etc.).

        Args:
            texts: List of text strings to embed (chunks, queries, etc.).
                Sent to embedder service in batch for efficiency.

        Returns:
            List of embedding vectors (one per input text). Each vector is
            a list of floats with dimensionality matching the model
            (e.g., 384 for all-MiniLM-L6-v2, 768 for BERT-base).

        Raises:
            ServiceUnavailableError: If embedder service unavailable after
                3 retry attempts. Includes original httpx exception.
            ValidationError: If request validation fails, response parsing
                fails, or embedding count doesn't match input count.
                These errors do NOT trigger retry.
            EmbeddingServiceError: Base exception for other embedding errors.

        Note:
            The @retry decorator automatically retries on ServiceUnavailableError.
            ValidationError is used to prevent retry for non-transient failures.

        Example:
            >>> service = HTTPEmbeddingService("http://embedder:8001")
            >>> embeddings = await service.generate_embeddings(
            ...     ["hello world", "semantic search"]
            ... )
            >>> print(f"Generated {len(embeddings)} embeddings")
            >>> print(f"Dimension: {len(embeddings[0])}")
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
