"""Integration tests for ChunkRepositoryImpl.

Uses in-memory SQLite database with SQLAlchemy async API.
Tests the full mapping between domain entities and ORM models.
"""
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.core.database import Base
from app.core.enums import UploadStatus
from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document
from app.infrastructure.db.repositories.chunk_repository_impl import \
    ChunkRepositoryImpl
from app.infrastructure.db.repositories.document_repository_impl import \
    DocumentRepositoryImpl


@pytest.fixture
async def async_session():
    """Create an in-memory SQLite database for testing."""
    # Use aiosqlite for async SQLite
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Yield session
    async with async_session_maker() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest.fixture
def chunk_repository(async_session):
    """Create ChunkRepositoryImpl instance."""
    return ChunkRepositoryImpl(async_session)


@pytest.fixture
def document_repository(async_session):
    """Create DocumentRepositoryImpl instance."""
    return DocumentRepositoryImpl(async_session)


@pytest.fixture
async def sample_document(document_repository):
    """Create a sample document for testing."""
    document = Document(
        id=uuid4(),
        title="Test Document",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.PROCESSING,
    )
    return await document_repository.save(document)


@pytest.mark.asyncio
async def test_save_batch_chunks(chunk_repository, sample_document):
    """Test saving multiple chunks atomically."""
    # Arrange
    chunks = [
        Chunk(
            id=uuid4(),
            document_id=sample_document.id,
            content=f"Chunk {i} content",
            tokens=10,
        )
        for i in range(3)
    ]

    # Act
    saved_chunks = await chunk_repository.save_batch(chunks)

    # Assert
    assert len(saved_chunks) == 3
    for original, saved in zip(chunks, saved_chunks):
        assert saved.id == original.id
        assert saved.content == original.content


@pytest.mark.asyncio
async def test_save_batch_with_metadata(chunk_repository, sample_document):
    """Test saving chunks with metadata."""
    # Arrange
    chunk = Chunk(
        id=uuid4(),
        document_id=sample_document.id,
        content="Test content",
        tokens=5,
        metadata={"section": "Introduction", "page": 1},
    )

    # Act
    saved = await chunk_repository.save_batch([chunk])

    # Assert
    assert len(saved) == 1
    assert saved[0].metadata == {"section": "Introduction", "page": 1}


@pytest.mark.asyncio
async def test_save_batch_with_optional_fields(chunk_repository, sample_document):
    """Test saving chunks with optional section fields."""
    # Arrange
    chunk = Chunk(
        id=uuid4(),
        document_id=sample_document.id,
        content="Test content",
        tokens=5,
        section_title="Chapter 1",
        section_level=1,
        page_number=10,
    )

    # Act
    saved = await chunk_repository.save_batch([chunk])

    # Assert
    assert len(saved) == 1
    assert saved[0].section_title == "Chapter 1"
    assert saved[0].section_level == 1
    assert saved[0].page_number == 10


@pytest.mark.asyncio
async def test_save_batch_with_embedding(chunk_repository, sample_document):
    """Test saving chunks with embedding vectors."""
    # Arrange
    chunk = Chunk(
        id=uuid4(),
        document_id=sample_document.id,
        content="Test content",
        tokens=5,
        embedding_vector=[0.1, 0.2, 0.3, 0.4, 0.5],
    )

    # Act
    saved = await chunk_repository.save_batch([chunk])

    # Assert
    assert len(saved) == 1
    # Note: embedding vectors are NOT stored in PostgreSQL - they go to Qdrant
    # So we don't test retrieval of embeddings from DB


@pytest.mark.asyncio
async def test_find_by_document_id(chunk_repository, sample_document):
    """Test retrieving chunks by document ID."""
    # Arrange - create chunks for this document
    chunks = [
        Chunk(
            id=uuid4(), document_id=sample_document.id, content=f"Chunk {i}", tokens=5
        )
        for i in range(3)
    ]
    await chunk_repository.save_batch(chunks)

    # Act
    found_chunks = await chunk_repository.find_by_document_id(sample_document.id)

    # Assert
    assert len(found_chunks) == 3
    found_ids = {chunk.id for chunk in found_chunks}
    expected_ids = {chunk.id for chunk in chunks}
    assert found_ids == expected_ids


@pytest.mark.asyncio
async def test_find_by_document_id_empty(chunk_repository, sample_document):
    """Test finding chunks for document with no chunks."""
    # Act - no chunks created
    found_chunks = await chunk_repository.find_by_document_id(sample_document.id)

    # Assert
    assert len(found_chunks) == 0


