"""Pydantic schemas for generation API."""
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ChunkInput(BaseModel):
    """Document chunk for context."""
    text: str = Field(..., description="Chunk text content")
    document_id: str = Field(..., description="Source document ID")
    chunk_index: int = Field(..., description="Chunk index in document")


class GenerateRequest(BaseModel):
    """Request to generate summary from chunks."""
    query: str = Field(..., description="User's search query")
    chunks: List[ChunkInput] = Field(..., description="Retrieved document chunks")
    model: str = Field(..., description="Ollama model to use")


class GenerateResponse(BaseModel):
    """Generated summary response."""
    summary: str = Field(..., description="Generated summary with citations")
    model_used: str = Field(..., description="Model that generated the summary")
    tokens_used: int = Field(..., description="Approximate tokens used")


class Model(BaseModel):
    """Model information with provider support."""
    name: str = Field(..., description="Qualified name: 'openai:gpt-5', 'llama3.2'")
    display_name: str = Field(..., description="Human-readable: 'GPT-5', 'Llama 3.2'")
    provider: str = Field(..., description="'ollama', 'openai', 'anthropic', 'google'")
    size: str = Field(..., description="'70B', 'N/A'")
    description: str = Field(..., description="Capability description")
    capabilities: List[str] = Field(default_factory=list, description="['reasoning', 'coding']")
    modified_at: str = Field(default="", description="ISO timestamp")


class ModelsResponse(BaseModel):
    """Response containing list of available models."""
    models: List[Model] = Field(..., description="Available models from all providers")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")


class ReadinessResponse(BaseModel):
    """Readiness check response."""
    status: str = Field(..., description="Readiness status")
    ollama_connected: bool = Field(..., description="Ollama connectivity status")
