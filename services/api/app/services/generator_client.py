"""Client for Generator service."""
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import GenerationServiceError

logger = logging.getLogger(__name__)


class GeneratorClient:
    """Async HTTP client for Generator service."""

    def __init__(self, base_url: str | None = None):
        """Initialize generator client."""
        self.base_url = base_url or settings.generator.url
        self.timeout = 30.0  # 30 second timeout for generation

    async def generate_summary(
        self, query: str, chunks: list[dict[str, Any]], model: str
    ) -> dict[str, Any] | None:
        """
        Generate summary from chunks.

        Args:
            query: Search query
            chunks: Retrieved chunks with text, document_id, chunk_index
            model: Model to use for generation

        Returns:
            Generation response or None if failed
        """
        url = f"{self.base_url}/api/v1/generate"

        # Format chunks for generator
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
                else:
                    logger.warning(f"Generator returned {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Generator request failed: {e}")
            return None

    async def generate(
        self, prompt: str, max_tokens: int = 150, temperature: float = 0.3
    ) -> Any | None:
        """
        Generate text from a prompt using the generator service.

        Args:
            prompt: Text prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Generation response object with 'text' attribute, or None if failed
        """
        url = f"{self.base_url}/api/v1/generate"

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
                    # Return object with 'text' attribute for compatibility
                    return type(
                        "GenerateResponse", (), {"text": result.get("text", "")}
                    )()
                else:
                    logger.warning(f"Generator returned {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Generator request failed: {e}")
            return None

    async def list_models(self) -> list[dict[str, Any]]:
        """
        List available models from Generator.

        Returns:
            List of model info dictionaries

        Raises:
            GenerationServiceError: If the generator service is unavailable or returns an error
        """
        url = f"{self.base_url}/api/v1/models"

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    return data.get("models", [])  # type: ignore[no-any-return]
                else:
                    logger.warning(f"Failed to list models: {response.status_code}")
                    raise GenerationServiceError(
                        operation="list_models",
                        original_error=Exception(f"HTTP {response.status_code}")
                    )

        except httpx.HTTPError as e:
            logger.error(f"Failed to list models: {e}")
            raise GenerationServiceError(
                operation="list_models",
                original_error=e
            )
        except GenerationServiceError:
            # Re-raise our custom exception
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing models: {e}")
            raise GenerationServiceError(
                operation="list_models",
                original_error=e
            )
