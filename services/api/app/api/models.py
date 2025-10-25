"""API request/response models for hexagonal architecture HTTP layer.

These Pydantic models define the API contracts for the hexagonal architecture.
They translate between HTTP requests/responses and domain entities/value objects.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# Document Upload Models
class UploadDocumentRequest(BaseModel):
    """Request model for document upload.

    Note: File is handled separately as UploadFile in FastAPI.
    """

    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    description: Optional[str] = Field(None, description="Optional document description")


class DocumentResponse(BaseModel):
    """Response model for document entity."""

    id: UUID
    title: str
    file_name: str
    file_type: str
    created_at: datetime
    upload_status: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None


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

    documents: List[DocumentResponse]
    total: int
    page: int
    limit: int


# Search Models
class SearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., min_length=1, description="Search query text")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")
    document_id: Optional[UUID] = Field(None, description="Optional document ID filter")


class ChunkSearchResult(BaseModel):
    """Result item for search response."""

    chunk_id: UUID
    document_id: UUID
    content: str
    score: float = Field(..., description="Similarity score")
    tokens: Optional[int] = None


class SearchResponse(BaseModel):
    """Response model for search operation."""

    query: str
    results: List[ChunkSearchResult]
    total_results: int


# Error Response Models
class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str
    error_code: Optional[str] = None
