"""Shared pytest fixtures for generator service tests."""

import pytest
from unittest.mock import Mock, AsyncMock, patch


@pytest.fixture
def mock_llm_response():
    """Standard mock LLM response for testing."""
    return {
        "id": "test-completion-id",
        "choices": [{"message": {"content": "Test response"}}],
        "model": "test-model",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20}
    }


@pytest.fixture
def test_generation_config():
    """Test configuration for generation service."""
    return {
        "provider": "openai",
        "model": "openai:gpt-5-mini",
        "temperature": 0.7,
        "max_tokens": 100
    }


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    client = Mock()
    client.messages = Mock()
    client.messages.create = AsyncMock()
    return client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = AsyncMock()
    return client


@pytest.fixture
def mock_google_client():
    """Mock Google client."""
    client = Mock()
    client.generate_content = AsyncMock()
    return client


@pytest.fixture
def anthropic_provider():
    """Create AnthropicProvider for testing."""
    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        from app.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider()


@pytest.fixture
def openai_provider():
    """Create OpenAIProvider for testing."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        from app.providers.openai_provider import OpenAIProvider
        return OpenAIProvider()


@pytest.fixture
def google_provider():
    """Create GoogleProvider for testing."""
    with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
        with patch('google.generativeai.configure'):
            from app.providers.google_provider import GoogleProvider
            return GoogleProvider()


