"""Delete document use case."""
import logging
from uuid import UUID

from app.core.exceptions import DocumentNotFoundError
from app.ports.repositories import ChunkRepository, DocumentRepository
from app.ports.services import VectorStore

logger = logging.getLogger(__name__)


class DeleteDocumentUseCase:
    """Use case for deleting documents and associated resources.

    Coordinates deletion across multiple storage layers.
    """

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        vector_store: VectorStore
    ):
        """Initialize with repository and vector store dependencies."""
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self.vector_store = vector_store

    async def execute(self, document_id: UUID) -> None:
        """Delete document and all associated data.

        Args:
            document_id: Document UUID to delete

        Raises:
            DocumentNotFoundError: If document doesn't exist
        """
        # 1. Verify document exists
        document = await self.document_repo.find_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(str(document_id))

        logger.info(f"Deleting document {document_id}")

        # 2. Delete from vector store
        await self.vector_store.delete_by_document(document_id)
        logger.debug(f"Deleted vectors for document {document_id}")

        # 3. Delete chunks (may cascade from document deletion, but explicit is safer)
        await self.chunk_repo.delete_by_document_id(document_id)
        logger.debug(f"Deleted chunks for document {document_id}")

        # 4. Delete document
        await self.document_repo.delete(document_id)
        logger.info(f"Successfully deleted document {document_id}")
