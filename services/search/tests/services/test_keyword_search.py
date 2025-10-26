"""Tests for keyword search service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.services.keyword_search import KeywordSearchService
from app.models.domain import Chunk


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def keyword_service():
    """Keyword search service."""
    return KeywordSearchService()


@pytest.mark.asyncio
async def test_search_returns_chunks(keyword_service, mock_db_session):
    """Test keyword search returns chunk objects."""
    # Mock database result
    doc_id = uuid4()
    chunk_id = uuid4()

    mock_row = MagicMock()
    mock_row.id = chunk_id
    mock_row.document_id = doc_id
    mock_row.content = "Python programming language"
    mock_row.tokens = 3
    mock_row.document_title = "Python Guide"
    mock_row.rank = 0.95

    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row]
    mock_db_session.execute.return_value = mock_result

    # Execute search
    results = await keyword_service.search(
        session=mock_db_session,
        query_text="Python",
        top_k=10
    )

    # Verify
    assert len(results) == 1
    assert isinstance(results[0], Chunk)
    assert results[0].content == "Python programming language"
    assert results[0].document_title == "Python Guide"
    assert results[0].score is not None


@pytest.mark.asyncio
async def test_search_with_document_filter(keyword_service, mock_db_session):
    """Test keyword search with document filter."""
    doc_id = uuid4()

    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db_session.execute.return_value = mock_result

    await keyword_service.search(
        session=mock_db_session,
        query_text="test",
        top_k=10,
        document_id=doc_id
    )

    # Verify execute was called
    assert mock_db_session.execute.called
