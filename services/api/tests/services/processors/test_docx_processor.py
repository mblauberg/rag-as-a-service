import pytest
from app.services.processors.docx_processor import DOCXProcessor


def test_docx_processor_supports_docx():
    """Test that DOCX processor supports DOCX files"""
    processor = DOCXProcessor()
    assert processor.supports_file_type("docx") is True
    assert processor.supports_file_type("pdf") is False
