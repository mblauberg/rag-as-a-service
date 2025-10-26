"""Reciprocal Rank Fusion service for combining search results."""
import logging
from collections import defaultdict
from app.models.domain import Chunk

logger = logging.getLogger(__name__)


class RRFFusionService:
    """Reciprocal Rank Fusion (RRF) for merging ranked lists.

    RRF combines multiple ranked lists without score normalization.
    Formula: score(chunk) = sum(1 / (k + rank(chunk)))
    where k=60 is research-proven constant.

    Reference: "Reciprocal rank fusion outperforms condorcet and
    individual rank learning methods" (SIGIR 2009)
    """

    def __init__(self, k: int = 60):
        """Initialize RRF fusion service.

        Args:
            k: RRF constant (default 60, optimal for most cases)
        """
        self.k = k

    def fuse(self, result_sets: list[list[Chunk]]) -> list[Chunk]:
        """Fuse multiple ranked lists using Reciprocal Rank Fusion algorithm.

        Implements RRF (Cormack et al., SIGIR 2009) to merge results from
        different retrieval methods without requiring score normalization:

        For each chunk across all result sets:
            RRF_score = sum(1 / (k + rank_in_list))

        where k=60 is the RRF constant and rank starts at 1.

        RRF is particularly effective for hybrid search because:
        - No score normalization needed (vector scores vs keyword scores)
        - Robust to outliers in individual rankings
        - Balances contribution from all result sets
        - Research-proven to outperform Condorcet and score-based fusion

        Args:
            result_sets: List of ranked chunk lists to fuse. Each list should
                be pre-sorted by descending relevance. Can come from different
                retrieval methods (e.g., [vector_results, keyword_results]).

        Returns:
            Single fused list of unique chunks, sorted by RRF score (descending).
            Chunks appearing in multiple input lists receive higher scores due
            to additive RRF formula.

        Example:
            >>> fusion = RRFFusionService(k=60)
            >>> vector_results = [chunk1, chunk2, chunk3]
            >>> keyword_results = [chunk2, chunk4, chunk1]
            >>> fused = fusion.fuse([vector_results, keyword_results])
            >>> # chunk2 and chunk1 rank higher (appear in both lists)
        """
        if not result_sets:
            return []

        if len(result_sets) == 1:
            return result_sets[0]

        # Accumulate RRF scores
        scores: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, Chunk] = {}

        for result_set in result_sets:
            for rank, chunk in enumerate(result_set, start=1):
                chunk_key = str(chunk.id)
                # RRF formula: 1 / (k + rank)
                scores[chunk_key] += 1.0 / (self.k + rank)
                chunk_map[chunk_key] = chunk

        # Sort by RRF score (descending)
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Build result list
        fused_chunks = [chunk_map[chunk_id] for chunk_id, _ in sorted_ids]

        logger.info(
            f"Fused {len(result_sets)} result sets into {len(fused_chunks)} unique chunks"
        )

        return fused_chunks
