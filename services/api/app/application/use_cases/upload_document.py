"""Upload document use case."""
import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from app.core.enums import UploadStatus
from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document
from app.ports.repositories import ChunkRepository, DocumentRepository
from app.ports.services import EmbeddingService, FileProcessor, TextChunker, VectorStore

logger = logging.getLogger(__name__)


@dataclass
class UploadDocumentCommand:
    """Input DTO for upload document use case."""

    title: str
    file_name: str
    file_content: bytes
    description: str | None = None


class UploadDocumentUseCase:
    """Use case orchestrating document upload workflow.

    Coordinates file processing, chunking, embedding, and persistence.
    Follows single responsibility - orchestration only, no business logic.
    """

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        file_processor: FileProcessor,
        chunker: TextChunker
    ):
        """Initialize use case with injected dependencies (ports)."""
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.file_processor = file_processor
        self.chunker = chunker

    async def execute(self, command: UploadDocumentCommand) -> tuple[Document, int]:
        """Execute document upload workflow.

        Args:
            command: Upload parameters

        Returns:
            Tuple of (created document, chunk count)

        Raises:
            Various exceptions from ports if operations fail
        """
        # 1. Create domain entity
        document = Document(
            id=uuid4(),
            title=command.title,
            file_name=command.file_name,
            file_type=self._detect_file_type(command.file_name),
            created_at=datetime.utcnow(),
            upload_status=UploadStatus.PROCESSING,
            description=command.description
        )

        # 2. Persist document (initial state)
        document = await self.document_repo.save(document)
        logger.info(f"Created document {document.id} in PROCESSING state")

        try:
            # 3. Extract text from file
            text = await self.file_processor.extract_text(
                command.file_content,
                document.file_type
            )
            logger.debug(f"Extracted {len(text)} characters from {document.file_name}")

            # 4. Chunk text
            chunk_texts = await self.chunker.chunk(text)
            logger.debug(f"Created {len(chunk_texts)} chunks")

            # 5. Create chunk entities
            chunks = [
                Chunk(
                    id=uuid4(),
                    document_id=document.id,
                    content=chunk_text,
                    tokens=self._count_tokens(chunk_text)
                )
                for chunk_text in chunk_texts
            ]

            # 6. Persist chunks
            chunks = await self.chunk_repo.save_batch(chunks)
            logger.debug(f"Persisted {len(chunks)} chunks to database")

            # 7. Generate embeddings
            embeddings = await self.embedding_service.generate_embeddings(
                [c.content for c in chunks]
            )
            logger.debug(f"Generated {len(embeddings)} embeddings")

            # 8. Update chunks with embeddings
            for chunk, embedding in zip(chunks, embeddings, strict=False):
                chunk.embedding_vector = embedding

            # 9. Store vectors in vector database
            await self.vector_store.upsert(chunks)
            logger.debug(f"Stored {len(chunks)} vectors in vector DB")

            # 10. Mark document as completed (domain logic)
            document.mark_completed()
            await self.document_repo.save(document)
            logger.info(f"Document {document.id} completed successfully")

            return document, len(chunks)

        except Exception as e:
            # Use domain logic for failure state
            logger.error(f"Document {document.id} processing failed: {e}")
            document.mark_failed()
            await self.document_repo.save(document)
            raise

    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from extension."""
        return filename.rsplit('.', 1)[-1].lower() if '.' in filename else "unknown"

    def _count_tokens(self, text: str) -> int:
        """Estimate token count (simple word-based approximation)."""
        return len(text.split())
