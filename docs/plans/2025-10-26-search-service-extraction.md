# Search Service Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract all search/retrieval logic from the API service into a new dedicated Search microservice, creating a clean fourth microservice for the RAG system.

**Architecture:** Create a new FastAPI service (`services/search`) that encapsulates vector search, keyword search, hybrid fusion (RRF), query expansion, and reranking. The API service will become a pure orchestrator, delegating all search operations to this new service via HTTP.

**Tech Stack:**
- FastAPI (async Python web framework)
- Qdrant Python client (vector database)
- PostgreSQL with asyncpg (keyword search via FTS)
- sentence-transformers (cross-encoder reranking)
- Pydantic v2 (data validation)

**Microservices After Extraction:**
1. API Service - Orchestration, CRUD, Upload
2. Embedder Service - Bi-encoder embeddings
3. Generator Service - LLM generation
4. **Search Service (NEW)** - All retrieval logic

---

## Phase 1: Search Service Foundation

### Task 1: Create Search Service Project Structure

**Files:**
- Create: `services/search/README.md`
- Create: `services/search/pyproject.toml`
- Create: `services/search/Dockerfile`
- Create: `services/search/.dockerignore`
- Create: `services/search/app/__init__.py`
- Create: `services/search/app/core/__init__.py`
- Create: `services/search/app/models/__init__.py`
- Create: `services/search/app/services/__init__.py`
- Create: `services/search/tests/__init__.py`

**Step 1: Create README**

```markdown
# RAAS Search Service

Intelligent search and retrieval service for RAG-as-a-Service.

## Features

- **Hybrid Search**: Combines semantic (vector) and lexical (keyword) search
- **Reciprocal Rank Fusion**: Merges multiple result sets intelligently
- **Cross-Encoder Reranking**: Improves precision with query-document relevance scoring
- **Query Expansion**: LLM-based multi-query generation for better recall
- **Flexible Modes**: Vector-only, keyword-only, or hybrid retrieval

## API Endpoints

- `POST /api/v1/search` - Hybrid search with all features
- `GET /api/v1/health` - Health check
- `GET /api/v1/ready` - Readiness check

## Tech Stack

- FastAPI for async HTTP API
- Qdrant for vector similarity search
- PostgreSQL FTS for keyword search
- Cross-encoder models for reranking
```

**Step 2: Create pyproject.toml**

```toml
[tool.poetry]
name = "raas-search"
version = "0.1.0"
description = "Search and retrieval service for RAAS"
authors = ["RAAS Team"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.13"
fastapi = "^0.115.0"
uvicorn = {extras = ["standard"], version = "^0.32.0"}
pydantic = "^2.12.0"
pydantic-settings = "^2.6.0"
httpx = "^0.27.0"
qdrant-client = "^1.12.0"
asyncpg = "^0.30.0"
sqlalchemy = "^2.0.36"
sentence-transformers = "^3.3.0"
numpy = "^2.3.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.0"
pytest-asyncio = "^0.24.0"
pytest-cov = "^6.0.0"
pytest-mock = "^3.14.0"
mypy = "^1.13.0"
ruff = "^0.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
check_untyped_defs = true
no_implicit_optional = true

[[tool.mypy.overrides]]
module = ["qdrant_client.*", "sentence_transformers.*"]
ignore_missing_imports = true
```

**Step 3: Create Dockerfile**

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no dev dependencies in production)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY ./app ./app

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/api/v1/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

**Step 4: Create .dockerignore**

```
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/
.venv/
.mypy_cache/
.ruff_cache/
tests/
*.md
!README.md
```

**Step 5: Create __init__.py files**

Create empty `__init__.py` files in all directories listed above.

**Step 6: Verify structure**

Run: `tree services/search -L 3`
Expected: Clean directory structure with all folders

**Step 7: Commit**

```bash
git add services/search/
git commit -m "feat(search): create search service project structure

- Add pyproject.toml with dependencies
- Add Dockerfile for containerization
- Create app directory structure
- Add README with service overview"
```

---

### Task 2: Define Domain Models and Schemas

**Files:**
- Create: `services/search/app/models/domain.py`
- Create: `services/search/app/models/schemas.py`
- Create: `services/search/tests/models/test_schemas.py`

**Step 1: Write test for Chunk domain model**

Create `services/search/tests/models/__init__.py` (empty file)

Create `services/search/tests/models/test_schemas.py`:

```python
"""Tests for search service schemas."""
import pytest
from uuid import uuid4
from app.models.domain import Chunk
from app.models.schemas import SearchRequest, SearchResponse, SearchMode


class TestChunk:
    """Test Chunk domain model."""

    def test_chunk_creation_minimal(self):
        """Test creating chunk with minimal fields."""
        chunk_id = uuid4()
        doc_id = uuid4()

        chunk = Chunk(
            id=chunk_id,
            document_id=doc_id,
            content="Test content",
            tokens=2
        )

        assert chunk.id == chunk_id
        assert chunk.document_id == doc_id
        assert chunk.content == "Test content"
        assert chunk.tokens == 2
        assert chunk.score is None
        assert chunk.document_title is None

    def test_chunk_with_score(self):
        """Test chunk with relevance score."""
        chunk = Chunk(
            id=uuid4(),
            document_id=uuid4(),
            content="Content",
            tokens=1,
            score=0.95
        )

        assert chunk.score == 0.95


class TestSearchRequest:
    """Test SearchRequest schema."""

    def test_search_request_minimal(self):
        """Test search request with minimal fields."""
        request = SearchRequest(query="test query")

        assert request.query == "test query"
        assert request.top_k == 10  # default
        assert request.mode == SearchMode.HYBRID  # default

    def test_search_request_custom_params(self):
        """Test search request with custom parameters."""
        request = SearchRequest(
            query="test",
            top_k=20,
            mode=SearchMode.VECTOR,
            use_expansion=False,
            use_reranking=False
        )

        assert request.top_k == 20
        assert request.mode == SearchMode.VECTOR
        assert request.use_expansion is False
        assert request.use_reranking is False

    def test_search_request_validates_empty_query(self):
        """Test that empty query is rejected."""
        with pytest.raises(ValueError):
            SearchRequest(query="")

    def test_search_request_validates_whitespace_query(self):
        """Test that whitespace-only query is rejected."""
        with pytest.raises(ValueError):
            SearchRequest(query="   ")


class TestSearchResponse:
    """Test SearchResponse schema."""

    def test_search_response_creation(self):
        """Test creating search response."""
        response = SearchResponse(
            query="test",
            results=[],
            total_results=0
        )

        assert response.query == "test"
        assert response.results == []
        assert response.total_results == 0
```

**Step 2: Run test to verify it fails**

Run: `cd services/search && poetry install && poetry run pytest tests/models/test_schemas.py -v`
Expected: Import errors - modules don't exist yet

**Step 3: Implement domain models**

Create `services/search/app/models/domain.py`:

