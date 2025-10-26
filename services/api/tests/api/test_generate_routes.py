"""Tests for summary generation endpoints."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_generate_summary_success(async_client, sample_document_with_chunks):
    """Test successful summary generation."""
    # Get chunk IDs from the sample document
    chunk_ids = []
    for chunk in sample_document_with_chunks.chunks:
        chunk_ids.append(str(chunk.id))

    request_data = {
        "query": "what is semantic search?",
        "chunk_ids": chunk_ids,
        "model": "gpt-5-mini"
    }

    # Mock generator client response
    mock_response = {
        "summary": "Semantic search uses embeddings to find meaning.",
        "model_used": "gpt-5-mini"
    }

    with patch("app.api.routes.generate.GeneratorClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.generate_summary.return_value = mock_response
        mock_client.return_value = mock_instance

        response = await async_client.post("/api/v1/generate/summary", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Semantic search uses embeddings to find meaning."
    assert data["model_used"] == "gpt-5-mini"


@pytest.mark.asyncio
async def test_generate_summary_empty_chunk_ids(async_client):
    """Test summary generation with empty chunk IDs."""
    request_data = {
        "query": "test query",
        "chunk_ids": [],
        "model": "gpt-5-mini"
    }

    response = await async_client.post("/api/v1/generate/summary", json=request_data)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_generate_summary_invalid_chunk_ids(async_client):
    """Test summary generation with nonexistent chunk IDs."""
    request_data = {
        "query": "test query",
        "chunk_ids": [str(uuid4()), str(uuid4())],
        "model": "gpt-5-mini"
    }

    response = await async_client.post("/api/v1/generate/summary", json=request_data)
    assert response.status_code == 404
    detail = response.json()["detail"].lower()
    assert "no chunks found" in detail or "not found" in detail


@pytest.mark.asyncio
async def test_generate_summary_generator_failure(async_client, sample_document_with_chunks):
    """Test summary generation when generator service fails."""
    # Get chunk IDs from the sample document
    chunk_ids = []
    for chunk in sample_document_with_chunks.chunks:
        chunk_ids.append(str(chunk.id))

    request_data = {
        "query": "test query",
        "chunk_ids": chunk_ids,
        "model": "gpt-5-mini"
    }

    with patch("app.api.routes.generate.GeneratorClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.generate_summary.return_value = None
        mock_client.return_value = mock_instance

        response = await async_client.post("/api/v1/generate/summary", json=request_data)

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()
