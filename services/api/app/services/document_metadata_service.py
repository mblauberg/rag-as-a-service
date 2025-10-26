"""Service for document database CRUD operations."""
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.models import (DocumentDetailResponse, DocumentListResponse,
                            DocumentResponse)
from app.core.enums import EmbeddingStatus, UploadStatus
from app.core.exceptions import DocumentNotFoundError
from app.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)


class DocumentMetadataService:
    """Service handling database CRUD operations for documents."""

    async def create_document(
        self,
        db: AsyncSession,
        title: str,
        description: str | None,
        file_name: str,
        file_type: str,
        file_size: int,
        file_path: str,
        document_type: str,
    ) -> Document:
        """
        Create a new document record in the database.

        Args:
            db: Database session
            title: Document title
            description: Optional description
            file_name: Original filename
            file_type: MIME type
            file_size: Size in bytes
            file_path: Path where file is stored
            document_type: Document type enum value

        Returns:
            Created Document instance with ID assigned
        """
        document = Document(
            title=title,
            description=description,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            document_type=document_type,
            upload_status=UploadStatus.PROCESSING.value,
            embedding_status=EmbeddingStatus.PENDING.value,
        )
        db.add(document)
        await db.flush()  # Get the document ID
        logger.info(f"Created document record with ID: {document.id}")
        return document

    async def get_documents(
        self, db: AsyncSession, page: int = 1, limit: int = 20
    ) -> DocumentListResponse:
        """
        Get paginated list of documents.

        Args:
            db: Database session
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Paginated document list
        """
        # Get total count
        count_query = select(func.count(Document.id))
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # Get paginated documents
        offset = (page - 1) * limit
        query = (
            select(Document)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(query)
        documents = result.scalars().all()

        return DocumentListResponse(
            total=total or 0,
            page=page,
            limit=limit,
            documents=[DocumentResponse.model_validate(doc) for doc in documents],
        )

    async def get_document_by_id(
        self, db: AsyncSession, document_id: UUID
    ) -> DocumentDetailResponse | None:
        """
        Get detailed document information including chunks.

        Args:
            db: Database session
            document_id: Document UUID

        Returns:
            Document detail or None if not found
        """
        query = (
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.id == document_id)
        )
        result = await db.execute(query)
        document = result.scalar_one_or_none()

        if document:
            return DocumentDetailResponse.model_validate(document)
        return None

    async def delete_document(self, db: AsyncSession, document_id: UUID) -> Document:
        """
        Delete document record from database.

        Args:
            db: Database session
            document_id: Document UUID

        Returns:
            Deleted Document instance (before deletion)

        Raises:
            DocumentNotFoundError: If document doesn't exist
        """
        # Get document
        query = select(Document).where(Document.id == document_id)
        result = await db.execute(query)
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentNotFoundError(str(document_id))

        # Delete from database (cascades to chunks)
        await db.delete(document)
        await db.commit()
        logger.info(f"Deleted document record: {document_id}")

        return document

    async def update_embedding_status(
        self, db: AsyncSession, document_id: UUID, status: str
    ) -> None:
        """
        Update document embedding status.

        Args:
            db: Database session
            document_id: Document UUID
            status: New status value (e.g., "completed", "failed")
        """
        query = select(Document).where(Document.id == document_id)
        result = await db.execute(query)
        document = result.scalar_one_or_none()

        if document:
            document.embedding_status = status
            await db.commit()
            logger.info(
                f"Updated embedding status to {status} for document {document_id}"
            )
        else:
            logger.warning(
                f"Document {document_id} not found when updating embedding status"
            )

    async def update_upload_status(
        self, db: AsyncSession, document_id: UUID, status: str
    ) -> None:
        """
        Update document upload status.

        Args:
            db: Database session
            document_id: Document UUID
            status: New status value (e.g., "completed", "failed")
        """
        query = select(Document).where(Document.id == document_id)
        result = await db.execute(query)
        document = result.scalar_one_or_none()

        if document:
            document.upload_status = status
            await db.commit()
            logger.info(f"Updated upload status to {status} for document {document_id}")
        else:
            logger.warning(
                f"Document {document_id} not found when updating upload status"
            )

    async def create_chunk_records(
        self, db: AsyncSession, document_id: UUID, chunks_data: list[dict[str, Any]]
    ) -> list[DocumentChunk]:
        """
        Create chunk records in the database.

        Args:
            db: Database session
            document_id: Parent document UUID
            chunks_data: List of chunk data dictionaries from processing pipeline

        Returns:
            List of created DocumentChunk instances
        """
        chunk_objects = []
        for idx, chunk_data in enumerate(chunks_data):
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=idx,
                chunk_text=chunk_data["content"],
                token_count=None,  # Legacy field kept for backward compatibility
                section_title=chunk_data.get("section_title"),
                section_level=chunk_data.get("section_level", 0),
                page_number=chunk_data.get("page_number"),
                chunk_tokens=chunk_data.get(
                    "tokens"
                ),  # New semantic chunking token count
                chunk_metadata=chunk_data.get("metadata", {}),
            )
            chunk_objects.append(chunk)
            db.add(chunk)

        await db.flush()  # Ensure chunk IDs are assigned
        logger.info(
            f"Created {len(chunk_objects)} chunk records for document {document_id}"
        )
        return chunk_objects
