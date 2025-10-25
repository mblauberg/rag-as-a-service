"""
Reciprocal Rank Fusion (RRF) for combining search results.

RRF is a simple and effective method for merging ranked lists without
needing to normalize different scoring schemes.

Formula: score(d) = sum(1 / (k + rank(d)))
where k=60 is the research-proven constant.
"""
from typing import List
from collections import defaultdict
from app.models.document import DocumentChunk


def reciprocal_rank_fusion(
    results_a: List[DocumentChunk],
    results_b: List[DocumentChunk],
    k: int = 60
) -> List[DocumentChunk]:
    """
    Combine two ranked result lists using Reciprocal Rank Fusion.

    Args:
        results_a: First ranked list (e.g., BM25 results)
        results_b: Second ranked list (e.g., vector results)
        k: Constant for RRF formula (default: 60, research-proven)

    Returns:
        Combined list ranked by RRF score
    """
    scores = defaultdict(float)
    chunk_map = {}  # id -> chunk object

    # Score from first list
    for rank, chunk in enumerate(results_a, start=1):
        scores[chunk.id] += 1.0 / (k + rank)
        chunk_map[chunk.id] = chunk

    # Score from second list
    for rank, chunk in enumerate(results_b, start=1):
        scores[chunk.id] += 1.0 / (k + rank)
        chunk_map[chunk.id] = chunk

    # Sort by RRF score (descending)
    sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Return chunks in RRF order
    return [chunk_map[chunk_id] for chunk_id, score in sorted_ids]


def reciprocal_rank_fusion_multi(
    result_sets: List[List[DocumentChunk]],
    k: int = 60
) -> List[DocumentChunk]:
    """
    Combine multiple ranked result lists using RRF.

    Used for query expansion where multiple query variants produce
    multiple result sets.

    Args:
        result_sets: List of ranked result lists
        k: Constant for RRF formula (default: 60)

    Returns:
        Combined list ranked by RRF score
    """
    scores = defaultdict(float)
    chunk_map = {}

    # Accumulate scores from all result sets
    for results in result_sets:
        for rank, chunk in enumerate(results, start=1):
            scores[chunk.id] += 1.0 / (k + rank)
            chunk_map[chunk.id] = chunk

    # Sort by RRF score (descending)
    sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Return chunks in RRF order
    return [chunk_map[chunk_id] for chunk_id, score in sorted_ids]
