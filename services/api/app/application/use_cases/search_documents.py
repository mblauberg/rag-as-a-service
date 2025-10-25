"""Search documents use case."""
import logging

from app.domain.entities.chunk import Chunk
from app.domain.value_objects.search_query import SearchQuery
from app.ports.services import EmbeddingService, VectorStore

logger = logging.getLogger(__name__)


class SearchDocumentsUseCase:
    """Use case for semantic document search.

    Orchestrates query embedding and vector search.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore
    ):
        """Initialize with embedding and vector store dependencies."""
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    async def execute(self, query: SearchQuery) -> list[Chunk]:
        """Execute semantic search.

        Args:
            query: Search query value object

        Returns:
            List of relevant chunks ordered by similarity
        """
        logger.info(f"Searching for: '{query.text}' (top_k={query.top_k})")

        # 1. Generate query embedding
        query_embeddings = await self.embedding_service.generate_embeddings([query.text])
        query_vector = query_embeddings[0]

        # 2. Search vector store
        results = await self.vector_store.search(
            query_vector=query_vector,
            top_k=query.top_k
        )

        logger.info(f"Found {len(results)} results")
        return results
