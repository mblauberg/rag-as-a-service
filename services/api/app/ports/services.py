"""Service port definitions for external dependencies.

These ports abstract external services (embedding, generation, vector store),
allowing implementations to be swapped without changing business logic.
"""
from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.chunk import Chunk


class EmbeddingService(ABC):
    """Port for embedding generation service."""

    @abstractmethod
    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (one per input text)

        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        pass


class VectorStore(ABC):
    """Port for vector database operations."""

    @abstractmethod
    async def upsert(self, chunks: list[Chunk]) -> None:
        """Insert or update chunk vectors in vector database.

        Args:
            chunks: List of chunks with embedding_vector populated

        Raises:
            VectorStoreError: If upsert operation fails
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        top_k: int,
        document_id: UUID | None = None
    ) -> list[Chunk]:
        """Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            document_id: Optional filter by document

        Returns:
            List of most similar chunks (ordered by similarity)
        """
        pass

    @abstractmethod
    async def delete_by_document(self, document_id: UUID) -> None:
        """Delete all vectors for a document.

        Args:
            document_id: Document UUID

        Raises:
            VectorStoreError: If deletion fails
        """
        pass


class GenerationService(ABC):
    """Port for LLM text generation service."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: list[str],
        model: str | None = None
    ) -> str:
        """Generate text response using LLM.

        Args:
            prompt: User query/prompt
            context: Retrieved context chunks
            model: Optional model identifier

        Returns:
            Generated text response

        Raises:
            GenerationServiceError: If generation fails
        """
        pass


class FileProcessor(ABC):
    """Port for file processing operations."""

    @abstractmethod
    async def extract_text(self, file_content: bytes, file_type: str) -> str:
        """Extract text from file content.

        Args:
            file_content: Raw file bytes
            file_type: File type (pdf, docx, txt, etc.)

        Returns:
            Extracted text content

        Raises:
            FileProcessingError: If text extraction fails
        """
        pass


class TextChunker(ABC):
    """Port for text chunking operations."""

    @abstractmethod
    async def chunk(self, text: str) -> list[str]:
        """Chunk text into semantic segments.

        Args:
            text: Input text to chunk

        Returns:
            List of text chunks

        Raises:
            ChunkingError: If chunking fails
        """
        pass
