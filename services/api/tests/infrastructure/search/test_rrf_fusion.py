"""Tests for RRF fusion service."""
from uuid import uuid4

import pytest

from app.domain.entities.chunk import Chunk
from app.infrastructure.search.rrf_fusion_service import RRFFusionServiceImpl


def test_rrf_fusion_combines_two_lists():
    """Test RRF correctly fuses two ranked lists."""
    # Create test chunks
    chunk_a = Chunk(id=uuid4(), document_id=uuid4(), content="A", tokens=1)
    chunk_b = Chunk(id=uuid4(), document_id=uuid4(), content="B", tokens=1)
    chunk_c = Chunk(id=uuid4(), document_id=uuid4(), content="C", tokens=1)

    # List 1: A, B, C
    # List 2: C, A, B
    # RRF should favor A and C (appear in both top positions)

    list1 = [chunk_a, chunk_b, chunk_c]
    list2 = [chunk_c, chunk_a, chunk_b]

    service = RRFFusionServiceImpl()
    fused = service.fuse([list1, list2], k=60)

    # A and C should be top 2
    assert chunk_a in fused[:2]
    assert chunk_c in fused[:2]


def test_rrf_fusion_handles_empty_lists():
    """Test RRF handles empty result sets gracefully."""
    service = RRFFusionServiceImpl()

    fused = service.fuse([[], []], k=60)

    assert fused == []


def test_rrf_fusion_deduplicates_chunks():
    """Test RRF deduplicates chunks appearing in multiple lists."""
    chunk_a = Chunk(id=uuid4(), document_id=uuid4(), content="A", tokens=1)

    # Same chunk in both lists
    list1 = [chunk_a]
    list2 = [chunk_a]

    service = RRFFusionServiceImpl()
    fused = service.fuse([list1, list2], k=60)

    # Should appear once with combined score
    assert len(fused) == 1
    assert fused[0].id == chunk_a.id


def test_rrf_fusion_raises_error_for_unsupported_method():
    """Test that unsupported fusion methods raise ValueError."""
    service = RRFFusionServiceImpl()
    chunk = Chunk(id=uuid4(), document_id=uuid4(), content="test", tokens=1)

    with pytest.raises(ValueError, match="Unsupported fusion method: weighted"):
        service.fuse([[chunk]], method="weighted", k=60)
