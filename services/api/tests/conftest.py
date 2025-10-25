"""Pytest configuration and fixtures for API tests."""
import os

# Set test environment variables before importing app modules
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("EMBEDDER_URL", "http://localhost:8001")
os.environ.setdefault("GENERATOR_URL", "http://localhost:8002")
os.environ.setdefault("UPLOAD_DIR", "/tmp/raas-test-uploads")

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.dependencies import get_qdrant_client
from app.core.qdrant_client import QdrantClientWrapper
from app.models.document import Document, DocumentChunk


# Test database URL - use PostgreSQL if DATABASE_URL env var is set, otherwise SQLite
TEST_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest_asyncio.fixture
async def db_engine():
    """
    Create test database engine.

    Uses PostgreSQL if DATABASE_URL is set, otherwise in-memory SQLite for fast tests.
    """
    # Configure engine based on database type
    engine_kwargs = {"echo": False}
    is_postgres = "postgresql" in TEST_DATABASE_URL

    if "sqlite" in TEST_DATABASE_URL:
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine_kwargs["poolclass"] = StaticPool
    else:
        # PostgreSQL configuration
        engine_kwargs["pool_pre_ping"] = True

    engine = create_async_engine(TEST_DATABASE_URL, **engine_kwargs)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # For PostgreSQL, apply additional FTS migration for text_search_vector column
        if is_postgres:
            await conn.execute(text("""
                ALTER TABLE document_chunks
                ADD COLUMN IF NOT EXISTS text_search_vector tsvector
                GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED;
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_text_search
                ON document_chunks
                USING GIN (text_search_vector);
            """))

    yield engine

    # Drop all tables (cleanup)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide database session for tests.

    Creates a new session for each test with automatic rollback.
    """
    AsyncTestingSessionLocal = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with AsyncTestingSessionLocal() as session:
        yield session


@pytest.fixture
def mock_qdrant_client():
    """
    Provide mocked Qdrant client.

    Returns a mock QdrantClientWrapper with common methods stubbed.
    """
    mock = Mock(spec=QdrantClientWrapper)

    # Mock health check
    mock.health_check = AsyncMock(return_value=True)

    # Mock collection initialization
    mock.ensure_collection_exists = AsyncMock(return_value=None)

    # Mock search
    mock.search = AsyncMock(return_value=[])

    # Mock delete
    mock.delete_points = AsyncMock(return_value=None)

    return mock


@pytest.fixture
def mock_embedder_client():
    """
    Provide mocked HTTP client for embedder service.

    Returns a mock AsyncClient with stubbed responses.
    """
    mock = AsyncMock(spec=AsyncClient)

    # Mock health check
    health_response = Mock()
    health_response.status_code = 200
    health_response.json.return_value = {"status": "healthy"}

    # Mock embed endpoint
    embed_response = Mock()
    embed_response.status_code = 200
    embed_response.json.return_value = {"success": True, "count": 1}

    # Mock embed query endpoint
    embed_query_response = Mock()
    embed_query_response.status_code = 200
    embed_query_response.json.return_value = {
        "embedding": [0.1] * 384  # 384-dim vector
    }

    # Configure mock to return appropriate responses based on URL
    async def mock_post(*args, **kwargs):
        url = args[0] if args else kwargs.get('url', '')
        if 'embed' in url and 'query' not in url:
            return embed_response
        elif 'query' in url:
            return embed_query_response
        return Mock(status_code=404)

    async def mock_get(*args, **kwargs):
        url = args[0] if args else kwargs.get('url', '')
        if 'health' in url:
            return health_response
        return Mock(status_code=404)

    mock.post = AsyncMock(side_effect=mock_post)
    mock.get = AsyncMock(side_effect=mock_get)

    return mock


@pytest_asyncio.fixture
async def async_client(db_session, mock_qdrant_client, mock_embedder_client):
    """
    Provide async test client with dependency overrides.

    Overrides database and Qdrant dependencies with mocks.
    """
    # Override dependencies
    async def override_get_db():
        yield db_session

    def override_get_qdrant_client():
        return mock_qdrant_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_qdrant_client] = override_get_qdrant_client

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_document(db_session) -> Document:
    """
    Create sample document in database.

    Returns a Document instance for testing.
    """
    document = Document(
        id=uuid4(),
        title="Test Document",
        description="Test description",
        file_name="test.pdf",
        file_type="application/pdf",
        file_size=1024,
        file_path="/test/path/test.pdf",
        upload_status="completed",
        embedding_status="completed"
    )

    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    return document


@pytest_asyncio.fixture
async def sample_document_with_chunks(db_session) -> Document:
    """
    Create sample document with chunks in database.

    Returns a Document instance with associated chunks for testing.
    """
    document = Document(
        id=uuid4(),
        title="Test Document with Chunks",
        description="Test description",
        file_name="test.pdf",
        file_type="application/pdf",
        file_size=1024,
        file_path="/test/path/test.pdf",
        upload_status="completed",
        embedding_status="completed"
    )

    db_session.add(document)
    await db_session.flush()

    # Add chunks
    for i in range(3):
        chunk = DocumentChunk(
            id=uuid4(),
            document_id=document.id,
            chunk_index=i,
            chunk_text=f"This is chunk {i} text content for testing.",
            qdrant_point_id=uuid4(),
            token_count=10
        )
        db_session.add(chunk)

    await db_session.commit()
    await db_session.refresh(document)

    return document


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
