"""DTO mapper functions for converting domain entities to API response models.

These mappers provide a centralized place for entity-to-DTO conversions,
eliminating code duplication across route handlers and ensuring consistent
mapping logic throughout the HTTP adapter layer.
"""
from app.api.models import ChunkSearchResult, DocumentChunkResponse, DocumentResponse
from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document


def document_to_response(document: Document) -> DocumentResponse:
    """Convert a domain Document entity to a DocumentResponse DTO.

    This mapper centralizes the conversion logic between the domain layer
    and the HTTP adapter layer, ensuring consistent field mapping across
    all endpoints that return document information.

    Args:
        document: Domain Document entity to convert

    Returns:
        DocumentResponse DTO suitable for API responses

    Example:
        >>> from uuid import uuid4
        >>> from datetime import datetime, UTC
        >>> from app.core.enums import UploadStatus
        >>> doc = Document(
        ...     id=uuid4(),
        ...     title="Sample Document",
        ...     file_name="sample.pdf",
        ...     file_type="pdf",
        ...     created_at=datetime.now(UTC),
        ...     upload_status=UploadStatus.COMPLETED,
        ...     description="A test document",
        ...     file_path="/uploads/sample.pdf",
        ...     file_size=1024
        ... )
        >>> response = document_to_response(doc)
        >>> response.title
        'Sample Document'
    """
    return DocumentResponse(
        id=document.id,
        title=document.title,
        file_name=document.file_name,
        file_type=document.file_type,
        created_at=document.created_at,
        upload_status=document.upload_status.value,
        description=document.description,
        file_path=document.file_path,
        file_size=document.file_size,
    )


def chunk_to_search_result(chunk: Chunk, score: float = 0.0) -> ChunkSearchResult:
    """Convert a domain Chunk entity to a ChunkSearchResult DTO.

    This mapper centralizes the conversion logic between the domain layer
    and the HTTP adapter layer for search results, ensuring consistent
    field mapping and score handling.

    Args:
        chunk: Domain Chunk entity to convert
        score: Similarity score from vector search (default: 0.0)
            Note: Current implementation may not have scores available
            from the use case, so default is provided for compatibility

    Returns:
        ChunkSearchResult DTO suitable for search API responses

    Example:
        >>> from uuid import uuid4
        >>> chunk = Chunk(
        ...     id=uuid4(),
        ...     document_id=uuid4(),
        ...     content="Sample chunk text",
        ...     tokens=10,
        ...     embedding_vector=[0.1, 0.2, 0.3]
        ... )
        >>> result = chunk_to_search_result(chunk, score=0.95)
        >>> result.score
        0.95
        >>> result.content
        'Sample chunk text'
    """
    return ChunkSearchResult(
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        content=chunk.content,
        score=score,
        tokens=chunk.tokens,
    )


def chunk_to_response(chunk: Chunk) -> DocumentChunkResponse:
    """Convert a domain Chunk entity to a DocumentChunkResponse DTO.

    Args:
        chunk: Domain Chunk entity to convert

    Returns:
        DocumentChunkResponse DTO suitable for API responses

    Note:
        chunk_index defaults to 0 and should be set by the caller
    """
    from datetime import UTC, datetime

    return DocumentChunkResponse(
        id=chunk.id,
        chunk_index=0,  # Default, should be overridden by caller
        chunk_text=chunk.content,
        token_count=chunk.tokens,
        section_title=chunk.section_title,
        section_level=chunk.section_level or 0,
        page_number=chunk.page_number,
        chunk_tokens=chunk.tokens,
        chunk_metadata=chunk.metadata or {},
        created_at=datetime.now(
            UTC
        ),  # Use current time as chunks don't have created_at in domain
    )
