"""FileProcessor infrastructure adapter implementation.

This module implements the FileProcessor port interface for extracting
text from various file formats (PDF, TXT, DOCX, MD, CSV).
"""
import csv
from io import BytesIO, StringIO

from docx import Document
from pypdf import PdfReader

from app.core.exceptions import FileProcessingError
from app.ports.services import FileProcessor


class FileProcessorImpl(FileProcessor):
    """Implementation of FileProcessor port using pypdf for PDF extraction."""

    SUPPORTED_TYPES = {"pdf", "txt", "docx", "md", "markdown", "csv"}

    async def extract_text(self, file_content: bytes, file_type: str) -> str:  # type: ignore[return]
        """Extract text from file content.

        Args:
            file_content: Raw file bytes
            file_type: File type (pdf, txt)

        Returns:
            Extracted text content

        Raises:
            FileProcessingError: If text extraction fails or file type is unsupported
        """
        # Validate file content is not None (empty bytes b"" is valid)
        if file_content is None:
            raise FileProcessingError(
                operation="extract_text",
                original_error=ValueError("File content is None"),
            )

        # Normalize file type (remove leading dot, convert to lowercase)
        normalized_type = file_type.lower().lstrip(".")

        if normalized_type not in self.SUPPORTED_TYPES:
            raise FileProcessingError(
                operation="extract_text",
                original_error=ValueError(f"Unsupported file type: {file_type}"),
            )

        try:
            if normalized_type == "pdf":
                return await self._extract_from_pdf(file_content)
            elif normalized_type == "txt":
                return await self._extract_from_txt(file_content)
            elif normalized_type == "docx":
                return await self._extract_from_docx(file_content)
            elif normalized_type in ("md", "markdown"):
                return await self._extract_from_markdown(file_content)
            elif normalized_type == "csv":
                return await self._extract_from_csv(file_content)
        except FileProcessingError:
            # Re-raise FileProcessingError as-is
            raise
        except Exception as e:
            raise FileProcessingError(
                operation=f"extract_text from {normalized_type}", original_error=e
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
                operation="Failed to extract text from pdf", original_error=e
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
                operation="Failed to decode text file", original_error=e
            )

    async def _extract_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file.

        Args:
            file_content: DOCX file bytes

        Returns:
            Extracted text content

        Raises:
            FileProcessingError: If DOCX extraction fails
        """
        try:
            docx_file = BytesIO(file_content)
            doc = Document(docx_file)

            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)

            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text)
                    if row_text:
                        text_parts.append(" | ".join(row_text))

            return "\n\n".join(text_parts)

        except Exception as e:
            raise FileProcessingError(
                operation="Failed to extract text from docx", original_error=e
            )

    async def _extract_from_markdown(self, file_content: bytes) -> str:
        """Extract text from Markdown file.

        Markdown files are plain text, so we just decode them.

        Args:
            file_content: Markdown file bytes

        Returns:
            Decoded text content

        Raises:
            FileProcessingError: If text decoding fails
        """
        try:
            return file_content.decode("utf-8")
        except UnicodeDecodeError as e:
            raise FileProcessingError(
                operation="Failed to decode markdown file", original_error=e
            )

    async def _extract_from_csv(self, file_content: bytes) -> str:
        """Extract text from CSV file.

        Converts CSV data to a readable text format.

        Args:
            file_content: CSV file bytes

        Returns:
            Text representation of CSV data

        Raises:
            FileProcessingError: If CSV processing fails
        """
        try:
            # Decode bytes to string
            csv_text = file_content.decode("utf-8")

            # Parse CSV
            csv_file = StringIO(csv_text)
            reader = csv.reader(csv_file)

            # Convert rows to text
            text_parts = []
            for row in reader:
                if row:  # Skip empty rows
                    text_parts.append(" | ".join(row))

            return "\n".join(text_parts)

        except UnicodeDecodeError as e:
            raise FileProcessingError(
                operation="Failed to decode CSV file", original_error=e
            )
        except Exception as e:
            raise FileProcessingError(
                operation="Failed to extract text from csv", original_error=e
            )
