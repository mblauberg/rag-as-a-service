"""Client for Generator service."""
import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.exceptions import GenerationServiceError, ServiceUnavailableError

logger = logging.getLogger(__name__)


class GeneratorClient:
    """Async HTTP client for Generator service."""

    def __init__(self, base_url: str | None = None):
        """Initialize generator client."""
        self.base_url = base_url or settings.generator.url
        self.timeout = 30.0  # 30 second timeout for generation

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ServiceUnavailableError),
    )
    async def generate_summary(
        self, query: str, chunks: list[dict[str, Any]], model: str
    ) -> dict[str, Any] | None:
        """Generate summary from chunks with retry logic.

        Args:
            query: Search query
            chunks: Retrieved chunks with text, document_id, chunk_index
            model: Model to use for generation

        Returns:
            Generation response or None if failed

        Raises:
            ServiceUnavailableError: Retried up to 3 times with exponential backoff
        """
        url = f"{self.base_url}/api/v1/generate/"

        chunk_inputs = [
            {
                "text": chunk["text"],
                "document_id": chunk["document_id"],
                "chunk_index": chunk.get("chunk_index", 0),
            }
            for chunk in chunks
        ]

        payload = {"query": query, "chunks": chunk_inputs, "model": model}

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True
            ) as client:
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    logger.info("Successfully generated summary")
                    return response.json()  # type: ignore[no-any-return]
                elif response.status_code == 503:
                    logger.warning("Generator service temporarily unavailable")
                    raise ServiceUnavailableError(
                        "Generator service temporarily unavailable"
                    )
                else:
                    logger.warning(f"Generator returned {response.status_code}")
                    return None

        except ServiceUnavailableError:
            raise
        except httpx.ConnectError as e:
            logger.error(f"Connection to generator failed: {e}")
            raise ServiceUnavailableError(
                "Unable to reach generator service", original_error=e
            ) from e
        except httpx.TimeoutException as e:
            logger.error(f"Generator request exceeded timeout: {e}")
            raise ServiceUnavailableError(
                "Generator service did not respond in time", original_error=e
            ) from e
        except Exception as e:
            logger.error(f"Generator request failed: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ServiceUnavailableError),
    )
    async def generate(
        self, prompt: str, max_tokens: int = 150, temperature: float = 0.3
    ) -> Any | None:
        """Generate text from a prompt with retry logic.

        Args:
            prompt: Text prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generation response object with 'text' attribute, or None if failed

        Raises:
            ServiceUnavailableError: Retried up to 3 times with exponential backoff
        """
        url = f"{self.base_url}/api/v1/generate/"

        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True
            ) as client:
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    result = response.json()
                    return type(
                        "GenerateResponse", (), {"text": result.get("text", "")}
                    )()
                elif response.status_code == 503:
                    logger.warning("Generator service temporarily unavailable")
                    raise ServiceUnavailableError(
                        "Generator service temporarily unavailable"
                    )
                else:
                    logger.warning(f"Generator returned {response.status_code}")
                    return None

        except ServiceUnavailableError:
            raise
        except httpx.ConnectError as e:
            logger.error(f"Generator connection failed: {e}")
            raise ServiceUnavailableError(
                "Cannot establish connection to generator", original_error=e
            ) from e
        except httpx.TimeoutException as e:
            logger.error(f"Request to generator timed out: {e}")
            raise ServiceUnavailableError(
                "No response from generator service", original_error=e
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error in generation: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ServiceUnavailableError),
    )
    async def list_models(self) -> list[dict[str, Any]]:
        """List available models from Generator with retry logic.

        Returns:
            List of model info dictionaries

        Raises:
            ServiceUnavailableError: Retried up to 3 times with exponential backoff
            GenerationServiceError: Generator service returned an error
        """
        url = f"{self.base_url}/api/v1/models/"

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    return data.get("models", [])  # type: ignore[no-any-return]
                elif response.status_code == 503:
                    logger.warning("Generator service temporarily unavailable")
                    raise ServiceUnavailableError(
                        "Generator service temporarily unavailable"
                    )
                else:
                    logger.warning(f"Failed to list models: {response.status_code}")
                    raise GenerationServiceError(
                        operation="list_models",
                        original_error=Exception(f"HTTP {response.status_code}")
                    )

        except ServiceUnavailableError:
            raise
        except httpx.ConnectError as e:
            logger.error(f"Could not reach generator service: {e}")
            raise ServiceUnavailableError(
                "Generator service connection unavailable", original_error=e
            ) from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout while listing models: {e}")
            raise ServiceUnavailableError(
                "Generator took too long to respond", original_error=e
            ) from e
        except GenerationServiceError:
            raise
        except Exception as e:
            logger.error(f"Model listing failed unexpectedly: {e}")
            raise GenerationServiceError(
                operation="list_models",
                original_error=e
            ) from e
