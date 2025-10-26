"""Embedding service for generating and storing vector embeddings."""
import logging
from typing import Any, List
from sentence_transformers import SentenceTransformer
import numpy as np
import numpy.typing as npt
from qdrant_client.models import PointStruct
from uuid import UUID

from app.core.config import settings
from app.core.qdrant_client import qdrant_client
from app.models.schemas import ChunkItem

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings and storing them in Qdrant."""

    def __init__(self) -> None:
        """Initialize the embedding service."""
        self.model: SentenceTransformer | None = None
        self.model_loaded = False

    def load_model(self) -> None:
        """Load sentence-transformers model into memory.

        Downloads and initializes the embedding model specified in settings.
        This is a one-time operation at service startup to avoid:
        - Repeated model downloads on each request
        - Cold-start latency for first embedding request
        - Resource contention from concurrent downloads

        The model is loaded into CPU memory (optimized with ONNX if available)
        and reused for all subsequent embedding requests. Model weights are
        cached locally after first download (~100-400MB depending on model).

        Common models:
        - all-MiniLM-L6-v2: 384-dim, fast, good quality (recommended)
        - all-mpnet-base-v2: 768-dim, slower, best quality
        - multi-qa-MiniLM-L6-cos-v1: 384-dim, optimized for QA

        Raises:
            Exception: If model download fails (network error, invalid model name)
                or if model initialization fails (corrupted weights, etc.).

        Note:
            Should be called exactly once during service startup (in main.py).
            Subsequent calls will reload the model unnecessarily.
        """
        try:
            logger.info(f"Loading model: {settings.model_name}")
            self.model = SentenceTransformer(settings.model_name)
            self.model_loaded = True
            logger.info(f"Model loaded successfully. Dimension: {settings.model_dimension}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector embeddings for batch of texts.

        Uses sentence-transformers to create semantic embeddings that capture
        the meaning of text. The model encodes text into fixed-size dense
        vectors where semantically similar texts have similar vectors
        (measured by cosine similarity).

        Process:
        1. Tokenize texts using model's tokenizer (BERT-style WordPiece)
        2. Pass through transformer encoder (BERT, RoBERTa, etc.)
        3. Apply pooling (mean/CLS) to get fixed-size sentence embedding
        4. Normalize to unit length (for cosine similarity)

        Batch processing provides efficiency benefits:
        - GPU/CPU parallelization across batch
        - Amortized tokenization overhead
        - Better throughput for multiple texts

        Args:
            texts: List of text strings to embed. Can be sentences, paragraphs,
                or short documents. Very long texts may be truncated to model's
                max length (typically 512 tokens for BERT-based models).

        Returns:
            List of embedding vectors (one per input text). Each vector is a
            list of floats with dimensionality matching the model architecture:
            - 384 dimensions for MiniLM models
            - 768 dimensions for BERT-base models
            - 1024 dimensions for BERT-large models

        Raises:
            RuntimeError: If model not loaded. Must call load_model() first
                during service initialization.

        Note:
            Embeddings are normalized to unit length, making cosine similarity
            equivalent to dot product (faster computation).

        Example:
            >>> service = EmbeddingService()
            >>> service.load_model()
            >>> embeddings = service.generate_embeddings([
            ...     "machine learning algorithms",
            ...     "deep neural networks"
            ... ])
            >>> print(f"Generated {len(embeddings)} vectors")
            >>> print(f"Dimension: {len(embeddings[0])}")
        """
        if not self.model_loaded or self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            embeddings: npt.NDArray[Any] = self.model.encode(
                texts,
                batch_size=settings.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            return embeddings.tolist()  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    async def embed_and_store_chunks(self, chunks: List[ChunkItem]) -> bool:
        """Generate embeddings for chunks and store in Qdrant vector database.

        Implements the complete chunk embedding pipeline:
        1. Extract text from chunk items
        2. Generate embeddings in batches (CPU-optimized)
        3. Prepare Qdrant point structures with vectors and metadata
        4. Upsert vectors into Qdrant collection

        This method bridges document processing and vector search by
        transforming text chunks into searchable vector representations.

        Metadata stored with each vector includes:
        - document_id: Parent document UUID for filtering
        - chunk_index: Position in document for result ordering
        - text: Original chunk content for retrieval
        - Additional custom metadata from chunk items

        Args:
            chunks: List of ChunkItem objects containing:
                - id: Unique chunk UUID
                - text: Chunk content to embed
                - metadata: Dict with document_id, chunk_index, etc.

        Returns:
            True if all chunks successfully embedded and stored.
            False if any error occurs during embedding or storage.

        Note:
            Errors are logged but not raised, allowing graceful degradation.
            In production, consider raising exceptions for proper error handling.

        Example:
            >>> service = EmbeddingService()
            >>> service.load_model()
            >>> chunks = [
            ...     ChunkItem(
            ...         id=uuid4(),
            ...         text="chunk content",
            ...         metadata={"document_id": doc_id, "chunk_index": 0}
            ...     )
            ... ]
            >>> success = await service.embed_and_store_chunks(chunks)
        """
        try:
            # Extract texts
            texts = [chunk.text for chunk in chunks]

            # Generate embeddings in batches
            logger.info(f"Generating embeddings for {len(texts)} chunks")
            embeddings = self.generate_embeddings(texts)

            # Prepare points for Qdrant
            points = []
            for chunk, embedding in zip(chunks, embeddings):
                point = PointStruct(
                    id=str(chunk.id),
                    vector=embedding,
                    payload={
                        "text": chunk.text,
                        "document_id": chunk.metadata.get("document_id"),
                        "chunk_index": chunk.metadata.get("chunk_index"),
                        **chunk.metadata  # Include any additional metadata
                    }
                )
                points.append(point)

            # Store in Qdrant
            logger.info(f"Storing {len(points)} vectors in Qdrant")
            qdrant_client.upsert_vectors(points)

            logger.info(f"Successfully processed and stored {len(chunks)} chunks")
            return True

        except Exception as e:
            logger.error(f"Error in embed_and_store_chunks: {e}")
            return False

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query text

        Returns:
            Query embedding vector

        Raises:
            RuntimeError: If model is not loaded
        """
        if not self.model_loaded or self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            embedding: npt.NDArray[Any] = self.model.encode(
                [query],
                show_progress_bar=False,
                convert_to_numpy=True
            )[0]
            return embedding.tolist()  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise


# Global embedding service instance
embedding_service = EmbeddingService()
