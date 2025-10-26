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
        """
        Load the sentence-transformers model.

        This should be called once at startup to avoid repeated downloads.
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
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors

        Raises:
            RuntimeError: If model is not loaded
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
        """
        Generate embeddings for chunks and store them in Qdrant.

        Args:
            chunks: List of chunk items with text and metadata

        Returns:
            True if successful, False otherwise
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
