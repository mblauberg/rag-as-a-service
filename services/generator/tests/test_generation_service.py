"""Test generation service integration."""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.generation_service import GenerationService
from app.models.schemas import ChunkInput, Model


@pytest.mark.asyncio
async def test_generate_summary_success():
    """Test successful summary generation."""
    chunks = [
        ChunkInput(text="ML is AI", document_id="doc1", chunk_index=0),
        ChunkInput(text="Learns from data", document_id="doc1", chunk_index=1)
    ]
    query = "What is ML?"

    # Mock the provider_registry
    mock_registry = AsyncMock()
    mock_registry.generate.return_value = (
        "Machine learning [1] is AI that learns from data [2].",
        "ollama"
    )

    with patch('app.services.generation_service.provider_registry', mock_registry):
        service = GenerationService()
        response = await service.generate_summary(
            query=query,
            chunks=chunks,
            model="llama3.2"
        )

        assert response.summary == "Machine learning [1] is AI that learns from data [2]."
        assert response.model_used == "llama3.2"
        # Token tracking not implemented yet
        assert response.tokens_used == 0


@pytest.mark.asyncio
async def test_generate_summary_with_default_model():
    """Test generation falls back to default model."""
    chunks = [ChunkInput(text="Test", document_id="doc1", chunk_index=0)]
    query = "Test query"

    # Mock the provider_registry
    mock_registry = AsyncMock()
    mock_registry.generate.return_value = ("Test response [1].", "ollama")

    with patch('app.services.generation_service.provider_registry', mock_registry):
        with patch('app.services.generation_service.settings') as mock_settings:
            mock_settings.default_model = "llama3.2"

            service = GenerationService()
            response = await service.generate_summary(query, chunks, model=None)

            # Should use default model
            assert response.model_used == "llama3.2"


@pytest.mark.asyncio
async def test_list_available_models():
    """Test listing available models."""
    mock_models = [
        Model(
            name="llama3.2",
            display_name="Llama3.2",
            provider="ollama",
            size="2.0GB",
            description="Local Ollama model",
            capabilities=["local"],
            modified_at="2024-01-01T00:00:00Z"
        ),
        Model(
            name="openai:gpt-5",
            display_name="GPT-5",
            provider="openai",
            size="N/A",
            description="Best intelligence",
            capabilities=["reasoning", "coding"],
            modified_at="2025-08-01"
        )
    ]

    # Mock the provider_registry
    mock_registry = AsyncMock()
    mock_registry.list_all_models.return_value = mock_models

    with patch('app.services.generation_service.provider_registry', mock_registry):
        service = GenerationService()
        models = await service.list_available_models()

        assert len(models.models) == 2
        assert models.models[0].name == "llama3.2"
        assert models.models[1].name == "openai:gpt-5"
