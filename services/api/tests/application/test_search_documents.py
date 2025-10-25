"""Tests for SearchDocumentsUseCase."""
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from app.application.use_cases.search_documents import SearchDocumentsUseCase, SearchMode
from app.domain.value_objects.search_query import SearchQuery
from app.domain.entities.chunk import Chunk
from app.ports.services import EmbeddingService, VectorStore, QueryAugmenter, FusionService


@pytest.mark.asyncio
async def test_search_documents_success():
    """Test successful document search."""
    mock_embedding_service = Mock(spec=EmbeddingService)
    mock_vector_store = Mock(spec=VectorStore)

    # Mock embeddings generation
    query_vector = [0.1, 0.2, 0.3]
    mock_embedding_service.generate_embeddings = AsyncMock(return_value=[query_vector])

    # Mock search results
    result_chunks = [
        Chunk(
            id=uuid4(),
            document_id=uuid4(),
            content="Relevant chunk 1",
            tokens=3,
            embedding_vector=[0.1, 0.2, 0.3]
        ),
        Chunk(
            id=uuid4(),
            document_id=uuid4(),
            content="Relevant chunk 2",
            tokens=3,
            embedding_vector=[0.15, 0.25, 0.35]
        )
    ]
    mock_vector_store.search = AsyncMock(return_value=result_chunks)

    use_case = SearchDocumentsUseCase(
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store
    )

    # Execute search
    query = SearchQuery(text="test query", top_k=5)
    results = await use_case.execute(query, mode=SearchMode.VECTOR)

    # Verify results
    assert len(results) == 2
    assert results[0].content == "Relevant chunk 1"
    assert results[1].content == "Relevant chunk 2"

    # Verify interactions
    mock_embedding_service.generate_embeddings.assert_called_once_with(["test query"])
    mock_vector_store.search.assert_called_once_with(
        query_vector=query_vector,
        top_k=5
    )


@pytest.mark.asyncio
async def test_search_documents_empty_results():
    """Test search with no results."""
    mock_embedding_service = Mock(spec=EmbeddingService)
    mock_vector_store = Mock(spec=VectorStore)

    mock_embedding_service.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    mock_vector_store.search = AsyncMock(return_value=[])

    use_case = SearchDocumentsUseCase(
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store
    )

    query = SearchQuery(text="nonexistent query", top_k=10)
    results = await use_case.execute(query, mode=SearchMode.VECTOR)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_with_query_expansion():
    """Test search with query expansion enabled."""
    # Mock services
    mock_embedding_service = Mock(spec=EmbeddingService)
    mock_vector_store = Mock(spec=VectorStore)
    mock_query_augmenter = Mock(spec=QueryAugmenter)
    mock_fusion_service = Mock(spec=FusionService)

    # Mock query expansion
    mock_query_augmenter.expand = AsyncMock(return_value=[
        "How do I scale Kubernetes?",
        "Kubernetes scaling methods",
        "How to increase pod replicas in K8s"
    ])

    # Mock embeddings for each variant
    mock_embedding_service.generate_embeddings = AsyncMock(
        side_effect=[
            [[0.1, 0.2, 0.3]],
            [[0.15, 0.25, 0.35]],
            [[0.12, 0.22, 0.32]]
        ]
    )

    # Mock search results for each variant
    chunk1 = Chunk(
        id=uuid4(),
        document_id=uuid4(),
        content="Chunk from query 1",
        tokens=4,
        embedding_vector=[0.1, 0.2, 0.3]
    )
    chunk2 = Chunk(
        id=uuid4(),
        document_id=uuid4(),
        content="Chunk from query 2",
        tokens=4,
        embedding_vector=[0.15, 0.25, 0.35]
    )
    chunk3 = Chunk(
        id=uuid4(),
        document_id=uuid4(),
        content="Chunk from query 3",
        tokens=4,
        embedding_vector=[0.12, 0.22, 0.32]
    )

    mock_vector_store.search = AsyncMock(
        side_effect=[
            [chunk1],
            [chunk2],
            [chunk3]
        ]
    )

    # Mock fusion
    fused_chunks = [chunk1, chunk2, chunk3]
    mock_fusion_service.fuse = Mock(return_value=fused_chunks)

    # Create use case with all dependencies
    use_case = SearchDocumentsUseCase(
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store,
        query_augmenter=mock_query_augmenter,
        fusion_service=mock_fusion_service
    )

    # Execute search with expansion
    query = SearchQuery(text="How do I scale Kubernetes?", top_k=5)
    results = await use_case.execute(query, mode=SearchMode.VECTOR, use_expansion=True)

    # Verify expansion was called
    mock_query_augmenter.expand.assert_called_once_with(
        "How do I scale Kubernetes?",
        num_variants=2
    )

    # Verify 3 searches were performed (original + 2 variants)
    assert mock_vector_store.search.call_count == 3

    # Verify fusion was called with all result sets
    mock_fusion_service.fuse.assert_called_once()
    call_args = mock_fusion_service.fuse.call_args
    assert len(call_args.kwargs['result_sets']) == 3

    # Verify results
    assert len(results) <= 5  # Should respect top_k