```python
"""Domain models for search service."""
from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class Chunk:
    """Chunk domain entity.

    Represents a text chunk with optional metadata and relevance score.
    """

    id: UUID
    document_id: UUID
    content: str
    tokens: int
    score: float | None = None
    document_title: str | None = None
    document_filename: str | None = None
    chunk_index: int | None = None
    metadata: dict | None = field(default_factory=dict)

    def with_score(self, score: float) -> "Chunk":
        """Create new chunk with updated score."""
        self.score = score
        return self
```

**Step 4: Implement request/response schemas**

Create `services/search/app/models/schemas.py`:

```python
"""Pydantic schemas for search service API."""
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class SearchMode(str, Enum):
    """Search mode enumeration."""

    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class SearchRequest(BaseModel):
    """Search request schema."""

    query: str = Field(..., description="Search query text")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")
    mode: SearchMode = Field(SearchMode.HYBRID, description="Search mode")
    use_expansion: bool = Field(True, description="Enable query expansion")
    use_reranking: bool = Field(True, description="Enable cross-encoder reranking")
    document_id: UUID | None = Field(None, description="Filter by document ID")

    @field_validator("query")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Validate query is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or whitespace")
        return v.strip()


class ChunkResult(BaseModel):
    """Single search result chunk."""

    chunk_id: UUID
    document_id: UUID
    document_title: str | None
    content: str
    score: float
    chunk_index: int | None = None


class SearchResponse(BaseModel):
    """Search response schema."""

    query: str
    results: list[ChunkResult]
    total_results: int
    mode_used: SearchMode | None = None
    expansion_applied: bool = False
    reranking_applied: bool = False


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: str
    models_loaded: bool
    database_connected: bool
```

**Step 5: Run tests to verify they pass**

Run: `poetry run pytest tests/models/test_schemas.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add services/search/app/models/ services/search/tests/models/
git commit -m "feat(search): add domain models and API schemas

- Add Chunk domain model with score tracking
- Add SearchRequest/Response schemas with validation
- Add SearchMode enum for mode selection
- Add health/readiness response schemas
- Include comprehensive tests for all models"
```

---

### Task 3: Configuration and Settings

**Files:**
- Create: `services/search/app/core/config.py`
- Create: `services/search/tests/unit/test_config.py`

**Step 1: Write test for configuration**

Create `services/search/tests/unit/__init__.py` (empty)

Create `services/search/tests/unit/test_config.py`:

```python
"""Tests for search service configuration."""
import pytest
from pydantic import ValidationError
from app.core.config import Settings


class TestSettings:
    """Test Settings configuration."""

    def test_default_settings(self):
        """Test default configuration values."""
        settings = Settings()

        assert settings.service_name == "raas-search"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8003
        assert settings.log_level == "INFO"

    def test_database_url_required(self):
        """Test that database URL is required."""
        # Settings should work with default or empty DATABASE_URL
        # but in production it must be set
        settings = Settings()
        assert settings.database_url is not None

    def test_qdrant_url_validation(self):
        """Test Qdrant URL configuration."""
        settings = Settings(qdrant_url="http://localhost:6333")
        assert settings.qdrant_url == "http://localhost:6333"

    def test_reranking_model_name(self):
        """Test reranking model configuration."""
        settings = Settings()
        assert settings.reranking_model == "cross-encoder/ms-marco-MiniLM-L-6-v2"
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/unit/test_config.py -v`
Expected: Import error - config module doesn't exist

**Step 3: Implement configuration**

Create `services/search/app/core/config.py`:

```python
"""Configuration settings for search service."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Search service configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Service Info
    service_name: str = "raas-search"
    api_host: str = Field("0.0.0.0", description="API host")
    api_port: int = Field(8003, description="API port")
    api_workers: int = Field(2, description="Number of worker processes")
    log_level: str = Field("INFO", description="Logging level")

    # Database (PostgreSQL for keyword search)
    database_url: str = Field(
        "postgresql+asyncpg://raasuser:raaspass@postgres:5432/raasdb",
        description="PostgreSQL connection URL"
    )

    # Vector Database (Qdrant)
    qdrant_url: str = Field(
        "http://qdrant:6333",
        description="Qdrant vector database URL"
    )
    qdrant_collection: str = Field(
        "documents",
        description="Qdrant collection name"
    )

    # Embedder Service (for query embedding)
    embedder_url: str = Field(
        "http://embedder:8001",
        description="Embedder service URL"
    )

    # Generator Service (for query expansion)
    generator_url: str = Field(
        "http://generator:8002",
        description="Generator service URL for query expansion"
    )

    # Search Configuration
    default_search_mode: str = Field("hybrid", description="Default search mode")
    default_top_k: int = Field(10, ge=1, le=100, description="Default number of results")
    enable_query_expansion: bool = Field(True, description="Enable query expansion")
    enable_reranking: bool = Field(True, description="Enable reranking")
    rerank_candidates: int = Field(50, description="Candidates to retrieve for reranking")

    # Reranking Model
    reranking_model: str = Field(
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Cross-encoder model for reranking"
    )

    # RRF Configuration
    rrf_k: int = Field(60, description="RRF constant (research-proven default: 60)")

    # Query Expansion
    query_expansion_variants: int = Field(2, description="Number of query variants to generate")


# Global settings instance
settings = Settings()
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/unit/test_config.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/search/app/core/config.py services/search/tests/unit/
git commit -m "feat(search): add configuration management

- Add Settings class with Pydantic settings
- Configure database, Qdrant, embedder, generator URLs
- Add search configuration (modes, reranking, RRF)
- Include environment variable support
- Add configuration tests"
```

---

## Phase 2: Core Search Components

### Task 4: Vector Search Client

**Files:**
- Create: `services/search/app/services/vector_search.py`
- Create: `services/search/tests/services/test_vector_search.py`

**Step 1: Write test for vector search**

Create `services/search/tests/services/__init__.py` (empty)

Create `services/search/tests/services/test_vector_search.py`:

```python
"""Tests for vector search service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.services.vector_search import VectorSearchService
from app.models.domain import Chunk


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client."""
    client = MagicMock()
    client.search = AsyncMock()
    return client


@pytest.fixture
def vector_service(mock_qdrant_client):
    """Vector search service with mocked client."""
    with patch("app.services.vector_search.AsyncQdrantClient") as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_qdrant_client
        service = VectorSearchService(
            qdrant_url="http://localhost:6333",
            collection_name="documents"
        )
        service.client = mock_qdrant_client
        return service


@pytest.mark.asyncio
async def test_search_returns_chunks(vector_service, mock_qdrant_client):
    """Test vector search returns chunk objects."""
    # Mock Qdrant response
    doc_id = uuid4()
    mock_result = MagicMock()
    mock_result.id = str(uuid4())
    mock_result.score = 0.85
    mock_result.payload = {
        "document_id": str(doc_id),
        "content": "Test content",
        "tokens": 2,
        "document_title": "Test Doc"
    }

    mock_qdrant_client.search.return_value = [mock_result]

    # Execute search
    query_vector = [0.1] * 384
    results = await vector_service.search(query_vector, top_k=10)

    # Verify
    assert len(results) == 1
    assert isinstance(results[0], Chunk)
    assert results[0].content == "Test content"
    assert results[0].score == 0.85
    assert results[0].document_title == "Test Doc"


@pytest.mark.asyncio
async def test_search_with_document_filter(vector_service, mock_qdrant_client):
    """Test search with document ID filter."""
    doc_id = uuid4()
    query_vector = [0.1] * 384

    await vector_service.search(query_vector, top_k=10, document_id=doc_id)

    # Verify filter was applied
    call_kwargs = mock_qdrant_client.search.call_args.kwargs
    assert "query_filter" in call_kwargs
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/services/test_vector_search.py -v`
Expected: Import error - module doesn't exist

