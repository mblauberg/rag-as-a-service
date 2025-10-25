"""Tests for Chunk domain entity."""
import pytest
from uuid import uuid4

from app.domain.entities.chunk import Chunk


def test_chunk_creation():
    """Test creating a chunk entity."""
    chunk_id = uuid4()
    doc_id = uuid4()

    chunk = Chunk(
        id=chunk_id,
        document_id=doc_id,
        content="This is chunk content",
        tokens=5
    )

    assert chunk.id == chunk_id
    assert chunk.document_id == doc_id
    assert chunk.content == "This is chunk content"
    assert chunk.tokens == 5
    assert chunk.embedding_vector is None


def test_chunk_has_embedding():
    """Test checking if chunk has embedding."""
    chunk_no_embedding = Chunk(
        id=uuid4(),
        document_id=uuid4(),
        content="Test",
        tokens=1
    )

    chunk_with_embedding = Chunk(
        id=uuid4(),
        document_id=uuid4(),
        content="Test",
        tokens=1,
        embedding_vector=[0.1, 0.2, 0.3]
    )

    assert not chunk_no_embedding.has_embedding()
    assert chunk_with_embedding.has_embedding()


def test_chunk_metadata():
    """Test chunk with metadata."""
    chunk = Chunk(
        id=uuid4(),
        document_id=uuid4(),
        content="Test content",
        tokens=2,
        metadata={"section": "Introduction", "page": 1}
    )

    assert chunk.metadata["section"] == "Introduction"
    assert chunk.metadata["page"] == 1
