"""Main search orchestrator coordinating all search operations.

Extracted from services/api/app/application/use_cases/search_documents.py
and adapted for search service architecture (removed hexagonal architecture patterns).
"""
import httpx
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Chunk
from app.models.schemas import SearchMode
from app.services.vector_search import VectorSearchService
from app.services.keyword_search import KeywordSearchService
from app.services.fusion import RRFFusionService
from app.services.reranker import CrossEncoderReranker

logger = logging.getLogger(__name__)


class EmbedderClient:
    """Client for embedder service."""

    def __init__(self, embedder_url: str, timeout: float = 30.0):
        """Initialize embedder client.

        Args:
            embedder_url: Base URL of embedder service
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.embedder_url = embedder_url
        self.timeout = timeout

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text via embedder service.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.embedder_url}/api/v1/generate-embeddings",
                json={"texts": [text]},
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            embeddings = data.get("embeddings")
            if not isinstance(embeddings, list) or len(embeddings) == 0:
                raise ValueError("Invalid embedding response from embedder service")
            first_embedding = embeddings[0]
            if not isinstance(first_embedding, list):
                raise ValueError("Invalid embedding format")
            return first_embedding


class SearchOrchestrator:
    """Main orchestrator for search operations.

    Coordinates vector search, keyword search, fusion, and reranking.

    Supports three search modes (from API's SearchDocumentsUseCase):
    - VECTOR: Pure semantic search using embeddings
    - KEYWORD: Pure lexical/BM25 search using PostgreSQL FTS
    - HYBRID: Combines both with RRF fusion (RECOMMENDED, +18-22% accuracy)
    """

    def __init__(
        self,
        vector_service: VectorSearchService,
        keyword_service: KeywordSearchService,
        fusion_service: RRFFusionService,
        reranker: CrossEncoderReranker,
        embedder_client: EmbedderClient,
    ):
        """Initialize search orchestrator.

        Args:
            vector_service: Vector search service
            keyword_service: Keyword search service
            fusion_service: RRF fusion service
            reranker: Cross-encoder reranker
            embedder_client: Client for embedder service
        """
        self.vector_service = vector_service
        self.keyword_service = keyword_service
        self.fusion_service = fusion_service
        self.reranker = reranker
        self.embedder_client = embedder_client

    async def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.HYBRID,
        top_k: int = 10,
        use_reranking: bool = True,
        use_expansion: bool = False,
        document_id: UUID | None = None,
        db_session: AsyncSession | None = None,
    ) -> list[Chunk]:
        """Execute search with specified mode and options.

        Extracted from SearchDocumentsUseCase.execute() but simplified:
        - Removed SearchQuery value object (just use string)
        - Removed query expansion (future enhancement)
        - Kept core orchestration logic

        Args:
            query: Search query text
            mode: Search mode (vector/keyword/hybrid)
            top_k: Number of final results
            use_reranking: Enable cross-encoder reranking
            use_expansion: Enable query expansion (not implemented yet)
            document_id: Optional document filter
            db_session: Database session (required for keyword/hybrid)

        Returns:
            Ranked list of chunks
        """
        # Determine retrieval k for reranking (from API's logic)
        retrieval_k = top_k
        if use_reranking:
            retrieval_k = max(top_k, 50)  # Get more candidates for reranking

        logger.info(
            f"Search: query='{query[:50]}', mode={mode}, top_k={top_k}, "
            f"reranking={use_reranking}, retrieval_k={retrieval_k}"
        )

        # Execute search based on mode
        if mode == SearchMode.VECTOR:
            initial_results = await self._vector_search(query, retrieval_k, document_id)
        elif mode == SearchMode.KEYWORD:
            if not db_session:
                raise ValueError("Database session required for keyword search")
            initial_results = await self._keyword_search(
                query, retrieval_k, document_id, db_session
            )
        elif mode == SearchMode.HYBRID:
            if not db_session:
                raise ValueError("Database session required for hybrid search")
            initial_results = await self._hybrid_search(
                query, retrieval_k, document_id, db_session
            )
        else:
            raise ValueError(f"Unknown search mode: {mode}")

        # Apply reranking if enabled (from API's logic)
        if use_reranking and len(initial_results) > 0:
            final_results = await self.reranker.rerank(query, initial_results, top_k)
            logger.info(f"Reranked {len(initial_results)} to {len(final_results)} results")
        else:
            final_results = initial_results[:top_k]

        return final_results

    async def _vector_search(
        self, query: str, top_k: int, document_id: UUID | None
    ) -> list[Chunk]:
        """Execute vector-only search.

        Extracted from SearchDocumentsUseCase._vector_search()
        """
        # Generate query embedding
        query_vector = await self.embedder_client.generate_embedding(query)

        # Search Qdrant
        results = await self.vector_service.search(query_vector, top_k, document_id)

        logger.info(f"Vector search: {len(results)} results")
        return results

    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        document_id: UUID | None,
        db_session: AsyncSession,
    ) -> list[Chunk]:
        """Execute keyword-only search.

        Extracted from SearchDocumentsUseCase._keyword_search()
        """
        results = await self.keyword_service.search(db_session, query, top_k, document_id)

        logger.info(f"Keyword search: {len(results)} results")
        return results

    async def _hybrid_search(
        self,
        query: str,
        top_k: int,
        document_id: UUID | None,
        db_session: AsyncSession,
    ) -> list[Chunk]:
        """Execute hybrid search with RRF fusion.

        Extracted from SearchDocumentsUseCase._hybrid_search()
        Uses same algorithm: retrieve 2x results from each method for better fusion.
        """
        # Retrieve 2x results from each method for better fusion
        retrieval_k = top_k * 2

        # Parallel retrieval (semantic + lexical)
        vector_results = await self._vector_search(query, retrieval_k, document_id)
        keyword_results = await self.keyword_service.search(
            db_session, query, retrieval_k, document_id
        )

        logger.info(
            f"Hybrid retrieval: {len(vector_results)} vector, "
            f"{len(keyword_results)} keyword"
        )

        # Fuse with RRF
        fused_results = self.fusion_service.fuse([vector_results, keyword_results])

        # Return top_k after fusion
        final_results = fused_results[:top_k]

        logger.info(f"Hybrid search: {len(final_results)} fused results")
        return final_results
