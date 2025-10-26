"""Base document processor interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DocumentElement:
    """Represents a structured element from a document."""

    content: str
    element_type: str  # paragraph, heading, table, list_item, etc.
    metadata: dict[str, Any]
    page_number: int | None = None
    section_level: int | None = None
    section_title: str | None = None


@dataclass
class ProcessedDocument:
    """Represents a fully processed document."""

    elements: list[DocumentElement]
    metadata: dict[str, Any]
    document_type: str


class BaseDocumentProcessor(ABC):
    """Base class for document processors."""

    @abstractmethod
    def process(self, file_path: Path) -> ProcessedDocument:
        """
        Process document and extract structured elements.

        Args:
            file_path: Path to document file

        Returns:
            ProcessedDocument with structured elements
        """
        pass

    @abstractmethod
    def supports_file_type(self, file_type: str) -> bool:
        """
        Check if processor supports given file type.

        Args:
            file_type: File type (e.g., 'pdf', 'docx')

        Returns:
            True if supported
        """
        pass
