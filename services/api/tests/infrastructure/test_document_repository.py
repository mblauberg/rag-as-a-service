"""Integration tests for DocumentRepositoryImpl.

Uses in-memory SQLite database with SQLAlchemy async API.
Tests the full mapping between domain entities and ORM models.
"""
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.enums import UploadStatus
from app.domain.entities.document import Document
from app.infrastructure.db.repositories.document_repository_impl import DocumentRepositoryImpl


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
def document_repository(async_session):
    """Create DocumentRepositoryImpl instance."""
    return DocumentRepositoryImpl(async_session)


@pytest.mark.asyncio
async def test_save_document(document_repository):
    """Test saving a new document."""
    # Arrange
    document = Document(
        id=uuid4(),
        title="Test Document",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.PROCESSING,
        description="Test description",
    )

    # Act
    saved_document = await document_repository.save(document)

    # Assert
    assert saved_document.id == document.id
    assert saved_document.title == document.title
    assert saved_document.upload_status == UploadStatus.PROCESSING


@pytest.mark.asyncio
async def test_find_by_id(document_repository):
    """Test finding document by ID."""
    # Arrange - create and save a document
    document = Document(
        id=uuid4(),
        title="Find Me",
        file_name="findme.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.COMPLETED,
    )
    await document_repository.save(document)

    # Act
    found = await document_repository.find_by_id(document.id)

    # Assert
    assert found is not None
    assert found.id == document.id
    assert found.title == "Find Me"
    assert found.upload_status == UploadStatus.COMPLETED


@pytest.mark.asyncio
async def test_find_by_id_not_found(document_repository):
    """Test finding non-existent document returns None."""
    # Act
    found = await document_repository.find_by_id(uuid4())

    # Assert
    assert found is None


@pytest.mark.asyncio
async def test_update_document(document_repository):
    """Test updating an existing document."""
    # Arrange - create initial document
    document = Document(
        id=uuid4(),
        title="Original Title",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.PROCESSING,
    )
    await document_repository.save(document)

    # Act - update the document
    document.title = "Updated Title"
    document.upload_status = UploadStatus.COMPLETED
    updated = await document_repository.save(document)

    # Assert - verify changes persisted
    found = await document_repository.find_by_id(document.id)
    assert found is not None
    assert found.title == "Updated Title"
    assert found.upload_status == UploadStatus.COMPLETED


@pytest.mark.asyncio
async def test_find_all_pagination(document_repository):
    """Test paginated document retrieval."""
    # Arrange - create multiple documents
    for i in range(5):
        document = Document(
            id=uuid4(),
            title=f"Document {i}",
            file_name=f"doc{i}.pdf",
            file_type="pdf",
            created_at=datetime.now(UTC),
            upload_status=UploadStatus.COMPLETED,
        )
        await document_repository.save(document)

    # Act - get first page
    documents, total = await document_repository.find_all(page=1, limit=3)

    # Assert
    assert len(documents) == 3
    assert total == 5


@pytest.mark.asyncio
async def test_find_all_second_page(document_repository):
    """Test retrieving second page of results."""
    # Arrange - create 5 documents
    for i in range(5):
        document = Document(
            id=uuid4(),
            title=f"Document {i}",
            file_name=f"doc{i}.pdf",
            file_type="pdf",
            created_at=datetime.now(UTC),
            upload_status=UploadStatus.COMPLETED,
        )
        await document_repository.save(document)

    # Act - get second page
    documents, total = await document_repository.find_all(page=2, limit=3)

    # Assert
    assert len(documents) == 2  # Remaining documents
    assert total == 5


@pytest.mark.asyncio
async def test_delete_document(document_repository):
    """Test deleting a document."""
    # Arrange - create document
    document = Document(
        id=uuid4(),
        title="Delete Me",
        file_name="delete.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.COMPLETED,
    )
    await document_repository.save(document)

    # Act - delete document
    await document_repository.delete(document.id)

    # Assert - verify deleted
    found = await document_repository.find_by_id(document.id)
    assert found is None


@pytest.mark.asyncio
async def test_enum_mapping(document_repository):
    """Test that UploadStatus enum is properly mapped to/from database."""
    # Test all enum values
    for status in [
        UploadStatus.PENDING,
        UploadStatus.PROCESSING,
        UploadStatus.COMPLETED,
        UploadStatus.FAILED,
    ]:
        document = Document(
            id=uuid4(),
            title=f"Test {status.value}",
            file_name="test.pdf",
            file_type="pdf",
            created_at=datetime.now(UTC),
            upload_status=status,
        )

        # Save and retrieve
        await document_repository.save(document)
        found = await document_repository.find_by_id(document.id)

        # Assert enum is preserved
        assert found is not None
        assert found.upload_status == status
        assert isinstance(found.upload_status, UploadStatus)


@pytest.mark.asyncio
async def test_optional_fields(document_repository):
    """Test that optional fields are properly handled."""
    # Arrange - document with optional fields
    document = Document(
        id=uuid4(),
        title="With Optional Fields",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.COMPLETED,
        description="A description",
        file_path="/path/to/file",
        file_size=1024,
    )
    await document_repository.save(document)

    # Act
    found = await document_repository.find_by_id(document.id)

    # Assert
    assert found is not None
    assert found.description == "A description"
    assert found.file_path == "/path/to/file"
    assert found.file_size == 1024


@pytest.mark.asyncio
async def test_optional_fields_none(document_repository):
    """Test that None values in optional fields are handled."""
    # Arrange - document without optional fields
    document = Document(
        id=uuid4(),
        title="Minimal Document",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.PENDING,
        description=None,
        file_path=None,
        file_size=None,
    )
    await document_repository.save(document)

    # Act
    found = await document_repository.find_by_id(document.id)

    # Assert
    assert found is not None
    assert found.description is None
    assert found.file_path is None
    assert found.file_size is None
