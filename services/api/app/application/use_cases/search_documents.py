"""Search documents use case."""
import logging
from enum import Enum

from app.domain.entities.chunk import Chunk
from app.domain.value_objects.search_query import SearchQuery
from app.ports.services import (
    EmbeddingService,
    VectorStore,
    KeywordStore,
    FusionService,
    QueryAugmenter
)

logger = logging.getLogger(__name__)


class SearchMode(str, Enum):
    """Search mode selection."""
    VECTOR = "vector"      # Semantic only
    KEYWORD = "keyword"    # BM25 only
    HYBRID = "hybrid"      # RRF fusion (RECOMMENDED)


class SearchDocumentsUseCase:
    """Use case for document search with hybrid retrieval.

    Supports three search modes:
    - VECTOR: Pure semantic search
    - KEYWORD: Pure lexical/BM25 search
    - HYBRID: Combines both with RRF fusion (DEFAULT)

    Hybrid search provides 18-22% accuracy improvement over
    vector-only search according to 2025 research.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        keyword_store: KeywordStore | None = None,
        fusion_service: FusionService | None = None,
        query_augmenter: QueryAugmenter | None = None
    ):
        """Initialize with required dependencies.

        Args:
            embedding_service: For query embedding
            vector_store: For semantic search
            keyword_store: For BM25 search (optional, required for hybrid)
            fusion_service: For result fusion (optional, required for hybrid)
            query_augmenter: For query expansion (optional, for multi-query search)
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.keyword_store = keyword_store
        self.fusion_service = fusion_service
        self.query_augmenter = query_augmenter

    async def execute(
        self,
        query: SearchQuery,
        mode: SearchMode = SearchMode.HYBRID,
        use_expansion: bool = True,
        fusion_k: int = 60
    ) -> list[Chunk]:
        """Execute document search with specified mode and optional query expansion.

        Args:
            query: Search query value object
            mode: Search mode (vector/keyword/hybrid)
            use_expansion: Enable multi-query expansion (default True)
            fusion_k: RRF constant for hybrid mode (default 60)

        Returns:
            List of relevant chunks ordered by relevance

        Raises:
            ValueError: If hybrid mode requested but dependencies missing
        """
        logger.info(
            f"Searching: '{query.text}' "
            f"(mode={mode}, top_k={query.top_k}, expansion={use_expansion})"
        )

        # Query expansion if enabled and available
        if use_expansion and self.query_augmenter:
            expanded_queries = await self.query_augmenter.expand(
                query.text,
                num_variants=2
            )

            # Search with each query variant
            all_result_sets = []
            for q_text in expanded_queries:
                variant_query = SearchQuery(text=q_text, top_k=query.top_k)

                if mode == SearchMode.HYBRID:
                    results = await self._hybrid_search(variant_query, fusion_k)
                elif mode == SearchMode.VECTOR:
                    results = await self._vector_search(variant_query)
                else:  # KEYWORD
                    results = await self._keyword_search(variant_query)

                all_result_sets.append(results)

            # Fuse all expanded query results
            if self.fusion_service and len(all_result_sets) > 1:
                final_results = self.fusion_service.fuse(
                    result_sets=all_result_sets,
                    k=fusion_k
                )[:query.top_k]
            else:
                final_results = all_result_sets[0][:query.top_k]

            logger.info(
                f"Multi-query search: {len(expanded_queries)} queries, "
                f"{len(final_results)} final results"
            )

            return final_results

        # Standard search without expansion
        if mode == SearchMode.VECTOR:
            return await self._vector_search(query)

        elif mode == SearchMode.KEYWORD:
            return await self._keyword_search(query)

        elif mode == SearchMode.HYBRID:
            return await self._hybrid_search(query, fusion_k)

        else:
            raise ValueError(f"Unknown search mode: {mode}")

    async def _vector_search(self, query: SearchQuery) -> list[Chunk]:
        """Pure semantic search using embeddings."""
        query_embeddings = await self.embedding_service.generate_embeddings(
            [query.text]
        )
        query_vector = query_embeddings[0]

        results = await self.vector_store.search(
            query_vector=query_vector,
            top_k=query.top_k
        )

        logger.info(f"Vector search: {len(results)} results")
        return results

    async def _keyword_search(self, query: SearchQuery) -> list[Chunk]:
        """Pure lexical search using BM25."""
        if self.keyword_store is None:
            raise ValueError("KeywordStore not configured")

        results = await self.keyword_store.search(
            query_text=query.text,
            top_k=query.top_k
        )

        logger.info(f"Keyword search: {len(results)} results")
        return results

    async def _hybrid_search(
        self,
        query: SearchQuery,
        fusion_k: int
    ) -> list[Chunk]:
        """Hybrid search combining vector and keyword with RRF fusion.

        Retrieves 2x results from each method, then fuses to top_k.
        This ensures better coverage before fusion.
        """
        if self.keyword_store is None or self.fusion_service is None:
            raise ValueError("Hybrid search requires KeywordStore and FusionService")

        # Retrieve 2x results from each method for better fusion
        retrieval_k = query.top_k * 2

        # Parallel retrieval (semantic + lexical)
        vector_results = await self._vector_search(
            SearchQuery(text=query.text, top_k=retrieval_k)
        )
        keyword_results = await self.keyword_store.search(
            query_text=query.text,
            top_k=retrieval_k
        )

        logger.info(
            f"Hybrid retrieval: {len(vector_results)} vector, "
            f"{len(keyword_results)} keyword"
        )

        # Fuse with RRF
        fused_results = self.fusion_service.fuse(
            result_sets=[vector_results, keyword_results],
            method="rrf",
            k=fusion_k
        )

        # Return top_k after fusion
        final_results = fused_results[:query.top_k]

        logger.info(f"Hybrid search: {len(final_results)} final results")
        return final_results
