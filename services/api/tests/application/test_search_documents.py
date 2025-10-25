"""Tests for SearchDocumentsUseCase."""
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from app.application.use_cases.search_documents import SearchDocumentsUseCase
from app.domain.value_objects.search_query import SearchQuery
from app.domain.entities.chunk import Chunk
from app.ports.services import EmbeddingService, VectorStore


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
    results = await use_case.execute(query)

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
    results = await use_case.execute(query)

    assert len(results) == 0
