"""
Unit tests for HybridSearchService.

Tests hybrid search combining BM25 (lexical) and vector (semantic) search
using Reciprocal Rank Fusion.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4, UUID
from app.services.hybrid_search_service import HybridSearchService
from app.models.document import DocumentChunk


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return Mock()


@pytest.fixture
def mock_embedder_client():
    """Mock embedder client."""
    return Mock()


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client."""
    return Mock()


@pytest.fixture
def sample_chunks():
    """Create sample document chunks for testing."""
    doc_id = uuid4()

    chunk1 = DocumentChunk(
        id=uuid4(),
        document_id=doc_id,
        chunk_index=0,
        chunk_text="Kubernetes deployment configuration for production environments",
        token_count=8
    )
    chunk1.bm25_score = 0.95

    chunk2 = DocumentChunk(
        id=uuid4(),
        document_id=doc_id,
        chunk_index=1,
        chunk_text="Docker container networking and service discovery mechanisms",
        token_count=8
    )
    chunk2.bm25_score = 0.85

    chunk3 = DocumentChunk(
        id=uuid4(),
        document_id=doc_id,
        chunk_index=2,
        chunk_text="Python programming best practices and design patterns",
        token_count=7
    )
    chunk3.bm25_score = 0.75

    return [chunk1, chunk2, chunk3]


@pytest.mark.asyncio
async def test_hybrid_search_combines_bm25_and_vector_results(
    mock_db_session,
    mock_embedder_client,
    mock_qdrant_client,
    sample_chunks
):
    """Test that hybrid search combines BM25 and vector search results."""
    # Setup - mock BM25 results
    bm25_results = [sample_chunks[0], sample_chunks[1]]  # k8s, docker

    # Setup - mock vector results
    vector_results = [sample_chunks[1], sample_chunks[2]]  # docker, python

    # Create service
    service = HybridSearchService(
        mock_db_session,
        mock_embedder_client,
        mock_qdrant_client
    )

    # Mock the individual search methods
    with patch.object(service.bm25_service, 'search', new_callable=AsyncMock) as mock_bm25, \
         patch.object(service.vector_service, 'search', new_callable=AsyncMock) as mock_vector:

        mock_bm25.return_value = bm25_results
        mock_vector.return_value = vector_results

        # Execute
        result = await service.search("kubernetes deployment", limit=10)

        # Verify both search methods were called
        mock_bm25.assert_called_once()
        mock_vector.assert_called_once()

        # Verify result structure
        assert "results" in result
        assert "retrieval_method" in result
        assert result["retrieval_method"] == "hybrid"
        assert "metadata" in result

        # Verify metadata contains counts
        metadata = result["metadata"]
        assert "bm25_count" in metadata
        assert "vector_count" in metadata
        assert "overlap_count" in metadata

        assert metadata["bm25_count"] == 2
        assert metadata["vector_count"] == 2
        assert metadata["overlap_count"] == 1  # chunk2 appears in both


@pytest.mark.asyncio
async def test_hybrid_search_uses_parallel_execution(
    mock_db_session,
    mock_embedder_client,
    mock_qdrant_client,
    sample_chunks
):
    """Test that hybrid search executes BM25 and vector search in parallel."""
    import asyncio

    # Track execution order to verify parallelism
    execution_log = []

    async def mock_bm25_search(*args, **kwargs):
        execution_log.append(("bm25_start", asyncio.get_running_loop().time()))
        await asyncio.sleep(0.1)  # Simulate delay
        execution_log.append(("bm25_end", asyncio.get_running_loop().time()))
        return [sample_chunks[0]]

    async def mock_vector_search(*args, **kwargs):
        execution_log.append(("vector_start", asyncio.get_running_loop().time()))
        await asyncio.sleep(0.1)  # Simulate delay
        execution_log.append(("vector_end", asyncio.get_running_loop().time()))
        return [sample_chunks[1]]

    service = HybridSearchService(
        mock_db_session,
        mock_embedder_client,
        mock_qdrant_client
    )

    with patch.object(service.bm25_service, 'search', side_effect=mock_bm25_search), \
         patch.object(service.vector_service, 'search', side_effect=mock_vector_search):

        start_time = asyncio.get_running_loop().time()
        result = await service.search("test query", limit=5)
        end_time = asyncio.get_running_loop().time()

        # Total execution should be ~0.1s (parallel), not ~0.2s (sequential)
        # Allow some margin for overhead
        assert (end_time - start_time) < 0.15, "Searches should run in parallel"

        # Both searches should have started before either finished
        bm25_start = next(t for op, t in execution_log if op == "bm25_start")
        vector_start = next(t for op, t in execution_log if op == "vector_start")
        bm25_end = next(t for op, t in execution_log if op == "bm25_end")
        vector_end = next(t for op, t in execution_log if op == "vector_end")

        # Check that both started before either ended (parallel execution)
        assert bm25_start < bm25_end
        assert vector_start < vector_end


