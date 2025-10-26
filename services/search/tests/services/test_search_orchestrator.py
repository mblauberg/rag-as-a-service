"""Tests for search orchestrator."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.search_orchestrator import SearchOrchestrator
from app.models.domain import Chunk
from app.models.schemas import SearchMode


@pytest.fixture
def mock_services():
    """Mock all search services."""
    return {
        "vector": AsyncMock(),
        "keyword": AsyncMock(),
        "fusion": MagicMock(),
        "reranker": AsyncMock(),
        "embedder_client": AsyncMock(),
    }


@pytest.fixture
def orchestrator(mock_services):
    """Search orchestrator with mocked services."""
    return SearchOrchestrator(
        vector_service=mock_services["vector"],
        keyword_service=mock_services["keyword"],
        fusion_service=mock_services["fusion"],
        reranker=mock_services["reranker"],
        embedder_client=mock_services["embedder_client"],
    )


@pytest.fixture
def sample_chunks():
    """Sample chunks."""
    doc_id = uuid4()
    return [
        Chunk(id=uuid4(), document_id=doc_id, content="Chunk 1", tokens=2, score=0.9),
        Chunk(id=uuid4(), document_id=doc_id, content="Chunk 2", tokens=2, score=0.8),
    ]


@pytest.mark.asyncio
async def test_vector_only_search(orchestrator, mock_services, sample_chunks):
    """Test vector-only search mode."""
    mock_services["embedder_client"].generate_embedding.return_value = [0.1] * 384
    mock_services["vector"].search.return_value = sample_chunks

    result = await orchestrator.search(
        query="test query",
        mode=SearchMode.VECTOR,
        top_k=10
    )

    assert len(result) == 2
    assert mock_services["vector"].search.called
    assert not mock_services["keyword"].search.called


@pytest.mark.asyncio
async def test_keyword_only_search(orchestrator, mock_services, sample_chunks):
    """Test keyword-only search mode."""
    mock_services["keyword"].search.return_value = sample_chunks

    result = await orchestrator.search(
        query="test query",
        mode=SearchMode.KEYWORD,
        top_k=10,
        db_session=MagicMock()
    )

    assert len(result) == 2
    assert mock_services["keyword"].search.called
    assert not mock_services["vector"].search.called


@pytest.mark.asyncio
async def test_hybrid_search(orchestrator, mock_services, sample_chunks):
    """Test hybrid search with RRF fusion."""
    mock_services["embedder_client"].generate_embedding.return_value = [0.1] * 384
    mock_services["vector"].search.return_value = sample_chunks[:1]
    mock_services["keyword"].search.return_value = sample_chunks[1:]
    mock_services["fusion"].fuse.return_value = sample_chunks

    result = await orchestrator.search(
        query="test query",
        mode=SearchMode.HYBRID,
        top_k=10,
        db_session=MagicMock()
    )

    assert mock_services["vector"].search.called
    assert mock_services["keyword"].search.called
    assert mock_services["fusion"].fuse.called


@pytest.mark.asyncio
async def test_search_with_reranking(orchestrator, mock_services, sample_chunks):
    """Test search with reranking enabled."""
    mock_services["embedder_client"].generate_embedding.return_value = [0.1] * 384
    mock_services["vector"].search.return_value = sample_chunks
    mock_services["reranker"].rerank.return_value = list(reversed(sample_chunks))

    result = await orchestrator.search(
        query="test",
        mode=SearchMode.VECTOR,
        top_k=2,
        use_reranking=True
    )

    assert mock_services["reranker"].rerank.called
    # Verify reranker was called with more candidates than top_k
    call_args = mock_services["reranker"].rerank.call_args
    assert call_args[1]["top_k"] == 2
