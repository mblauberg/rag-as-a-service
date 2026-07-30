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
        model="openai:gpt-5-mini"
    )
    assert request.query == "What is machine learning?"
    assert len(request.chunks) == 2
    assert request.model == "openai:gpt-5-mini"


def test_generate_response_valid():
    """Test GenerateResponse with valid data."""
    response = GenerateResponse(
        summary="Machine learning [1] is a subset of AI that learns from data [2].",
        model_used="openai:gpt-5-mini",
        tokens_used=150
    )
    assert "[1]" in response.summary
    assert response.model_used == "openai:gpt-5-mini"
    assert response.tokens_used == 150


def test_model_info_valid():
    """Test Model schema with cloud provider model."""
    model = Model(
        name="anthropic:claude-sonnet-4-5",
        display_name="Claude Sonnet 4.5",
        provider="anthropic",
        size="N/A",
        description="Balanced performance and intelligence",
        capabilities=["reasoning", "coding"],
        modified_at="2025-01-01T00:00:00Z"
    )
    assert model.name == "anthropic:claude-sonnet-4-5"
    assert model.display_name == "Claude Sonnet 4.5"
    assert model.provider == "anthropic"
    assert model.size == "N/A"
    assert "reasoning" in model.capabilities


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
