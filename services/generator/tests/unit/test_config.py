"""Tests for configuration settings."""
import os
from app.core.config import settings


def test_default_provider_toggles():
    """Provider toggles should have correct defaults."""
    # Reset settings to defaults
    os.environ.clear()
    from app.core.config import Settings
    test_settings = Settings()

    # Ollama enabled by default
    assert test_settings.enable_ollama is True

    # External providers disabled by default
    assert test_settings.enable_openai is False
    assert test_settings.enable_anthropic is False
    assert test_settings.enable_google is False


def test_api_keys_optional():
    """API keys should be optional (empty string by default)."""
    os.environ.clear()
    from app.core.config import Settings
    test_settings = Settings()

    assert test_settings.openai_api_key == ""
    assert test_settings.anthropic_api_key == ""
    assert test_settings.google_api_key == ""