@pytest.mark.asyncio
async def test_search_with_expansion_disabled():
    """Test that expansion can be disabled."""
    mock_embedding_service = Mock(spec=EmbeddingService)
    mock_vector_store = Mock(spec=VectorStore)
    mock_query_augmenter = Mock(spec=QueryAugmenter)

    # Mock services
    mock_embedding_service.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    mock_vector_store.search = AsyncMock(return_value=[])
    mock_query_augmenter.expand = AsyncMock()

    use_case = SearchDocumentsUseCase(
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store,
        query_augmenter=mock_query_augmenter
    )

    # Execute with expansion disabled
    query = SearchQuery(text="test query", top_k=5)
    await use_case.execute(query, mode=SearchMode.VECTOR, use_expansion=False)

    # Verify expansion was not called
    mock_query_augmenter.expand.assert_not_called()

    # Verify only one search was performed
    assert mock_vector_store.search.call_count == 1


@pytest.mark.asyncio
async def test_search_without_augmenter():
    """Test that search works when augmenter is None."""
    mock_embedding_service = Mock(spec=EmbeddingService)
    mock_vector_store = Mock(spec=VectorStore)

    # Mock services
    mock_embedding_service.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    mock_vector_store.search = AsyncMock(return_value=[])

    # Create use case without augmenter
    use_case = SearchDocumentsUseCase(
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store,
        query_augmenter=None
    )

    # Execute with expansion enabled (should fall back to standard search)
    query = SearchQuery(text="test query", top_k=5)
    await use_case.execute(query, mode=SearchMode.VECTOR, use_expansion=True)

    # Verify only one search was performed
    assert mock_vector_store.search.call_count == 1


@pytest.mark.asyncio
async def test_search_expansion_with_single_result_set():
    """Test expansion handles case when fusion service is None."""
    mock_embedding_service = Mock(spec=EmbeddingService)
    mock_vector_store = Mock(spec=VectorStore)
    mock_query_augmenter = Mock(spec=QueryAugmenter)

    # Mock query expansion
    mock_query_augmenter.expand = AsyncMock(return_value=[
        "test query"
    ])

    # Mock embeddings
    mock_embedding_service.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

    # Mock search results
    chunk1 = Chunk(
        id=uuid4(),
        document_id=uuid4(),
        content="Test chunk",
        tokens=2,
        embedding_vector=[0.1, 0.2, 0.3]
    )
    mock_vector_store.search = AsyncMock(return_value=[chunk1])

    # Create use case without fusion service
    use_case = SearchDocumentsUseCase(
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store,
        query_augmenter=mock_query_augmenter,
        fusion_service=None
    )

    # Execute with expansion
    query = SearchQuery(text="test query", top_k=5)
    results = await use_case.execute(query, mode=SearchMode.VECTOR, use_expansion=True)

    # Should return first result set without fusion
    assert len(results) <= 5
    assert results[0].content == "Test chunk"
