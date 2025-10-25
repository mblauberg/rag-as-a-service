"""FileProcessor infrastructure adapter implementation.

This module implements the FileProcessor port interface for extracting
text from various file formats (PDF, TXT).
"""
from io import BytesIO

from pypdf import PdfReader

from app.core.exceptions import FileProcessingError
from app.ports.services import FileProcessor


class FileProcessorImpl(FileProcessor):
    """Implementation of FileProcessor port using pypdf for PDF extraction."""

    SUPPORTED_TYPES = {"pdf", "txt"}

    async def extract_text(self, file_content: bytes, file_type: str) -> str:
        """Extract text from file content.

        Args:
            file_content: Raw file bytes
            file_type: File type (pdf, txt)

        Returns:
            Extracted text content

        Raises:
            FileProcessingError: If text extraction fails or file type is unsupported
        """
        # Normalize file type (remove leading dot, convert to lowercase)
        normalized_type = file_type.lower().lstrip(".")

        if normalized_type not in self.SUPPORTED_TYPES:
            raise FileProcessingError(
                operation="extract_text",
                original_error=ValueError(f"Unsupported file type: {file_type}")
            )

        try:
            if normalized_type == "pdf":
                return await self._extract_from_pdf(file_content)
            elif normalized_type == "txt":
                return await self._extract_from_txt(file_content)
        except FileProcessingError:
            # Re-raise FileProcessingError as-is
            raise
        except Exception as e:
            raise FileProcessingError(
                operation=f"extract_text from {normalized_type}",
                original_error=e
            )

    async def _extract_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file.

        Args:
            file_content: PDF file bytes

        Returns:
            Extracted text content

        Raises:
            FileProcessingError: If PDF extraction fails
        """
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PdfReader(pdf_file)

            text_parts = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n".join(text_parts)

        except Exception as e:
            raise FileProcessingError(
                operation="Failed to extract text from pdf",
                original_error=e
            )

    async def _extract_from_txt(self, file_content: bytes) -> str:
        """Extract text from plain text file.

        Args:
            file_content: Text file bytes

        Returns:
            Decoded text content

        Raises:
            FileProcessingError: If text decoding fails
        """
        try:
            return file_content.decode("utf-8")
        except UnicodeDecodeError as e:
            raise FileProcessingError(
                operation="Failed to decode text file",
                original_error=e
            )
