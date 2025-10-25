"""Pydantic schemas for request/response validation."""
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    CSV = "csv"
    XLSX = "xlsx"
    PPTX = "pptx"
    HTML = "html"


# Document Schemas
class DocumentBase(BaseModel):
    """Base document schema."""

    title: str = Field(..., max_length=500, description="Document title")
    description: str | None = Field(None, description="Optional document description")


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""

    pass


class DocumentChunkResponse(BaseModel):
    """Schema for document chunk response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chunk_index: int
    chunk_text: str
    token_count: int | None = None
    section_title: str | None = None
    section_level: int | None = 0
    page_number: int | None = None
    chunk_tokens: int | None = None
    chunk_metadata: dict[str, Any] = {}
    created_at: datetime


class DocumentResponse(DocumentBase):
    """Schema for document response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_name: str
    file_type: str
    file_size: int
    file_path: str | None = None
    upload_status: str
    embedding_status: str
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    """Schema for detailed document response with chunks."""

    model_config = ConfigDict(from_attributes=True)

    chunks: list[DocumentChunkResponse] = []


class DocumentListResponse(BaseModel):
    """Schema for paginated document list."""

    total: int
    page: int
    limit: int
    documents: list[DocumentResponse]


class DocumentUploadResponse(DocumentResponse):
    """Schema for document upload response - extends DocumentResponse."""

    model_config = ConfigDict(from_attributes=True)

    message: str
    chunk_count: int


# Search Schemas
class SearchRequest(BaseModel):
    """Schema for search request."""

    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    document_ids: list[UUID] | None = Field(None, description="Optional list of document IDs to filter")
    model: str | None = Field(None, description="LLM model for generation (optional)")


class SearchResultItem(BaseModel):
    """Schema for individual search result."""

    chunk_id: UUID
    document_id: UUID
    document_title: str
    chunk_text: str
    chunk_index: int
    score: float = Field(..., description="Similarity score")
    section_title: str | None = None
    page_number: int | None = None
    chunk_metadata: dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Schema for search response with optional generation."""

    query: str
    summary: str | None = Field(None, description="Generated summary with citations")
    chunks: list[SearchResultItem]
    model_used: str | None = Field(None, description="Model used for generation")
    total_results: int
    retrieval_method: str | None = Field(None, description="Retrieval method used (vector, hybrid, etc.)")
    expanded_queries: list[str] | None = Field(None, description="Expanded query variants (for advanced search)")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata about the search")


# Health Schemas
class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str


class ServiceStatus(BaseModel):
    """Schema for individual service status."""

    name: str
    status: str
    details: str | None = None


class ReadinessResponse(BaseModel):
    """Schema for readiness check response."""

    status: str
    services: list[ServiceStatus]


# Embedder Service Schemas
class EmbedChunkItem(BaseModel):
    """Schema for embedding chunk item."""

    id: str
    text: str
    metadata: dict


class EmbedRequest(BaseModel):
    """Schema for embed request to embedder service."""

    chunks: list[EmbedChunkItem]


class EmbedResponse(BaseModel):
    """Schema for embed response from embedder service."""

    success: bool
    count: int


class EmbedQueryRequest(BaseModel):
    """Schema for embed query request."""

    query: str


class EmbedQueryResponse(BaseModel):
    """Schema for embed query response."""

    embedding: list[float]