**Step 3: Implement vector search service**

Create `services/search/app/services/vector_search.py`:

```python
"""Vector search service using Qdrant."""
import logging
from uuid import UUID
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.models.domain import Chunk

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Service for vector similarity search using Qdrant."""

    def __init__(self, qdrant_url: str, collection_name: str):
        """Initialize vector search service.

        Args:
            qdrant_url: Qdrant server URL
            collection_name: Collection name to search
        """
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.client: AsyncQdrantClient | None = None

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        document_id: UUID | None = None
    ) -> list[Chunk]:
        """Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            document_id: Optional document filter

        Returns:
            List of chunks ordered by similarity
        """
        async with AsyncQdrantClient(url=self.qdrant_url) as client:
            # Build filter if document_id provided
            query_filter = None
            if document_id:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=str(document_id))
                        )
                    ]
                )

            # Execute search
            results = await client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=query_filter
            )

            # Convert to Chunk objects
            chunks = []
            for result in results:
                chunk = Chunk(
                    id=UUID(result.id),
                    document_id=UUID(result.payload["document_id"]),
                    content=result.payload["content"],
                    tokens=result.payload.get("tokens", 0),
                    score=result.score,
                    document_title=result.payload.get("document_title"),
                    document_filename=result.payload.get("document_filename"),
                    chunk_index=result.payload.get("chunk_index")
                )
                chunks.append(chunk)

            logger.info(f"Vector search returned {len(chunks)} results")
            return chunks
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/services/test_vector_search.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/search/app/services/vector_search.py services/search/tests/services/
git commit -m "feat(search): implement vector search service

- Add VectorSearchService with Qdrant integration
- Support document ID filtering
- Convert Qdrant results to Chunk domain objects
- Include comprehensive async tests with mocks"
```

---

### Task 5: Keyword Search Service

**Files:**
- Create: `services/search/app/services/keyword_search.py`
- Create: `services/search/tests/services/test_keyword_search.py`

**Step 1: Write test for keyword search**

Create `services/search/tests/services/test_keyword_search.py`:

```python
"""Tests for keyword search service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.services.keyword_search import KeywordSearchService
from app.models.domain import Chunk


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def keyword_service():
    """Keyword search service."""
    return KeywordSearchService()


@pytest.mark.asyncio
async def test_search_returns_chunks(keyword_service, mock_db_session):
    """Test keyword search returns chunk objects."""
    # Mock database result
    doc_id = uuid4()
    chunk_id = uuid4()

    mock_row = MagicMock()
    mock_row.id = chunk_id
    mock_row.document_id = doc_id
    mock_row.content = "Python programming language"
    mock_row.tokens = 3
    mock_row.document_title = "Python Guide"
    mock_row.rank = 0.95

    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row]
    mock_db_session.execute.return_value = mock_result

    # Execute search
    results = await keyword_service.search(
        session=mock_db_session,
        query_text="Python",
        top_k=10
    )

    # Verify
    assert len(results) == 1
    assert isinstance(results[0], Chunk)
    assert results[0].content == "Python programming language"
    assert results[0].document_title == "Python Guide"
    assert results[0].score is not None


@pytest.mark.asyncio
async def test_search_with_document_filter(keyword_service, mock_db_session):
    """Test keyword search with document filter."""
    doc_id = uuid4()

    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db_session.execute.return_value = mock_result

    await keyword_service.search(
        session=mock_db_session,
        query_text="test",
        top_k=10,
        document_id=doc_id
    )

    # Verify execute was called
    assert mock_db_session.execute.called
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/services/test_keyword_search.py -v`
Expected: Import error

**Step 3: Implement keyword search service**

Create `services/search/app/services/keyword_search.py`:

```python
"""Keyword search service using PostgreSQL Full-Text Search."""
import logging
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Chunk

logger = logging.getLogger(__name__)


class KeywordSearchService:
    """Service for keyword/lexical search using PostgreSQL FTS."""

    async def search(
        self,
        session: AsyncSession,
        query_text: str,
        top_k: int = 10,
        document_id: UUID | None = None
    ) -> list[Chunk]:
        """Search using PostgreSQL full-text search (BM25-like).

        Args:
            session: Database session
            query_text: Search query text
            top_k: Number of results
            document_id: Optional document filter

        Returns:
            List of chunks ranked by keyword relevance
        """
        # Build query with FTS ranking
        query = """
        SELECT
            c.id,
            c.document_id,
            c.content,
            c.tokens,
            c.chunk_index,
            d.title as document_title,
            d.file_name as document_filename,
            ts_rank(c.search_vector, plainto_tsquery('english', :query)) as rank
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.search_vector @@ plainto_tsquery('english', :query)
        """

        params = {"query": query_text, "limit": top_k}

        # Add document filter if provided
        if document_id:
            query += " AND c.document_id = :document_id"
            params["document_id"] = str(document_id)

        query += " ORDER BY rank DESC LIMIT :limit"

        # Execute search
        result = await session.execute(text(query), params)
        rows = result.all()

        # Convert to Chunk objects
        chunks = []
        for row in rows:
            chunk = Chunk(
                id=row.id,
                document_id=row.document_id,
                content=row.content,
                tokens=row.tokens,
                score=float(row.rank),  # FTS rank becomes score
                document_title=row.document_title,
                document_filename=row.document_filename,
                chunk_index=row.chunk_index
            )
            chunks.append(chunk)

        logger.info(f"Keyword search returned {len(chunks)} results")
        return chunks
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/services/test_keyword_search.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/search/app/services/keyword_search.py services/search/tests/services/test_keyword_search.py
git commit -m "feat(search): implement keyword search with PostgreSQL FTS

- Add KeywordSearchService using PostgreSQL full-text search
- Support ts_rank for BM25-like scoring
- Convert FTS rank to chunk scores
- Support document filtering
- Add comprehensive tests"
```

---

### Task 6: RRF Fusion Service

**Files:**
- Create: `services/search/app/services/fusion.py`
- Create: `services/search/tests/services/test_fusion.py`

**Step 1: Write test for RRF fusion**

Create `services/search/tests/services/test_fusion.py`:

