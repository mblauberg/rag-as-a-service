import pytest
from app.utils.file_type_detector import FileTypeDetector
from app.models.schemas import DocumentType


def test_detect_pdf():
    """Test PDF detection"""
    detector = FileTypeDetector()
    assert detector.detect_from_filename("document.pdf") == DocumentType.PDF


def test_detect_docx():
    """Test DOCX detection"""
    detector = FileTypeDetector()
    assert detector.detect_from_filename("report.docx") == DocumentType.DOCX


def test_detect_txt():
    """Test TXT detection"""
    detector = FileTypeDetector()
    assert detector.detect_from_filename("notes.txt") == DocumentType.TXT


def test_detect_markdown():
    """Test Markdown detection"""
    detector = FileTypeDetector()
    assert detector.detect_from_filename("README.md") == DocumentType.MD


def test_detect_csv():
    """Test CSV detection"""
    detector = FileTypeDetector()
    assert detector.detect_from_filename("data.csv") == DocumentType.CSV


def test_detect_unsupported():
    """Test unsupported file type"""
    detector = FileTypeDetector()
    with pytest.raises(ValueError, match="Unsupported file type"):
        detector.detect_from_filename("image.jpg")


def test_is_supported_true():
    """Test is_supported returns True for supported types"""
    detector = FileTypeDetector()
    assert detector.is_supported("document.pdf") is True


def test_is_supported_false():
    """Test is_supported returns False for unsupported types"""
    detector = FileTypeDetector()
    assert detector.is_supported("image.jpg") is False
