"""Tests for PostgreSQL keyword store."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.infrastructure.search.postgres_keyword_store import PostgresKeywordStoreImpl
from app.domain.entities.chunk import Chunk


@pytest.mark.asyncio
async def test_postgres_keyword_store_searches_with_fts():
    """Test PostgreSQL FTS search returns chunks."""
    # Mock database session
    db_session = AsyncMock()

    # Mock query result
    mock_row = MagicMock()
    mock_row.id = uuid4()
    mock_row.document_id = uuid4()
    mock_row.content = "Kubernetes orchestrates containers"
    mock_row.tokens = 10
    mock_row.chunk_metadata = {}
    mock_row.section_title = None
    mock_row.section_level = None
    mock_row.page_number = None
    mock_row.rank = 0.5

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]

    db_session.execute = AsyncMock(return_value=mock_result)

    # Create store and search
    store = PostgresKeywordStoreImpl(db_session)
    results = await store.search(
        query_text="Kubernetes containers",
        top_k=10
    )

    # Verify
    assert len(results) == 1
    assert results[0].content == "Kubernetes orchestrates containers"
    assert db_session.execute.called


@pytest.mark.asyncio
async def test_postgres_keyword_store_handles_document_filter():
    """Test document_id filter is applied."""
    db_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    db_session.execute = AsyncMock(return_value=mock_result)

    store = PostgresKeywordStoreImpl(db_session)
    doc_id = uuid4()

    await store.search(
        query_text="test",
        top_k=10,
        document_id=doc_id
    )

    # Verify execute was called with document_id in params
    call_args = db_session.execute.call_args
    params = call_args[0][1]
    assert params["document_id"] == str(doc_id)
