"""Cross-encoder reranker using Sentence Transformers.

Extracted from services/api/app/infrastructure/reranking/cross_encoder_reranker.py
and adapted for search service architecture.
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sentence_transformers import CrossEncoder

from app.models.domain import Chunk

logger = logging.getLogger(__name__)

# Shared thread pool for CPU-intensive reranking operations
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="reranker")


class CrossEncoderReranker:
    """Cross-encoder based reranking.

    Uses BERT-based cross-encoder to compute query-document
    relevance scores. More accurate but slower than bi-encoders.

    Recommended for reranking top-50 to top-10.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Initialize cross-encoder model.

        Args:
            model_name: HuggingFace cross-encoder model
                       (default: MS MARCO MiniLM - fast and accurate)
        """
        logger.info(f"Loading cross-encoder model: {model_name}")
        self.model = CrossEncoder(model_name, device='cpu')
        logger.info("Cross-encoder model loaded")

    def _compute_scores(self, pairs: list[tuple[str, str]]) -> np.ndarray:
        """Compute cross-encoder scores in thread pool.

        This is CPU-intensive, so we run it in a thread executor
        to avoid blocking the async event loop.

        Args:
            pairs: List of (query, chunk) pairs

        Returns:
            Array of raw scores
        """
        return self.model.predict(pairs)

    async def rerank(self, query: str, chunks: list[Chunk], top_k: int) -> list[Chunk]:
        """Rerank chunks using cross-encoder for improved precision.

        Implements two-stage retrieval (bi-encoder + cross-encoder):
        1. First-stage retrieval uses fast bi-encoder (sentence-transformers)
           to retrieve candidate chunks (~50-100 results)
        2. Second-stage reranking uses slower but more accurate cross-encoder
           to precisely score query-chunk relevance

        Cross-encoders process query and chunk text JOINTLY through BERT,
        enabling attention between query and document tokens. This provides
        8-12% improvement in precision@10 over bi-encoder cosine similarity.

        The MS MARCO MiniLM cross-encoder is optimized for passage ranking and
        trained on millions of query-passage pairs from Bing search logs.

        Technical details:
        - Creates (query, chunk_text) pairs for batch scoring
        - Runs CPU-intensive BERT inference in thread pool (non-blocking)
        - Applies min-max normalization to map raw scores to [0, 1]
        - Attaches normalized scores to chunk.score field

        Args:
            query: Search query text (natural language).
            chunks: Candidate chunks from first-stage retrieval. Typically
                50-100 chunks retrieved by bi-encoder or hybrid search.
            top_k: Number of top-scored results to return after reranking.

        Returns:
            List of top_k chunks sorted by cross-encoder relevance score
            (descending). Each chunk.score contains normalized relevance in
            range [0, 1], where 1.0 is most relevant.

        Note:
            CPU-intensive model inference runs in thread executor to avoid
            blocking the async event loop. This allows concurrent request
            processing while reranking is in progress.

        Example:
            >>> reranker = CrossEncoderReranker()
            >>> candidates = await vector_search(query, top_k=50)
            >>> reranked = await reranker.rerank(query, candidates, top_k=10)
            >>> print(f"Top result score: {reranked[0].score:.4f}")
        """
        if not chunks:
            return []

        # Create query-chunk pairs
        pairs = [(query, chunk.content) for chunk in chunks]

        # Score all pairs (batch processing) in thread executor
        loop = asyncio.get_running_loop()
        raw_scores = await loop.run_in_executor(_executor, self._compute_scores, pairs)

        # Normalize scores to 0-1 range using min-max normalization
        min_score = float(np.min(raw_scores))
        max_score = float(np.max(raw_scores))
        score_range = max_score - min_score

        if score_range > 0:
            normalized_scores = [(s - min_score) / score_range for s in raw_scores]
        else:
            # All scores identical - assign 1.0 to all
            normalized_scores = [1.0] * len(raw_scores)

        # Sort by normalized score (descending) and attach scores
        chunk_scores = list(zip(chunks, normalized_scores))
        chunk_scores.sort(key=lambda x: x[1], reverse=True)

        # Attach normalized scores to chunks and return top_k
        reranked_chunks = []
        for chunk, score in chunk_scores[:top_k]:
            chunk.score = float(score)
            reranked_chunks.append(chunk)

        logger.info(f"Reranked {len(chunks)} chunks to top {len(reranked_chunks)}")
        return reranked_chunks
