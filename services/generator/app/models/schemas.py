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


class ModelInfo(BaseModel):
    """Information about an available model."""
    name: str = Field(..., description="Model name")
    size: str = Field(..., description="Model size (e.g., '2GB')")
    modified_at: str = Field(..., description="Last modified timestamp")


class Model(BaseModel):
    """Model information with provider details."""
    name: str  # Unique identifier (e.g., "llama3.3:70b", "openai:gpt-5")
    display_name: str  # Human-readable name (e.g., "Llama 3.3 70B", "GPT-5")
    provider: str  # Provider name: "ollama", "openai", "anthropic", "google"
    size: str  # Model size (e.g., "8B", "70B", "N/A" for API models)
    description: str = ""  # Capability description
    capabilities: List[str] = []  # ["reasoning", "coding", "creative"]
    modified_at: str  # ISO 8601 timestamp


class ModelsResponse(BaseModel):
    """List of available models."""
    models: List[Model] = Field(..., description="Available models from all providers")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")


class ReadinessResponse(BaseModel):
    """Readiness check response."""
    status: str = Field(..., description="Readiness status")
    ollama_connected: bool = Field(..., description="Ollama connectivity status")
