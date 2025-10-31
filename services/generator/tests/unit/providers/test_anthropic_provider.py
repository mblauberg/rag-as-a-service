import pytest
from unittest.mock import Mock, patch, AsyncMock
from anthropic.types import TextBlock
from app.providers.anthropic_provider import AnthropicProvider
from app.models.schemas import Model


def test_is_available_with_api_key():
    """is_available returns True when API key is set"""
    # Arrange
    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        provider = AnthropicProvider()

        # Act
        result = provider.is_available()

        # Assert
        assert result is True


def test_is_available_without_api_key():
    """is_available returns False when API key is missing"""
    # Arrange
    with patch.dict('os.environ', {}, clear=True):
        provider = AnthropicProvider()

        # Act
        result = provider.is_available()

        # Assert
        assert result is False


@pytest.mark.asyncio
async def test_list_models_returns_claude_models(anthropic_provider):
    """list_models returns predefined Claude models"""
    # Arrange
    # Provider created by fixture

    # Act
    models = await anthropic_provider.list_models()

    # Assert
    assert len(models) >= 3  # Opus, Sonnet, Haiku
    opus = next(m for m in models if m.name == "anthropic:claude-opus-4-1-20250805")
    assert opus.display_name == "Claude Opus 4.1"
    assert opus.provider == "anthropic"
    assert "powerful" in opus.description.lower()


@pytest.mark.asyncio
async def test_list_models_returns_versioned_api_names():
    """Test that list_models returns actual API model names with version dates."""
    from unittest.mock import MagicMock

    provider = AnthropicProvider()
    provider.client = MagicMock()  # Make it available

    models = await provider.list_models()

    model_names = [m.name for m in models]
    assert "anthropic:claude-opus-4-1-20250805" in model_names
    assert "anthropic:claude-sonnet-4-5-20250929" in model_names
    assert "anthropic:claude-haiku-4-5-20251001" in model_names


@pytest.mark.asyncio
async def test_generate_calls_anthropic_api(anthropic_provider):
    """generate calls Anthropic API with correct parameters"""
    # Arrange
    mock_block = Mock(spec=TextBlock)
    mock_block.text = "Generated summary"
    mock_response = Mock()
    mock_response.content = [mock_block]

    # Act
    with patch.object(anthropic_provider.client.messages, 'create', new_callable=AsyncMock, return_value=mock_response) as mock_create:
        result = await anthropic_provider.generate("anthropic:claude-sonnet-4-5", "query", "context")

        # Assert
        assert result == "Generated summary"
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "claude-sonnet-4-5"  # Strip prefix
