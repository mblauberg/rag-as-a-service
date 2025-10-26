"""File type detection and text extraction utilities."""
try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FileProcessor:
    """Utility class for file processing and text extraction."""

    @staticmethod
    def detect_file_type(file_path: str) -> str:
        """
        Detect file MIME type.

        Args:
            file_path: Path to file

        Returns:
            MIME type string
        """
        # Fallback to extension-based detection
        suffix = Path(file_path).suffix.lower()
        mime_map = {
            ".txt": "text/plain",
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
        }

        if MAGIC_AVAILABLE:
            try:
                mime = magic.Magic(mime=True)
                return mime.from_file(file_path)
            except Exception as e:
                logger.warning(f"Could not detect file type with magic: {e}")
                return mime_map.get(suffix, "application/octet-stream")
        else:
            return mime_map.get(suffix, "application/octet-stream")

    @staticmethod
    def extract_text(file_path: str, file_type: str) -> str:
        """
        Extract text content from file based on type.

        Args:
            file_path: Path to file
            file_type: MIME type of file

        Returns:
            Extracted text content

        Raises:
            ValueError: If file type is not supported
        """
        if file_type == "text/plain" or file_type.startswith("text/"):
            return FileProcessor._extract_text_plain(file_path)
        elif file_type == "application/pdf":
            return FileProcessor._extract_text_pdf(file_path)
        elif "wordprocessingml" in file_type or file_type == "application/msword":
            return FileProcessor._extract_text_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    def _extract_text_plain(file_path: str) -> str:
        """Extract text from plain text file."""
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def _extract_text_pdf(file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            from PyPDF2 import PdfReader  # type: ignore[import-not-found]

            reader = PdfReader(file_path)
            text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            return "\n\n".join(text)
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise ValueError(f"Could not extract text from PDF: {str(e)}") from e

    @staticmethod
    def _extract_text_docx(file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            from docx import Document

            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)
            return "\n\n".join(text)
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            raise ValueError(f"Could not extract text from DOCX: {str(e)}") from e


# Global file processor instance
file_processor = FileProcessor()
