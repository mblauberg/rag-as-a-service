"""Search service HTTP client.

Delegates all search operations to the dedicated search microservice.
"""
import logging
import httpx
from uuid import UUID

from app.domain.entities.chunk import Chunk

logger = logging.getLogger(__name__)


class SearchServiceClient:
    """HTTP client for search microservice.

    Replaces direct search implementations (SearchDocumentsUseCase) with
    HTTP calls to dedicated search service.
    """

    def __init__(self, search_url: str, timeout: float = 60.0):
        """Initialize search service client.

        Args:
            search_url: Base URL of search service (e.g., http://search:8003)
            timeout: HTTP timeout in seconds
        """
        self.search_url = search_url
        self.timeout = timeout

    async def search(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 10,
        use_reranking: bool = True,
        use_expansion: bool = True,
        document_id: UUID | None = None,
    ) -> list[Chunk]:
        """Execute search via search service.

        Args:
            query: Search query text
            mode: Search mode (vector/keyword/hybrid)
            top_k: Number of results to return
            use_reranking: Enable cross-encoder reranking
            use_expansion: Enable query expansion
            document_id: Optional document ID filter

        Returns:
            List of ranked chunks

        Raises:
            httpx.HTTPStatusError: If search service returns error
            httpx.RequestError: If cannot connect to search service
        """
        request_data = {
            "query": query,
            "mode": mode,
            "top_k": top_k,
            "use_reranking": use_reranking,
            "use_expansion": use_expansion,
        }

        if document_id:
            request_data["document_id"] = str(document_id)

        logger.info(
            f"Calling search service: query='{query[:50]}', mode={mode}, top_k={top_k}"
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.search_url}/api/v1/search",
                json=request_data
            )
            response.raise_for_status()
            data = response.json()

        # Convert response to Chunk entities
        # Search service returns ChunkResult DTOs, convert to domain entities
        chunks = []
        for result in data["results"]:
            chunk = Chunk(
                id=UUID(result["chunk_id"]),
                document_id=UUID(result["document_id"]),
                content=result["content"],
                tokens=0,  # Not critical for search results
                score=result["score"],
            )
            # Set optional fields
            chunk.document_title = result.get("document_title")
            chunk.chunk_index = result.get("chunk_index")
            chunks.append(chunk)

        logger.info(f"Search service returned {len(chunks)} results")
        return chunks
