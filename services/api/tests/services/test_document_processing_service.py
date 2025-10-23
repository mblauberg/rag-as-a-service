import pytest
from pathlib import Path
from app.services.document_processing_service import DocumentProcessingService
from app.models.schemas import DocumentType


def test_get_processor_for_pdf():
    """Test getting processor for PDF"""
    service = DocumentProcessingService()
    processor = service.get_processor(DocumentType.PDF)
    assert processor is not None
    assert processor.supports_file_type("pdf")


def test_get_processor_for_docx():
    """Test getting processor for DOCX"""
    service = DocumentProcessingService()
    processor = service.get_processor(DocumentType.DOCX)
    assert processor is not None
    assert processor.supports_file_type("docx")


def test_get_processor_unsupported():
    """Test getting processor for unsupported type raises error"""
    service = DocumentProcessingService()
    # XLSX not yet registered
    with pytest.raises(ValueError, match="Unsupported document type"):
        service.get_processor(DocumentType.XLSX)
