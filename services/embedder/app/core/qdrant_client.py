"""Qdrant client wrapper for collection management and vector operations."""
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List

from app.core.config import settings

logger = logging.getLogger(__name__)


class QdrantClientWrapper:
    """Wrapper class for Qdrant client operations."""

    def __init__(self) -> None:
        """Initialize Qdrant client and ensure collection exists."""
        self.client = QdrantClient(url=settings.qdrant_url)
        self.collection_name = settings.collection_name
        self._initialize_collection()

    def _initialize_collection(self) -> None:
        """
        Ensure the documents collection exists with proper configuration.

        Creates a collection with 384-dimensional vectors using cosine distance
        if it doesn't already exist.
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating collection '{self.collection_name}'")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.model_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection '{self.collection_name}' created successfully")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")
        except Exception as e:
            logger.error(f"Error initializing collection: {e}")
            raise

    def upsert_vectors(self, points: List[PointStruct]) -> None:
        """
        Upsert vectors into the collection.

        Args:
            points: List of PointStruct objects containing vectors and metadata

        Raises:
            Exception: If upsert operation fails
        """
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Successfully upserted {len(points)} vectors")
        except Exception as e:
            logger.error(f"Error upserting vectors: {e}")
            raise

    def health_check(self) -> bool:
        """
        Check if Qdrant is accessible.

        Returns:
            True if Qdrant is healthy, False otherwise
        """
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


# Global Qdrant client instance
qdrant_client = QdrantClientWrapper()