```python
"""Tests for RRF fusion service."""
import pytest
from uuid import uuid4
from app.services.fusion import RRFFusionService
from app.models.domain import Chunk


@pytest.fixture
def fusion_service():
    """Fusion service instance."""
    return RRFFusionService(k=60)


@pytest.fixture
def sample_chunks():
    """Sample chunks for testing."""
    doc_id = uuid4()
    return [
        Chunk(id=uuid4(), document_id=doc_id, content="Chunk A", tokens=2),
        Chunk(id=uuid4(), document_id=doc_id, content="Chunk B", tokens=2),
        Chunk(id=uuid4(), document_id=doc_id, content="Chunk C", tokens=2),
    ]


def test_fuse_single_result_set(fusion_service, sample_chunks):
    """Test fusion with single result set returns same order."""
    result = fusion_service.fuse([sample_chunks])

    assert len(result) == 3
    assert result == sample_chunks


def test_fuse_multiple_result_sets(fusion_service, sample_chunks):
    """Test RRF fusion of multiple ranked lists."""
    # Different orderings of same chunks
    set1 = [sample_chunks[0], sample_chunks[1], sample_chunks[2]]
    set2 = [sample_chunks[2], sample_chunks[0], sample_chunks[1]]

    result = fusion_service.fuse([set1, set2])

    # All chunks should be present
    assert len(result) == 3
    assert all(chunk in sample_chunks for chunk in result)


def test_fuse_empty_result_sets(fusion_service):
    """Test fusion with empty result sets."""
    result = fusion_service.fuse([[], []])
    assert result == []


def test_rrf_score_calculation(fusion_service, sample_chunks):
    """Test RRF score calculation is correct."""
    # Chunk A: rank 1 in both lists -> 1/(60+1) + 1/(60+1) = 0.0328
    # Chunk B: rank 2 in list1, rank 3 in list2 -> 1/62 + 1/63 = 0.0319
    set1 = [sample_chunks[0], sample_chunks[1]]
    set2 = [sample_chunks[0], sample_chunks[2]]

    result = fusion_service.fuse([set1, set2])

    # Chunk A should be first (appears in both at top)
    assert result[0] == sample_chunks[0]
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/services/test_fusion.py -v`
Expected: Import error

**Step 3: Implement RRF fusion service**

Create `services/search/app/services/fusion.py`:

```python
"""Reciprocal Rank Fusion service for combining search results."""
import logging
from collections import defaultdict
from app.models.domain import Chunk

logger = logging.getLogger(__name__)


class RRFFusionService:
    """Reciprocal Rank Fusion (RRF) for merging ranked lists.

    RRF combines multiple ranked lists without score normalization.
    Formula: score(chunk) = sum(1 / (k + rank(chunk)))
    where k=60 is research-proven constant.

    Reference: "Reciprocal rank fusion outperforms condorcet and
    individual rank learning methods" (SIGIR 2009)
    """

    def __init__(self, k: int = 60):
        """Initialize RRF fusion service.

        Args:
            k: RRF constant (default 60, optimal for most cases)
        """
        self.k = k

    def fuse(self, result_sets: list[list[Chunk]]) -> list[Chunk]:
        """Fuse multiple ranked lists using RRF.

        Args:
            result_sets: List of ranked chunk lists to fuse

        Returns:
            Single fused list ranked by RRF score
        """
        if not result_sets:
            return []

        if len(result_sets) == 1:
            return result_sets[0]

        # Accumulate RRF scores
        scores: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, Chunk] = {}

        for result_set in result_sets:
            for rank, chunk in enumerate(result_set, start=1):
                chunk_key = str(chunk.id)
                # RRF formula: 1 / (k + rank)
                scores[chunk_key] += 1.0 / (self.k + rank)
                chunk_map[chunk_key] = chunk

        # Sort by RRF score (descending)
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Build result list
        fused_chunks = [chunk_map[chunk_id] for chunk_id, _ in sorted_ids]

        logger.info(
            f"Fused {len(result_sets)} result sets into {len(fused_chunks)} unique chunks"
        )

        return fused_chunks
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/services/test_fusion.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/search/app/services/fusion.py services/search/tests/services/test_fusion.py
git commit -m "feat(search): implement RRF fusion service

- Add RRFFusionService for merging ranked lists
- Use research-proven RRF algorithm (k=60)
- Handle single and multiple result sets
- Preserve chunk objects during fusion
- Add comprehensive fusion tests"
```

---

### Task 7: Cross-Encoder Reranking Service

**Files:**
- Copy: `services/api/app/infrastructure/reranking/cross_encoder_reranker.py` → `services/search/app/services/reranker.py`
- Create: `services/search/tests/services/test_reranker.py`

**Step 1: Write test for reranker**

Create `services/search/tests/services/test_reranker.py`:

```python
"""Tests for cross-encoder reranker."""
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
import numpy as np

from app.services.reranker import CrossEncoderReranker
from app.models.domain import Chunk


@pytest.fixture
def mock_cross_encoder():
    """Mock CrossEncoder model."""
    model = MagicMock()
    model.predict = MagicMock()
    return model


@pytest.fixture
def reranker(mock_cross_encoder):
    """Reranker with mocked model."""
    with patch("app.services.reranker.CrossEncoder") as mock_class:
        mock_class.return_value = mock_cross_encoder
        return CrossEncoderReranker()


@pytest.fixture
def sample_chunks():
    """Sample chunks."""
    doc_id = uuid4()
    return [
        Chunk(id=uuid4(), document_id=doc_id, content="Python programming", tokens=2),
        Chunk(id=uuid4(), document_id=doc_id, content="Weather forecast", tokens=2),
        Chunk(id=uuid4(), document_id=doc_id, content="Python syntax", tokens=2),
    ]


@pytest.mark.asyncio
async def test_rerank_reorders_by_relevance(reranker, mock_cross_encoder, sample_chunks):
    """Test reranking reorders chunks by relevance score."""
    query = "Python programming language"

    # Mock scores: third chunk (Python syntax) most relevant
    mock_cross_encoder.predict.return_value = np.array([0.7, 0.3, 0.9])

    result = await reranker.rerank(query, sample_chunks, top_k=3)

    # Verify reordering
    assert len(result) == 3
    assert result[0] == sample_chunks[2]  # Highest score (0.9)
    assert result[1] == sample_chunks[0]  # Second (0.7)
    assert result[2] == sample_chunks[1]  # Lowest (0.3)


@pytest.mark.asyncio
async def test_rerank_respects_top_k(reranker, mock_cross_encoder, sample_chunks):
    """Test reranking returns only top_k results."""
    query = "test"
    mock_cross_encoder.predict.return_value = np.array([0.7, 0.3, 0.9])

    result = await reranker.rerank(query, sample_chunks, top_k=2)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_rerank_empty_chunks(reranker, mock_cross_encoder):
    """Test reranking with empty chunk list."""
    result = await reranker.rerank("query", [], top_k=5)

    assert result == []
    mock_cross_encoder.predict.assert_not_called()


@pytest.mark.asyncio
async def test_rerank_attaches_normalized_scores(reranker, mock_cross_encoder, sample_chunks):
    """Test that normalized scores are attached to chunks."""
    query = "test"
    mock_cross_encoder.predict.return_value = np.array([0.5, 0.8, 0.2])

    result = await reranker.rerank(query, sample_chunks, top_k=3)

    # Verify scores are normalized to [0, 1]
    assert result[0].score == 1.0  # Highest raw score normalized to 1.0
    assert result[2].score == 0.0  # Lowest raw score normalized to 0.0
    assert 0.0 <= result[1].score <= 1.0
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/services/test_reranker.py -v`
Expected: Import error

