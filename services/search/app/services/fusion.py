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
        """Fuse multiple ranked lists using RRF.

        Args:
            result_sets: List of ranked chunk lists to fuse

        Returns:
            Single fused list ranked by RRF score
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
