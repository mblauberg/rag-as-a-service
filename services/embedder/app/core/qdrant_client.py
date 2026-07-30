"""Qdrant client wrapper for collection management and vector operations."""
import logging
import time
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings

logger = logging.getLogger(__name__)


class QdrantClientWrapper:
    """Wrapper class for Qdrant client operations."""

    def __init__(self) -> None:
        """Initialize Qdrant client and ensure collection exists."""
        self.qdrant_url = settings.qdrant_url
        self.collection_name = settings.collection_name
        self.client = None
        self._initialize_collection()

    def _initialize_collection(self) -> None:
        """Ensure the documents collection exists with proper configuration.

        Creates collection with configured vector dimensions using cosine distance.
        Retries on connection failures with exponential backoff.
        """
        max_retries = 10
        retry_delay = 3

        for attempt in range(max_retries):
            try:
                client = QdrantClient(url=self.qdrant_url)
                collections = client.get_collections().collections
                collection_names = [c.name for c in collections]

                if self.collection_name not in collection_names:
                    logger.info(f"Creating collection '{self.collection_name}'")
                    client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=settings.model_dimension,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Collection '{self.collection_name}' created successfully")
                else:
                    logger.info(f"Collection '{self.collection_name}' already exists")

                self.client = client
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Error initializing collection (attempt {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"Error initializing collection after {max_retries} attempts: {e}")
                    raise

    def upsert_vectors(self, points: List[PointStruct]) -> None:
        """Upsert vectors into the collection.

        Args:
            points: List of PointStruct objects with vectors and metadata.

        Raises:
            Exception: If upsert operation fails.
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
        """Check if Qdrant is accessible.

        Returns:
            True if Qdrant is healthy, False otherwise.
        """
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


_qdrant_client: QdrantClientWrapper | None = None

def get_qdrant_client() -> QdrantClientWrapper:
    """Get or create the global Qdrant client instance."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClientWrapper()
    return _qdrant_client
