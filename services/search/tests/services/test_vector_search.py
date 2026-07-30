"""Tests for vector search service."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.domain import Chunk
from app.services.vector_search import VectorSearchService


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client."""
    client = MagicMock()
    client.search = AsyncMock()
    return client


@pytest.fixture
def vector_service(mock_qdrant_client):
    """Vector search service with mocked client."""
    with patch("app.services.vector_search.AsyncQdrantClient") as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_qdrant_client
        service = VectorSearchService(
            qdrant_url="http://localhost:6333",
            collection_name="documents"
        )
        service.client = mock_qdrant_client
        return service


@pytest.mark.asyncio
async def test_search_returns_chunks(vector_service, mock_qdrant_client):
    """Test vector search returns chunk objects."""
    # Mock Qdrant response
    doc_id = uuid4()
    mock_result = MagicMock()
    mock_result.id = str(uuid4())
    mock_result.score = 0.85
    mock_result.payload = {
        "document_id": str(doc_id),
        "content": "Test content",
        "tokens": 2,
        "document_title": "Test Doc"
    }

    mock_qdrant_client.search.return_value = [mock_result]

    # Execute search
    query_vector = [0.1] * 384
    results = await vector_service.search(query_vector, top_k=10)

    # Verify
    assert len(results) == 1
    assert isinstance(results[0], Chunk)
    assert results[0].content == "Test content"
    assert results[0].score == 0.85
    assert results[0].document_title == "Test Doc"


@pytest.mark.asyncio
async def test_search_with_document_filter(vector_service, mock_qdrant_client):
    """Test search with document ID filter."""
    doc_id = uuid4()
    query_vector = [0.1] * 384

    await vector_service.search(query_vector, top_k=10, document_id=doc_id)

    # Verify filter was applied
    call_kwargs = mock_qdrant_client.search.call_args.kwargs
    assert "query_filter" in call_kwargs
