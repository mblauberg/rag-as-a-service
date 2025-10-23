"""Base document processor interface."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentElement:
    """Represents a structured element from a document."""
    content: str
    element_type: str  # paragraph, heading, table, list_item, etc.
    metadata: Dict[str, Any]
    page_number: Optional[int] = None
    section_level: Optional[int] = None
    section_title: Optional[str] = None


@dataclass
class ProcessedDocument:
    """Represents a fully processed document."""
    elements: List[DocumentElement]
    metadata: Dict[str, Any]
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
