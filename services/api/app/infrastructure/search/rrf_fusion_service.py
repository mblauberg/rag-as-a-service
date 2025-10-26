"""Reciprocal Rank Fusion implementation for result fusion."""
from collections import defaultdict

from app.domain.entities.chunk import Chunk
from app.ports.services import FusionService


class RRFFusionServiceImpl(FusionService):
    """Reciprocal Rank Fusion (RRF) implementation.

    RRF combines multiple ranked lists without needing score normalization.
    Formula: score(d) = sum(1 / (k + rank(d)))
    where k=60 is the research-proven constant.

    Reference: "Reciprocal rank fusion outperforms condorcet and
    individual rank learning methods" (SIGIR 2009)
    """

    def fuse(
        self, result_sets: list[list[Chunk]], method: str = "rrf", k: int = 60
    ) -> list[Chunk]:
        """Fuse multiple ranked lists using RRF.

        Args:
            result_sets: List of ranked chunk lists
            method: Fusion algorithm (only "rrf" supported now)
            k: RRF constant (60 is optimal for most cases)

        Returns:
            Single fused list ranked by RRF score
        """
        if method != "rrf":
            raise ValueError(f"Unsupported fusion method: {method}")

        scores = defaultdict(float)
        chunk_map = {}  # id -> chunk object

        # Accumulate RRF scores from all result sets
        for results in result_sets:
            for rank, chunk in enumerate(results, start=1):
                # RRF formula: 1 / (k + rank)
                scores[chunk.id] += 1.0 / (k + rank)
                chunk_map[chunk.id] = chunk

        # Sort by RRF score (descending)
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Return chunks in RRF order
        return [chunk_map[chunk_id] for chunk_id, _ in sorted_ids]