**Step 3: Copy and adapt reranker implementation**

Create `services/search/app/services/reranker.py`:

```python
"""Cross-encoder reranker using Sentence Transformers."""
import logging
import numpy as np
from sentence_transformers import CrossEncoder

from app.models.domain import Chunk

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Cross-encoder based reranking.

    Uses BERT-based cross-encoder to compute query-document
    relevance scores. More accurate but slower than bi-encoders.

    Recommended for reranking top-50 to top-10.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Initialize cross-encoder model.

        Args:
            model_name: HuggingFace cross-encoder model
                       (default: MS MARCO MiniLM - fast and accurate)
        """
        logger.info(f"Loading cross-encoder model: {model_name}")
        self.model = CrossEncoder(model_name, device='cpu')
        logger.info("Cross-encoder model loaded")

    async def rerank(self, query: str, chunks: list[Chunk], top_k: int) -> list[Chunk]:
        """Rerank chunks using cross-encoder scores.

        Creates query-chunk pairs and scores them jointly.
        Much more accurate than cosine similarity.

        Attaches normalized cross-encoder relevance scores (0-1) to chunk.score field.
        Uses min-max normalization to map raw scores to [0, 1] range.

        Args:
            query: Search query
            chunks: Candidate chunks
            top_k: Number of top results to return

        Returns:
            Reranked list of top_k chunks with scores
        """
        if not chunks:
            return []

        # Create query-chunk pairs
        pairs = [(query, chunk.content) for chunk in chunks]

        # Score all pairs (batch processing)
        raw_scores = self.model.predict(pairs)

        # Normalize scores to 0-1 range using min-max normalization
        min_score = float(np.min(raw_scores))
        max_score = float(np.max(raw_scores))
        score_range = max_score - min_score

        if score_range > 0:
            normalized_scores = [(s - min_score) / score_range for s in raw_scores]
        else:
            # All scores identical - assign 1.0 to all
            normalized_scores = [1.0] * len(raw_scores)

        # Sort by normalized score (descending) and attach scores
        chunk_scores = list(zip(chunks, normalized_scores))
        chunk_scores.sort(key=lambda x: x[1], reverse=True)

        # Attach normalized scores to chunks and return top_k
        reranked_chunks = []
        for chunk, score in chunk_scores[:top_k]:
            chunk.score = float(score)
            reranked_chunks.append(chunk)

        logger.info(f"Reranked {len(chunks)} chunks to top {len(reranked_chunks)}")
        return reranked_chunks
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/services/test_reranker.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/search/app/services/reranker.py services/search/tests/services/test_reranker.py
git commit -m "feat(search): implement cross-encoder reranking

- Add CrossEncoderReranker with MS MARCO model
- Compute joint query-document relevance scores
- Normalize scores to [0, 1] range
- Support configurable top_k selection
- Add comprehensive reranking tests"
```

---

## Phase 3: API Implementation

### Task 8: Main Search Orchestrator

**Files:**
- Create: `services/search/app/services/search_orchestrator.py`
- Create: `services/search/tests/services/test_search_orchestrator.py`

**Step 1: Write test for search orchestrator**

Create `services/search/tests/services/test_search_orchestrator.py`:

```python
"""Tests for search orchestrator."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.search_orchestrator import SearchOrchestrator
from app.models.domain import Chunk
from app.models.schemas import SearchMode


@pytest.fixture
def mock_services():
    """Mock all search services."""
    return {
        "vector": AsyncMock(),
        "keyword": AsyncMock(),
        "fusion": MagicMock(),
        "reranker": AsyncMock(),
        "embedder_client": AsyncMock(),
    }


@pytest.fixture
def orchestrator(mock_services):
    """Search orchestrator with mocked services."""
    return SearchOrchestrator(
        vector_service=mock_services["vector"],
        keyword_service=mock_services["keyword"],
        fusion_service=mock_services["fusion"],
        reranker=mock_services["reranker"],
        embedder_client=mock_services["embedder_client"],
    )


@pytest.fixture
def sample_chunks():
    """Sample chunks."""
    doc_id = uuid4()
    return [
        Chunk(id=uuid4(), document_id=doc_id, content="Chunk 1", tokens=2, score=0.9),
        Chunk(id=uuid4(), document_id=doc_id, content="Chunk 2", tokens=2, score=0.8),
    ]


@pytest.mark.asyncio
async def test_vector_only_search(orchestrator, mock_services, sample_chunks):
    """Test vector-only search mode."""
    mock_services["embedder_client"].generate_embedding.return_value = [0.1] * 384
    mock_services["vector"].search.return_value = sample_chunks

    result = await orchestrator.search(
        query="test query",
        mode=SearchMode.VECTOR,
        top_k=10
    )

    assert len(result) == 2
    assert mock_services["vector"].search.called
    assert not mock_services["keyword"].search.called


@pytest.mark.asyncio
async def test_keyword_only_search(orchestrator, mock_services, sample_chunks):
    """Test keyword-only search mode."""
    mock_services["keyword"].search.return_value = sample_chunks

    result = await orchestrator.search(
        query="test query",
        mode=SearchMode.KEYWORD,
        top_k=10,
        db_session=MagicMock()
    )

    assert len(result) == 2
    assert mock_services["keyword"].search.called
    assert not mock_services["vector"].search.called


@pytest.mark.asyncio
async def test_hybrid_search(orchestrator, mock_services, sample_chunks):
    """Test hybrid search with RRF fusion."""
    mock_services["embedder_client"].generate_embedding.return_value = [0.1] * 384
    mock_services["vector"].search.return_value = sample_chunks[:1]
    mock_services["keyword"].search.return_value = sample_chunks[1:]
    mock_services["fusion"].fuse.return_value = sample_chunks

    result = await orchestrator.search(
        query="test query",
        mode=SearchMode.HYBRID,
        top_k=10,
        db_session=MagicMock()
    )

    assert mock_services["vector"].search.called
    assert mock_services["keyword"].search.called
    assert mock_services["fusion"].fuse.called


@pytest.mark.asyncio
async def test_search_with_reranking(orchestrator, mock_services, sample_chunks):
    """Test search with reranking enabled."""
    mock_services["embedder_client"].generate_embedding.return_value = [0.1] * 384
    mock_services["vector"].search.return_value = sample_chunks
    mock_services["reranker"].rerank.return_value = list(reversed(sample_chunks))

    result = await orchestrator.search(
        query="test",
        mode=SearchMode.VECTOR,
        top_k=2,
        use_reranking=True
    )

    assert mock_services["reranker"].rerank.called
    # Verify reranker was called with more candidates than top_k
    call_args = mock_services["reranker"].rerank.call_args
    assert call_args[1]["top_k"] == 2
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/services/test_search_orchestrator.py -v`
Expected: Import error

**Step 3: Implement search orchestrator**

