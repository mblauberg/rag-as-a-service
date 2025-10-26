"""Test Ollama client service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ollama_client import OllamaClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_list_models_with_available_models_returns_model_list():
    """Test listing available models."""
    mock_response = {
        "models": [
            {"name": "llama3.2", "size": 2000000000, "modified_at": "2024-01-01T00:00:00Z"},
            {"name": "mistral", "size": 4000000000, "modified_at": "2024-01-02T00:00:00Z"}
        ]
    }

    with patch('ollama.AsyncClient') as mock_client_class:
        mock_instance = AsyncMock()
        mock_instance.list.return_value = mock_response
        mock_client_class.return_value = mock_instance

        client = OllamaClient()
        models = await client.list_models()

        assert len(models) == 2
        assert models[0]["name"] == "llama3.2"
        assert models[1]["name"] == "mistral"


@pytest.mark.asyncio
async def test_generate_with_valid_prompt_returns_response():
    """Test generating text with Ollama."""
    mock_response = {
        "response": "This is a test summary [1].",
        "total_duration": 1000000000,
        "prompt_eval_count": 50,
        "eval_count": 20
    }

    with patch('ollama.AsyncClient') as mock_client_class:
        mock_instance = AsyncMock()
        mock_instance.generate.return_value = mock_response
        mock_client_class.return_value = mock_instance

        client = OllamaClient()
        result = await client.generate(
            model="llama3.2",
            prompt="Test prompt"
        )

        assert result["response"] == "This is a test summary [1]."
        assert "total_duration" in result


@pytest.mark.asyncio
async def test_check_health_when_ollama_available_returns_true():
    """Test health check when Ollama is available."""
    with patch('ollama.AsyncClient') as mock_client_class:
        mock_instance = AsyncMock()
        mock_instance.list.return_value = {"models": []}
        mock_client_class.return_value = mock_instance

        client = OllamaClient()
        is_healthy = await client.check_health()

        assert is_healthy is True


@pytest.mark.asyncio
async def test_check_health_when_connection_fails_returns_false():
    """Test health check when Ollama is unavailable."""
    with patch('ollama.AsyncClient') as mock_client_class:
        mock_instance = AsyncMock()
        mock_instance.list.side_effect = Exception("Connection refused")
        mock_client_class.return_value = mock_instance

        client = OllamaClient()
        is_healthy = await client.check_health()

        assert is_healthy is False
