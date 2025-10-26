"""Tests for hybrid search use case."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.use_cases.search_documents import (SearchDocumentsUseCase,
                                                        SearchMode)
from app.domain.entities.chunk import Chunk
from app.domain.value_objects.search_query import SearchQuery


@pytest.mark.asyncio
async def test_hybrid_search_calls_both_stores():
    """Test hybrid mode retrieves from both vector and keyword stores."""
    # Mock dependencies
    embedding_service = AsyncMock()
    vector_store = AsyncMock()
    keyword_store = AsyncMock()
    fusion_service = MagicMock()  # Synchronous mock for sync method

    # Configure mocks
    chunk1 = Chunk(id=uuid4(), document_id=uuid4(), content="test1", tokens=1)
    chunk2 = Chunk(id=uuid4(), document_id=uuid4(), content="test2", tokens=1)

    embedding_service.generate_embeddings.return_value = [[0.1] * 384]
    vector_store.search.return_value = [chunk1]
    keyword_store.search.return_value = [chunk2]
    fusion_service.fuse.return_value = [chunk1, chunk2]

    use_case = SearchDocumentsUseCase(
        embedding_service=embedding_service,
        vector_store=vector_store,
        keyword_store=keyword_store,
        fusion_service=fusion_service,
    )

    query = SearchQuery(text="test query", top_k=10)

    results = await use_case.execute(query, mode=SearchMode.HYBRID)

    # Verify both stores were called
    vector_store.search.assert_called_once()
    keyword_store.search.assert_called_once()
    fusion_service.fuse.assert_called_once()
    assert len(results) == 2


@pytest.mark.asyncio
async def test_hybrid_search_retrieves_2x_before_fusion():
    """Test hybrid mode retrieves 2x results before fusion."""
    embedding_service = AsyncMock()
    vector_store = AsyncMock()
    keyword_store = AsyncMock()
    fusion_service = MagicMock()  # Synchronous mock for sync method

    embedding_service.generate_embeddings.return_value = [[0.1] * 384]
    vector_store.search.return_value = []
    keyword_store.search.return_value = []
    fusion_service.fuse.return_value = []

    use_case = SearchDocumentsUseCase(
        embedding_service=embedding_service,
        vector_store=vector_store,
        keyword_store=keyword_store,
        fusion_service=fusion_service,
    )

    query = SearchQuery(text="test query", top_k=10)

    await use_case.execute(query, mode=SearchMode.HYBRID)

    # Verify retrieval_k = top_k * 2
    # Check that keyword_store.search was called with top_k=20 (2x)
    call_kwargs = keyword_store.search.call_args.kwargs
    assert call_kwargs["top_k"] == 20
