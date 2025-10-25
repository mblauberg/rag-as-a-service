import pytest
from app.services.processors.pdf_processor import PDFProcessor


def test_pdf_processor_supports_pdf():
    """Test that PDF processor supports PDF files"""
    processor = PDFProcessor()
    assert processor.supports_file_type("pdf") is True
    assert processor.supports_file_type("docx") is False