@pytest.mark.asyncio
async def test_find_by_document_id_multiple_documents(
    chunk_repository, document_repository, sample_document
):
    """Test that chunks are correctly filtered by document ID."""
    # Arrange - create second document
    doc2 = Document(
        id=uuid4(),
        title="Second Document",
        file_name="doc2.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.PROCESSING,
    )
    doc2 = await document_repository.save(doc2)

    # Create chunks for both documents
    chunks_doc1 = [
        Chunk(
            id=uuid4(),
            document_id=sample_document.id,
            content=f"Doc1 Chunk {i}",
            tokens=5,
        )
        for i in range(2)
    ]
    chunks_doc2 = [
        Chunk(id=uuid4(), document_id=doc2.id, content=f"Doc2 Chunk {i}", tokens=5)
        for i in range(3)
    ]

    await chunk_repository.save_batch(chunks_doc1 + chunks_doc2)

    # Act - find chunks for first document
    found = await chunk_repository.find_by_document_id(sample_document.id)

    # Assert - only chunks from first document
    assert len(found) == 2
    assert all(chunk.document_id == sample_document.id for chunk in found)


@pytest.mark.asyncio
async def test_delete_by_document_id(chunk_repository, sample_document):
    """Test deleting all chunks for a document."""
    # Arrange - create chunks
    chunks = [
        Chunk(
            id=uuid4(), document_id=sample_document.id, content=f"Chunk {i}", tokens=5
        )
        for i in range(3)
    ]
    await chunk_repository.save_batch(chunks)

    # Verify chunks exist
    found = await chunk_repository.find_by_document_id(sample_document.id)
    assert len(found) == 3

    # Act - delete chunks
    await chunk_repository.delete_by_document_id(sample_document.id)

    # Assert - chunks deleted
    found = await chunk_repository.find_by_document_id(sample_document.id)
    assert len(found) == 0


@pytest.mark.asyncio
async def test_delete_by_document_id_leaves_other_documents(
    chunk_repository, document_repository, sample_document
):
    """Test that deleting chunks for one document doesn't affect others."""
    # Arrange - create second document with chunks
    doc2 = Document(
        id=uuid4(),
        title="Second Document",
        file_name="doc2.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.PROCESSING,
    )
    doc2 = await document_repository.save(doc2)

    chunks_doc1 = [
        Chunk(
            id=uuid4(),
            document_id=sample_document.id,
            content=f"Doc1 Chunk {i}",
            tokens=5,
        )
        for i in range(2)
    ]
    chunks_doc2 = [
        Chunk(id=uuid4(), document_id=doc2.id, content=f"Doc2 Chunk {i}", tokens=5)
        for i in range(3)
    ]

    await chunk_repository.save_batch(chunks_doc1 + chunks_doc2)

    # Act - delete chunks for first document only
    await chunk_repository.delete_by_document_id(sample_document.id)

    # Assert - doc1 chunks deleted, doc2 chunks remain
    found_doc1 = await chunk_repository.find_by_document_id(sample_document.id)
    found_doc2 = await chunk_repository.find_by_document_id(doc2.id)

    assert len(found_doc1) == 0
    assert len(found_doc2) == 3


@pytest.mark.asyncio
async def test_empty_metadata_default(chunk_repository, sample_document):
    """Test that chunks without metadata get empty dict."""
    # Arrange
    chunk = Chunk(
        id=uuid4(),
        document_id=sample_document.id,
        content="Test",
        tokens=1
        # No metadata specified
    )

    # Act
    saved = await chunk_repository.save_batch([chunk])
    found = await chunk_repository.find_by_document_id(sample_document.id)

    # Assert
    assert saved[0].metadata == {}
    assert found[0].metadata == {}


@pytest.mark.asyncio
async def test_cascade_delete_on_document_deletion(
    chunk_repository, document_repository, sample_document
):
    """Test that chunks are deleted when parent document is deleted (cascade)."""
    # Arrange - create chunks
    chunks = [
        Chunk(
            id=uuid4(), document_id=sample_document.id, content=f"Chunk {i}", tokens=5
        )
        for i in range(3)
    ]
    await chunk_repository.save_batch(chunks)

    # Verify chunks exist
    found = await chunk_repository.find_by_document_id(sample_document.id)
    assert len(found) == 3

    # Act - delete parent document
    await document_repository.delete(sample_document.id)

    # Assert - chunks should be cascade deleted
    found = await chunk_repository.find_by_document_id(sample_document.id)
    assert len(found) == 0
