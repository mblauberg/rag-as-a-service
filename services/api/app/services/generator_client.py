"""Client for Generator service."""
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeneratorClient:
    """Async HTTP client for Generator service."""

    def __init__(self, base_url: str = None):
        """Initialize generator client."""
        self.base_url = base_url or settings.generator_url
        self.timeout = 30.0  # 30 second timeout for generation

    async def generate_summary(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        model: str
    ) -> Optional[Dict[str, Any]]:
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
                "chunk_index": chunk.get("chunk_index", 0)
            }
            for chunk in chunks
        ]

        payload = {
            "query": query,
            "chunks": chunk_inputs,
            "model": model
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    logger.info("Successfully generated summary")
                    return response.json()
                else:
                    logger.warning(f"Generator returned {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Generator request failed: {e}")
            return None

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models from Generator.

        Returns:
            List of model info dictionaries
        """
        url = f"{self.base_url}/api/v1/models"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    return data.get("models", [])
                else:
                    logger.warning(f"Failed to list models: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
