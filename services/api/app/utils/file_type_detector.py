"""File type detection utility."""
from enum import Enum
from pathlib import Path


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    CSV = "csv"
    XLSX = "xlsx"
    PPTX = "pptx"
    HTML = "html"


class FileTypeDetector:
    """Detect document type from filename or content."""

    EXTENSION_MAP = {
        '.pdf': DocumentType.PDF,
        '.docx': DocumentType.DOCX,
        '.txt': DocumentType.TXT,
        '.md': DocumentType.MD,
        '.markdown': DocumentType.MD,
        '.csv': DocumentType.CSV,
        '.xlsx': DocumentType.XLSX,
        '.xls': DocumentType.XLSX,
        '.pptx': DocumentType.PPTX,
        '.ppt': DocumentType.PPTX,
        '.html': DocumentType.HTML,
        '.htm': DocumentType.HTML,
    }

    def detect_from_filename(self, filename: str) -> DocumentType:
        """
        Detect document type from filename extension.

        Args:
            filename: Name of file

        Returns:
            DocumentType enum value

        Raises:
            ValueError: If file type is not supported
        """
        extension = Path(filename).suffix.lower()

        if extension not in self.EXTENSION_MAP:
            raise ValueError(f"Unsupported file type: {extension}")

        return self.EXTENSION_MAP[extension]

    def is_supported(self, filename: str) -> bool:
        """
        Check if file type is supported.

        Args:
            filename: Name of file

        Returns:
            True if supported, False otherwise
        """
        extension = Path(filename).suffix.lower()
        return extension in self.EXTENSION_MAP
