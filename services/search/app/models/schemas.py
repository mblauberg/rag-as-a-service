"""Pydantic schemas for search service API."""
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class SearchMode(str, Enum):
    """Search mode enumeration."""

    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class SearchRequest(BaseModel):
    """Search request schema."""

    query: str = Field(..., description="Search query text")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")
    mode: SearchMode = Field(SearchMode.HYBRID, description="Search mode")
    use_expansion: bool = Field(True, description="Enable query expansion")
    use_reranking: bool = Field(True, description="Enable cross-encoder reranking")
    document_id: UUID | None = Field(None, description="Filter by document ID")

    @field_validator("query")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Validate query is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or whitespace")
        return v.strip()


class ChunkResult(BaseModel):
    """Single search result chunk."""

    chunk_id: UUID
    document_id: UUID
    document_title: str | None
    content: str
    score: float
    chunk_index: int | None = None


class SearchResponse(BaseModel):
    """Search response schema."""

    query: str
    results: list[ChunkResult]
    total_results: int
    mode_used: SearchMode | None = None
    expansion_applied: bool = False
    reranking_applied: bool = False


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: str
    models_loaded: bool
    database_connected: bool
