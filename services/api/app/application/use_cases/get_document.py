"""Get document use case."""
import logging
from uuid import UUID

from app.core.exceptions import DocumentNotFoundError
from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document
from app.ports.repositories import ChunkRepository, DocumentRepository

logger = logging.getLogger(__name__)


class GetDocumentUseCase:
    """Use case for retrieving a single document with its chunks."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository
    ):
        """Initialize with repository dependencies."""
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo

    async def execute(self, document_id: UUID) -> tuple[Document, list[Chunk]]:
        """Get document by ID with all associated chunks.

        Args:
            document_id: Document UUID to retrieve

        Returns:
            Tuple of (document, chunks)

        Raises:
            DocumentNotFoundError: If document doesn't exist
        """
        # Get document
        document = await self.document_repo.find_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(str(document_id))

        # Get chunks
        chunks = await self.chunk_repo.find_by_document_id(document_id)

        logger.info(f"Retrieved document {document_id} with {len(chunks)} chunks")
        return document, chunks
