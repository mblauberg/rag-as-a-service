"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


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
    section_title: Optional[str] = None
    section_level: Optional[int] = 0
    page_number: Optional[int] = None
    chunk_tokens: Optional[int] = None
    chunk_metadata: Dict[str, Any] = {}
    created_at: datetime


class DocumentResponse(DocumentBase):
    """Schema for document response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_name: str
    file_type: str
    file_size: int
    file_path: Optional[str] = None
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
    document_ids: Optional[List[UUID]] = Field(None, description="Optional list of document IDs to filter")
    model: Optional[str] = Field(None, description="LLM model for generation (optional)")


class SearchResultItem(BaseModel):
    """Schema for individual search result."""

    chunk_id: UUID
    document_id: UUID
    document_title: str
    chunk_text: str
    chunk_index: int
    score: float = Field(..., description="Similarity score")
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    chunk_metadata: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Schema for search response with optional generation."""

    query: str
    summary: Optional[str] = Field(None, description="Generated summary with citations")
    chunks: List[SearchResultItem]
    model_used: Optional[str] = Field(None, description="Model used for generation")
    total_results: int
    retrieval_method: Optional[str] = Field(None, description="Retrieval method used (vector, hybrid, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about the search")


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
