"""Test application constants"""
from app.core.constants import (
    EMBEDDING_DIMENSION,
    DEFAULT_SEARCH_LIMIT,
    MAX_SEARCH_LIMIT,
    DEFAULT_CHUNK_MIN_SIZE,
    DEFAULT_CHUNK_MAX_SIZE,
    SEMANTIC_BREAKPOINT_PERCENTILE,
    MAX_UPLOAD_SIZE_MB,
    EMBEDDER_TIMEOUT_SECONDS,
    GENERATOR_TIMEOUT_SECONDS,
)


def test_embedding_dimension():
    """Test embedding dimension constant"""
    assert EMBEDDING_DIMENSION == 384
    assert isinstance(EMBEDDING_DIMENSION, int)


def test_search_limits():
    """Test search limit constants"""
    assert DEFAULT_SEARCH_LIMIT == 10
    assert MAX_SEARCH_LIMIT == 100
    assert DEFAULT_SEARCH_LIMIT < MAX_SEARCH_LIMIT


def test_chunking_sizes():
    """Test chunking size constants"""
    assert DEFAULT_CHUNK_MIN_SIZE == 128
    assert DEFAULT_CHUNK_MAX_SIZE == 512
    assert DEFAULT_CHUNK_MIN_SIZE < DEFAULT_CHUNK_MAX_SIZE


def test_semantic_percentile():
    """Test semantic breakpoint percentile"""
    assert SEMANTIC_BREAKPOINT_PERCENTILE == 95
    assert 0 <= SEMANTIC_BREAKPOINT_PERCENTILE <= 100


def test_upload_size():
    """Test max upload size"""
    assert MAX_UPLOAD_SIZE_MB == 100
    assert MAX_UPLOAD_SIZE_MB > 0


def test_timeout_values():
    """Test timeout constants"""
    assert EMBEDDER_TIMEOUT_SECONDS == 30.0
    assert GENERATOR_TIMEOUT_SECONDS == 60.0
    assert isinstance(EMBEDDER_TIMEOUT_SECONDS, float)
    assert isinstance(GENERATOR_TIMEOUT_SECONDS, float)
