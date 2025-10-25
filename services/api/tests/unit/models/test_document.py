"""Test document models use enums"""
from app.models.document import Document, DocumentChunk
from app.core.enums import UploadStatus, EmbeddingStatus


def test_document_column_defaults_use_enums():
    """Test Document model columns have enum defaults"""
    # Check that Column defaults are set to enum values
    upload_col = Document.__table__.columns['upload_status']
    embedding_col = Document.__table__.columns['embedding_status']

    # Column defaults should be enum values
    assert upload_col.default.arg == UploadStatus.PENDING.value
    assert embedding_col.default.arg == EmbeddingStatus.PENDING.value


def test_document_can_set_enum_status():
    """Test Document can be set with enum values"""
    doc = Document(
        title="Test",
        description="Test doc",
        file_name="test.pdf",
        file_type="application/pdf",
        file_size=1024,
        upload_status=UploadStatus.PROCESSING.value,
        embedding_status=EmbeddingStatus.PROCESSING.value
    )

    assert doc.upload_status == UploadStatus.PROCESSING.value
    assert doc.embedding_status == EmbeddingStatus.PROCESSING.value


def test_document_status_is_string_type():
    """Test status values are string types for database compatibility"""
    doc = Document(
        title="Test",
        description="Test doc",
        file_name="test.pdf",
        file_type="application/pdf",
        file_size=1024,
        upload_status=UploadStatus.COMPLETED.value,
        embedding_status=EmbeddingStatus.COMPLETED.value
    )

    # When explicitly set, should be strings
    assert isinstance(doc.upload_status, str)
    assert isinstance(doc.embedding_status, str)
    assert doc.upload_status == "completed"
    assert doc.embedding_status == "completed"
