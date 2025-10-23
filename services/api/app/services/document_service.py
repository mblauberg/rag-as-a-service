"""Document processing service orchestrating upload, chunking, and embedding."""
import os
import aiofiles
from uuid import uuid4, UUID
from pathlib import Path
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging
import httpx

from app.models.document import Document, DocumentChunk
from app.models.schemas import DocumentResponse, DocumentDetailResponse, DocumentListResponse
from app.services.chunking_service import chunking_service
from app.utils.file_processing import file_processor
from app.core.config import settings
from app.core.qdrant_client import QdrantClientWrapper
from app.core.exceptions import (
    DocumentNotFoundError,
    QdrantConnectionError,
    EmbedderServiceError,
    FileOperationError,
    TextExtractionError
)
from app.services.document_processing_service import DocumentProcessingService
from app.utils.file_type_detector import FileTypeDetector

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document operations."""

    def __init__(
        self,
        qdrant_client: QdrantClientWrapper,
        http_client: httpx.AsyncClient
    ):
        """
        Initialize document service with injected dependencies.

        Args:
            qdrant_client: Qdrant client wrapper for vector operations
            http_client: HTTP client for embedder service communication
        """
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.qdrant_client = qdrant_client
        self.http_client = http_client
        self.embedder_url = settings.embedder_url
        self.processing_service = DocumentProcessingService()
        self.file_detector = FileTypeDetector()

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

        Args:
            db: Database session
            file_content: File binary content
            filename: Original filename
            title: Document title
            description: Optional description

        Returns:
            Tuple of (Document, chunk_count)
        """
        # Detect document type from filename
        try:
            document_type = self.file_detector.detect_from_filename(filename)
        except ValueError as e:
            logger.error(f"Unsupported file type for {filename}: {e}")
            raise FileOperationError("detect_file_type", filename, e)

        # Generate unique file path
        file_id = uuid4()
        file_extension = Path(filename).suffix
        file_path = self.upload_dir / f"{file_id}{file_extension}"

        # Save file to disk
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
            raise FileOperationError("write", str(file_path), e)

        # Detect MIME type
        file_type = file_processor.detect_file_type(str(file_path))
        file_size = len(file_content)

        # Create document record
        document = Document(
            title=title,
            description=description,
            file_name=filename,
            file_type=file_type,
            file_size=file_size,
            file_path=str(file_path),
            document_type=document_type.value,
            upload_status="processing",
            embedding_status="pending"
        )
        db.add(document)
        await db.flush()  # Get the document ID

        try:
            # Process and chunk document using new processing pipeline
            chunks_data = self.processing_service.process_and_chunk(
                file_path,
                document_type
            )

            # Create chunk records with metadata
            chunk_objects = []
            for idx, chunk_data in enumerate(chunks_data):
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=idx,
                    chunk_text=chunk_data['content'],
                    token_count=chunk_data.get('tokens'),
                    section_title=chunk_data.get('section_title'),
                    section_level=chunk_data.get('section_level', 0),
                    page_number=chunk_data.get('page_number'),
                    chunk_tokens=chunk_data.get('tokens'),
                    chunk_metadata=chunk_data.get('metadata', {})
                )
                chunk_objects.append(chunk)
                db.add(chunk)

            document.upload_status = "completed"
            await db.commit()
            await db.refresh(document)

            # Trigger embedding generation asynchronously
            await self._trigger_embedding(document.id, chunk_objects)

            return document, len(chunks_data)

        except (TextExtractionError, FileOperationError) as e:
            # Re-raise custom exceptions as-is
            logger.error(f"Error processing document: {e}")
            document.upload_status = "failed"
            await db.commit()
            raise
        except Exception as e:
            # Wrap unexpected exceptions
            logger.error(f"Unexpected error processing document: {e}")
            document.upload_status = "failed"
            await db.commit()
            raise

    async def _trigger_embedding(
        self,
        document_id: UUID,
        chunks: List[DocumentChunk]
    ) -> None:
        """
        Trigger embedding generation for document chunks.

        Args:
            document_id: Document UUID
            chunks: List of document chunks
        """
        try:
            # Prepare chunks for embedder
            chunks_data = [
                {
                    "id": str(chunk.id),
                    "text": chunk.chunk_text,
                    "metadata": {
                        "document_id": str(document_id),
                        "chunk_index": chunk.chunk_index
                    }
                }
                for chunk in chunks
            ]

            # Send to embedder service using injected HTTP client
            try:
                response = await self.http_client.post(
                    f"{self.embedder_url}/embed",
                    json={"chunks": chunks_data},
                    timeout=300.0  # 5 minutes for large batches
                )
                response.raise_for_status()
                result = response.json()
                success = result.get("success", False)

                if success:
                    logger.info(f"Successfully triggered embedding for document {document_id}")
                else:
                    logger.error(f"Failed to trigger embedding for document {document_id}")
                    raise EmbedderServiceError("embed_chunks", Exception("Embedder returned success=false"))
            except httpx.HTTPError as e:
                logger.error(f"HTTP error communicating with embedder: {e}")
                raise EmbedderServiceError("embed_chunks", e)

        except EmbedderServiceError as e:
            logger.error(f"Error triggering embeddings: {e}")
            # Don't re-raise - this is a background operation, document is already saved
        except Exception as e:
            logger.error(f"Unexpected error triggering embeddings: {e}")

    async def get_documents(
        self,
        db: AsyncSession,
        page: int = 1,
        limit: int = 20
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
            documents=[DocumentResponse.model_validate(doc) for doc in documents]
        )

    async def get_document_detail(
        self,
        db: AsyncSession,
        document_id: UUID
    ) -> Optional[DocumentDetailResponse]:
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

    async def delete_document(
        self,
        db: AsyncSession,
        document_id: UUID
    ) -> None:
        """
        Delete document and associated resources.

        Args:
            db: Database session
            document_id: Document UUID

        Raises:
            DocumentNotFoundError: If document doesn't exist
            QdrantConnectionError: If vector deletion fails
            FileOperationError: If file deletion fails
        """
        # Get document
        query = select(Document).where(Document.id == document_id)
        result = await db.execute(query)
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentNotFoundError(str(document_id))

        # Delete vectors from Qdrant
        try:
            await self.qdrant_client.delete_by_document_id(str(document_id))
        except Exception as e:
            logger.error(f"Error deleting vectors from Qdrant: {e}")
            raise QdrantConnectionError("delete_by_document_id", e)

        # Delete file from disk
        if document.file_path:
            file_path = Path(document.file_path)
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted file: {file_path}")
                else:
                    logger.warning(f"File not found at stored path: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
                raise FileOperationError("delete", str(file_path), e)
        else:
            # Fallback for old records without file_path - use glob pattern
            logger.warning(f"Document {document_id} has no file_path, attempting glob pattern fallback")
            for file in self.upload_dir.glob(f"{document_id}*"):
                try:
                    file.unlink()
                    logger.info(f"Deleted file via glob pattern: {file}")
                except Exception as e:
                    logger.error(f"Error deleting file via glob: {e}")
                    raise FileOperationError("delete", str(file), e)

        # Delete from database (cascades to chunks)
        await db.delete(document)
        await db.commit()
