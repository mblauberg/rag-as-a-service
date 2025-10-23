"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# Document Schemas
class DocumentBase(BaseModel):
    """Base document schema."""

    title: str = Field(..., max_length=500, description="Document title")
    description: Optional[str] = Field(None, description="Optional document description")


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""

    pass


class DocumentChunkResponse(BaseModel):
    """Schema for document chunk response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chunk_index: int
    chunk_text: str
    token_count: Optional[int] = None
    created_at: datetime


class DocumentResponse(DocumentBase):
    """Schema for document response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_name: str
    file_type: str
    file_size: int
    upload_status: str
    embedding_status: str
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    """Schema for detailed document response with chunks."""

    model_config = ConfigDict(from_attributes=True)

    chunks: List[DocumentChunkResponse] = []


class DocumentListResponse(BaseModel):
    """Schema for paginated document list."""

    total: int
    page: int
    limit: int
    documents: List[DocumentResponse]


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""

    document: DocumentResponse
    message: str
    chunk_count: int


# Search Schemas
class SearchRequest(BaseModel):
    """Schema for search request."""

    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    document_ids: Optional[List[UUID]] = Field(None, description="Optional list of document IDs to filter")


class SearchResultItem(BaseModel):
    """Schema for individual search result."""

    chunk_id: UUID
    document_id: UUID
    document_title: str
    chunk_text: str
    chunk_index: int
    score: float = Field(..., description="Similarity score")


class SearchResponse(BaseModel):
    """Schema for search response."""

    query: str
    results: List[SearchResultItem]
    total_results: int


# Health Schemas
class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str


class ServiceStatus(BaseModel):
    """Schema for individual service status."""

    name: str
    status: str
    details: Optional[str] = None


class ReadinessResponse(BaseModel):
    """Schema for readiness check response."""

    status: str
    services: List[ServiceStatus]


# Embedder Service Schemas
class EmbedChunkItem(BaseModel):
    """Schema for embedding chunk item."""

    id: str
    text: str
    metadata: dict


class EmbedRequest(BaseModel):
    """Schema for embed request to embedder service."""

    chunks: List[EmbedChunkItem]


class EmbedResponse(BaseModel):
    """Schema for embed response from embedder service."""

    success: bool
    count: int


class EmbedQueryRequest(BaseModel):
    """Schema for embed query request."""

    query: str


class EmbedQueryResponse(BaseModel):
    """Schema for embed query response."""

    embedding: List[float]
