"""Tests for Reranker port."""
from uuid import uuid4

import pytest

from app.domain.entities.chunk import Chunk
from app.ports.services import Reranker


class MockReranker(Reranker):
    """Mock implementation for testing."""

    async def rerank(self, query: str, chunks: list[Chunk], top_k: int) -> list[Chunk]:
        """Return top_k chunks in reverse order (mock reranking)."""
        # Reverse the list as a simple mock reranking strategy
        reranked = list(reversed(chunks))
        return reranked[:top_k]


@pytest.mark.asyncio
async def test_reranker_port_contract():
    """Test that Reranker port has correct interface."""
    reranker = MockReranker()

    # Create test chunks
    doc_id = uuid4()
    chunks = [
        Chunk(
            id=uuid4(),
            document_id=doc_id,
            content=f"Test content {i}",
            tokens=10,
            embedding_vector=[0.1 * i] * 384,
        )
        for i in range(5)
    ]

    results = await reranker.rerank(query="test query", chunks=chunks, top_k=3)

    assert isinstance(results, list)
    assert all(isinstance(chunk, Chunk) for chunk in results)


@pytest.mark.asyncio
async def test_reranker_respects_top_k():
    """Test that rerank respects top_k parameter."""
    reranker = MockReranker()

    # Create test chunks
    doc_id = uuid4()
    chunks = [
        Chunk(id=uuid4(), document_id=doc_id, content=f"Test content {i}", tokens=10)
        for i in range(10)
    ]

    # Test with top_k=3
    results = await reranker.rerank("test", chunks, top_k=3)
    assert len(results) == 3

    # Test with top_k=5
    results = await reranker.rerank("test", chunks, top_k=5)
    assert len(results) == 5

    # Test with top_k greater than chunks length
    results = await reranker.rerank("test", chunks, top_k=20)
    assert len(results) <= len(chunks)


@pytest.mark.asyncio
async def test_reranker_preserves_chunk_data():
    """Test that reranking preserves all chunk data."""
    reranker = MockReranker()

    # Create chunk with all fields populated
    doc_id = uuid4()
    chunk_id = uuid4()
    original_chunk = Chunk(
        id=chunk_id,
        document_id=doc_id,
        content="Important test content",
        tokens=25,
        embedding_vector=[0.5] * 384,
        metadata={"source": "test.pdf", "page": 1},
        section_title="Introduction",
        section_level=1,
        page_number=1,
    )

    results = await reranker.rerank(
        query="test query", chunks=[original_chunk], top_k=1
    )

    # Verify all fields are preserved
    assert len(results) == 1
    reranked_chunk = results[0]

    assert reranked_chunk.id == chunk_id
    assert reranked_chunk.document_id == doc_id
    assert reranked_chunk.content == "Important test content"
    assert reranked_chunk.tokens == 25
    assert reranked_chunk.embedding_vector == [0.5] * 384
    assert reranked_chunk.metadata == {"source": "test.pdf", "page": 1}
    assert reranked_chunk.section_title == "Introduction"
    assert reranked_chunk.section_level == 1
    assert reranked_chunk.page_number == 1


@pytest.mark.asyncio
async def test_reranker_handles_empty_chunks():
    """Test that rerank handles empty chunk list."""
    reranker = MockReranker()

    results = await reranker.rerank(query="test query", chunks=[], top_k=5)

    assert isinstance(results, list)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_reranker_handles_single_chunk():
    """Test that rerank handles single chunk correctly."""
    reranker = MockReranker()

    doc_id = uuid4()
    chunk = Chunk(id=uuid4(), document_id=doc_id, content="Single chunk", tokens=10)

    results = await reranker.rerank(query="test query", chunks=[chunk], top_k=5)

    assert len(results) == 1
    assert results[0].content == "Single chunk"
