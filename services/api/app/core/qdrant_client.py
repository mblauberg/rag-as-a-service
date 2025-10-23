"""Qdrant client wrapper for vector operations."""
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.core.config import settings


class QdrantClientWrapper:
    """Wrapper class for Qdrant client operations."""

    def __init__(self):
        """Initialize Qdrant client."""
        self.client = QdrantClient(url=settings.qdrant_url)
        self.collection_name = "documents"
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Ensure the documents collection exists with proper configuration."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=384,  # all-MiniLM-L6-v2 dimension
                    distance=Distance.COSINE
                )
            )

    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.0,
        document_ids: Optional[List[str]] = None
    ) -> List[dict]:
        """
        Search for similar vectors in Qdrant.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            document_ids: Optional list of document IDs to filter by

        Returns:
            List of search results with scores and payloads
        """
        query_filter = None
        if document_ids:
            query_filter = {
                "must": [
                    {
                        "key": "document_id",
                        "match": {"any": document_ids}
                    }
                ]
            }

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
            with_payload=True
        )

        return [
            {
                "id": str(result.id),
                "score": result.score,
                "payload": result.payload
            }
            for result in results
        ]

    async def delete_by_document_id(self, document_id: str) -> None:
        """
        Delete all vectors associated with a document.

        Args:
            document_id: Document UUID to delete vectors for
        """
        self.client.delete(
            collection_name=self.collection_name,
            points_selector={
                "filter": {
                    "must": [
                        {
                            "key": "document_id",
                            "match": {"value": document_id}
                        }
                    ]
                }
            }
        )

    def health_check(self) -> bool:
        """
        Check if Qdrant is accessible.

        Returns:
            True if Qdrant is healthy, False otherwise
        """
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False


# Global Qdrant client instance
qdrant_client = QdrantClientWrapper()
