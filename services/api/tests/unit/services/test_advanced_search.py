"""
Unit tests for advanced search with query expansion.

Tests the integration of query expansion with hybrid search:
- Query expansion generates alternative queries
- Hybrid search executed for each query variant
- Multi-set RRF combines all results
- LLM failure handled gracefully
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from app.services.hybrid_search_service import HybridSearchService
from app.services.query_expansion import QueryExpansionService
from app.models.document import DocumentChunk


@pytest.mark.asyncio
async def test_search_with_expansion_expands_query_and_searches():
    """Test advanced search expands query and searches with all variants"""
    # Create mock dependencies
    mock_db = AsyncMock()
    mock_qdrant = MagicMock()
    mock_http_client = AsyncMock()
    mock_generator = MagicMock()

    # Create hybrid search service
    hybrid_service = HybridSearchService(
        mock_db,
        mock_qdrant,
        mock_http_client
    )

    # Mock query expansion service
    mock_expansion_service = AsyncMock(spec=QueryExpansionService)
    mock_expansion_service.expand_query = AsyncMock(return_value=[
        "k8s deployment",  # Original
        "kubernetes deployment configuration",  # Alternative 1
        "container orchestration deployment"  # Alternative 2
    ])

    # Mock hybrid search to return different results for each query
    chunk1 = DocumentChunk(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        document_id=UUID("10000000-0000-0000-0000-000000000001"),
        chunk_index=0,
        chunk_text="Kubernetes deployment guide",
        token_count=5
    )
    chunk2 = DocumentChunk(
        id=UUID("00000000-0000-0000-0000-000000000002"),
        document_id=UUID("10000000-0000-0000-0000-000000000001"),
        chunk_index=1,
        chunk_text="Container orchestration basics",
        token_count=4
    )
    chunk3 = DocumentChunk(
        id=UUID("00000000-0000-0000-0000-000000000003"),
        document_id=UUID("10000000-0000-0000-0000-000000000001"),
        chunk_index=2,
        chunk_text="K8s deployment troubleshooting",
        token_count=4
    )

    # Mock search method to return different results
    async def mock_search(query, limit=10, document_ids=None):
        if "k8s" in query.lower():
            return {
                "results": [chunk1, chunk3],
                "retrieval_method": "hybrid",
                "metadata": {"bm25_count": 2, "vector_count": 2}
            }
        elif "kubernetes" in query.lower():
            return {
                "results": [chunk1, chunk2],
                "retrieval_method": "hybrid",
                "metadata": {"bm25_count": 2, "vector_count": 2}
            }
        elif "container" in query.lower():
            return {
                "results": [chunk2, chunk3],
                "retrieval_method": "hybrid",
                "metadata": {"bm25_count": 2, "vector_count": 2}
            }
        return {"results": [], "retrieval_method": "hybrid", "metadata": {}}

    hybrid_service.search = AsyncMock(side_effect=mock_search)

    # Inject mock expansion service
    hybrid_service.expansion_service = mock_expansion_service

    # Execute search with expansion
    result = await hybrid_service.search_with_expansion(
        query="k8s deployment",
        limit=10
    )

    # Verify query expansion was called
    mock_expansion_service.expand_query.assert_called_once_with("k8s deployment")

    # Verify search was called 3 times (once per query variant)
    assert hybrid_service.search.call_count == 3

    # Verify results are returned
    assert "results" in result
    assert len(result["results"]) > 0

    # Verify retrieval method is correct
    assert result["retrieval_method"] == "hybrid_with_expansion"

    # Verify expanded queries are in response
    assert "expanded_queries" in result
    assert result["expanded_queries"] == [
        "k8s deployment",
        "kubernetes deployment configuration",
        "container orchestration deployment"
    ]

    # Verify metadata
    assert "metadata" in result
    assert result["metadata"]["query_count"] == 3


@pytest.mark.asyncio
async def test_search_with_expansion_applies_multi_set_rrf():
    """Test that multi-set RRF is applied to merge results from all queries"""
    # Create mock dependencies
    mock_db = AsyncMock()
    mock_qdrant = MagicMock()
    mock_http_client = AsyncMock()

    # Create hybrid search service
    hybrid_service = HybridSearchService(
        mock_db,
        mock_qdrant,
        mock_http_client
    )

    # Mock expansion service - returns 3 queries
    mock_expansion_service = AsyncMock(spec=QueryExpansionService)
    mock_expansion_service.expand_query = AsyncMock(return_value=[
        "query1", "query2", "query3"
    ])

    # Create test chunks
    chunk1 = DocumentChunk(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        document_id=UUID("10000000-0000-0000-0000-000000000001"),
        chunk_index=0,
        chunk_text="Result 1",
        token_count=2
    )
    chunk2 = DocumentChunk(
        id=UUID("00000000-0000-0000-0000-000000000002"),
        document_id=UUID("10000000-0000-0000-0000-000000000001"),
        chunk_index=1,
        chunk_text="Result 2",
        token_count=2
    )
    chunk3 = DocumentChunk(
        id=UUID("00000000-0000-0000-0000-000000000003"),
        document_id=UUID("10000000-0000-0000-0000-000000000001"),
        chunk_index=2,
        chunk_text="Result 3",
        token_count=2
    )

    # Mock search to return different chunks
    # chunk1 appears in all 3 results (should rank highest)
    # chunk2 appears in 2 results
    # chunk3 appears in 1 result
    search_results = [
        {"results": [chunk1, chunk2], "retrieval_method": "hybrid", "metadata": {}},
        {"results": [chunk1, chunk3], "retrieval_method": "hybrid", "metadata": {}},
        {"results": [chunk1, chunk2], "retrieval_method": "hybrid", "metadata": {}},
    ]

    hybrid_service.search = AsyncMock(side_effect=search_results)
    hybrid_service.expansion_service = mock_expansion_service

    # Execute search with expansion
    result = await hybrid_service.search_with_expansion(
        query="test query",
        limit=10
    )

    # Verify chunk1 appears first (in all result sets)
    assert result["results"][0].id == chunk1.id

    # Verify chunk2 appears second (in 2 result sets)
    assert result["results"][1].id == chunk2.id

    # Verify all unique chunks are present
    result_ids = [chunk.id for chunk in result["results"]]
    assert chunk1.id in result_ids
    assert chunk2.id in result_ids
    assert chunk3.id in result_ids


@pytest.mark.asyncio
async def test_search_with_expansion_handles_llm_failure():
    """Test graceful fallback when query expansion fails"""
    # Create mock dependencies
    mock_db = AsyncMock()
    mock_qdrant = MagicMock()
    mock_http_client = AsyncMock()

    # Create hybrid search service
    hybrid_service = HybridSearchService(
        mock_db,
        mock_qdrant,
        mock_http_client
    )

    # Mock expansion service that returns only original query (expansion failed)
    mock_expansion_service = AsyncMock(spec=QueryExpansionService)
    mock_expansion_service.expand_query = AsyncMock(return_value=[
        "original query"  # Only original, no alternatives
    ])

    # Create test chunk
    chunk1 = DocumentChunk(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        document_id=UUID("10000000-0000-0000-0000-000000000001"),
        chunk_index=0,
        chunk_text="Result",
        token_count=1
    )

    # Mock search
    hybrid_service.search = AsyncMock(return_value={
        "results": [chunk1],
        "retrieval_method": "hybrid",
        "metadata": {"bm25_count": 1, "vector_count": 1}
    })
    hybrid_service.expansion_service = mock_expansion_service

    # Execute search with expansion
    result = await hybrid_service.search_with_expansion(
        query="original query",
        limit=10
    )

    # Should still work with single query
    assert result["retrieval_method"] == "hybrid_with_expansion"
    assert len(result["results"]) > 0

    # Should have only 1 query (original)
    assert result["expanded_queries"] == ["original query"]

    # Search should have been called once
    assert hybrid_service.search.call_count == 1


@pytest.mark.asyncio
async def test_search_with_expansion_respects_limit():
    """Test that final results respect the limit parameter"""
    # Create mock dependencies
    mock_db = AsyncMock()
    mock_qdrant = MagicMock()
    mock_http_client = AsyncMock()

    # Create hybrid search service
    hybrid_service = HybridSearchService(
        mock_db,
        mock_qdrant,
        mock_http_client
    )

    # Mock expansion service
    mock_expansion_service = AsyncMock(spec=QueryExpansionService)
    mock_expansion_service.expand_query = AsyncMock(return_value=[
        "q1", "q2", "q3"
    ])

    # Create 20 test chunks
    chunks = [
        DocumentChunk(
            id=UUID(f"00000000-0000-0000-0000-{i:012d}"),
            document_id=UUID("10000000-0000-0000-0000-000000000001"),
            chunk_index=i,
            chunk_text=f"Chunk {i}",
            token_count=2
        )
        for i in range(20)
    ]

    # Mock search to return many results
    hybrid_service.search = AsyncMock(return_value={
        "results": chunks[:15],  # Return 15 chunks per search
        "retrieval_method": "hybrid",
        "metadata": {}
    })
    hybrid_service.expansion_service = mock_expansion_service

    # Execute with limit=5
    result = await hybrid_service.search_with_expansion(
        query="test",
        limit=5
    )

    # Should return exactly 5 results
    assert len(result["results"]) == 5


@pytest.mark.asyncio
async def test_search_with_expansion_includes_metadata():
    """Test that metadata includes query count and total candidates"""
    # Create mock dependencies
    mock_db = AsyncMock()
    mock_qdrant = MagicMock()
    mock_http_client = AsyncMock()

    # Create hybrid search service
    hybrid_service = HybridSearchService(
        mock_db,
        mock_qdrant,
        mock_http_client
    )

    # Mock expansion service
    mock_expansion_service = AsyncMock(spec=QueryExpansionService)
    mock_expansion_service.expand_query = AsyncMock(return_value=[
        "q1", "q2", "q3"
    ])

    # Create test chunks
    chunk1 = DocumentChunk(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        document_id=UUID("10000000-0000-0000-0000-000000000001"),
        chunk_index=0,
        chunk_text="Result",
        token_count=1
    )

    # Mock search - each returns 5 results
    hybrid_service.search = AsyncMock(return_value={
        "results": [chunk1] * 5,
        "retrieval_method": "hybrid",
        "metadata": {}
    })
    hybrid_service.expansion_service = mock_expansion_service

    # Execute
    result = await hybrid_service.search_with_expansion(
        query="test",
        limit=10
    )

    # Verify metadata
    assert "metadata" in result
    assert result["metadata"]["query_count"] == 3
    # Total candidates = 3 queries * 5 results = 15
    assert result["metadata"]["total_candidates"] == 15
