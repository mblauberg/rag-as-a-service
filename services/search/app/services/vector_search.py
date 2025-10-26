"""Vector search service using Qdrant."""
import logging
from uuid import UUID
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.models.domain import Chunk

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Service for vector similarity search using Qdrant."""

    def __init__(self, qdrant_url: str, collection_name: str):
        """Initialize vector search service.

        Args:
            qdrant_url: Qdrant server URL
            collection_name: Collection name to search
        """
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        # Initialize persistent client to avoid resource leak
        self._client = AsyncQdrantClient(url=self.qdrant_url)

    @property
    def client(self) -> AsyncQdrantClient:
        """Get Qdrant client instance."""
        return self._client

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        document_id: UUID | None = None
    ) -> list[Chunk]:
        """Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            document_id: Optional document filter

        Returns:
            List of chunks ordered by similarity
        """
        client = self.client

        # Build filter if document_id provided
        query_filter = None
        if document_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=str(document_id))
                    )
                ]
            )

        # Execute search
        results = await client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter
        )

        # Convert to Chunk objects
        chunks = []
        for result in results:
            chunk = Chunk(
                id=UUID(result.id),
                document_id=UUID(result.payload["document_id"]),
                content=result.payload["content"],
                tokens=result.payload.get("tokens", 0),
                score=result.score,
                document_title=result.payload.get("document_title"),
                document_filename=result.payload.get("document_filename"),
                chunk_index=result.payload.get("chunk_index")
            )
            chunks.append(chunk)

        logger.info(f"Vector search returned {len(chunks)} results")
        return chunks
