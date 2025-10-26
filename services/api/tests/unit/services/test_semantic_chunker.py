import pytest

from app.services.chunking.semantic_chunker import SemanticChunker


@pytest.mark.asyncio
async def test_semantic_chunker_creates_coherent_chunks():
    """Test that semantic chunker splits on semantic boundaries"""
    chunker = SemanticChunker(
        min_chunk_size=50, max_chunk_size=200, breakpoint_percentile=95.0
    )

    # Text with clear semantic shift
    text = """
    Kubernetes is a container orchestration platform. It manages containerized applications.
    It provides automated deployment and scaling capabilities.

    Python is a programming language. It is widely used for data science and web development.
    Python has a simple and readable syntax.
    """

    chunks = await chunker.chunk_text(text)

    # Should create at least 2 chunks (k8s topic vs Python topic)
    assert len(chunks) >= 2

    # First chunk should be about Kubernetes
    assert (
        "kubernetes" in chunks[0].text.lower() or "container" in chunks[0].text.lower()
    )

    # Later chunk should be about Python
    assert any("python" in chunk.text.lower() for chunk in chunks[1:])


@pytest.mark.asyncio
async def test_semantic_chunker_respects_size_limits():
    """Test that chunks respect min/max size constraints"""
    chunker = SemanticChunker(min_chunk_size=100, max_chunk_size=500)

    text = "Short sentence. " * 100  # Repeated text

    chunks = await chunker.chunk_text(text)

    for chunk in chunks:
        token_count = len(chunk.text.split())
        assert 100 <= token_count <= 500, f"Chunk size {token_count} outside limits"
