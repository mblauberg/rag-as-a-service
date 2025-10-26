"""Integration tests for summary generation flow."""
import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_full_summary_generation_flow(async_client, sample_document_with_chunks, db_session):
    """Test complete flow: get chunk IDs → generate summary."""
    # Get the chunks from the document
    from app.infrastructure.db.repositories.chunk_repository_impl import ChunkRepositoryImpl

    chunk_repo = ChunkRepositoryImpl(db_session)
    chunks = await chunk_repo.find_by_document_id(sample_document_with_chunks.id)
    chunk_ids = [str(chunk.id) for chunk in chunks]

    assert len(chunk_ids) > 0, "Sample document should have chunks"

    # Generate summary from those chunks
    mock_summary = {
        "summary": "Semantic search uses vector embeddings [1] to understand meaning [2].",
        "model_used": "gpt-5-mini"
    }

    with patch("app.api.routes.generate.GeneratorClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.generate_summary.return_value = mock_summary
        mock_client.return_value = mock_instance

        summary_response = await async_client.post(
            "/api/v1/generate/summary",
            json={
                "query": "semantic search",
                "chunk_ids": chunk_ids,
                "model": "gpt-5-mini"
            }
        )

    assert summary_response.status_code == 200
    summary_data = summary_response.json()
    assert "embeddings" in summary_data["summary"]
    assert summary_data["model_used"] == "gpt-5-mini"


@pytest.mark.asyncio
async def test_summary_generation_with_empty_chunk_list(async_client):
    """Test summary generation with empty chunk list."""
    # Attempting to generate summary with empty chunk list should fail validation
    summary_response = await async_client.post(
        "/api/v1/generate/summary",
        json={
            "query": "test query",
            "chunk_ids": [],
            "model": "gpt-5-mini"
        }
    )
    assert summary_response.status_code == 422


@pytest.mark.asyncio
async def test_summary_generation_with_invalid_chunk_ids(async_client):
    """Test summary generation with nonexistent chunk IDs."""
    from uuid import uuid4

    summary_response = await async_client.post(
        "/api/v1/generate/summary",
        json={
            "query": "test query",
            "chunk_ids": [str(uuid4()), str(uuid4())],
            "model": "gpt-5-mini"
        }
    )
    # Should get 404 because chunks don't exist
    assert summary_response.status_code == 404
