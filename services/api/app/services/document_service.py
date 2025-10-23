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

    async def create_document(
        self,
        db: AsyncSession,
        file_content: bytes,
        filename: str,
        title: str,
        description: Optional[str] = None
    ) -> tuple[Document, int]:
        """
        Create a new document with file upload and chunking.

        Args:
            db: Database session
            file_content: File binary content
            filename: Original filename
            title: Document title
            description: Optional description

        Returns:
            Tuple of (Document, chunk_count)
        """
        # Generate unique file path
        file_id = uuid4()
        file_extension = Path(filename).suffix
        file_path = self.upload_dir / f"{file_id}{file_extension}"

        # Save file to disk
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)

        # Detect file type
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
            upload_status="processing",
            embedding_status="pending"
        )
        db.add(document)
        await db.flush()  # Get the document ID

        try:
            # Extract text
            text = file_processor.extract_text(str(file_path), file_type)

            # Chunk text
            chunks = chunking_service.chunk_text(text)

            # Create chunk records
            chunk_objects = []
            for idx, chunk_text in enumerate(chunks):
                token_count = chunking_service.estimate_token_count(chunk_text)
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=idx,
                    chunk_text=chunk_text,
                    token_count=token_count
                )
                chunk_objects.append(chunk)
                db.add(chunk)

            document.upload_status = "completed"
            await db.commit()
            await db.refresh(document)

            # Trigger embedding generation asynchronously
            await self._trigger_embedding(document.id, chunk_objects)

            return document, len(chunks)

        except Exception as e:
            logger.error(f"Error processing document: {e}")
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

        except Exception as e:
            logger.error(f"Error triggering embeddings: {e}")

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
    ) -> bool:
        """
        Delete document and associated resources.

        Args:
            db: Database session
            document_id: Document UUID

        Returns:
            True if deleted, False if not found
        """
        # Get document
        query = select(Document).where(Document.id == document_id)
        result = await db.execute(query)
        document = result.scalar_one_or_none()

        if not document:
            return False

        # Delete vectors from Qdrant
        try:
            await self.qdrant_client.delete_by_document_id(str(document_id))
        except Exception as e:
            logger.error(f"Error deleting vectors from Qdrant: {e}")

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
        else:
            # Fallback for old records without file_path - use glob pattern
            logger.warning(f"Document {document_id} has no file_path, attempting glob pattern fallback")
            for file in self.upload_dir.glob(f"{document_id}*"):
                try:
                    file.unlink()
                    logger.info(f"Deleted file via glob pattern: {file}")
                except Exception as e:
                    logger.error(f"Error deleting file via glob: {e}")

        # Delete from database (cascades to chunks)
        await db.delete(document)
        await db.commit()

        return True
