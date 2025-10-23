import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.providers.openai_provider import OpenAIProvider
from app.models.schemas import Model


@pytest.fixture
def openai_provider():
    """Create OpenAIProvider for testing."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        return OpenAIProvider()


def test_is_available_with_api_key():
    """is_available returns True when API key is set"""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        provider = OpenAIProvider()
        assert provider.is_available() is True


def test_is_available_without_api_key():
    """is_available returns False when API key is missing"""
    with patch.dict('os.environ', {}, clear=True):
        provider = OpenAIProvider()
        assert provider.is_available() is False


@pytest.mark.asyncio
async def test_list_models_returns_openai_models(openai_provider):
    """list_models returns predefined OpenAI models"""
    models = await openai_provider.list_models()

    assert len(models) >= 3  # gpt-5, gpt-5-mini, gpt-4.1

    gpt5 = next(m for m in models if m.name == "openai:gpt-5")
    assert gpt5.display_name == "GPT-5"
    assert gpt5.provider == "openai"
    assert "intelligence" in gpt5.description.lower()


@pytest.mark.asyncio
async def test_generate_calls_openai_api(openai_provider):
    """generate calls OpenAI API with correct parameters"""
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Generated summary"))]

    with patch.object(openai_provider.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response) as mock_create:
        result = await openai_provider.generate("openai:gpt-5", "query", "context")

        assert result == "Generated summary"
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-5"  # Strip prefix
        assert len(call_kwargs["messages"]) >= 1
