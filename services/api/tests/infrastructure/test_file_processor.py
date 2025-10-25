"""Tests for FileProcessor infrastructure adapter."""
import pytest
from io import BytesIO
from pypdf import PdfWriter

from app.infrastructure.processing.file_processor import FileProcessorImpl
from app.core.exceptions import FileProcessingError


@pytest.fixture
def file_processor():
    """Create FileProcessor instance."""
    return FileProcessorImpl()


@pytest.fixture
def sample_pdf_bytes():
    """Create a simple PDF file in memory."""
    pdf_writer = PdfWriter()
    pdf_writer.add_blank_page(width=200, height=200)

    # Add some text to the page
    from pypdf.generic import NameObject, TextStringObject
    page = pdf_writer.pages[0]
    # Note: This is a simplified PDF. For real text, we'd need more complex structure
    # For testing, we'll use a different approach - create from scratch

    buffer = BytesIO()
    pdf_writer.write(buffer)
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def sample_pdf_with_text():
    """Create a PDF with actual extractable text."""
    # Create a simple PDF with text using reportlab
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 700, "Hello World! This is test content.")
        c.save()
        buffer.seek(0)
        return buffer.read()
    except ImportError:
        # Fallback: Create a basic PDF manually
        # This is a minimal valid PDF with text
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 55 >>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World! This is test content.) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
424
%%EOF"""
        return pdf_content


@pytest.fixture
def sample_text_bytes():
    """Create sample text file bytes."""
    return b"This is a sample text file.\nIt has multiple lines.\nFor testing purposes."


class TestFileProcessorImpl:
    """Test suite for FileProcessorImpl."""

    @pytest.mark.asyncio
    async def test_extract_text_from_txt_file(self, file_processor, sample_text_bytes):
        """Test extracting text from a plain text file."""
        result = await file_processor.extract_text(sample_text_bytes, "txt")

        assert result == "This is a sample text file.\nIt has multiple lines.\nFor testing purposes."
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_extract_text_from_pdf_file(self, file_processor, sample_pdf_with_text):
        """Test extracting text from a PDF file."""
        result = await file_processor.extract_text(sample_pdf_with_text, "pdf")

        # PDF extraction might have some formatting differences
        assert "Hello World" in result
        assert "test content" in result
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_extract_text_from_empty_txt_file(self, file_processor):
        """Test extracting text from an empty text file."""
        empty_bytes = b""
        result = await file_processor.extract_text(empty_bytes, "txt")

        assert result == ""

    @pytest.mark.asyncio
    async def test_extract_text_from_txt_with_special_chars(self, file_processor):
        """Test extracting text with special characters."""
        special_text = "Hello 世界! Special chars: é, ñ, ü, 你好"
        special_bytes = special_text.encode("utf-8")

        result = await file_processor.extract_text(special_bytes, "txt")

        assert result == special_text

    @pytest.mark.asyncio
    async def test_extract_text_unsupported_file_type(self, file_processor):
        """Test that unsupported file types raise FileProcessingError."""
        sample_bytes = b"Some content"

        with pytest.raises(FileProcessingError) as exc_info:
            await file_processor.extract_text(sample_bytes, "docx")

        assert "Unsupported file type" in str(exc_info.value)
        assert "docx" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_text_from_corrupted_pdf(self, file_processor):
        """Test that corrupted PDF raises FileProcessingError."""
        corrupted_pdf = b"Not a real PDF file"

        with pytest.raises(FileProcessingError) as exc_info:
            await file_processor.extract_text(corrupted_pdf, "pdf")

        assert "Failed to extract text from pdf" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_text_from_pdf_with_no_text(self, file_processor, sample_pdf_bytes):
        """Test extracting from PDF with no text content (blank page)."""
        # This should succeed but return empty or minimal text
        result = await file_processor.extract_text(sample_pdf_bytes, "pdf")

        assert isinstance(result, str)
        # Blank PDFs might have some metadata or be empty
        assert len(result) >= 0

    @pytest.mark.asyncio
    async def test_extract_text_invalid_utf8(self, file_processor):
        """Test that invalid UTF-8 in text file raises FileProcessingError."""
        invalid_bytes = b"\x80\x81\x82\x83"  # Invalid UTF-8 sequence

        with pytest.raises(FileProcessingError) as exc_info:
            await file_processor.extract_text(invalid_bytes, "txt")

        assert "Failed to decode text file" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_text_case_insensitive_file_type(self, file_processor, sample_text_bytes):
        """Test that file types are handled case-insensitively."""
        result_lower = await file_processor.extract_text(sample_text_bytes, "txt")
        result_upper = await file_processor.extract_text(sample_text_bytes, "TXT")

        assert result_lower == result_upper

    @pytest.mark.asyncio
    async def test_extract_text_with_file_type_extension(self, file_processor, sample_text_bytes):
        """Test that file type with dot prefix works."""
        result_no_dot = await file_processor.extract_text(sample_text_bytes, "txt")
        result_with_dot = await file_processor.extract_text(sample_text_bytes, ".txt")

        assert result_no_dot == result_with_dot
