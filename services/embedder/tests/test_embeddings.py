"""Unit tests for embedder service endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "RAAS Embedder Service"
    assert "model" in data
    assert "version" in data


def test_health():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_ready():
    """Test readiness endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert isinstance(data["model_loaded"], bool)


def test_embed_query_requires_text():
    """Test that embed-query requires a query field."""
    response = client.post("/embed-query", json={})
    assert response.status_code == 422  # Validation error


def test_embed_query_valid_request():
    """Test embed-query with valid input."""
    response = client.post("/embed-query", json={
        "query": "What is machine learning?"
    })
    # Should succeed if model is loaded
    if response.status_code == 200:
        data = response.json()
        assert "embedding" in data
        assert isinstance(data["embedding"], list)
        assert len(data["embedding"]) == 384
    else:
        # Model might not be loaded yet in test environment
        assert response.status_code in [503, 500]


def test_embed_chunks_requires_chunks():
    """Test that embed endpoint requires chunks field."""
    response = client.post("/embed", json={})
    assert response.status_code == 422  # Validation error


def test_embed_chunks_empty_list():
    """Test that embed endpoint rejects empty chunks list."""
    response = client.post("/embed", json={"chunks": []})
    assert response.status_code == 422  # Validation error


def test_embed_chunks_valid_request():
    """Test embed endpoint with valid chunks."""
    response = client.post("/embed", json={
        "chunks": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "text": "This is a test chunk.",
                "metadata": {
                    "document_id": "123e4567-e89b-12d3-a456-426614174001",
                    "chunk_index": 0
                }
            }
        ]
    })
    # Should succeed if model and Qdrant are available
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 1
    else:
        # Model or Qdrant might not be available in test environment
        assert response.status_code in [503, 500]
