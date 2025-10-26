"""Tests for QdrantVectorStore implementation.

Uses mocked QdrantClient to test vector store upsert and delete operations.
Search functionality has been moved to the dedicated search microservice.
"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from app.core.exceptions import VectorStoreError
from app.domain.entities.chunk import Chunk
from app.infrastructure.vector_store.qdrant_store import QdrantVectorStoreImpl


@pytest.fixture
def mock_qdrant_client():
    """Create a mocked QdrantClient."""
    client = AsyncMock()
    return client


@pytest.fixture
def vector_store(mock_qdrant_client):
    """Create QdrantVectorStoreImpl with mocked client."""
    return QdrantVectorStoreImpl(
        client=mock_qdrant_client, collection_name="test_collection"
    )


@pytest.fixture
def sample_chunks():
    """Create sample chunks with embeddings."""
    doc_id = uuid4()
    return [
        Chunk(
            id=uuid4(),
            document_id=doc_id,
            content="First chunk content",
            tokens=10,
            embedding_vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"page": 1},
        ),
        Chunk(
            id=uuid4(),
            document_id=doc_id,
            content="Second chunk content",
            tokens=12,
            embedding_vector=[0.5, 0.4, 0.3, 0.2, 0.1],
            metadata={"page": 2},
        ),
        Chunk(
            id=uuid4(),
            document_id=doc_id,
            content="Third chunk content",
            tokens=8,
            embedding_vector=[0.3, 0.3, 0.3, 0.3, 0.3],
            section_title="Introduction",
            section_level=1,
            page_number=3,
        ),
    ]


@pytest.mark.asyncio
async def test_upsert_success(vector_store, mock_qdrant_client, sample_chunks):
    """Test successful upsert of chunks to Qdrant."""
    # Arrange
    mock_qdrant_client.upsert = AsyncMock()

    # Act
    await vector_store.upsert(sample_chunks)

    # Assert
    mock_qdrant_client.upsert.assert_called_once()
    call_args = mock_qdrant_client.upsert.call_args

    # Verify collection name
    assert call_args.kwargs["collection_name"] == "test_collection"

    # Verify points structure
    points = call_args.kwargs["points"]
    assert len(points) == 3

    # Check first point
    point = points[0]
    assert isinstance(point, PointStruct)
    assert point.id == str(sample_chunks[0].id)
    assert point.vector == sample_chunks[0].embedding_vector
    assert point.payload["document_id"] == str(sample_chunks[0].document_id)
    assert point.payload["content"] == sample_chunks[0].content
    assert point.payload["tokens"] == sample_chunks[0].tokens
    assert point.payload["metadata"] == {"page": 1}


@pytest.mark.asyncio
async def test_upsert_with_optional_fields(
    vector_store, mock_qdrant_client, sample_chunks
):
    """Test upsert correctly handles optional fields."""
    # Arrange
    mock_qdrant_client.upsert = AsyncMock()

    # Act
    await vector_store.upsert([sample_chunks[2]])  # Has section fields

    # Assert
    points = mock_qdrant_client.upsert.call_args.kwargs["points"]
    payload = points[0].payload

    assert payload["section_title"] == "Introduction"
    assert payload["section_level"] == 1
    assert payload["page_number"] == 3


@pytest.mark.asyncio
async def test_upsert_without_optional_fields(vector_store, mock_qdrant_client):
    """Test upsert handles chunks without optional fields."""
    # Arrange
    chunk = Chunk(
        id=uuid4(),
        document_id=uuid4(),
        content="Test content",
        tokens=5,
        embedding_vector=[0.1, 0.2, 0.3],
        # No section_title, section_level, page_number
    )
    mock_qdrant_client.upsert = AsyncMock()

    # Act
    await vector_store.upsert([chunk])

    # Assert
    points = mock_qdrant_client.upsert.call_args.kwargs["points"]
    payload = points[0].payload

    assert payload["section_title"] is None
    assert payload["section_level"] is None
    assert payload["page_number"] is None


@pytest.mark.asyncio
async def test_upsert_empty_list(vector_store, mock_qdrant_client):
    """Test upsert with empty chunk list does nothing."""
    # Arrange
    mock_qdrant_client.upsert = AsyncMock()

    # Act
    await vector_store.upsert([])

    # Assert - should not call upsert
    mock_qdrant_client.upsert.assert_not_called()


@pytest.mark.asyncio
async def test_upsert_without_embeddings_raises_error(vector_store, mock_qdrant_client):
    """Test upsert raises error if chunks don't have embeddings."""
    # Arrange
    chunk = Chunk(
        id=uuid4(),
        document_id=uuid4(),
        content="Test content",
        tokens=5,
        embedding_vector=None,  # No embedding
    )

    # Act & Assert
    with pytest.raises(VectorStoreError) as exc_info:
        await vector_store.upsert([chunk])

    assert "missing embedding vector" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_upsert_client_error_raises_vector_store_error(
    vector_store, mock_qdrant_client, sample_chunks
):
    """Test that Qdrant client errors are wrapped in VectorStoreError."""
    # Arrange
    mock_qdrant_client.upsert = AsyncMock(
        side_effect=Exception("Qdrant connection failed")
    )

    # Act & Assert
    with pytest.raises(VectorStoreError) as exc_info:
        await vector_store.upsert(sample_chunks)

    assert "upsert" in str(exc_info.value).lower()
    assert exc_info.value.original_error is not None


@pytest.mark.asyncio
async def test_delete_by_document_success(vector_store, mock_qdrant_client):
    """Test successful deletion of chunks by document ID."""
    # Arrange
    doc_id = uuid4()
    mock_qdrant_client.delete = AsyncMock()

    # Act
    await vector_store.delete_by_document(doc_id)

    # Assert
    mock_qdrant_client.delete.assert_called_once()
    call_args = mock_qdrant_client.delete.call_args

    assert call_args.kwargs["collection_name"] == "test_collection"

    # Verify filter
    points_selector = call_args.kwargs["points_selector"]
    query_filter = points_selector.filter

    assert isinstance(query_filter, Filter)
    assert len(query_filter.must) == 1

    field_condition = query_filter.must[0]
    assert field_condition.key == "document_id"
    assert field_condition.match.value == str(doc_id)


@pytest.mark.asyncio
async def test_delete_by_document_client_error_raises_vector_store_error(
    vector_store, mock_qdrant_client
):
    """Test that delete errors are wrapped in VectorStoreError."""
    # Arrange
    mock_qdrant_client.delete = AsyncMock(side_effect=Exception("Delete failed"))

    # Act & Assert
    with pytest.raises(VectorStoreError) as exc_info:
        await vector_store.delete_by_document(uuid4())

    assert "delete" in str(exc_info.value).lower()
    assert exc_info.value.original_error is not None


@pytest.mark.asyncio
async def test_metadata_serialization(vector_store, mock_qdrant_client):
    """Test that metadata dictionary is properly serialized."""
    # Arrange
    chunk = Chunk(
        id=uuid4(),
        document_id=uuid4(),
        content="Test",
        tokens=5,
        embedding_vector=[0.1, 0.2],
        metadata={"nested": {"key": "value"}, "list": [1, 2, 3], "string": "test"},
    )
    mock_qdrant_client.upsert = AsyncMock()

    # Act
    await vector_store.upsert([chunk])

    # Assert
    points = mock_qdrant_client.upsert.call_args.kwargs["points"]
    payload = points[0].payload

    assert payload["metadata"] == {
        "nested": {"key": "value"},
        "list": [1, 2, 3],
        "string": "test",
    }
