"""Tests for configuration settings."""
import os
from app.core.config import settings


def test_provider_toggles_with_defaults_enables_ollama_only():
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


def test_api_keys_without_environment_variables_default_to_empty():
    """API keys should be optional (empty string by default)."""
    os.environ.clear()
    from app.core.config import Settings
    test_settings = Settings()

    assert test_settings.openai_api_key == ""
    assert test_settings.anthropic_api_key == ""
    assert test_settings.google_api_key == ""
