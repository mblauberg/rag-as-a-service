"""API request/response models for hexagonal architecture HTTP layer.

These Pydantic models define the API contracts for the hexagonal architecture.
They translate between HTTP requests/responses and domain entities/value objects.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# Document Upload Models
class UploadDocumentRequest(BaseModel):
    """Request model for document upload.

    Note: File is handled separately as UploadFile in FastAPI.
    """

    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    description: str | None = Field(None, description="Optional document description")


class DocumentResponse(BaseModel):
    """Response model for document entity."""

    model_config = {"from_attributes": True}

    id: UUID
    title: str
    file_name: str
    file_type: str
    created_at: datetime
    upload_status: str
    description: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    embedding_status: str | None = None
    updated_at: datetime | None = None


class UploadDocumentResponse(BaseModel):
    """Response model for document upload operation."""

    document: DocumentResponse
    chunk_count: int
    message: str = "Document uploaded and processed successfully"


# Document List Models
class ListDocumentsRequest(BaseModel):
    """Request model for listing documents (query parameters)."""

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(20, ge=1, le=100, description="Items per page")


class ListDocumentsResponse(BaseModel):
    """Response model for paginated document list."""

    documents: list[DocumentResponse]
    total: int
    page: int
    limit: int


# Search Models
class SearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., min_length=1, description="Search query text")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")
    document_id: UUID | None = Field(None, description="Optional document ID filter")


class ChunkSearchResult(BaseModel):
    """Result item for search response."""

    chunk_id: UUID
    document_id: UUID
    content: str
    score: float = Field(..., description="Similarity score")
    tokens: int | None = None


class SearchResponse(BaseModel):
    """Response model for search operation."""

    query: str
    results: list[ChunkSearchResult]
    total_results: int


# Error Response Models
class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str
    error_code: str | None = None


# Legacy document metadata schemas (used by document_metadata_service)
class DocumentChunkResponse(BaseModel):
    """Schema for document chunk response."""

    model_config = {"from_attributes": True}

    id: UUID
    chunk_index: int
    chunk_text: str
    token_count: int | None = None
    section_title: str | None = None
    section_level: int | None = 0
    page_number: int | None = None
    chunk_tokens: int | None = None
    chunk_metadata: dict = {}
    created_at: datetime


class DocumentDetailResponse(BaseModel):
    """Schema for detailed document response with chunks."""

    model_config = {"from_attributes": True}

    id: UUID
    title: str
    file_name: str
    file_type: str
    file_size: int
    file_path: str | None = None
    upload_status: str
    embedding_status: str
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    chunks: list[DocumentChunkResponse] = []


class DocumentListResponse(BaseModel):
    """Schema for paginated document list."""

    total: int
    page: int
    limit: int
    documents: list[DocumentResponse]
