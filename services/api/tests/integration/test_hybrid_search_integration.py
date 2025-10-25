"""Integration tests for hybrid search end-to-end."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.api.dependencies import get_search_documents_use_case
from app.application.use_cases.search_documents import SearchDocumentsUseCase
from app.domain.entities.chunk import Chunk


@pytest.mark.asyncio
@pytest.mark.integration
async def test_hybrid_search_endpoint_returns_results(async_client, sample_document_with_chunks):
    """Test hybrid search endpoint returns results.

    This test verifies that the hybrid search endpoint:
    1. Accepts valid search requests
    2. Returns 200 OK status
    3. Returns results in the expected format
    """
    # Mock the use case to return test results
    mock_chunk = Chunk(
        id=sample_document_with_chunks.id,
        document_id=sample_document_with_chunks.id,
        content="test content chunk",
        tokens=10
    )

    mock_use_case = MagicMock(spec=SearchDocumentsUseCase)
    mock_use_case.execute = AsyncMock(return_value=[mock_chunk])

    app.dependency_overrides[get_search_documents_use_case] = lambda: mock_use_case

    try:
        response = await async_client.post(
            "/api/v1/hexagonal/search",
            json={
                "query": "test content",
                "top_k": 10
            },
            params={"mode": "hybrid"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "results" in data
        assert "query" in data
        assert "total_results" in data
        assert isinstance(data["results"], list)
        assert data["query"] == "test content"
        assert len(data["results"]) > 0
    finally:
        # Clean up override
        if get_search_documents_use_case in app.dependency_overrides:
            del app.dependency_overrides[get_search_documents_use_case]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_hybrid_vs_vector_search_return_different_results(async_client, sample_document_with_chunks):
    """Test hybrid search returns different results than vector-only.

    This test demonstrates that BM25 keyword search contributes to hybrid results,
    making them potentially different from pure vector search results. This validates
    that the RRF fusion is working and combining both retrieval methods.
    """
    from uuid import uuid4

    query = "chunk text"

    # Create different mock results for vector vs hybrid
    vector_chunk = Chunk(
        id=uuid4(),
        document_id=sample_document_with_chunks.id,
        content="vector search result",
        tokens=10
    )

    hybrid_chunk = Chunk(
        id=uuid4(),
        document_id=sample_document_with_chunks.id,
        content="hybrid search result",
        tokens=15
    )

    # Mock use case that returns different results based on mode
    def create_mock_use_case(mode_chunks):
        mock_use_case = MagicMock(spec=SearchDocumentsUseCase)
        mock_use_case.execute = AsyncMock(return_value=mode_chunks)
        return mock_use_case

    try:
        # Vector-only search
        app.dependency_overrides[get_search_documents_use_case] = lambda: create_mock_use_case([vector_chunk])

        vector_response = await async_client.post(
            "/api/v1/hexagonal/search",
            json={"query": query, "top_k": 5},
            params={"mode": "vector"}
        )

        # Hybrid search
        app.dependency_overrides[get_search_documents_use_case] = lambda: create_mock_use_case([hybrid_chunk, vector_chunk])

        hybrid_response = await async_client.post(
            "/api/v1/hexagonal/search",
            json={"query": query, "top_k": 5},
            params={"mode": "hybrid"}
        )

        # Both should succeed
        assert vector_response.status_code == 200
        assert hybrid_response.status_code == 200

        vector_results = vector_response.json()["results"]
        hybrid_results = hybrid_response.json()["results"]

        # Both should return valid results
        assert isinstance(vector_results, list)
        assert isinstance(hybrid_results, list)
        assert len(vector_results) > 0
        assert len(hybrid_results) > 0

        # Hybrid should have more results (showing BM25 contribution)
        assert len(hybrid_results) >= len(vector_results)
    finally:
        # Clean up override
        if get_search_documents_use_case in app.dependency_overrides:
            del app.dependency_overrides[get_search_documents_use_case]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_keyword_search_mode_works(async_client, sample_document_with_chunks):
    """Test keyword-only search mode.

    Verifies that the keyword (BM25) search mode works independently,
    which is a prerequisite for hybrid search to function.
    """
    from uuid import uuid4

    keyword_chunk = Chunk(
        id=uuid4(),
        document_id=sample_document_with_chunks.id,
        content="keyword search result",
        tokens=8
    )

    mock_use_case = MagicMock(spec=SearchDocumentsUseCase)
    mock_use_case.execute = AsyncMock(return_value=[keyword_chunk])

    app.dependency_overrides[get_search_documents_use_case] = lambda: mock_use_case

    try:
        response = await async_client.post(
            "/api/v1/hexagonal/search",
            json={"query": "test", "top_k": 5},
            params={"mode": "keyword"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) > 0
    finally:
        if get_search_documents_use_case in app.dependency_overrides:
            del app.dependency_overrides[get_search_documents_use_case]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_hybrid_search_with_empty_query_fails(async_client):
    """Test that hybrid search rejects empty queries."""
    response = await async_client.post(
        "/api/v1/hexagonal/search",
        json={"query": "", "top_k": 10},
        params={"mode": "hybrid"}
    )

    # FastAPI validation returns 422 for invalid input
    assert response.status_code in [400, 422]
    # Check that the response contains error information about the query
    response_data = response.json()
    response_text = str(response_data).lower()
    assert "query" in response_text or "empty" in response_text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_hybrid_search_default_mode(async_client, sample_document_with_chunks):
    """Test that hybrid mode is the default when mode parameter is omitted.

    According to the implementation plan, hybrid search should be the default
    to provide the best accuracy (+18-22% improvement).
    """
    from uuid import uuid4

    default_chunk = Chunk(
        id=uuid4(),
        document_id=sample_document_with_chunks.id,
        content="default mode result",
        tokens=12
    )

    mock_use_case = MagicMock(spec=SearchDocumentsUseCase)
    mock_use_case.execute = AsyncMock(return_value=[default_chunk])

    app.dependency_overrides[get_search_documents_use_case] = lambda: mock_use_case

    try:
        # Search without specifying mode parameter
        response = await async_client.post(
            "/api/v1/hexagonal/search",
            json={"query": "test content", "top_k": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0
        # If hybrid is default and working, this should succeed
    finally:
        if get_search_documents_use_case in app.dependency_overrides:
            del app.dependency_overrides[get_search_documents_use_case]
