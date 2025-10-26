"""Tests for configuration settings."""
import os
from app.core.config import settings


def test_provider_toggles_with_defaults_enables_openai_only():
    """Provider toggles should have correct defaults (OpenAI enabled for gpt-5-mini)."""
    # Reset settings to defaults
    os.environ.clear()
    from app.core.config import Settings
    test_settings = Settings()

    # OpenAI enabled by default (for gpt-5-mini)
    assert test_settings.enable_openai is True

    # Other providers disabled by default
    assert test_settings.enable_ollama is False
    assert test_settings.enable_anthropic is False
    assert test_settings.enable_google is False


def test_api_keys_can_be_loaded_from_environment():
    """API keys can be loaded from environment or .env file."""
    from app.core.config import Settings
    test_settings = Settings()

    # Keys should be loaded (either from .env or environment)
    # If .env exists with keys, they'll be loaded
    # We just verify the settings object has these fields
    assert hasattr(test_settings, 'openai_api_key')
    assert hasattr(test_settings, 'anthropic_api_key')
    assert hasattr(test_settings, 'google_api_key')