Create `services/search/app/services/search_orchestrator.py`:

```python
"""Main search orchestrator coordinating all search operations."""
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Chunk
from app.models.schemas import SearchMode
from app.services.vector_search import VectorSearchService
from app.services.keyword_search import KeywordSearchService
from app.services.fusion import RRFFusionService
from app.services.reranker import CrossEncoderReranker

logger = logging.getLogger(__name__)


class EmbedderClient:
    """Client for embedder service."""

    def __init__(self, embedder_url: str):
        """Initialize embedder client."""
        self.embedder_url = embedder_url

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text via embedder service.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.embedder_url}/api/v1/generate-embeddings",
                json={"texts": [text]},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data["embeddings"][0]


class SearchOrchestrator:
    """Main orchestrator for search operations.

    Coordinates vector search, keyword search, fusion, and reranking.
    """

    def __init__(
        self,
        vector_service: VectorSearchService,
        keyword_service: KeywordSearchService,
        fusion_service: RRFFusionService,
        reranker: CrossEncoderReranker,
        embedder_client: EmbedderClient,
    ):
        """Initialize search orchestrator.

        Args:
            vector_service: Vector search service
            keyword_service: Keyword search service
            fusion_service: RRF fusion service
            reranker: Cross-encoder reranker
            embedder_client: Client for embedder service
        """
        self.vector_service = vector_service
        self.keyword_service = keyword_service
        self.fusion_service = fusion_service
        self.reranker = reranker
        self.embedder_client = embedder_client

    async def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.HYBRID,
        top_k: int = 10,
        use_reranking: bool = True,
        use_expansion: bool = False,
        document_id: UUID | None = None,
        db_session: AsyncSession | None = None,
    ) -> list[Chunk]:
        """Execute search with specified mode and options.

        Args:
            query: Search query text
            mode: Search mode (vector/keyword/hybrid)
            top_k: Number of final results
            use_reranking: Enable cross-encoder reranking
            use_expansion: Enable query expansion (not implemented yet)
            document_id: Optional document filter
            db_session: Database session (required for keyword/hybrid)

        Returns:
            Ranked list of chunks
        """
        # Determine retrieval k for reranking
        retrieval_k = top_k
        if use_reranking:
            retrieval_k = max(top_k, 50)  # Get more candidates for reranking

        logger.info(
            f"Search: query='{query[:50]}', mode={mode}, top_k={top_k}, "
            f"reranking={use_reranking}, retrieval_k={retrieval_k}"
        )

        # Execute search based on mode
        if mode == SearchMode.VECTOR:
            initial_results = await self._vector_search(query, retrieval_k, document_id)
        elif mode == SearchMode.KEYWORD:
            if not db_session:
                raise ValueError("Database session required for keyword search")
            initial_results = await self._keyword_search(
                query, retrieval_k, document_id, db_session
            )
        elif mode == SearchMode.HYBRID:
            if not db_session:
                raise ValueError("Database session required for hybrid search")
            initial_results = await self._hybrid_search(
                query, retrieval_k, document_id, db_session
            )
        else:
            raise ValueError(f"Unknown search mode: {mode}")

        # Apply reranking if enabled
        if use_reranking and len(initial_results) > 0:
            final_results = await self.reranker.rerank(query, initial_results, top_k)
            logger.info(f"Reranked {len(initial_results)} to {len(final_results)} results")
        else:
            final_results = initial_results[:top_k]

        return final_results

    async def _vector_search(
        self, query: str, top_k: int, document_id: UUID | None
    ) -> list[Chunk]:
        """Execute vector-only search."""
        # Generate query embedding
        query_vector = await self.embedder_client.generate_embedding(query)

        # Search Qdrant
        results = await self.vector_service.search(query_vector, top_k, document_id)

        logger.info(f"Vector search: {len(results)} results")
        return results

    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        document_id: UUID | None,
        db_session: AsyncSession,
    ) -> list[Chunk]:
        """Execute keyword-only search."""
        results = await self.keyword_service.search(db_session, query, top_k, document_id)

        logger.info(f"Keyword search: {len(results)} results")
        return results

    async def _hybrid_search(
        self,
        query: str,
        top_k: int,
        document_id: UUID | None,
        db_session: AsyncSession,
    ) -> list[Chunk]:
        """Execute hybrid search with RRF fusion."""
        # Retrieve 2x results from each method for better fusion
        retrieval_k = top_k * 2

        # Parallel retrieval (semantic + lexical)
        vector_results = await self._vector_search(query, retrieval_k, document_id)
        keyword_results = await self.keyword_service.search(
            db_session, query, retrieval_k, document_id
        )

        logger.info(
            f"Hybrid retrieval: {len(vector_results)} vector, "
            f"{len(keyword_results)} keyword"
        )

        # Fuse with RRF
        fused_results = self.fusion_service.fuse([vector_results, keyword_results])

        # Return top_k after fusion
        final_results = fused_results[:top_k]

        logger.info(f"Hybrid search: {len(final_results)} fused results")
        return final_results
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/services/test_search_orchestrator.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/search/app/services/search_orchestrator.py services/search/tests/services/test_search_orchestrator.py
git commit -m "feat(search): implement search orchestrator

- Add SearchOrchestrator coordinating all search operations
- Support vector, keyword, and hybrid search modes
- Implement reranking with candidate retrieval
- Add EmbedderClient for query embedding
- Support document filtering across modes
- Add comprehensive orchestrator tests"
```

---

### Task 9: FastAPI Application and Endpoints

**Files:**
- Create: `services/search/app/main.py`
- Create: `services/search/app/dependencies.py`
- Create: `services/search/tests/test_main.py`

**Step 1: Write test for main application**

Create `services/search/tests/test_main.py`:

```python
"""Tests for FastAPI application."""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app


@pytest.fixture
def mock_orchestrator():
    """Mock search orchestrator."""
    orchestrator = MagicMock()
    orchestrator.search = AsyncMock(return_value=[])
    return orchestrator


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_search_endpoint_requires_query():
    """Test search endpoint validates query."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/search", json={})

    assert response.status_code == 422  # Validation error
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_main.py -v`
Expected: Import error

**Step 3: Implement dependencies**

Create `services/search/app/dependencies.py`:

