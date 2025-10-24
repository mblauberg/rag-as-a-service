def test_semantic_chunking_config_defaults():
    """Test semantic chunking configuration has correct defaults"""
    from app.core.config import Settings

    settings = Settings()

    assert settings.CHUNKING_STRATEGY in ["semantic", "recursive"]
    assert settings.SEMANTIC_MIN_CHUNK_SIZE == 128
    assert settings.SEMANTIC_MAX_CHUNK_SIZE == 512
    assert settings.SEMANTIC_BREAKPOINT_PERCENTILE == 95.0
