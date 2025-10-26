"""Tests for QdrantVectorStore implementation.

Uses mocked QdrantClient to test vector store operations without
requiring an actual Qdrant instance.
"""
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from qdrant_client.models import (FieldCondition, Filter, MatchValue,
                                  PointStruct, ScoredPoint)

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
async def test_search_success(vector_store, mock_qdrant_client):
    """Test successful vector search."""
    # Arrange
    query_vector = [0.2, 0.3, 0.4, 0.3, 0.2]
    doc_id = uuid4()

    # Mock search response
    mock_scored_points = [
        ScoredPoint(
            id=str(uuid4()),
            score=0.95,
            version=1,
            payload={
                "document_id": str(doc_id),
                "content": "Matching chunk",
                "tokens": 8,
                "metadata": {},
                "section_title": None,
                "section_level": None,
                "page_number": None,
            },
            vector=None,
        ),
        ScoredPoint(
            id=str(uuid4()),
            score=0.87,
            version=1,
            payload={
                "document_id": str(doc_id),
                "content": "Another match",
                "tokens": 10,
                "metadata": {"page": 1},
                "section_title": "Intro",
                "section_level": 1,
                "page_number": 1,
            },
            vector=None,
        ),
    ]
    mock_qdrant_client.search = AsyncMock(return_value=mock_scored_points)

    # Act
    results = await vector_store.search(
        query_vector=query_vector, top_k=5, document_id=None
    )

    # Assert
    mock_qdrant_client.search.assert_called_once()
    call_args = mock_qdrant_client.search.call_args

    assert call_args.kwargs["collection_name"] == "test_collection"
    assert call_args.kwargs["query_vector"] == query_vector
    assert call_args.kwargs["limit"] == 5
    assert call_args.kwargs["query_filter"] is None

    # Verify results
    assert len(results) == 2
    assert isinstance(results[0], Chunk)
    assert results[0].content == "Matching chunk"
    assert results[0].tokens == 8
    assert results[1].content == "Another match"
    assert results[1].section_title == "Intro"


@pytest.mark.asyncio
async def test_search_with_document_filter(vector_store, mock_qdrant_client):
    """Test search with document_id filter."""
    # Arrange
    query_vector = [0.1, 0.2, 0.3]
    doc_id = uuid4()
    mock_qdrant_client.search = AsyncMock(return_value=[])

    # Act
    await vector_store.search(query_vector=query_vector, top_k=10, document_id=doc_id)

    # Assert
    call_args = mock_qdrant_client.search.call_args
    query_filter = call_args.kwargs["query_filter"]

    # Verify filter structure
    assert query_filter is not None
    assert isinstance(query_filter, Filter)
    assert len(query_filter.must) == 1

    field_condition = query_filter.must[0]
    assert isinstance(field_condition, FieldCondition)
    assert field_condition.key == "document_id"
    assert isinstance(field_condition.match, MatchValue)
    assert field_condition.match.value == str(doc_id)


@pytest.mark.asyncio
async def test_search_uuid_conversion(vector_store, mock_qdrant_client):
    """Test that UUIDs are properly converted from strings in results."""
    # Arrange
    chunk_id = uuid4()
    doc_id = uuid4()

    mock_scored_point = ScoredPoint(
        id=str(chunk_id),
        score=0.95,
        version=1,
        payload={
            "document_id": str(doc_id),
            "content": "Test",
            "tokens": 5,
            "metadata": {},
            "section_title": None,
            "section_level": None,
            "page_number": None,
        },
        vector=None,
    )
    mock_qdrant_client.search = AsyncMock(return_value=[mock_scored_point])

    # Act
    results = await vector_store.search([0.1, 0.2], top_k=1)

    # Assert
    assert results[0].id == chunk_id
    assert results[0].document_id == doc_id
    assert isinstance(results[0].id, UUID)
    assert isinstance(results[0].document_id, UUID)


@pytest.mark.asyncio
async def test_search_empty_results(vector_store, mock_qdrant_client):
    """Test search with no matching results."""
    # Arrange
    mock_qdrant_client.search = AsyncMock(return_value=[])

    # Act
    results = await vector_store.search([0.1, 0.2, 0.3], top_k=5)

    # Assert
    assert results == []


@pytest.mark.asyncio
async def test_search_client_error_raises_vector_store_error(
    vector_store, mock_qdrant_client
):
    """Test that search errors are wrapped in VectorStoreError."""
    # Arrange
    mock_qdrant_client.search = AsyncMock(side_effect=Exception("Search failed"))

    # Act & Assert
    with pytest.raises(VectorStoreError) as exc_info:
        await vector_store.search([0.1, 0.2], top_k=5)

    assert "search" in str(exc_info.value).lower()


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
