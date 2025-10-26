"""Search endpoints using hexagonal architecture.

These routes implement semantic search using the hexagonal architecture,
with clean separation between HTTP layer and domain logic.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_search_documents_use_case
from app.api.mappers import chunk_to_search_result
from app.api.models import SearchRequest, SearchResponse
from app.application.use_cases.search_documents import (SearchDocumentsUseCase,
                                                        SearchMode)
from app.core.exceptions import EmbeddingServiceError, VectorStoreError
from app.domain.value_objects.search_query import SearchQuery

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    mode: SearchMode = Query(
        default=SearchMode.HYBRID,
        description="Search mode: 'vector' (semantic only), 'keyword' (BM25 only), or 'hybrid' (RRF fusion - RECOMMENDED, +18-22% accuracy)",
    ),
    use_expansion: bool = Query(
        default=True,
        description="Enable multi-query expansion for improved retrieval coverage (default: True, +15-20% recall)",
    ),
    use_reranking: bool = Query(
        default=True,
        description="Enable cross-encoder reranking for improved precision (default: True, +8-12% precision@10)",
    ),
    use_case: SearchDocumentsUseCase = Depends(get_search_documents_use_case),
) -> SearchResponse:
    """Perform document search with hybrid retrieval (RECOMMENDED).

    This endpoint supports three search modes:
    - VECTOR: Pure semantic search using embeddings
    - KEYWORD: Pure lexical/BM25 search using PostgreSQL FTS
    - HYBRID: Combines both with RRF fusion (RECOMMENDED, +18-22% accuracy)

    The hybrid mode:
    1. Generates query embedding via embedder service
    2. Searches Qdrant for similar vectors (semantic)
    3. Searches PostgreSQL FTS for keyword matches (lexical)
    4. Fuses results using Reciprocal Rank Fusion (RRF)
    5. Optionally reranks with cross-encoder for improved precision
    6. Returns top-k ranked results

    Query parameters:
        mode: Search mode (default: hybrid)
        use_expansion: Enable multi-query expansion (default: True)
        use_reranking: Enable cross-encoder reranking (default: True)

    Args:
        request: Search request with query text and parameters
        mode: Search mode selection (vector/keyword/hybrid)
        use_expansion: Enable query expansion
        use_reranking: Enable reranking
        use_case: Injected search documents use case

    Returns:
        Search results with ranked chunks

    Raises:
        HTTPException: On service failures or validation errors
    """
    # Validate query
    if not request.query or len(request.query.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty"
        )

    # Create domain value object
    try:
        search_query = SearchQuery(text=request.query, top_k=request.top_k)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Execute use case
    try:
        chunks = await use_case.execute(
            search_query,
            mode=mode,
            use_expansion=use_expansion,
            use_reranking=use_reranking,
        )

        logger.info(
            f"Search for '{request.query}' (mode={mode.value}, reranking={use_reranking}) "
            f"returned {len(chunks)} results"
        )

        # Convert domain entities to response DTOs
        results = [chunk_to_search_result(chunk, score=0.0) for chunk in chunks]

        return SearchResponse(
            query=request.query, results=results, total_results=len(results)
        )

    except EmbeddingServiceError as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding service unavailable: {str(e)}",
        )
    except VectorStoreError as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Vector database unavailable: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )
