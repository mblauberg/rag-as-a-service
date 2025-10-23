"""Test generation service integration."""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.generation_service import GenerationService
from app.models.schemas import ChunkInput


@pytest.mark.asyncio
async def test_generate_summary_success():
    """Test successful summary generation."""
    chunks = [
        ChunkInput(text="ML is AI", document_id="doc1", chunk_index=0),
        ChunkInput(text="Learns from data", document_id="doc1", chunk_index=1)
    ]
    query = "What is ML?"

    mock_ollama_response = {
        "response": "Machine learning [1] is AI that learns from data [2].",
        "prompt_eval_count": 50,
        "eval_count": 20
    }

    with patch('app.services.generation_service.OllamaClient') as mock_client_class:
        mock_instance = AsyncMock()
        mock_instance.generate.return_value = mock_ollama_response
        mock_client_class.return_value = mock_instance

        service = GenerationService()
        response = await service.generate_summary(
            query=query,
            chunks=chunks,
            model="llama3.2"
        )

        assert response.summary == "Machine learning [1] is AI that learns from data [2]."
        assert response.model_used == "llama3.2"
        assert response.tokens_used == 70  # prompt_eval_count + eval_count


@pytest.mark.asyncio
async def test_generate_summary_with_default_model():
    """Test generation falls back to default model."""
    chunks = [ChunkInput(text="Test", document_id="doc1", chunk_index=0)]
    query = "Test query"

    mock_ollama_response = {
        "response": "Test response [1].",
        "prompt_eval_count": 10,
        "eval_count": 5
    }

    with patch('app.services.generation_service.OllamaClient') as mock_client_class:
        with patch('app.services.generation_service.settings') as mock_settings:
            mock_settings.default_model = "llama3.2"

            mock_instance = AsyncMock()
            mock_instance.generate.return_value = mock_ollama_response
            mock_client_class.return_value = mock_instance

            service = GenerationService()
            response = await service.generate_summary(query, chunks, model=None)

            # Should use default model
            assert response.model_used == "llama3.2"


@pytest.mark.asyncio
async def test_list_available_models():
    """Test listing available models."""
    mock_models = [
        {"name": "llama3.2", "size": 2000000000, "modified_at": "2024-01-01T00:00:00Z"},
        {"name": "mistral", "size": 4000000000, "modified_at": "2024-01-02T00:00:00Z"}
    ]

    with patch('app.services.generation_service.OllamaClient') as mock_client_class:
        mock_instance = AsyncMock()
        mock_instance.list_models.return_value = mock_models
        mock_client_class.return_value = mock_instance

        service = GenerationService()
        models = await service.list_available_models()

        assert len(models.models) == 2
        assert models.models[0].name == "llama3.2"
        assert models.models[1].name == "mistral"
