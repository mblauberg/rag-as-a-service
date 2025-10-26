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
    """Port for vector database operations.

    Used only for document upload/delete operations.
    Search is now handled by the dedicated search microservice.
    """

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
        self, prompt: str, context: list[str], model: str | None = None
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


class QueryAugmenter(ABC):
    """Port for query expansion and augmentation.

    Generates alternative phrasings or related queries
    to improve retrieval coverage.
    """

    @abstractmethod
    async def expand(
        self, query: str, num_variants: int = 2, method: str = "llm"
    ) -> list[str]:
        """Expand query into multiple variants.

        Args:
            query: Original query
            num_variants: Number of variants to generate (default 2)
            method: Expansion method ("llm", "synonyms", etc.)

        Returns:
            List containing original + variant queries
        """
        pass
