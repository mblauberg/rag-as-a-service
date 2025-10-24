"""Semantic search endpoint."""
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.core.database import get_db
from app.core.dependencies import get_qdrant_client, get_http_client
from app.core.qdrant_client import QdrantClientWrapper
from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.models.schemas import SearchRequest, SearchResponse, SearchResultItem
from app.services.generator_client import GeneratorClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client),
    http_client: httpx.AsyncClient = Depends(get_http_client)
):
    """
    Perform semantic search across documents.

    Generates an embedding for the query, searches Qdrant for similar vectors,
    and joins results with document metadata from PostgreSQL.

    Args:
        request: Search request with query and optional filters
        db: Database session
        qdrant_client: Qdrant client for vector operations
        http_client: HTTP client for embedder service

    Returns:
        Search results with document metadata and similarity scores

    Raises:
        HTTPException: If embedding generation or search fails
    """
    # Generate query embedding using embedder service
    try:
        response = await http_client.post(
            f"{settings.embedder_url}/embed-query",
            json={"query": request.query},
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()
        query_embedding = result["embedding"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate query embedding: {str(e)}"
        )

    # Search Qdrant
    try:
        document_ids_str = None
        if request.document_ids:
            document_ids_str = [str(doc_id) for doc_id in request.document_ids]

        qdrant_results = await qdrant_client.search(
            query_vector=query_embedding,
            limit=request.limit,
            score_threshold=0.0,
            document_ids=document_ids_str
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

    # If no results, return early
    if not qdrant_results:
        return SearchResponse(
            query=request.query,
            summary=None,
            chunks=[],
            model_used=None,
            total_results=0
        )

    # Extract chunk IDs from Qdrant results
    chunk_ids = [UUID(result["id"]) for result in qdrant_results]

    # Fetch chunk and document metadata from database
    query = (
        select(DocumentChunk, Document)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(DocumentChunk.id.in_(chunk_ids))
    )
    db_result = await db.execute(query)
    chunks_with_docs = {chunk.id: (chunk, doc) for chunk, doc in db_result}

    # Combine Qdrant results with database metadata
    results = []
    for qdrant_result in qdrant_results:
        chunk_id = UUID(qdrant_result["id"])
        if chunk_id in chunks_with_docs:
            chunk, document = chunks_with_docs[chunk_id]
            results.append(
                SearchResultItem(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    document_title=document.title,
                    chunk_text=chunk.chunk_text,
                    chunk_index=chunk.chunk_index,
                    score=qdrant_result["score"],
                    section_title=chunk.section_title,
                    page_number=chunk.page_number,
                    chunk_metadata=chunk.chunk_metadata or {}
                )
            )

    # Generate summary if model specified
    summary = None
    model_used = None

    if request.model and results:
        generator_client = GeneratorClient()

        # Prepare chunks for generator (top 5)
        chunks_for_gen = [
            {
                "text": result.chunk_text,
                "document_id": str(result.document_id),
                "chunk_index": result.chunk_index
            }
            for result in results[:5]
        ]

        gen_response = await generator_client.generate_summary(
            query=request.query,
            chunks=chunks_for_gen,
            model=request.model
        )

        if gen_response:
            summary = gen_response.get("summary")
            model_used = gen_response.get("model_used")
            logger.info(f"Generated summary using {model_used}")
        else:
            logger.warning("Summary generation failed, returning chunks only")

    return SearchResponse(
        query=request.query,
        summary=summary,
        chunks=results,
        model_used=model_used,
        total_results=len(results)
    )
