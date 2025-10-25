"""Search endpoints using hexagonal architecture.

These routes implement semantic search using the hexagonal architecture,
with clean separation between HTTP layer and domain logic.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_search_documents_use_case
from app.api.models import ChunkSearchResult, SearchRequest, SearchResponse
from app.application.use_cases.search_documents import SearchDocumentsUseCase
from app.core.exceptions import EmbeddingServiceError, VectorStoreError
from app.domain.value_objects.search_query import SearchQuery

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    use_case: SearchDocumentsUseCase = Depends(get_search_documents_use_case)
):
    """Perform semantic search across documents.

    This endpoint:
    1. Generates query embedding via embedder service
    2. Searches Qdrant for similar vectors
    3. Returns ranked results with metadata

    Args:
        request: Search request with query text and parameters
        use_case: Injected search documents use case

    Returns:
        Search results with similarity scores

    Raises:
        HTTPException: On service failures or validation errors
    """
    # Validate query
    if not request.query or len(request.query.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )

    # Create domain value object
    try:
        search_query = SearchQuery(
            text=request.query,
            top_k=request.top_k
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Execute use case
    try:
        chunks = await use_case.execute(search_query)

        logger.info(f"Search for '{request.query}' returned {len(chunks)} results")

        # Convert domain entities to response DTOs
        results = [
            ChunkSearchResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                content=chunk.content,
                score=0.0,  # Score is not available in current Chunk entity
                tokens=chunk.tokens
            )
            for chunk in chunks
        ]

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results)
        )

    except EmbeddingServiceError as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding service unavailable: {str(e)}"
        )
    except VectorStoreError as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Vector database unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
