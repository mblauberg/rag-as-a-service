"""Pydantic schemas for request/response validation."""
from typing import Any, Dict, List

from pydantic import BaseModel, Field


# Embedding Request Schemas
class ChunkItem(BaseModel):
    """Schema for a single chunk to embed."""

    id: str = Field(..., description="Unique chunk identifier (UUID)")
    text: str = Field(..., min_length=1, description="Text content to embed")
    metadata: Dict[str, Any] = Field(..., description="Metadata including document_id and chunk_index")


class EmbedRequest(BaseModel):
    """Schema for batch embedding request."""

    chunks: List[ChunkItem] = Field(min_length=1, description="List of chunks to embed")


class EmbedResponse(BaseModel):
    """Schema for embedding response."""

    success: bool = Field(..., description="Whether embedding operation succeeded")
    count: int = Field(..., description="Number of chunks processed")
    message: str = Field(default="", description="Optional message or error details")


# Query Embedding Schemas
class EmbedQueryRequest(BaseModel):
    """Schema for query embedding request."""

    query: str = Field(..., min_length=1, description="Search query text to embed")


class EmbedQueryResponse(BaseModel):
    """Schema for query embedding response."""

    embedding: List[float] = Field(..., description="Query embedding vector")


# Health Schemas
class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str = Field(..., description="Health status")


class ReadinessResponse(BaseModel):
    """Schema for readiness check response."""

    status: str = Field(..., description="Readiness status")
    model_loaded: bool = Field(..., description="Whether the embedding model is loaded")


# Batch Text Embedding Schemas (without storage)
class GenerateEmbeddingsRequest(BaseModel):
    """Schema for batch text embedding request without storage."""

    texts: List[str] = Field(min_length=1, description="List of texts to embed")


class GenerateEmbeddingsResponse(BaseModel):
    """Schema for batch text embedding response."""

    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
