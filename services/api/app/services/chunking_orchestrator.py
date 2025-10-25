"""Service for orchestrating document chunking and embedding workflows."""
from uuid import UUID
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import httpx

from app.models.document import DocumentChunk
from app.services.document_processing_service import DocumentProcessingService
from app.services.document_metadata_service import DocumentMetadataService
from app.models.schemas import DocumentType
from app.core.config import settings
from app.core.enums import EmbeddingStatus
from app.core.exceptions import (
    TextExtractionError,
    FileOperationError,
    EmbedderServiceError
)

logger = logging.getLogger(__name__)


class ChunkingOrchestrator:
    """Service orchestrating document chunking workflow and embedding triggers."""

    def __init__(self, metadata_service: DocumentMetadataService):
        """
        Initialize chunking orchestrator with injected dependencies.

        Args:
            metadata_service: Service for database metadata operations
        """
        self.processing_service = DocumentProcessingService()
        self.metadata_service = metadata_service
        self.embedder_url = settings.embedder.url

    async def process_and_chunk(
        self,
        db: AsyncSession,
        document_id: UUID,
        file_path: Path,
        document_type: DocumentType
    ) -> List[DocumentChunk]:
        """
        Process document, create chunks, and store in database.

        Args:
            db: Database session
            document_id: Document UUID
            file_path: Path to document file
            document_type: Type of document

        Returns:
            List of created DocumentChunk instances

        Raises:
            TextExtractionError: If text extraction fails
            FileOperationError: If file operations fail
        """
        # Process and chunk document using processing pipeline
        chunks_data = await self.processing_service.process_and_chunk(
            file_path,
            document_type
        )
        logger.info(f"Processed document {document_id} into {len(chunks_data)} chunks")

        # Create chunk records using metadata service
        chunk_objects = await self.metadata_service.create_chunk_records(
            db,
            document_id,
            chunks_data
        )

        return chunk_objects

    async def trigger_embedding(
        self,
        db: AsyncSession,
        document_id: UUID,
        chunks: List[DocumentChunk]
    ) -> None:
        """
        Trigger embedding generation for document chunks and update status.

        Uses DocumentMetadataService to update embedding status instead of
        direct database operations to avoid code duplication.

        Args:
            db: Database session
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

            # Send to embedder service using local HTTP client
            try:
                async with httpx.AsyncClient(timeout=300.0) as http_client:
                    response = await http_client.post(
                        f"{self.embedder_url}/embed",
                        json={"chunks": chunks_data}
                    )
                    response.raise_for_status()
                    result = response.json()
                    success = result.get("success", False)

                if success:
                    logger.info(f"Successfully triggered embedding for document {document_id}")
                    # Use metadata service to update status
                    await self.metadata_service.update_embedding_status(
                        db,
                        document_id,
                        EmbeddingStatus.COMPLETED.value
                    )
                else:
                    logger.error(f"Failed to trigger embedding for document {document_id}")
                    # Use metadata service to update status
                    await self.metadata_service.update_embedding_status(
                        db,
                        document_id,
                        EmbeddingStatus.FAILED.value
                    )
                    raise EmbedderServiceError("embed_chunks", Exception("Embedder returned success=false"))

            except httpx.HTTPError as e:
                logger.error(f"HTTP error communicating with embedder: {e}")
                # Use metadata service to update status
                await self.metadata_service.update_embedding_status(
                    db,
                    document_id,
                    EmbeddingStatus.FAILED.value
                )
                raise EmbedderServiceError("embed_chunks", e)

        except EmbedderServiceError as e:
            logger.error(f"Error triggering embeddings: {e}")
            # Don't re-raise - this is a background operation, document is already saved
        except Exception as e:
            logger.error(f"Unexpected error triggering embeddings: {e}")
            # Use metadata service to update status
            try:
                await self.metadata_service.update_embedding_status(
                    db,
                    document_id,
                    EmbeddingStatus.FAILED.value
                )
            except Exception as db_error:
                logger.error(f"Failed to update embedding status after error: {db_error}")
