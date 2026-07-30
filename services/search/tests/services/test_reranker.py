"""Tests for cross-encoder reranker."""
from unittest.mock import MagicMock, patch
from uuid import uuid4

import numpy as np
import pytest

from app.models.domain import Chunk
from app.services.reranker import CrossEncoderReranker


@pytest.fixture
def mock_cross_encoder():
    """Mock CrossEncoder model."""
    model = MagicMock()
    model.predict = MagicMock()
    return model


@pytest.fixture
def reranker(mock_cross_encoder):
    """Reranker with mocked model."""
    with patch("app.services.reranker.CrossEncoder") as mock_class:
        mock_class.return_value = mock_cross_encoder
        return CrossEncoderReranker()


@pytest.fixture
def sample_chunks():
    """Sample chunks."""
    doc_id = uuid4()
    return [
        Chunk(id=uuid4(), document_id=doc_id, content="Python programming", tokens=2),
        Chunk(id=uuid4(), document_id=doc_id, content="Weather forecast", tokens=2),
        Chunk(id=uuid4(), document_id=doc_id, content="Python syntax", tokens=2),
    ]


@pytest.mark.asyncio
async def test_rerank_reorders_by_relevance(reranker, mock_cross_encoder, sample_chunks):
    """Test reranking reorders chunks by relevance score."""
    query = "Python programming language"

    # Mock scores: third chunk (Python syntax) most relevant
    mock_cross_encoder.predict.return_value = np.array([0.7, 0.3, 0.9])

    result = await reranker.rerank(query, sample_chunks, top_k=3)

    # Verify reordering
    assert len(result) == 3
    assert result[0] == sample_chunks[2]  # Highest score (0.9)
    assert result[1] == sample_chunks[0]  # Second (0.7)
    assert result[2] == sample_chunks[1]  # Lowest (0.3)


@pytest.mark.asyncio
async def test_rerank_respects_top_k(reranker, mock_cross_encoder, sample_chunks):
    """Test reranking returns only top_k results."""
    query = "test"
    mock_cross_encoder.predict.return_value = np.array([0.7, 0.3, 0.9])

    result = await reranker.rerank(query, sample_chunks, top_k=2)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_rerank_empty_chunks(reranker, mock_cross_encoder):
    """Test reranking with empty chunk list."""
    result = await reranker.rerank("query", [], top_k=5)

    assert result == []
    mock_cross_encoder.predict.assert_not_called()


@pytest.mark.asyncio
async def test_rerank_attaches_normalized_scores(reranker, mock_cross_encoder, sample_chunks):
    """Test that normalized scores are attached to chunks."""
    query = "test"
    mock_cross_encoder.predict.return_value = np.array([0.5, 0.8, 0.2])

    result = await reranker.rerank(query, sample_chunks, top_k=3)

    # Verify scores are normalized to [0, 1]
    assert result[0].score == 1.0  # Highest raw score normalized to 1.0
    assert result[2].score == 0.0  # Lowest raw score normalized to 0.0
    assert 0.0 <= result[1].score <= 1.0
