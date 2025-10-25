import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.providers.google_provider import GoogleProvider
from app.models.schemas import Model


@pytest.fixture
def google_provider():
    """Create GoogleProvider for testing."""
    with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
        with patch('google.generativeai.configure'):
            return GoogleProvider()


def test_is_available_with_api_key():
    """is_available returns True when API key is set"""
    with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
        with patch('google.generativeai.configure'):
            provider = GoogleProvider()
            assert provider.is_available() is True


def test_is_available_without_api_key():
    """is_available returns False when API key is missing"""
    with patch.dict('os.environ', {}, clear=True):
        provider = GoogleProvider()
        assert provider.is_available() is False


@pytest.mark.asyncio
async def test_list_models_returns_gemini_models(google_provider):
    """list_models returns predefined Gemini models"""
    models = await google_provider.list_models()

    assert len(models) >= 2  # Pro, Flash

    pro = next(m for m in models if m.name == "google:gemini-2-5-pro")
    assert pro.display_name == "Gemini 2.5 Pro"
    assert pro.provider == "google"
    assert "2M context" in pro.description


@pytest.mark.asyncio
async def test_generate_calls_gemini_api(google_provider):
    """generate calls Google Gemini API with correct parameters"""
    mock_response = Mock()
    mock_response.text = "Generated summary"

    mock_model = Mock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)

    with patch('google.generativeai.GenerativeModel', return_value=mock_model):
        result = await google_provider.generate("google:gemini-2-5-flash", "query", "context")

        assert result == "Generated summary"
        mock_model.generate_content_async.assert_called_once()
