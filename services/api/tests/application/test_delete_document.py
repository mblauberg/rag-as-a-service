"""Tests for DeleteDocumentUseCase."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.application.use_cases.delete_document import DeleteDocumentUseCase
from app.core.enums import UploadStatus
from app.core.exceptions import DocumentNotFoundError
from app.domain.entities.document import Document
from app.ports.repositories import ChunkRepository, DocumentRepository
from app.ports.services import VectorStore


@pytest.mark.asyncio
async def test_delete_document_success():
    """Test successful document deletion."""
    doc_id = uuid4()
    mock_doc_repo = Mock(spec=DocumentRepository)
    mock_chunk_repo = Mock(spec=ChunkRepository)
    mock_vector_store = Mock(spec=VectorStore)

    # Mock document exists
    mock_doc_repo.find_by_id = AsyncMock(
        return_value=Document(
            id=doc_id,
            title="Test",
            file_name="test.pdf",
            file_type="pdf",
            created_at=datetime.now(UTC),
            upload_status=UploadStatus.COMPLETED,
        )
    )
    mock_doc_repo.delete = AsyncMock()
    mock_chunk_repo.delete_by_document_id = AsyncMock()
    mock_vector_store.delete_by_document = AsyncMock()

    use_case = DeleteDocumentUseCase(
        document_repo=mock_doc_repo,
        chunk_repo=mock_chunk_repo,
        vector_store=mock_vector_store,
    )

    await use_case.execute(doc_id)

    # Verify all deletions occurred
    mock_vector_store.delete_by_document.assert_called_once_with(doc_id)
    mock_chunk_repo.delete_by_document_id.assert_called_once_with(doc_id)
    mock_doc_repo.delete.assert_called_once_with(doc_id)


@pytest.mark.asyncio
async def test_delete_document_not_found():
    """Test deleting non-existent document raises error."""
    doc_id = uuid4()
    mock_doc_repo = Mock(spec=DocumentRepository)
    mock_doc_repo.find_by_id = AsyncMock(return_value=None)

    use_case = DeleteDocumentUseCase(
        document_repo=mock_doc_repo,
        chunk_repo=Mock(spec=ChunkRepository),
        vector_store=Mock(spec=VectorStore),
    )

    with pytest.raises(DocumentNotFoundError):
        await use_case.execute(doc_id)
