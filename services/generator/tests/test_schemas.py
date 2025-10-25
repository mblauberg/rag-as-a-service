"""Test Pydantic schemas for generation service."""
import pytest
from app.models.schemas import GenerateRequest, GenerateResponse, Model


def test_generate_request_valid():
    """Test GenerateRequest with valid data."""
    request = GenerateRequest(
        query="What is machine learning?",
        chunks=[
            {"text": "ML is a subset of AI", "document_id": "doc1", "chunk_index": 0},
            {"text": "It learns from data", "document_id": "doc1", "chunk_index": 1}
        ],
        model="llama3.2"
    )
    assert request.query == "What is machine learning?"
    assert len(request.chunks) == 2
    assert request.model == "llama3.2"


def test_generate_response_valid():
    """Test GenerateResponse with valid data."""
    response = GenerateResponse(
        summary="Machine learning [1] is a subset of AI that learns from data [2].",
        model_used="llama3.2",
        tokens_used=150
    )
    assert "[1]" in response.summary
    assert response.model_used == "llama3.2"
    assert response.tokens_used == 150


def test_model_info_valid():
    """Test Model schema with basic Ollama model."""
    model = Model(
        name="llama3.2",
        display_name="Llama 3.2",
        provider="ollama",
        size="2GB",
        description="Local Ollama model",
        capabilities=["local"],
        modified_at="2024-01-01T00:00:00Z"
    )
    assert model.name == "llama3.2"
    assert model.display_name == "Llama 3.2"
    assert model.provider == "ollama"
    assert model.size == "2GB"
    assert "local" in model.capabilities


def test_model_with_provider_fields():
    """Model should support provider metadata."""
    model = Model(
        name="openai:gpt-5",
        display_name="GPT-5",
        provider="openai",
        size="N/A",
        description="Best overall intelligence",
        capabilities=["reasoning", "coding"],
        modified_at="2025-08-01"
    )

    assert model.name == "openai:gpt-5"
    assert model.provider == "openai"
    assert "reasoning" in model.capabilities
