import pytest
from unittest.mock import AsyncMock, patch
from app.providers.ollama_provider import OllamaProvider
from app.models.schemas import Model


@pytest.fixture
def ollama_provider():
    """Create OllamaProvider instance for testing."""
    return OllamaProvider(base_url="http://localhost:11434")


@pytest.mark.asyncio
async def test_is_available_when_healthy(ollama_provider):
    """is_available returns True when Ollama is healthy"""
    with patch('requests.get') as mock_get:
        mock_response = type('Response', (), {'status_code': 200})()
        mock_get.return_value = mock_response

        assert ollama_provider.is_available() is True


@pytest.mark.asyncio
async def test_is_available_when_unhealthy(ollama_provider):
    """is_available returns False when Ollama is unhealthy"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection failed")

        assert ollama_provider.is_available() is False


@pytest.mark.asyncio
async def test_list_models_returns_enhanced_schema(ollama_provider):
    """list_models returns models with enhanced schema"""
    mock_ollama_models = [
        {
            "name": "llama3.3:70b",
            "size": "70B",
            "modified_at": "2025-10-24T10:00:00Z"
        }
    ]

    with patch.object(ollama_provider.client, 'list_models', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_ollama_models

        models = await ollama_provider.list_models()

        assert len(models) == 1
        assert isinstance(models[0], Model)
        assert models[0].name == "llama3.3:70b"
        assert models[0].display_name == "Llama 3.3 70B"
        assert models[0].provider == "ollama"
        assert models[0].size == "70B"
        assert "local" in models[0].description.lower()


@pytest.mark.asyncio
async def test_generate_calls_ollama_client(ollama_provider):
    """generate delegates to ollama_client.generate"""
    with patch.object(ollama_provider.client, 'generate', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "Generated summary"

        result = await ollama_provider.generate("llama3.3:70b", "prompt", "context")

        assert result == "Generated summary"
        mock_gen.assert_called_once_with(
            model="llama3.3:70b",
            prompt="prompt",
            context="context"
        )
