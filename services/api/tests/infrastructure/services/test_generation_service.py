"""Tests for HTTP generation service adapter."""
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import GenerationServiceError
from app.infrastructure.services.generation_service import \
    HTTPGenerationService


@pytest.fixture
def generation_service():
    """Create HTTPGenerationService instance for testing."""
    return HTTPGenerationService(generator_url="http://test-generator:8002")


@pytest.mark.asyncio
async def test_generate_returns_text_response(generation_service):
    """Test that generate returns text from LLM."""
    # Mock the GeneratorClient.generate method
    with patch.object(
        generation_service.client, "generate", new_callable=AsyncMock
    ) as mock_generate:
        # Mock response with 'text' attribute
        mock_result = type(
            "GenerateResponse", (), {"text": "Generated text response"}
        )()
        mock_generate.return_value = mock_result

        result = await generation_service.generate(prompt="Test prompt", context=[])

        assert result == "Generated text response"
        mock_generate.assert_called_once_with(
            prompt="Test prompt", max_tokens=150, temperature=0.7
        )


@pytest.mark.asyncio
async def test_generate_handles_dict_response(generation_service):
    """Test that generate handles dict-style response."""
    with patch.object(
        generation_service.client, "generate", new_callable=AsyncMock
    ) as mock_generate:
        # Mock response as dictionary
        mock_generate.return_value = {"text": "Response from dict"}

        result = await generation_service.generate(
            prompt="Test prompt", context=["context1"]
        )

        assert result == "Response from dict"


@pytest.mark.asyncio
async def test_generate_handles_string_response(generation_service):
    """Test that generate handles plain string response."""
    with patch.object(
        generation_service.client, "generate", new_callable=AsyncMock
    ) as mock_generate:
        # Mock response as plain string
        mock_generate.return_value = "Plain string response"

        result = await generation_service.generate(prompt="Test prompt", context=[])

        assert result == "Plain string response"


@pytest.mark.asyncio
async def test_generate_raises_error_on_none_response(generation_service):
    """Test that generate raises error when client returns None."""
    with patch.object(
        generation_service.client, "generate", new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.return_value = None

        with pytest.raises(GenerationServiceError) as exc_info:
            await generation_service.generate(prompt="Test prompt", context=[])

        assert "returned None" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_raises_error_on_unexpected_format(generation_service):
    """Test that generate raises error on unexpected response format."""
    with patch.object(
        generation_service.client, "generate", new_callable=AsyncMock
    ) as mock_generate:
        # Mock response with unexpected format
        mock_generate.return_value = 12345  # Number instead of text

        with pytest.raises(GenerationServiceError) as exc_info:
            await generation_service.generate(prompt="Test prompt", context=[])

        assert "Unexpected response format" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_wraps_unexpected_exceptions(generation_service):
    """Test that generate wraps unexpected exceptions."""
    with patch.object(
        generation_service.client, "generate", new_callable=AsyncMock
    ) as mock_generate:
        mock_generate.side_effect = ValueError("Unexpected error")

        with pytest.raises(GenerationServiceError) as exc_info:
            await generation_service.generate(prompt="Test prompt", context=[])

        assert "Unexpected error during generation" in str(exc_info.value)
        assert exc_info.value.original_error is not None
