"""Repository port definitions.

Repositories abstract data persistence, following the Repository pattern.
These are interfaces - infrastructure layer provides implementations.
"""
from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document


class DocumentRepository(ABC):
    """Port for document persistence operations."""

    @abstractmethod
    async def save(self, document: Document) -> Document:
        """Persist document to storage.

        Args:
            document: Document entity to persist

        Returns:
            Persisted document (may have generated fields)
        """
        pass

    @abstractmethod
    async def find_by_id(self, document_id: UUID) -> Document | None:
        """Retrieve document by ID.

        Args:
            document_id: Document UUID

        Returns:
            Document if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_all(self, page: int, limit: int) -> tuple[list[Document], int]:
        """Retrieve paginated documents.

        Args:
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (documents list, total count)
        """
        pass

    @abstractmethod
    async def delete(self, document_id: UUID) -> None:
        """Delete document from storage.

        Args:
            document_id: Document UUID to delete
        """
        pass


class ChunkRepository(ABC):
    """Port for chunk persistence operations."""

    @abstractmethod
    async def save_batch(self, chunks: list[Chunk]) -> list[Chunk]:
        """Persist multiple chunks atomically.

        Args:
            chunks: List of chunk entities

        Returns:
            Persisted chunks
        """
        pass

    @abstractmethod
    async def find_by_document_id(self, document_id: UUID) -> list[Chunk]:
        """Retrieve all chunks for a document.

        Args:
            document_id: Document UUID

        Returns:
            List of chunks (may be empty)
        """
        pass

    @abstractmethod
    async def delete_by_document_id(self, document_id: UUID) -> None:
        """Delete all chunks for a document.

        Args:
            document_id: Document UUID
        """
        pass
