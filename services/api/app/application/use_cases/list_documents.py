"""List documents use case."""
import logging

from app.domain.entities.document import Document
from app.ports.repositories import DocumentRepository

logger = logging.getLogger(__name__)


class ListDocumentsUseCase:
    """Use case for paginated document listing."""

    def __init__(self, document_repo: DocumentRepository):
        """Initialize with document repository."""
        self.document_repo = document_repo

    async def execute(self, page: int = 1, limit: int = 20) -> tuple[list[Document], int]:
        """List documents with pagination.

        Args:
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (documents, total_count)

        Raises:
            ValueError: If page < 1 or limit out of range
        """
        if page < 1:
            raise ValueError("Page must be >= 1")
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")

        logger.debug(f"Listing documents (page={page}, limit={limit})")

        documents, total = await self.document_repo.find_all(page=page, limit=limit)

        logger.info(f"Retrieved {len(documents)} documents (total: {total})")
        return documents, total