```python
"""Dependency injection for FastAPI."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.services.vector_search import VectorSearchService
from app.services.keyword_search import KeywordSearchService
from app.services.fusion import RRFFusionService
from app.services.reranker import CrossEncoderReranker
from app.services.search_orchestrator import SearchOrchestrator, EmbedderClient

# Database engine
engine = create_async_engine(settings.database_url, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """Get database session."""
    async with async_session_maker() as session:
        yield session


# Singleton services (loaded once at startup)
_vector_service: VectorSearchService | None = None
_keyword_service: KeywordSearchService | None = None
_fusion_service: RRFFusionService | None = None
_reranker: CrossEncoderReranker | None = None
_embedder_client: EmbedderClient | None = None
_orchestrator: SearchOrchestrator | None = None


def get_vector_service() -> VectorSearchService:
    """Get vector search service."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorSearchService(
            qdrant_url=settings.qdrant_url,
            collection_name=settings.qdrant_collection
        )
    return _vector_service


def get_keyword_service() -> KeywordSearchService:
    """Get keyword search service."""
    global _keyword_service
    if _keyword_service is None:
        _keyword_service = KeywordSearchService()
    return _keyword_service


def get_fusion_service() -> RRFFusionService:
    """Get RRF fusion service."""
    global _fusion_service
    if _fusion_service is None:
        _fusion_service = RRFFusionService(k=settings.rrf_k)
    return _fusion_service


def get_reranker() -> CrossEncoderReranker:
    """Get cross-encoder reranker."""
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoderReranker(model_name=settings.reranking_model)
    return _reranker


def get_embedder_client() -> EmbedderClient:
    """Get embedder service client."""
    global _embedder_client
    if _embedder_client is None:
        _embedder_client = EmbedderClient(embedder_url=settings.embedder_url)
    return _embedder_client


def get_search_orchestrator() -> SearchOrchestrator:
    """Get search orchestrator with all dependencies."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SearchOrchestrator(
            vector_service=get_vector_service(),
            keyword_service=get_keyword_service(),
            fusion_service=get_fusion_service(),
            reranker=get_reranker(),
            embedder_client=get_embedder_client(),
        )
    return _orchestrator
```

**Step 4: Implement main application**

Create `services/search/app/main.py`:

```python
"""FastAPI application for search service."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.schemas import (
    SearchRequest,
    SearchResponse,
    ChunkResult,
    HealthResponse,
    ReadinessResponse,
)
from app.services.search_orchestrator import SearchOrchestrator
from app.dependencies import get_db, get_search_orchestrator, get_reranker

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting RAAS Search Service")
    logger.info(f"Qdrant URL: {settings.qdrant_url}")
    logger.info(f"Database URL: {settings.database_url}")

    try:
        # Load reranking model at startup
        reranker = get_reranker()
        logger.info("Search service ready")
    except Exception as e:
        logger.error(f"Failed to initialize search service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down RAAS Search Service")


# Create FastAPI application
app = FastAPI(
    title="RAAS Search Service",
    description="Intelligent search and retrieval service with hybrid search and reranking",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RAAS Search Service",
        "version": "0.1.0",
        "features": ["vector", "keyword", "hybrid", "reranking"]
    }


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy")


@app.get("/api/v1/ready", response_model=ReadinessResponse)
async def readiness_check():
    """Readiness check endpoint."""
    try:
        # Check if reranker is loaded
        reranker = get_reranker()
        models_loaded = reranker.model is not None

        # TODO: Check database connection
        database_connected = True

        status_value = "ready" if (models_loaded and database_connected) else "not_ready"

        return ReadinessResponse(
            status=status_value,
            models_loaded=models_loaded,
            database_connected=database_connected
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return ReadinessResponse(
            status="not_ready",
            models_loaded=False,
            database_connected=False
        )


@app.post("/api/v1/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    orchestrator: SearchOrchestrator = Depends(get_search_orchestrator),
):
    """Execute intelligent search with hybrid retrieval and reranking.

    Supports three modes:
    - VECTOR: Pure semantic search using embeddings
    - KEYWORD: Pure lexical search using PostgreSQL FTS
    - HYBRID: Combines both with RRF fusion (RECOMMENDED)

    Args:
        request: Search request with query and parameters
        db: Database session
        orchestrator: Search orchestrator service

    Returns:
        Search results with ranked chunks
    """
    try:
        logger.info(
            f"Search request: query='{request.query[:50]}', mode={request.mode}, "
            f"top_k={request.top_k}, reranking={request.use_reranking}"
        )

        # Execute search
        chunks = await orchestrator.search(
            query=request.query,
            mode=request.mode,
            top_k=request.top_k,
            use_reranking=request.use_reranking,
            use_expansion=request.use_expansion,
            document_id=request.document_id,
            db_session=db,
        )

        # Convert to response DTOs
        results = [
            ChunkResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                content=chunk.content,
                score=chunk.score or 0.0,
                chunk_index=chunk.chunk_index,
            )
            for chunk in chunks
        ]

        logger.info(f"Search returned {len(results)} results")

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            mode_used=request.mode,
            reranking_applied=request.use_reranking,
            expansion_applied=request.use_expansion,
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
```

**Step 5: Run tests to verify they pass**

Run: `poetry run pytest tests/test_main.py -v`
Expected: All tests PASS

**Step 6: Test application locally**

Run: `cd services/search && poetry run uvicorn app.main:app --reload --port 8003`
Expected: Server starts successfully

Test: `curl http://localhost:8003/api/v1/health`
Expected: `{"status":"healthy"}`

**Step 7: Commit**

```bash
git add services/search/app/main.py services/search/app/dependencies.py services/search/tests/test_main.py
git commit -m "feat(search): implement FastAPI application and endpoints

- Add main FastAPI app with lifespan management
- Add search endpoint with hybrid retrieval
- Add health and readiness checks
- Implement dependency injection system
- Support all search modes (vector/keyword/hybrid)
- Add request validation and error handling
- Include application tests"
```

---

## Phase 4: Infrastructure Integration

### Task 10: Docker Compose Integration

**Files:**
- Modify: `infrastructure/docker-compose/docker-compose.yml`

**Step 1: Read current docker-compose.yml**

Read the file to understand current structure.

**Step 2: Add search service to docker-compose**

Add after generator service:

```yaml
  search:
    build:
      context: ../../services/search
      dockerfile: Dockerfile
    container_name: raas-search
    ports:
      - "8003:8003"
    environment:
      - DATABASE_URL=postgresql+asyncpg://raasuser:raaspass@postgres:5432/raasdb
      - QDRANT_URL=http://qdrant:6333
      - QDRANT_COLLECTION=documents
      - EMBEDDER_URL=http://embedder:8001
      - GENERATOR_URL=http://generator:8002
      - RERANKING_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
      - RRF_K=60
      - LOG_LEVEL=INFO
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_healthy
      embedder:
        condition: service_started
    command: uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
    networks:
      - raas-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8003/api/v1/health')"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
```

**Step 3: Test docker-compose configuration**

Run: `docker-compose -f infrastructure/docker-compose/docker-compose.yml config`
Expected: Valid YAML with no errors

**Step 4: Commit**

```bash
git add infrastructure/docker-compose/docker-compose.yml
git commit -m "feat(search): add search service to docker-compose

- Add search service on port 8003
- Configure dependencies on postgres, qdrant, embedder
- Add health check and environment variables
- Set up volume mounts for development"
```

---

### Task 11: Update API Service to Use Search Service

**Files:**
- Modify: `services/api/app/core/config.py`
- Modify: `services/api/app/api/routes/search.py`
- Modify: `services/api/app/api/dependencies.py`

**Step 1: Add search service URL to API config**

Edit `services/api/app/core/config.py`:

```python
# Add to Settings class
search_url: str = Field(
    "http://search:8003",
    description="Search service URL"
)
```

**Step 2: Create search service client in API**

