"""Test prompt service for RAG synthesis."""
import pytest
from app.services.prompt_service import PromptService
from app.models.schemas import ChunkInput


def test_build_rag_prompt_single_chunk():
    """Test building RAG prompt with single chunk."""
    service = PromptService()
    chunks = [
        ChunkInput(text="Machine learning is AI", document_id="doc1", chunk_index=0)
    ]
    query = "What is machine learning?"

    prompt = service.build_rag_prompt(query, chunks)

    assert "What is machine learning?" in prompt
    assert "[1] Machine learning is AI" in prompt
    assert "Cite sources using [1]" in prompt


def test_build_rag_prompt_multiple_chunks():
    """Test building RAG prompt with multiple chunks."""
    service = PromptService()
    chunks = [
        ChunkInput(text="ML is AI subset", document_id="doc1", chunk_index=0),
        ChunkInput(text="It learns from data", document_id="doc1", chunk_index=1),
        ChunkInput(text="Used for predictions", document_id="doc2", chunk_index=0)
    ]
    query = "Explain machine learning"

    prompt = service.build_rag_prompt(query, chunks)

    assert "[1] ML is AI subset" in prompt
    assert "[2] It learns from data" in prompt
    assert "[3] Used for predictions" in prompt
    assert "Explain machine learning" in prompt


def test_build_rag_prompt_empty_chunks():
    """Test building prompt with no chunks."""
    service = PromptService()
    chunks = []
    query = "Test query"

    prompt = service.build_rag_prompt(query, chunks)

    # Should still create valid prompt
    assert "Test query" in prompt
    assert "Context:" in prompt


def test_estimate_tokens():
    """Test token estimation."""
    service = PromptService()

    # Rough estimate: ~4 chars per token
    text = "This is a test sentence with some words."
    tokens = service.estimate_tokens(text)

    assert tokens > 0
    assert tokens < len(text)  # Should be less than character count