@pytest.mark.asyncio
async def test_hybrid_search_applies_rrf_fusion(
    mock_db_session,
    mock_embedder_client,
    mock_qdrant_client,
    sample_chunks
):
    """Test that hybrid search applies RRF to combine results."""
    # chunk1 appears only in BM25 (rank 1)
    # chunk2 appears in both BM25 (rank 2) and vector (rank 1)
    # chunk3 appears only in vector (rank 2)

    # Expected RRF scores (k=60):
    # chunk1: 1/(60+1) = 0.0164
    # chunk2: 1/(60+1) + 1/(60+2) = 0.0164 + 0.0161 = 0.0325
    # chunk3: 1/(60+2) = 0.0161

    # So order should be: chunk2, chunk1, chunk3

    bm25_results = [sample_chunks[0], sample_chunks[1]]  # chunk1, chunk2
    vector_results = [sample_chunks[1], sample_chunks[2]]  # chunk2, chunk3

    service = HybridSearchService(
        mock_db_session,
        mock_embedder_client,
        mock_qdrant_client
    )

    with patch.object(service.bm25_service, 'search', new_callable=AsyncMock) as mock_bm25, \
         patch.object(service.vector_service, 'search', new_callable=AsyncMock) as mock_vector:

        mock_bm25.return_value = bm25_results
        mock_vector.return_value = vector_results

        result = await service.search("test", limit=10)

        # chunk2 should be first (appears in both lists)
        assert len(result["results"]) == 3
        assert result["results"][0].id == sample_chunks[1].id


@pytest.mark.asyncio
async def test_hybrid_search_handles_empty_bm25_results(
    mock_db_session,
    mock_embedder_client,
    mock_qdrant_client,
    sample_chunks
):
    """Test hybrid search when BM25 returns no results."""
    bm25_results = []
    vector_results = [sample_chunks[0], sample_chunks[1]]

    service = HybridSearchService(
        mock_db_session,
        mock_embedder_client,
        mock_qdrant_client
    )

    with patch.object(service.bm25_service, 'search', new_callable=AsyncMock) as mock_bm25, \
         patch.object(service.vector_service, 'search', new_callable=AsyncMock) as mock_vector:

        mock_bm25.return_value = bm25_results
        mock_vector.return_value = vector_results

        result = await service.search("test", limit=10)

        # Should return vector results only
        assert len(result["results"]) == 2
        assert result["metadata"]["bm25_count"] == 0
        assert result["metadata"]["vector_count"] == 2
        assert result["metadata"]["overlap_count"] == 0


@pytest.mark.asyncio
async def test_hybrid_search_handles_empty_vector_results(
    mock_db_session,
    mock_embedder_client,
    mock_qdrant_client,
    sample_chunks
):
    """Test hybrid search when vector search returns no results."""
    bm25_results = [sample_chunks[0], sample_chunks[1]]
    vector_results = []

    service = HybridSearchService(
        mock_db_session,
        mock_embedder_client,
        mock_qdrant_client
    )

    with patch.object(service.bm25_service, 'search', new_callable=AsyncMock) as mock_bm25, \
         patch.object(service.vector_service, 'search', new_callable=AsyncMock) as mock_vector:

        mock_bm25.return_value = bm25_results
        mock_vector.return_value = vector_results

        result = await service.search("test", limit=10)

        # Should return BM25 results only
        assert len(result["results"]) == 2
        assert result["metadata"]["bm25_count"] == 2
        assert result["metadata"]["vector_count"] == 0
        assert result["metadata"]["overlap_count"] == 0


@pytest.mark.asyncio
async def test_hybrid_search_respects_limit(
    mock_db_session,
    mock_embedder_client,
    mock_qdrant_client,
    sample_chunks
):
    """Test that hybrid search respects the limit parameter."""
    # Create more chunks
    doc_id = uuid4()
    many_chunks = [
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=i,
            chunk_text=f"Chunk {i}",
            token_count=5
        )
        for i in range(20)
    ]

    bm25_results = many_chunks[:10]
    vector_results = many_chunks[5:15]

    service = HybridSearchService(
        mock_db_session,
        mock_embedder_client,
        mock_qdrant_client
    )

    with patch.object(service.bm25_service, 'search', new_callable=AsyncMock) as mock_bm25, \
         patch.object(service.vector_service, 'search', new_callable=AsyncMock) as mock_vector:

        mock_bm25.return_value = bm25_results
        mock_vector.return_value = vector_results

        result = await service.search("test", limit=5)

        # Should return only 5 results despite having more
        assert len(result["results"]) == 5
