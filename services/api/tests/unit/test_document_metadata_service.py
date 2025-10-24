"""Unit tests for DocumentMetadataService."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.document_metadata_service import DocumentMetadataService
from app.models.document import Document, DocumentChunk
from app.models.schemas import DocumentListResponse, DocumentDetailResponse
from app.core.exceptions import DocumentNotFoundError


@pytest.fixture
def metadata_service():
    """Create DocumentMetadataService instance."""
    return DocumentMetadataService()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    mock = AsyncMock(spec=AsyncSession)
    return mock


@pytest.fixture
def sample_document():
    """Create sample document for testing."""
    from datetime import datetime
    doc_id = uuid4()
    now = datetime.utcnow()
    return Document(
        id=doc_id,
        title="Test Document",
        description="Test description",
        file_name="test.pdf",
        file_type="application/pdf",
        file_size=1024,
        file_path="/uploads/test.pdf",
        document_type="pdf",
        upload_status="completed",
        embedding_status="pending",
        created_at=now,
        updated_at=now
    )


@pytest.fixture
def sample_chunks_data():
    """Create sample chunks data for testing."""
    return [
        {
            "content": "This is chunk 1",
            "section_title": "Introduction",
            "section_level": 1,
            "page_number": 1,
            "tokens": 10,
            "metadata": {"source": "test"}
        },
        {
            "content": "This is chunk 2",
            "section_title": "Body",
            "section_level": 1,
            "page_number": 2,
            "tokens": 12,
            "metadata": {"source": "test"}
        }
    ]


@pytest.mark.asyncio
class TestDocumentMetadataService:
    """Test suite for DocumentMetadataService."""

    async def test_create_document_success(self, metadata_service, mock_db):
        """Test successful document creation."""
        title = "Test Document"
        description = "Test description"
        file_name = "test.pdf"
        file_type = "application/pdf"
        file_size = 1024
        file_path = "/uploads/test.pdf"
        document_type = "pdf"

        # Mock flush to assign ID
        async def mock_flush():
            # Simulate ID assignment
            for call in mock_db.add.call_args_list:
                if call[0]:  # Check if there are positional args
                    obj = call[0][0]
                    if isinstance(obj, Document) and obj.id is None:
                        obj.id = uuid4()

        mock_db.flush.side_effect = mock_flush

        document = await metadata_service.create_document(
            db=mock_db,
            title=title,
            description=description,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            document_type=document_type
        )

        assert document.title == title
        assert document.description == description
        assert document.file_name == file_name
        assert document.file_type == file_type
        assert document.file_size == file_size
        assert document.file_path == file_path
        assert document.document_type == document_type
        assert document.upload_status == "processing"
        assert document.embedding_status == "pending"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    async def test_get_documents_success(self, metadata_service, mock_db, sample_document):
        """Test successful document list retrieval."""
        # Mock count query
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        # Mock documents query
        documents_result = MagicMock()
        documents_result.scalars.return_value.all.return_value = [sample_document]

        mock_db.execute.side_effect = [count_result, documents_result]

        result = await metadata_service.get_documents(mock_db, page=1, limit=20)

        assert isinstance(result, DocumentListResponse)
        assert result.total == 1
        assert result.page == 1
        assert result.limit == 20
        assert len(result.documents) == 1
        assert result.documents[0].title == "Test Document"

    async def test_get_documents_empty(self, metadata_service, mock_db):
        """Test document list retrieval with no documents."""
        # Mock count query
        count_result = MagicMock()
        count_result.scalar.return_value = 0

        # Mock documents query
        documents_result = MagicMock()
        documents_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [count_result, documents_result]

        result = await metadata_service.get_documents(mock_db, page=1, limit=20)

        assert result.total == 0
        assert len(result.documents) == 0

    async def test_get_documents_pagination(self, metadata_service, mock_db):
        """Test document list retrieval with pagination."""
        # Mock count query
        count_result = MagicMock()
        count_result.scalar.return_value = 50

        # Mock documents query
        documents_result = MagicMock()
        documents_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [count_result, documents_result]

        result = await metadata_service.get_documents(mock_db, page=2, limit=10)

        assert result.page == 2
        assert result.limit == 10
        assert result.total == 50

    async def test_get_document_by_id_success(self, metadata_service, mock_db, sample_document):
        """Test successful document retrieval by ID."""
        document_id = sample_document.id

        # Mock query result
        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = sample_document
        mock_db.execute.return_value = query_result

        result = await metadata_service.get_document_by_id(mock_db, document_id)

        assert result is not None
        assert isinstance(result, DocumentDetailResponse)
        assert result.title == "Test Document"

    async def test_get_document_by_id_not_found(self, metadata_service, mock_db):
        """Test document retrieval by ID when not found."""
        document_id = uuid4()

        # Mock query result
        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = query_result

        result = await metadata_service.get_document_by_id(mock_db, document_id)

        assert result is None

    async def test_delete_document_success(self, metadata_service, mock_db, sample_document):
        """Test successful document deletion."""
        document_id = sample_document.id

        # Mock query result
        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = sample_document
        mock_db.execute.return_value = query_result

        deleted_doc = await metadata_service.delete_document(mock_db, document_id)

        assert deleted_doc.id == document_id
        mock_db.delete.assert_called_once_with(sample_document)
        mock_db.commit.assert_called_once()

    async def test_delete_document_not_found(self, metadata_service, mock_db):
        """Test document deletion when document not found."""
        document_id = uuid4()

        # Mock query result
        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = query_result

        with pytest.raises(DocumentNotFoundError):
            await metadata_service.delete_document(mock_db, document_id)

        mock_db.delete.assert_not_called()

    async def test_update_embedding_status_success(self, metadata_service, mock_db, sample_document):
        """Test successful embedding status update."""
        document_id = sample_document.id
        new_status = "completed"

        # Mock query result
        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = sample_document
        mock_db.execute.return_value = query_result

        await metadata_service.update_embedding_status(mock_db, document_id, new_status)

        assert sample_document.embedding_status == new_status
        mock_db.commit.assert_called_once()

    async def test_update_embedding_status_not_found(self, metadata_service, mock_db):
        """Test embedding status update when document not found."""
        document_id = uuid4()

        # Mock query result
        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = query_result

        # Should not raise error, just log warning
        await metadata_service.update_embedding_status(mock_db, document_id, "completed")

        mock_db.commit.assert_not_called()

    async def test_update_upload_status_success(self, metadata_service, mock_db, sample_document):
        """Test successful upload status update."""
        document_id = sample_document.id
        new_status = "completed"

        # Mock query result
        query_result = MagicMock()
        query_result.scalar_one_or_none.return_value = sample_document
        mock_db.execute.return_value = query_result

        await metadata_service.update_upload_status(mock_db, document_id, new_status)

        assert sample_document.upload_status == new_status
        mock_db.commit.assert_called_once()

    async def test_create_chunk_records_success(self, metadata_service, mock_db, sample_chunks_data):
        """Test successful chunk records creation."""
        document_id = uuid4()

        # Mock flush to assign IDs
        async def mock_flush():
            for call in mock_db.add.call_args_list:
                if call[0]:
                    obj = call[0][0]
                    if isinstance(obj, DocumentChunk) and obj.id is None:
                        obj.id = uuid4()

        mock_db.flush.side_effect = mock_flush

        chunks = await metadata_service.create_chunk_records(
            db=mock_db,
            document_id=document_id,
            chunks_data=sample_chunks_data
        )

        assert len(chunks) == 2
        assert chunks[0].document_id == document_id
        assert chunks[0].chunk_index == 0
        assert chunks[0].chunk_text == "This is chunk 1"
        assert chunks[0].section_title == "Introduction"
        assert chunks[0].chunk_tokens == 10

        assert chunks[1].chunk_index == 1
        assert chunks[1].chunk_text == "This is chunk 2"
        assert mock_db.add.call_count == 2
        mock_db.flush.assert_called_once()

    async def test_create_chunk_records_empty(self, metadata_service, mock_db):
        """Test chunk records creation with empty data."""
        document_id = uuid4()

        chunks = await metadata_service.create_chunk_records(
            db=mock_db,
            document_id=document_id,
            chunks_data=[]
        )

        assert len(chunks) == 0
        mock_db.add.assert_not_called()
