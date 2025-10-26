"""Qdrant client wrapper for vector operations."""

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, VectorParams

from app.core.config import settings


class QdrantClientWrapper:
    """Wrapper class for Qdrant async client operations."""

    def __init__(self) -> None:
        """Initialize async Qdrant client."""
        self.client = AsyncQdrantClient(url=settings.qdrant_url)
        self.collection_name = "documents"
        self._initialized = False

    async def _ensure_collection(self) -> None:
        """Ensure the documents collection exists with proper configuration."""
        if self._initialized:
            return

        collections = await self.client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if self.collection_name not in collection_names:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=384, distance=Distance.COSINE  # all-MiniLM-L6-v2 dimension
                ),
            )

        self._initialized = True

    async def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float = 0.0,
        document_ids: list[str] | None = None,
    ) -> list[dict[str, object]]:
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
        await self._ensure_collection()

        query_filter = None
        if document_ids:
            query_filter = {
                "must": [{"key": "document_id", "match": {"any": document_ids}}]
            }

        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
            with_payload=True,
        )

        return [
            {"id": str(result.id), "score": result.score, "payload": result.payload}
            for result in results
        ]

    async def delete_by_document_id(self, document_id: str) -> None:
        """
        Delete all vectors associated with a document.

        Args:
            document_id: Document UUID to delete vectors for
        """
        await self._ensure_collection()

        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id", match=MatchValue(value=document_id)
                    )
                ]
            ),
        )

    async def health_check(self) -> bool:
        """
        Check if Qdrant is accessible.

        Returns:
            True if Qdrant is healthy, False otherwise
        """
        try:
            await self.client.get_collections()
            return True
        except Exception:
            return False


# Global Qdrant client instance
qdrant_client = QdrantClientWrapper()
