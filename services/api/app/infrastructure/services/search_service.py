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
        """Execute search via dedicated search microservice.

        Delegates all search operations to the search microservice, which
        handles:
        - Query embedding generation (via embedder service)
        - Vector search in Qdrant
        - Keyword search via PostgreSQL FTS
        - Hybrid search with RRF fusion
        - Cross-encoder reranking for precision

        This client implements the microservices pattern, separating search
        logic into a dedicated service for better scalability and isolation.

        Args:
            query: Natural language search query text.
            mode: Search mode - "vector" (semantic), "keyword" (lexical),
                or "hybrid" (fusion). Defaults to "hybrid" for best results.
            top_k: Number of final results to return after search/reranking.
                Defaults to 10.
            use_reranking: Enable cross-encoder reranking for improved precision.
                When True, retrieves 50+ candidates and reranks to top_k.
                Defaults to True.
            use_expansion: Enable query expansion (reserved for future use).
                Currently not implemented in search service.
            document_id: Optional UUID to filter results to specific document.
                Applied in both vector and keyword search components.

        Returns:
            List of Chunk domain entities ranked by relevance (descending).
            Converted from search service DTOs to API domain model.

        Raises:
            httpx.HTTPStatusError: If search service returns HTTP error status
                (4xx/5xx). Error includes response details for debugging.
            httpx.RequestError: If cannot connect to search service (network
                error, service down, DNS failure).
            RuntimeError: For unexpected errors during response parsing or
                entity conversion.

        Note:
            This client converts between API domain entities (Chunk) and
            search service DTOs (ChunkResult). The search service maintains
            its own database connection for keyword search.

        Example:
            >>> client = SearchServiceClient("http://search:8003")
            >>> results = await client.search(
            ...     query="machine learning algorithms",
            ...     mode="hybrid",
            ...     use_reranking=True
            ... )
            >>> print(f"Found {len(results)} results")
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

        try:
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
                chunk.document_title = result.get("document_title")  # type: ignore[attr-defined]
                chunk.chunk_index = result.get("chunk_index")  # type: ignore[attr-defined]
                chunks.append(chunk)

            logger.info(f"Search service returned {len(chunks)} results")
            return chunks

        except httpx.HTTPStatusError as e:
            # Add context to HTTP errors
            error_msg = f"Search service HTTP error (status={e.response.status_code}): {str(e)}"
            logger.error(error_msg)
            raise httpx.HTTPStatusError(
                message=error_msg,
                request=e.request,
                response=e.response,
            ) from e
        except httpx.RequestError as e:
            # Add context to connection errors
            error_msg = f"Search service connection error (url={self.search_url}): {str(e)}"
            logger.error(error_msg)
            raise httpx.RequestError(message=error_msg, request=e.request) from e
        except Exception as e:
            # Add context to unexpected errors
            error_msg = f"Search service unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