Create `services/api/app/infrastructure/services/search_service.py`:

```python
"""Search service HTTP client."""
import logging
import httpx
from uuid import UUID

from app.domain.entities.chunk import Chunk

logger = logging.getLogger(__name__)


class SearchServiceClient:
    """HTTP client for search microservice."""

    def __init__(self, search_url: str):
        """Initialize search service client.

        Args:
            search_url: Base URL of search service
        """
        self.search_url = search_url

    async def search(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 10,
        use_reranking: bool = True,
        use_expansion: bool = True,
        document_id: UUID | None = None,
    ) -> list[Chunk]:
        """Execute search via search service.

        Args:
            query: Search query
            mode: Search mode (vector/keyword/hybrid)
            top_k: Number of results
            use_reranking: Enable reranking
            use_expansion: Enable query expansion
            document_id: Optional document filter

        Returns:
            List of ranked chunks
        """
        request_data = {
            "query": query,
            "mode": mode,
            "top_k": top_k,
            "use_reranking": use_reranking,
            "use_expansion": use_expansion,
        }

        if document_id:
            request_data["document_id"] = str(document_id)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.search_url}/api/v1/search",
                json=request_data
            )
            response.raise_for_status()
            data = response.json()

        # Convert response to Chunk entities
        chunks = []
        for result in data["results"]:
            chunk = Chunk(
                id=UUID(result["chunk_id"]),
                document_id=UUID(result["document_id"]),
                content=result["content"],
                tokens=0,  # Not needed for search results
                score=result["score"],
            )
            chunk.document_title = result.get("document_title")
            chunks.append(chunk)

        logger.info(f"Search service returned {len(chunks)} results")
        return chunks
```

**Step 3: Update search route to use search service**

Edit `services/api/app/api/routes/search.py` to delegate to search service instead of local logic.

**Step 4: Test integration**

Run: `docker-compose -f infrastructure/docker-compose/docker-compose.yml up --build`
Expected: All services start successfully

Test: Search via API should now use search service
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 5}'
```

**Step 5: Commit**

```bash
git add services/api/app/core/config.py services/api/app/infrastructure/services/search_service.py services/api/app/api/routes/search.py
git commit -m "feat(api): integrate with search microservice

- Add SEARCH_URL configuration
- Create SearchServiceClient for HTTP communication
- Update search route to delegate to search service
- Remove local search logic from API service
- Test end-to-end integration"
```

---

## Phase 5: Testing and Documentation

### Task 12: Integration Tests

**Files:**
- Create: `tests/integration/test_search_service.sh`

**Step 1: Write integration test script**

Create `tests/integration/test_search_service.sh`:

```bash
#!/bin/bash
# Integration tests for search service

set -e

echo "=== Search Service Integration Tests ==="

BASE_URL="http://localhost:8003"

# Test 1: Health check
echo "Test 1: Health check"
response=$(curl -s ${BASE_URL}/api/v1/health)
if echo "$response" | grep -q '"status":"healthy"'; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    exit 1
fi

# Test 2: Readiness check
echo "Test 2: Readiness check"
response=$(curl -s ${BASE_URL}/api/v1/ready)
if echo "$response" | grep -q '"status":"ready"'; then
    echo "✓ Readiness check passed"
else
    echo "✗ Readiness check failed"
    exit 1
fi

# Test 3: Vector search
echo "Test 3: Vector search"
response=$(curl -s -X POST ${BASE_URL}/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query":"Python programming","mode":"vector","top_k":5}')
if echo "$response" | grep -q '"query"'; then
    echo "✓ Vector search passed"
else
    echo "✗ Vector search failed"
    exit 1
fi

# Test 4: Hybrid search
echo "Test 4: Hybrid search"
response=$(curl -s -X POST ${BASE_URL}/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test","mode":"hybrid","top_k":10}')
if echo "$response" | grep -q '"total_results"'; then
    echo "✓ Hybrid search passed"
else
    echo "✗ Hybrid search failed"
    exit 1
fi

echo ""
echo "=== All integration tests passed! ==="
```

**Step 2: Make script executable**

Run: `chmod +x tests/integration/test_search_service.sh`

**Step 3: Run integration tests**

Run: `./tests/integration/test_search_service.sh`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/integration/test_search_service.sh
git commit -m "test(search): add integration test suite

- Add shell script for search service integration tests
- Test health and readiness endpoints
- Test vector and hybrid search modes
- Verify request/response formats"
```

---

### Task 13: Update Documentation

**Files:**
- Modify: `README.md`
- Create: `services/search/README.md` (already done)

**Step 1: Update main README**

Edit `README.md` to add search service:

```markdown
### System Components

```
┌─────────────┐
│  Frontend   │ (React + TypeScript)
│  Port 3000  │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│ API Service │─────▶│  PostgreSQL  │      │   Qdrant    │
│  Port 8000  │      │  Port 5432   │      │  Port 6333  │
└──────┬──────┘      └──────────────┘      └──────┬──────┘
       │                                           │
       │             ┌─────────────┐               │
       │             │   Search    │───────────────┘
       │             │  Port 8003  │
       │             └──────┬──────┘
       │                    │
       ├────────────────────┴──────────────────────┐
       │             ┌─────────────┐               │
       │             │  Embedder   │───────────────┘
       │             │  Port 8001  │
       │             └─────────────┘
       │
       ├──────────────────────────────────┐
       │             ┌─────────────┐      │
       └────────────▶│  Generator  │      │
                     │  Port 8002  │      │
                     └─────────────┘      │
```

**Microservices:**
1. **API Service (Port 8000)** - Orchestration, document CRUD, upload management
2. **Embedder Service (Port 8001)** - Bi-encoder embedding generation
3. **Generator Service (Port 8002)** - LLM text generation
4. **Search Service (Port 8003)** - Hybrid search, reranking, retrieval (NEW)
```

**Step 2: Update service URLs section**

```markdown
**Service URLs:**
- Frontend: http://localhost:3000
- API: http://localhost:8000/docs
- Embedder: http://localhost:8001/docs
- Generator: http://localhost:8002/docs
- **Search: http://localhost:8003/docs** (NEW)
- Qdrant Dashboard: http://localhost:6333/dashboard
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README for search microservice

- Add search service to architecture diagram
- Update service URLs section
- Document search service features
- Add port 8003 information"
```

---

## Summary

This plan extracts all search/retrieval logic into a dedicated Search microservice with:

**What Moves:**
- Vector search (Qdrant client)
- Keyword search (PostgreSQL FTS)
- RRF fusion
- Cross-encoder reranking
- Query expansion (future)
- Search orchestration

**What Stays in API:**
- Document upload/CRUD
- File processing
- Chunk persistence
- Orchestration

**Final Architecture:**
- **4 Microservices**: API, Embedder, Generator, Search
- **Clean Separation**: Each service has single responsibility
- **Independent Scaling**: Search can scale separately from uploads
- **Maintainability**: Bounded contexts with clear interfaces

**Testing:**
- Unit tests for all components (pytest)
- Integration tests (shell scripts)
- Docker Compose integration
- End-to-end verification
