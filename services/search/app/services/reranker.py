"""Cross-encoder reranker using Sentence Transformers.

Extracted from services/api/app/infrastructure/reranking/cross_encoder_reranker.py
and adapted for search service architecture.
"""
import logging
import numpy as np
from sentence_transformers import CrossEncoder

from app.models.domain import Chunk

logger = logging.getLogger(__name__)


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

    async def rerank(self, query: str, chunks: list[Chunk], top_k: int) -> list[Chunk]:
        """Rerank chunks using cross-encoder scores.

        Creates query-chunk pairs and scores them jointly.
        Much more accurate than cosine similarity.

        Attaches normalized cross-encoder relevance scores (0-1) to chunk.score field.
        Uses min-max normalization to map raw scores to [0, 1] range.

        Args:
            query: Search query
            chunks: Candidate chunks
            top_k: Number of top results to return

        Returns:
            Reranked list of top_k chunks with scores
        """
        if not chunks:
            return []

        # Create query-chunk pairs
        pairs = [(query, chunk.content) for chunk in chunks]

        # Score all pairs (batch processing)
        raw_scores = self.model.predict(pairs)

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
