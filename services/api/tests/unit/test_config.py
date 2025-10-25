def test_semantic_chunking_config_defaults():
    """Test semantic chunking configuration has correct defaults"""
    from app.core.config import Settings

    settings = Settings()

    # Use new nested config structure
    assert settings.chunking.strategy in ["semantic", "recursive"]
    assert settings.chunking.min_chunk_size == 128
    assert settings.chunking.max_chunk_size == 512
    assert settings.chunking.breakpoint_percentile == 95
