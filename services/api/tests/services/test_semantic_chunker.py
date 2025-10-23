import pytest
from app.services.chunking.semantic_chunker import SemanticChunker


def test_chunk_simple_text():
    """Test basic text chunking"""
    chunker = SemanticChunker(chunk_size=50, overlap=10)
    text = "This is sentence one. This is sentence two. This is sentence three."

    chunks = chunker.chunk_text(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)


def test_chunk_respects_token_limit():
    """Test that chunks don't exceed token limit"""
    chunker = SemanticChunker(chunk_size=100, overlap=20)
    text = "word " * 200  # Create long text

    chunks = chunker.chunk_text(text)

    for chunk in chunks:
        token_count = chunker.count_tokens(chunk)
        # Allow small buffer due to character-to-token estimation
        assert token_count <= 110


def test_chunk_empty_text():
    """Test chunking empty text"""
    chunker = SemanticChunker(chunk_size=50, overlap=10)
    chunks = chunker.chunk_text("")
    assert chunks == []


def test_chunk_with_sections():
    """Test chunking with section context prepended"""
    chunker = SemanticChunker(chunk_size=100, overlap=20)
    text = "This is the main content of the section."
    section_path = "Document > Chapter 1 > Introduction"

    chunks = chunker.chunk_text(text, section_context=section_path)

    assert len(chunks) > 0
    # First chunk should include section context
    assert section_path in chunks[0]


def test_chunk_with_metadata():
    """Test chunk_with_metadata returns proper structure"""
    chunker = SemanticChunker(chunk_size=100, overlap=20)
    text = "This is test content for metadata extraction."

    chunks = chunker.chunk_with_metadata(text)

    assert len(chunks) > 0
    for chunk in chunks:
        assert 'content' in chunk
        assert 'tokens' in chunk
        assert isinstance(chunk['content'], str)
        assert isinstance(chunk['tokens'], int)
