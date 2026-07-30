"""Embedding service for generating and storing vector embeddings."""
import logging
from typing import Any, List
from uuid import UUID

import numpy as np
import numpy.typing as npt
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.qdrant_client import get_qdrant_client
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
        Model weights are cached locally (~100-400MB) for reuse.

        Raises:
            Exception: If model download or initialization fails.
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

        Uses sentence-transformers to create semantic embeddings that capture text meaning.
        Embeddings are normalized to unit length for cosine similarity.

        Args:
            texts: List of text strings to embed (sentences, paragraphs, or short documents).

        Returns:
            List of embedding vectors with dimensionality matching the model architecture.

        Raises:
            RuntimeError: If model not loaded.
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

        Extracts text from chunks, generates embeddings in batches, and upserts
        vectors with metadata (document_id, chunk_index, text) into Qdrant.

        Args:
            chunks: List of ChunkItem objects with id, text, and metadata.

        Returns:
            True if successful, False on error.
        """
        try:
            texts = [chunk.text for chunk in chunks]

            logger.info(f"Generating embeddings for {len(texts)} chunks")
            embeddings = self.generate_embeddings(texts)

            points = []
            for chunk, embedding in zip(chunks, embeddings):
                point = PointStruct(
                    id=str(chunk.id),
                    vector=embedding,
                    payload={
                        "text": chunk.text,
                        "document_id": chunk.metadata.get("document_id"),
                        "chunk_index": chunk.metadata.get("chunk_index"),
                        **chunk.metadata
                    }
                )
                points.append(point)

            logger.info(f"Storing {len(points)} vectors in Qdrant")
            get_qdrant_client().upsert_vectors(points)

            logger.info(f"Successfully processed and stored {len(chunks)} chunks")
            return True

        except Exception as e:
            logger.error(f"Error in embed_and_store_chunks: {e}")
            return False

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query.

        Args:
            query: Search query text.

        Returns:
            Query embedding vector.

        Raises:
            RuntimeError: If model is not loaded.
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


embedding_service = EmbeddingService()
