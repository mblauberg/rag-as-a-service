"""Tests for ListDocumentsUseCase."""
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from datetime import datetime, UTC

from app.application.use_cases.list_documents import ListDocumentsUseCase
from app.domain.entities.document import Document
from app.core.enums import UploadStatus
from app.ports.repositories import DocumentRepository


@pytest.mark.asyncio
async def test_list_documents_success():
    """Test successful document listing."""
    mock_doc_repo = Mock(spec=DocumentRepository)

    # Mock paginated results
    doc1 = Document(
        id=uuid4(),
        title="Document 1",
        file_name="doc1.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.COMPLETED
    )
    doc2 = Document(
        id=uuid4(),
        title="Document 2",
        file_name="doc2.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.COMPLETED
    )

    mock_doc_repo.find_all = AsyncMock(return_value=([doc1, doc2], 50))

    use_case = ListDocumentsUseCase(document_repo=mock_doc_repo)

    # Execute listing
    documents, total = await use_case.execute(page=1, limit=20)

    # Verify results
    assert len(documents) == 2
    assert total == 50
    assert documents[0].title == "Document 1"
    assert documents[1].title == "Document 2"

    # Verify interactions
    mock_doc_repo.find_all.assert_called_once_with(page=1, limit=20)


@pytest.mark.asyncio
async def test_list_documents_empty():
    """Test listing with no documents."""
    mock_doc_repo = Mock(spec=DocumentRepository)
    mock_doc_repo.find_all = AsyncMock(return_value=([], 0))

    use_case = ListDocumentsUseCase(document_repo=mock_doc_repo)

    documents, total = await use_case.execute(page=1, limit=20)

    assert len(documents) == 0
    assert total == 0


@pytest.mark.asyncio
async def test_list_documents_invalid_page():
    """Test listing with invalid page number."""
    mock_doc_repo = Mock(spec=DocumentRepository)
    use_case = ListDocumentsUseCase(document_repo=mock_doc_repo)

    with pytest.raises(ValueError, match="Page must be >= 1"):
        await use_case.execute(page=0, limit=20)


@pytest.mark.asyncio
async def test_list_documents_invalid_limit():
    """Test listing with invalid limit."""
    mock_doc_repo = Mock(spec=DocumentRepository)
    use_case = ListDocumentsUseCase(document_repo=mock_doc_repo)

    with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
        await use_case.execute(page=1, limit=0)

    with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
        await use_case.execute(page=1, limit=101)
