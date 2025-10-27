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
        """Search for semantically similar chunks using vector embeddings.

        Performs Approximate Nearest Neighbor (ANN) search in Qdrant vector
        database using cosine similarity metric. Returns chunks with embeddings
        most similar to the query vector.

        Qdrant uses HNSW (Hierarchical Navigable Small World) index for
        efficient ANN search, providing sub-linear query time even with
        millions of vectors.

        The similarity metric (cosine) measures the angle between query and
        chunk embeddings in high-dimensional space (typically 384 or 768
        dimensions for sentence-transformers models).

        Args:
            query_vector: Dense embedding vector for query, typically generated
                by sentence-transformers model. Must match dimensionality of
                indexed chunk embeddings (e.g., 384-dim for MiniLM).
            top_k: Number of most similar results to return. Defaults to 10.
            document_id: Optional UUID to restrict search to chunks from a
                single document. Uses Qdrant payload filtering.

        Returns:
            List of Chunk objects ordered by cosine similarity (descending).
            Each chunk includes:
            - score: Cosine similarity in range [0, 1] (1.0 = identical)
            - content: Original chunk text
            - document metadata: title, filename, chunk_index

        Note:
            Vector search excels at semantic matching (synonyms, paraphrases)
            but may miss exact keyword matches. For best results, use hybrid
            search combining vector + keyword approaches.

        Example:
            >>> service = VectorSearchService(...)
            >>> query_vec = await embedder.embed("machine learning")
            >>> results = await service.search(query_vec, top_k=10)
            >>> print(f"Top match: {results[0].content[:100]}")
            >>> print(f"Similarity: {results[0].score:.4f}")
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
        chunks: list[Chunk] = []
        for result in results:
            # Ensure result.id is treated as str or int
            result_id = result.id if isinstance(result.id, (str, int)) else str(result.id)
            if isinstance(result_id, int):
                result_id = str(result_id)

            # Handle payload safely
            payload = result.payload if result.payload is not None else {}

            # Extract and validate chunk_index
            chunk_index_val = payload.get("chunk_index")
            chunk_index: int | None = None
            if chunk_index_val is not None:
                chunk_index = int(chunk_index_val)

            # Support both "content" (new) and "text" (legacy) field names for backward compatibility
            content_text = payload.get("content") or payload.get("text", "")

            chunk = Chunk(
                id=UUID(result_id),
                document_id=UUID(str(payload.get("document_id", ""))),
                content=str(content_text),
                tokens=int(payload.get("tokens", 0)),
                score=result.score,
                document_title=str(payload.get("document_title")) if payload.get("document_title") else None,
                document_filename=str(payload.get("document_filename")) if payload.get("document_filename") else None,
                chunk_index=chunk_index
            )
            chunks.append(chunk)

        logger.info(f"Vector search returned {len(chunks)} results")
        return chunks
