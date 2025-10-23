"""Test Pydantic schemas for generation service."""
import pytest
from app.models.schemas import GenerateRequest, GenerateResponse, ModelInfo


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
    """Test ModelInfo schema."""
    model = ModelInfo(
        name="llama3.2",
        size="2GB",
        modified_at="2024-01-01T00:00:00Z"
    )
    assert model.name == "llama3.2"
    assert model.size == "2GB"
