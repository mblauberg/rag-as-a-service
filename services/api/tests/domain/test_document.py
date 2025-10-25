"""Tests for Document domain entity."""
import pytest
from datetime import datetime
from uuid import uuid4

from app.domain.entities.document import Document
from app.core.enums import UploadStatus


def test_document_creation():
    """Test creating a document entity."""
    doc_id = uuid4()
    now = datetime.utcnow()

    document = Document(
        id=doc_id,
        title="Test Document",
        file_name="test.pdf",
        file_type="pdf",
        created_at=now,
        upload_status=UploadStatus.PROCESSING
    )

    assert document.id == doc_id
    assert document.title == "Test Document"
    assert document.upload_status == UploadStatus.PROCESSING


def test_document_mark_completed():
    """Test marking document as completed."""
    document = Document(
        id=uuid4(),
        title="Test",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.utcnow(),
        upload_status=UploadStatus.PROCESSING
    )

    document.mark_completed()

    assert document.upload_status == UploadStatus.COMPLETED


def test_document_mark_failed():
    """Test marking document as failed."""
    document = Document(
        id=uuid4(),
        title="Test",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.utcnow(),
        upload_status=UploadStatus.PROCESSING
    )

    document.mark_failed()

    assert document.upload_status == UploadStatus.FAILED
