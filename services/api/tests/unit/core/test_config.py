"""Test configuration consolidation"""
import pytest
from pydantic import ValidationError

from app.core.config import (ChunkingConfig, EmbedderConfig, GeneratorConfig,
                             SearchConfig, Settings)


def test_chunking_config_defaults():
    """Test ChunkingConfig has correct defaults"""
    config = ChunkingConfig()
    assert config.strategy == "semantic"
    assert config.min_chunk_size == 128
    assert config.max_chunk_size == 512
    assert config.breakpoint_percentile == 95


def test_chunking_config_from_env(monkeypatch):
    """Test ChunkingConfig loads from environment variables"""
    monkeypatch.setenv("CHUNKING_STRATEGY", "recursive")
    monkeypatch.setenv("CHUNKING_MIN_CHUNK_SIZE", "256")
    monkeypatch.setenv("CHUNKING_MAX_CHUNK_SIZE", "1024")
    monkeypatch.setenv("CHUNKING_BREAKPOINT_PERCENTILE", "90")

    config = ChunkingConfig()
    assert config.strategy == "recursive"
    assert config.min_chunk_size == 256
    assert config.max_chunk_size == 1024
    assert config.breakpoint_percentile == 90


def test_chunking_config_validation():
    """Test ChunkingConfig validates inputs"""
    # Min size must be less than max size
    with pytest.raises(ValidationError):
        ChunkingConfig(min_chunk_size=1000, max_chunk_size=100)

    # Percentile must be 0-100
    with pytest.raises(ValidationError):
        ChunkingConfig(breakpoint_percentile=150)


def test_search_config_defaults():
    """Test SearchConfig has correct defaults"""
    config = SearchConfig()
    assert config.default_limit == 10
    assert config.max_limit == 100
    assert config.enable_reranking is True
    assert config.enable_query_expansion is True
    assert config.rrf_weight == 0.5


def test_search_config_from_env(monkeypatch):
    """Test SearchConfig loads from environment variables"""
    monkeypatch.setenv("SEARCH_DEFAULT_LIMIT", "20")
    monkeypatch.setenv("SEARCH_MAX_LIMIT", "200")
    monkeypatch.setenv("SEARCH_ENABLE_RERANKING", "false")
    monkeypatch.setenv("SEARCH_ENABLE_QUERY_EXPANSION", "false")
    monkeypatch.setenv("SEARCH_RRF_WEIGHT", "0.7")

    config = SearchConfig()
    assert config.default_limit == 20
    assert config.max_limit == 200
    assert config.enable_reranking is False
    assert config.enable_query_expansion is False
    assert config.rrf_weight == 0.7


def test_embedder_config_required_url(monkeypatch):
    """Test EmbedderConfig requires URL"""
    # Clear any existing EMBEDDER_URL env var
    monkeypatch.delenv("EMBEDDER_URL", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        EmbedderConfig()
    assert "url" in str(exc_info.value).lower()


def test_embedder_config_defaults(monkeypatch):
    """Test EmbedderConfig has correct defaults"""
    monkeypatch.setenv("EMBEDDER_URL", "http://localhost:8001")

    config = EmbedderConfig()
    assert config.url == "http://localhost:8001"
    assert config.batch_size == 32
    assert config.timeout == 30.0


def test_generator_config_defaults(monkeypatch):
    """Test GeneratorConfig has correct defaults"""
    monkeypatch.setenv("GENERATOR_URL", "http://localhost:8002")

    config = GeneratorConfig()
    assert config.url == "http://localhost:8002"
    assert config.timeout == 60.0
    assert config.default_model == "openai:gpt-4"


def test_settings_nested_configs(monkeypatch):
    """Test Settings includes nested configurations"""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("EMBEDDER_URL", "http://localhost:8001")
    monkeypatch.setenv("GENERATOR_URL", "http://localhost:8002")

    settings = Settings()
    assert isinstance(settings.chunking, ChunkingConfig)
    assert isinstance(settings.search, SearchConfig)
    assert isinstance(settings.embedder, EmbedderConfig)
    assert isinstance(settings.generator, GeneratorConfig)

    # Test nested access
    assert settings.chunking.min_chunk_size == 128
    assert settings.search.default_limit == 10
    assert settings.embedder.batch_size == 32
    assert settings.generator.timeout == 60.0
