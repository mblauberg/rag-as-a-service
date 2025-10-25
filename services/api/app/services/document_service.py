"""Document processing service using Facade pattern."""
from uuid import UUID
from pathlib import Path
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.document import Document
from app.models.schemas import DocumentDetailResponse, DocumentListResponse
from app.core.qdrant_client import QdrantClientWrapper
from app.core.exceptions import (
    DocumentNotFoundError,
    QdrantConnectionError,
    FileOperationError,
    TextExtractionError
)
from app.services.document_upload_service import DocumentUploadService
from app.services.document_metadata_service import DocumentMetadataService
from app.services.chunking_orchestrator import ChunkingOrchestrator

logger = logging.getLogger(__name__)


class DocumentService:
    """Facade service coordinating document operations across specialized services."""

    def __init__(
        self,
        upload_service: DocumentUploadService,
        metadata_service: DocumentMetadataService,
        chunking_orchestrator: ChunkingOrchestrator,
        qdrant_client: QdrantClientWrapper
    ):
        """
        Initialize document service with injected dependencies.

        Args:
            upload_service: Service for file I/O operations
            metadata_service: Service for database CRUD operations
            chunking_orchestrator: Service for chunking workflow coordination
            qdrant_client: Qdrant client wrapper for vector operations
        """
        self.upload_service = upload_service
        self.metadata_service = metadata_service
        self.chunking_orchestrator = chunking_orchestrator
        self.qdrant_client = qdrant_client

    async def create_document(
        self,
        db: AsyncSession,
        file_content: bytes,
        filename: str,
        title: str,
        description: Optional[str] = None
    ) -> tuple[Document, int]:
        """
        Create a new document with file upload and semantic chunking.

        Delegates to specialized services following Facade pattern.

        Args:
            db: Database session
            file_content: File binary content
            filename: Original filename
            title: Document title
            description: Optional description

        Returns:
            Tuple of (Document, chunk_count)
        """
        # Delegate file upload to upload service
        file_metadata = await self.upload_service.save_file(file_content, filename)

        # Delegate document record creation to metadata service
        document = await self.metadata_service.create_document(
            db=db,
            title=title,
            description=description,
            file_name=filename,
            file_type=file_metadata["file_type"],
            file_size=file_metadata["file_size"],
            file_path=file_metadata["file_path"],
            document_type=file_metadata["document_type"]
        )

        try:
            # Delegate chunking workflow to orchestrator
            from app.models.schemas import DocumentType
            document_type = DocumentType(file_metadata["document_type"])
            chunk_objects = await self.chunking_orchestrator.process_and_chunk(
                db=db,
                document_id=document.id,
                file_path=Path(file_metadata["file_path"]),
                document_type=document_type
            )

            # Update upload status to completed
            await self.metadata_service.update_upload_status(
                db=db,
                document_id=document.id,
                status="completed"
            )

            # Trigger embedding generation asynchronously
            await self.chunking_orchestrator.trigger_embedding(
                db=db,
                document_id=document.id,
                chunks=chunk_objects
            )

            return document, len(chunk_objects)

        except (TextExtractionError, FileOperationError) as e:
            # Re-raise custom exceptions as-is
            logger.error(f"Error processing document: {e}")
            await self.metadata_service.update_upload_status(
                db=db,
                document_id=document.id,
                status="failed"
            )
            raise
        except Exception as e:
            # Wrap unexpected exceptions
            logger.error(f"Unexpected error processing document: {e}")
            await self.metadata_service.update_upload_status(
                db=db,
                document_id=document.id,
                status="failed"
            )
            raise

    async def get_documents(
        self,
        db: AsyncSession,
        page: int = 1,
        limit: int = 20
    ) -> DocumentListResponse:
        """
        Get paginated list of documents.

        Delegates to metadata service.

        Args:
            db: Database session
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Paginated document list
        """
        return await self.metadata_service.get_documents(db, page, limit)

    async def get_document_detail(
        self,
        db: AsyncSession,
        document_id: UUID
    ) -> Optional[DocumentDetailResponse]:
        """
        Get detailed document information including chunks.

        Delegates to metadata service.

        Args:
            db: Database session
            document_id: Document UUID

        Returns:
            Document detail or None if not found
        """
        return await self.metadata_service.get_document_by_id(db, document_id)

    async def delete_document(
        self,
        db: AsyncSession,
        document_id: UUID
    ) -> None:
        """
        Delete document and associated resources.

        Coordinates deletion across services in proper order.

        Args:
            db: Database session
            document_id: Document UUID

        Raises:
            DocumentNotFoundError: If document doesn't exist
            QdrantConnectionError: If vector deletion fails
            FileOperationError: If file deletion fails
        """
        # Get document first to access file_path (delegates to metadata service)
        document_detail = await self.metadata_service.get_document_by_id(db, document_id)

        if not document_detail:
            raise DocumentNotFoundError(str(document_id))

        # Delete vectors from Qdrant
        try:
            await self.qdrant_client.delete_by_document_id(str(document_id))
        except Exception as e:
            logger.error(f"Error deleting vectors from Qdrant: {e}")
            raise QdrantConnectionError("delete_by_document_id", e)

        # Delete file from disk (delegates to upload service)
        if document_detail.file_path:
            await self.upload_service.delete_file(document_detail.file_path)

        # Delete from database - cascades to chunks (delegates to metadata service)
        await self.metadata_service.delete_document(db, document_id)
