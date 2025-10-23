"""Semantic search endpoint."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.qdrant_client import qdrant_client
from app.services.embedder_client import embedder_client
from app.models.document import Document, DocumentChunk
from app.models.schemas import SearchRequest, SearchResponse, SearchResultItem

router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform semantic search across documents.

    Generates an embedding for the query, searches Qdrant for similar vectors,
    and joins results with document metadata from PostgreSQL.

    Args:
        request: Search request with query and optional filters
        db: Database session

    Returns:
        Search results with document metadata and similarity scores

    Raises:
        HTTPException: If embedding generation or search fails
    """
    # Generate query embedding
    try:
        query_embedding = await embedder_client.embed_query(request.query)
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
            results=[],
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
                    score=qdrant_result["score"]
                )
            )

    return SearchResponse(
        query=request.query,
        results=results,
        total_results=len(results)
    )
