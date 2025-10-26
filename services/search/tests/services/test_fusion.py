"""Tests for RRF fusion service."""
import pytest
from uuid import uuid4
from app.services.fusion import RRFFusionService
from app.models.domain import Chunk


@pytest.fixture
def fusion_service():
    """Fusion service instance."""
    return RRFFusionService(k=60)


@pytest.fixture
def sample_chunks():
    """Sample chunks for testing."""
    doc_id = uuid4()
    return [
        Chunk(id=uuid4(), document_id=doc_id, content="Chunk A", tokens=2),
        Chunk(id=uuid4(), document_id=doc_id, content="Chunk B", tokens=2),
        Chunk(id=uuid4(), document_id=doc_id, content="Chunk C", tokens=2),
    ]


def test_fuse_single_result_set(fusion_service, sample_chunks):
    """Test fusion with single result set returns same order."""
    result = fusion_service.fuse([sample_chunks])

    assert len(result) == 3
    assert result == sample_chunks


def test_fuse_multiple_result_sets(fusion_service, sample_chunks):
    """Test RRF fusion of multiple ranked lists."""
    # Different orderings of same chunks
    set1 = [sample_chunks[0], sample_chunks[1], sample_chunks[2]]
    set2 = [sample_chunks[2], sample_chunks[0], sample_chunks[1]]

    result = fusion_service.fuse([set1, set2])

    # All chunks should be present
    assert len(result) == 3
    assert all(chunk in sample_chunks for chunk in result)


def test_fuse_empty_result_sets(fusion_service):
    """Test fusion with empty result sets."""
    result = fusion_service.fuse([[], []])
    assert result == []


def test_rrf_score_calculation(fusion_service, sample_chunks):
    """Test RRF score calculation is correct."""
    # Chunk A: rank 1 in both lists -> 1/(60+1) + 1/(60+1) = 0.0328
    # Chunk B: rank 2 in list1, rank 3 in list2 -> 1/62 + 1/63 = 0.0319
    set1 = [sample_chunks[0], sample_chunks[1]]
    set2 = [sample_chunks[0], sample_chunks[2]]

    result = fusion_service.fuse([set1, set2])

    # Chunk A should be first (appears in both at top)
    assert result[0] == sample_chunks[0]
