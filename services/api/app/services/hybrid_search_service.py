"""
Hybrid search combining BM25 (lexical) and vector (semantic) retrieval.

Uses Reciprocal Rank Fusion to combine results from:
- BM25: PostgreSQL full-text search for keyword matching
- Vector: Qdrant similarity search for semantic matching
"""
import asyncio
from typing import List, Dict, Any, Optional
from uuid import UUID
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.bm25_search import BM25SearchService
from app.services.fusion import reciprocal_rank_fusion
from app.models.document import DocumentChunk
from app.core.qdrant_client import QdrantClientWrapper
from app.core.config import settings


class VectorSearchService:
    """
    Vector search service wrapping Qdrant operations.

    Provides semantic search using embeddings.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        qdrant_client: QdrantClientWrapper,
        http_client: httpx.AsyncClient
    ):
        self.db_session = db_session
        self.qdrant_client = qdrant_client
        self.http_client = http_client

    async def search(
        self,
        query: str,
        limit: int = 20,
        document_ids: Optional[List[UUID]] = None
    ) -> List[DocumentChunk]:
        """
        Search chunks using vector similarity.

        Args:
            query: Search query
            limit: Maximum results to return
            document_ids: Optional filter by document IDs

        Returns:
            List of DocumentChunk objects ranked by similarity
        """
        # Generate query embedding using embedder service
        try:
            response = await self.http_client.post(
                f"{settings.embedder_url}/embed-query",
                json={"query": query},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            query_embedding = result["embedding"]
        except Exception as e:
            # Log error but don't fail - return empty results
            print(f"Embedder service error: {e}")
            return []

        # Search Qdrant
        try:
            document_ids_str = None
            if document_ids:
                document_ids_str = [str(doc_id) for doc_id in document_ids]

            qdrant_results = await self.qdrant_client.search(
                query_vector=query_embedding,
                limit=limit,
                score_threshold=0.0,
                document_ids=document_ids_str
            )
        except Exception as e:
            print(f"Qdrant search error: {e}")
            return []

        # Convert Qdrant results to DocumentChunk objects
        # Note: We're creating minimal chunks with just ID and score
        # The actual chunk data would need to be fetched from DB if needed
        chunks = []
        for qdrant_result in qdrant_results:
            chunk = DocumentChunk(
                id=UUID(qdrant_result["id"]),
                document_id=UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder
                chunk_index=0,
                chunk_text="",  # Will be filled by endpoint if needed
                token_count=0
            )
            # Store vector score as metadata
            chunk.vector_score = qdrant_result.get("score", 0.0)
            chunks.append(chunk)

        return chunks


class HybridSearchService:
    """
    Hybrid search combining:
    - BM25 (PostgreSQL FTS) for lexical matching
    - Vector search (Qdrant) for semantic matching
    - RRF for result fusion
    """

    def __init__(
        self,
        db_session: AsyncSession,
        qdrant_client: QdrantClientWrapper,
        http_client: httpx.AsyncClient
    ):
        self.bm25_service = BM25SearchService(db_session)
        self.vector_service = VectorSearchService(
            db_session,
            qdrant_client,
            http_client
        )

    async def search(
        self,
        query: str,
        limit: int = 10,
        bm25_limit: int = 20,
        vector_limit: int = 20,
        document_ids: Optional[List[UUID]] = None
    ) -> Dict[str, Any]:
        """
        Hybrid search combining BM25 and vector results.

        Args:
            query: Search query
            limit: Final number of results to return
            bm25_limit: Number of BM25 results to retrieve
            vector_limit: Number of vector results to retrieve
            document_ids: Optional filter by document IDs

        Returns:
            Dictionary with results and metadata
        """
        # Execute BM25 and vector searches in parallel
        bm25_task = asyncio.create_task(
            self.bm25_service.search(query, limit=bm25_limit)
        )
        vector_task = asyncio.create_task(
            self.vector_service.search(query, limit=vector_limit, document_ids=document_ids)
        )

        bm25_results, vector_results = await asyncio.gather(bm25_task, vector_task)

        # Fuse results using RRF
        fused_results = reciprocal_rank_fusion(bm25_results, vector_results)

        # Get top-K
        top_results = fused_results[:limit]

        # Calculate overlap
        bm25_ids = set(chunk.id for chunk in bm25_results)
        vector_ids = set(chunk.id for chunk in vector_results)
        overlap_count = len(bm25_ids & vector_ids)

        return {
            "results": top_results,
            "retrieval_method": "hybrid",
            "metadata": {
                "bm25_count": len(bm25_results),
                "vector_count": len(vector_results),
                "overlap_count": overlap_count
            }
        }
