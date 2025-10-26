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
        """Execute search with specified mode and optional reranking.

        Orchestrates the complete search pipeline:
        1. Executes search using selected mode (vector, keyword, or hybrid)
        2. Retrieves more candidates (50+) if reranking is enabled
        3. Applies cross-encoder reranking to improve precision
        4. Returns top_k most relevant results

        Hybrid mode (RECOMMENDED) combines semantic and lexical search using
        Reciprocal Rank Fusion (RRF), achieving 18-22% better accuracy than
        single-mode search.

        Reranking uses a cross-encoder (MS MARCO MiniLM) to score query-chunk
        pairs jointly, providing 8-12% improvement in precision@10 over
        bi-encoder similarity alone.

        Extracted from SearchDocumentsUseCase.execute() but simplified:
        - Removed SearchQuery value object (just use string)
        - Removed query expansion (future enhancement)
        - Kept core orchestration logic

        Args:
            query: Search query text (natural language).
            mode: Search mode - VECTOR (semantic), KEYWORD (lexical), or
                HYBRID (fusion of both). Defaults to HYBRID.
            top_k: Number of final results to return. Defaults to 10.
            use_reranking: Enable cross-encoder reranking for higher precision.
                When True, retrieves max(top_k, 50) candidates for reranking.
                Defaults to True.
            use_expansion: Enable query expansion (not implemented yet).
                Reserved for future query reformulation features.
            document_id: Optional UUID to filter results to specific document.
            db_session: AsyncSession for PostgreSQL queries. Required for
                KEYWORD and HYBRID modes, optional for VECTOR.

        Returns:
            List of Chunk objects ranked by relevance score (descending).
            Each chunk includes content, score, and document metadata.

        Raises:
            ValueError: If db_session is None for KEYWORD/HYBRID mode,
                or if mode is invalid.

        Example:
            >>> orchestrator = SearchOrchestrator(...)
            >>> results = await orchestrator.search(
            ...     query="machine learning algorithms",
            ...     mode=SearchMode.HYBRID,
            ...     top_k=10,
            ...     use_reranking=True
            ... )
            >>> print(f"Found {len(results)} results")
            >>> print(f"Top result score: {results[0].score:.4f}")
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
        """Execute semantic vector search using embeddings.

        Generates query embedding via embedder service and searches Qdrant
        vector database for similar document chunks using cosine similarity.

        This is a two-step process:
        1. Generate dense vector representation of query (via sentence-transformers)
        2. Search Qdrant for chunks with similar embeddings (ANN search)

        Extracted from SearchDocumentsUseCase._vector_search()

        Args:
            query: Natural language search query.
            top_k: Number of most similar chunks to retrieve.
            document_id: Optional UUID to restrict search to single document.

        Returns:
            List of chunks ranked by cosine similarity (descending).

        Raises:
            httpx.RequestError: If embedder service unavailable.
            ValueError: If embedder returns invalid response.
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
        """Execute lexical keyword search using PostgreSQL Full-Text Search.

        Uses PostgreSQL's built-in full-text search with ts_rank scoring,
        which provides BM25-like ranking. Good for exact term matching and
        named entity queries (e.g., product codes, person names).

        Extracted from SearchDocumentsUseCase._keyword_search()

        Args:
            query: Keyword query (tokenized by PostgreSQL).
            top_k: Number of top-ranked results to return.
            document_id: Optional UUID to filter to specific document.
            db_session: Active PostgreSQL session for FTS queries.

        Returns:
            List of chunks ranked by PostgreSQL ts_rank (descending).

        Note:
            PostgreSQL FTS creates tsvector from chunk content and searches
            using plainto_tsquery. Ranking is based on term frequency and
            document length normalization.
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
        """Execute hybrid search combining vector and keyword search with RRF fusion.

        Implements the recommended search strategy that achieves 18-22% better
        accuracy than single-mode search:

        1. Retrieve 2*top_k candidates from BOTH vector and keyword search
        2. Fuse results using Reciprocal Rank Fusion (RRF) algorithm
        3. Return top_k fused results

        RRF is rank-based fusion that doesn't require score normalization,
        making it robust to different scoring scales between vector similarity
        and keyword relevance.

        Extracted from SearchDocumentsUseCase._hybrid_search()
        Uses same algorithm: retrieve 2x results from each method for better fusion.

        Args:
            query: Natural language query (used for both vector and keyword).
            top_k: Final number of results after fusion.
            document_id: Optional UUID to filter both searches to same document.
            db_session: PostgreSQL session for keyword search component.

        Returns:
            List of chunks ranked by RRF fusion score (descending).
            Combines semantic relevance (vector) with term matching (keyword).

        Note:
            Retrieving 2*top_k candidates from each method provides better
            diversity for fusion algorithm, improving final result quality.
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
