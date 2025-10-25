import pytest
from app.services.fusion import reciprocal_rank_fusion, reciprocal_rank_fusion_multi
from app.models.document import DocumentChunk


def test_reciprocal_rank_fusion_combines_rankings():
    """Test RRF combines two result sets with proper scoring"""
    # Create mock chunks
    chunk_a = DocumentChunk(id=1, document_id=1, chunk_index=0, chunk_text="A")
    chunk_b = DocumentChunk(id=2, document_id=1, chunk_index=1, chunk_text="B")
    chunk_c = DocumentChunk(id=3, document_id=1, chunk_index=2, chunk_text="C")
    chunk_d = DocumentChunk(id=4, document_id=1, chunk_index=3, chunk_text="D")

    # Ranking 1: A, B, C
    results_1 = [chunk_a, chunk_b, chunk_c]

    # Ranking 2: C, D, A
    results_2 = [chunk_c, chunk_d, chunk_a]

    # RRF should favor A and C (appear in both lists)
    fused = reciprocal_rank_fusion(results_1, results_2, k=60)

    # A and C should rank higher (appear in both)
    fused_ids = [chunk.id for chunk in fused]

    # C appears high in both lists, should be first or second
    assert 3 in fused_ids[:2]

    # A appears in both lists
    assert 1 in fused_ids[:3]


def test_reciprocal_rank_fusion_multi():
    """Test RRF with multiple result sets (query expansion)"""
    chunk_a = DocumentChunk(id=1, document_id=1, chunk_index=0, chunk_text="A")
    chunk_b = DocumentChunk(id=2, document_id=1, chunk_index=1, chunk_text="B")
    chunk_c = DocumentChunk(id=3, document_id=1, chunk_index=2, chunk_text="C")

    results_1 = [chunk_a, chunk_b]
    results_2 = [chunk_b, chunk_c]
    results_3 = [chunk_a, chunk_c]

    fused = reciprocal_rank_fusion_multi([results_1, results_2, results_3], k=60)

    # All chunks appear in at least 2 lists, but B appears high in 2
    # A appears first in 2 lists
    fused_ids = [chunk.id for chunk in fused]

    assert len(fused_ids) == 3
    # A or B should be first (both appear in multiple lists at high ranks)
    assert fused_ids[0] in [1, 2]


def test_reciprocal_rank_fusion_with_empty_lists():
    """Test RRF handles empty input lists gracefully"""
    chunk_a = DocumentChunk(id=1, document_id=1, chunk_index=0, chunk_text="A")

    results_1 = [chunk_a]
    results_2 = []

    fused = reciprocal_rank_fusion(results_1, results_2, k=60)

    assert len(fused) == 1
    assert fused[0].id == 1


def test_reciprocal_rank_fusion_with_single_result():
    """Test RRF with only one result in each list"""
    chunk_a = DocumentChunk(id=1, document_id=1, chunk_index=0, chunk_text="A")
    chunk_b = DocumentChunk(id=2, document_id=1, chunk_index=1, chunk_text="B")

    results_1 = [chunk_a]
    results_2 = [chunk_b]

    fused = reciprocal_rank_fusion(results_1, results_2, k=60)

    assert len(fused) == 2
    # Both should have same score since they're both rank 1
    assert set([c.id for c in fused]) == {1, 2}


def test_reciprocal_rank_fusion_multi_with_empty_list():
    """Test multi-set RRF handles empty lists in the set"""
    chunk_a = DocumentChunk(id=1, document_id=1, chunk_index=0, chunk_text="A")
    chunk_b = DocumentChunk(id=2, document_id=1, chunk_index=1, chunk_text="B")

    results_1 = [chunk_a]
    results_2 = []
    results_3 = [chunk_b]

    fused = reciprocal_rank_fusion_multi([results_1, results_2, results_3], k=60)

    assert len(fused) == 2
    assert set([c.id for c in fused]) == {1, 2}


def test_reciprocal_rank_fusion_score_calculation():
    """Test that RRF scores are calculated correctly"""
    chunk_a = DocumentChunk(id=1, document_id=1, chunk_index=0, chunk_text="A")
    chunk_b = DocumentChunk(id=2, document_id=1, chunk_index=1, chunk_text="B")

    # A is rank 1 in both lists: score = 2 * (1/(60+1)) = 2/61
    # B is rank 2 in both lists: score = 2 * (1/(60+2)) = 2/62
    results_1 = [chunk_a, chunk_b]
    results_2 = [chunk_a, chunk_b]

    fused = reciprocal_rank_fusion(results_1, results_2, k=60)

    # A should be first (higher score)
    assert fused[0].id == 1
    assert fused[1].id == 2
