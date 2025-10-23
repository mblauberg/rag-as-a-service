"""Async client for the embedder service."""
import httpx
from typing import List, Dict
import logging

from app.core.config import settings
from app.models.schemas import EmbedRequest, EmbedResponse, EmbedQueryRequest, EmbedQueryResponse

logger = logging.getLogger(__name__)


class EmbedderClient:
    """Async client for communicating with the embedder service."""

    def __init__(self):
        """Initialize embedder client."""
        self.base_url = settings.embedder_url
        self.timeout = 300.0  # 5 minutes for large batches

    async def embed_chunks(self, chunks_data: List[Dict]) -> bool:
        """
        Send chunks to embedder service for embedding generation.

        Args:
            chunks_data: List of chunk dictionaries with id, text, and metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/embed",
                    json={"chunks": chunks_data}
                )
                response.raise_for_status()
                result = response.json()
                return result.get("success", False)
        except Exception as e:
            logger.error(f"Error embedding chunks: {e}")
            return False

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query text

        Returns:
            Query embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/embed-query",
                    json={"query": query}
                )
                response.raise_for_status()
                result = response.json()
                return result["embedding"]
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise Exception(f"Failed to generate query embedding: {str(e)}")

    async def health_check(self) -> bool:
        """
        Check if embedder service is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


# Global embedder client instance
embedder_client = EmbedderClient()
