"""Test generator service client."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Set environment variables before importing app modules
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("EMBEDDER_URL", "http://localhost:8001")
os.environ.setdefault("GENERATOR_URL", "http://localhost:8002")

from app.services.generator_client import GeneratorClient


@pytest.mark.asyncio
async def test_generate_summary_success():
    """Test successful summary generation."""
    chunks = [
        {"text": "ML is AI", "document_id": "doc1", "chunk_index": 0, "score": 0.95}
    ]
    query = "What is ML?"

    mock_response = {
        "summary": "Machine learning [1] is AI.",
        "model_used": "llama3.2",
        "tokens_used": 50
    }

    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response
        )

        client = GeneratorClient("http://localhost:8002")
        result = await client.generate_summary(query, chunks, "llama3.2")

        assert result["summary"] == "Machine learning [1] is AI."
        assert result["model_used"] == "llama3.2"


@pytest.mark.asyncio
async def test_generate_summary_failure():
    """Test handling generator service failure."""
    chunks = [{"text": "Test", "document_id": "doc1", "chunk_index": 0}]
    query = "Test query"

    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = AsyncMock(status_code=500)

        client = GeneratorClient("http://localhost:8002")
        result = await client.generate_summary(query, chunks, "llama3.2")

        # Should return None on failure
        assert result is None


@pytest.mark.asyncio
async def test_list_models_success():
    """Test listing available models."""
    mock_response = {
        "models": [
            {"name": "llama3.2", "size": "2GB", "modified_at": "2024-01-01T00:00:00Z"}
        ]
    }

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response
        )

        client = GeneratorClient("http://localhost:8002")
        models = await client.list_models()

        assert len(models) == 1
        assert models[0]["name"] == "llama3.2"
