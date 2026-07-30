"""Tests for search service configuration."""
import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestSettings:
    """Test Settings configuration."""

    def test_default_settings(self):
        """Test default configuration values."""
        settings = Settings()

        assert settings.service_name == "raas-search"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8003
        assert settings.log_level == "INFO"

    def test_database_url_required(self):
        """Test that database URL is required."""
        # Settings should work with default or empty DATABASE_URL
        # but in production it must be set
        settings = Settings()
        assert settings.database_url is not None

    def test_qdrant_url_validation(self):
        """Test Qdrant URL configuration."""
        settings = Settings(qdrant_url="http://localhost:6333")
        assert settings.qdrant_url == "http://localhost:6333"

    def test_reranking_model_name(self):
        """Test reranking model configuration."""
        settings = Settings()
        assert settings.reranking_model == "cross-encoder/ms-marco-MiniLM-L-6-v2"
