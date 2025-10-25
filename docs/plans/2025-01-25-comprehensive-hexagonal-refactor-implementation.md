# Comprehensive Hexagonal Architecture Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor RAAS to hexagonal architecture within each microservice, achieving full SOLID compliance, Python 3.13 compatibility, and 60-80% test coverage.

**Architecture:** Implement Ports & Adapters pattern with domain entities, application use cases, infrastructure adapters, and dependency injection. Maintain existing functionality while dramatically improving code quality and maintainability.

**Tech Stack:** Python 3.13, FastAPI 0.115+, Pydantic 2.8+, SQLAlchemy 2.0.36+, Poetry, pytest, mypy, ruff

---

## Phase 1: Foundation & Package Updates

### Task 1: Update Python Dependencies for 3.13 Compatibility

**Files:**
- Modify: `services/api/pyproject.toml`
- Modify: `services/embedder/pyproject.toml`
- Modify: `services/generator/pyproject.toml`

**Step 1: Update API service dependencies**

Edit `services/api/pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.13"

# Core framework (Python 3.13 compatible)
fastapi = "^0.115.0"
uvicorn = {extras = ["standard"], version = "^0.32.0"}
pydantic = "^2.8.0"            # CRITICAL: >=2.8.0 for Python 3.13
pydantic-settings = "^2.6.0"

# Database
sqlalchemy = "^2.0.36"
asyncpg = "^0.30.0"
alembic = "^1.14.0"

# HTTP
httpx = "^0.27.0"

# Vector DB
qdrant-client = "^1.12.0"

# File processing (updated versions)
pypdf = "^5.1.0"               # Updated from 3.x
python-docx = "^1.1.2"
openpyxl = "^3.1.5"
python-pptx = "^1.0.2"
aiofiles = "^24.1.0"
python-magic = "^0.4.27"

# NLP/ML
sentence-transformers = "^3.3.0"  # Updated from 2.x
tiktoken = "^0.8.0"
langchain-text-splitters = "^0.3.0"
langchain-core = "^0.3.0"
beautifulsoup4 = "^4.12.3"
lxml = "^5.3.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.0"
pytest-asyncio = "^0.24.0"
pytest-cov = "^6.0.0"
pytest-mock = "^3.14.0"
mypy = "^1.13.0"
ruff = "^0.8.0"
```

**Step 2: Update embedder service dependencies**

Edit `services/embedder/pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.13"
fastapi = "^0.115.0"
uvicorn = {extras = ["standard"], version = "^0.32.0"}
pydantic = "^2.8.0"
pydantic-settings = "^2.6.0"
sentence-transformers = "^3.3.0"
qdrant-client = "^1.12.0"
torch = "^2.7.0"
numpy = "^2.3.0"
tiktoken = "^0.8.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.0"
pytest-asyncio = "^0.24.0"
pytest-cov = "^6.0.0"
httpx = "^0.27.0"
mypy = "^1.13.0"
ruff = "^0.8.0"
```

**Step 3: Update generator service dependencies**

Edit `services/generator/pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.13"
fastapi = "^0.115.0"
uvicorn = {extras = ["standard"], version = "^0.32.0"}
pydantic = "^2.8.0"
pydantic-settings = "^2.6.0"
ollama = "^0.6.0"
httpx = "^0.27.0"
openai = "^1.59.0"
anthropic = "^0.42.0"
google-generativeai = "^0.8.5"

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.0"
pytest-asyncio = "^0.24.0"
pytest-cov = "^6.0.0"
httpx = "^0.27.0"
mypy = "^1.13.0"
ruff = "^0.8.0"
```

**Step 4: Update lock files**

Run:
```bash
cd services/api && poetry lock --no-update
cd ../embedder && poetry lock --no-update
cd ../generator && poetry lock --no-update
```

Expected: Lock files regenerated with Python 3.13 compatible versions

**Step 5: Install updated dependencies**

Run:
```bash
cd services/api && poetry install
cd ../embedder && poetry install
cd ../generator && poetry install
```

Expected: All packages install successfully

**Step 6: Commit dependency updates**

```bash
git add services/*/pyproject.toml services/*/poetry.lock
git commit -m "build: update dependencies for Python 3.13 compatibility

- Pydantic >=2.8.0 (required for Python 3.13)
- FastAPI >=0.115.0
- SQLAlchemy 2.0.36+
- sentence-transformers 3.3.0
- pypdf 5.1.0
- Updated all dev dependencies"
```

---

### Task 2: Add Linting and Type Checking Configuration

**Files:**
- Create: `services/api/pyproject.toml` (add sections)
- Create: `services/embedder/pyproject.toml` (add sections)
- Create: `services/generator/pyproject.toml` (add sections)

**Step 1: Add ruff configuration to API service**

Add to `services/api/pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]

ignore = [
    "E501",  # Line too long (handled by formatter)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = false  # Too strict for now
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true

[[tool.mypy.overrides]]
module = [
    "qdrant_client.*",
    "sentence_transformers.*",
    "langchain.*",
    "unstructured.*"
]
ignore_missing_imports = true
```

**Step 2: Copy configuration to other services**

Copy the same ruff and mypy configuration to:
- `services/embedder/pyproject.toml`
- `services/generator/pyproject.toml`

**Step 3: Run initial lint check**

Run:
```bash
cd services/api && poetry run ruff check app/
```

Expected: Linting errors shown (we'll fix incrementally)

**Step 4: Commit linting configuration**

```bash
git add services/*/pyproject.toml
git commit -m "build: add ruff and mypy configuration

- Line length 100
- Python 3.13 target
- Enable key linting rules
- Configure mypy for gradual typing"
```

---

## Phase 2: Domain Layer - API Service

### Task 3: Create Domain Entities

**Files:**
- Create: `services/api/app/domain/__init__.py`
- Create: `services/api/app/domain/entities/__init__.py`
- Create: `services/api/app/domain/entities/document.py`
- Create: `services/api/app/domain/entities/chunk.py`

**Step 1: Write test for Document entity**

Create `services/api/tests/domain/__init__.py` (empty file)

Create `services/api/tests/domain/test_document.py`:

```python
"""Tests for Document domain entity."""
import pytest
from datetime import datetime
from uuid import uuid4

from app.domain.entities.document import Document
from app.core.enums import UploadStatus


def test_document_creation():
    """Test creating a document entity."""
    doc_id = uuid4()
    now = datetime.utcnow()

    document = Document(
        id=doc_id,
        title="Test Document",
        file_name="test.pdf",
        file_type="pdf",
        created_at=now,
        upload_status=UploadStatus.PROCESSING
    )

    assert document.id == doc_id
    assert document.title == "Test Document"
    assert document.upload_status == UploadStatus.PROCESSING


def test_document_mark_completed():
    """Test marking document as completed."""
    document = Document(
        id=uuid4(),
        title="Test",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.utcnow(),
        upload_status=UploadStatus.PROCESSING
    )

    document.mark_completed()

    assert document.upload_status == UploadStatus.COMPLETED


def test_document_mark_failed():
    """Test marking document as failed."""
    document = Document(
        id=uuid4(),
        title="Test",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.utcnow(),
        upload_status=UploadStatus.PROCESSING
    )

    document.mark_failed()

    assert document.upload_status == UploadStatus.FAILED
```

**Step 2: Run tests to verify failure**

Run:
```bash
cd services/api && poetry run pytest tests/domain/test_document.py -v
```

Expected: FAIL with "No module named 'app.domain'"

**Step 3: Implement Document entity**

Create `services/api/app/domain/__init__.py`:

```python
"""Domain layer - pure business logic."""
```

Create `services/api/app/domain/entities/__init__.py`:

```python
"""Domain entities."""
from app.domain.entities.document import Document
from app.domain.entities.chunk import Chunk

__all__ = ["Document", "Chunk"]
```

Create `services/api/app/domain/entities/document.py`:

```python
"""Document domain entity."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Optional

from app.core.enums import UploadStatus


@dataclass
class Document:
    """Core document entity representing an uploaded document.

    Enforces business rules around document lifecycle transitions.
    Domain entity has no infrastructure dependencies.
    """

    id: UUID
    title: str
    file_name: str
    file_type: str
    created_at: datetime
    upload_status: UploadStatus
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None

    def mark_completed(self) -> None:
        """Transition document to completed state.

        Should be called after successful processing, chunking, and embedding.
        """
        self.upload_status = UploadStatus.COMPLETED

    def mark_failed(self) -> None:
        """Transition document to failed state.

        Called when processing, chunking, or embedding fails.
        """
        self.upload_status = UploadStatus.FAILED

    def is_processing(self) -> bool:
        """Check if document is currently being processed."""
        return self.upload_status == UploadStatus.PROCESSING

    def is_completed(self) -> bool:
        """Check if document processing is complete."""
        return self.upload_status == UploadStatus.COMPLETED
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd services/api && poetry run pytest tests/domain/test_document.py -v
```

Expected: PASS (3 tests)

**Step 5: Commit document entity**

```bash
git add services/api/app/domain/ services/api/tests/domain/
git commit -m "feat(api): add Document domain entity

- Pure business logic, no infrastructure dependencies
- Lifecycle state transitions (mark_completed, mark_failed)
- 100% test coverage for domain logic"
```

---

### Task 4: Create Chunk Entity and Value Objects

**Files:**
- Create: `services/api/app/domain/entities/chunk.py`
- Create: `services/api/app/domain/value_objects/__init__.py`
- Create: `services/api/app/domain/value_objects/search_query.py`
- Create: `services/api/tests/domain/test_chunk.py`
- Create: `services/api/tests/domain/test_search_query.py`

**Step 1: Write tests for Chunk entity**

Create `services/api/tests/domain/test_chunk.py`:

```python
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
```

**Step 2: Write tests for SearchQuery value object**

Create `services/api/tests/domain/test_search_query.py`:

```python
"""Tests for SearchQuery value object."""
import pytest

from app.domain.value_objects.search_query import SearchQuery


def test_search_query_creation():
    """Test creating a search query."""
    query = SearchQuery(text="test query", top_k=10)

    assert query.text == "test query"
    assert query.top_k == 10


def test_search_query_default_top_k():
    """Test default top_k value."""
    query = SearchQuery(text="test")

    assert query.top_k == 5


def test_search_query_immutable():
    """Test that SearchQuery is immutable."""
    query = SearchQuery(text="test", top_k=5)

    with pytest.raises(Exception):  # dataclass frozen raises on assignment
        query.text = "modified"


def test_search_query_validates_top_k_min():
    """Test top_k minimum validation."""
    with pytest.raises(ValueError, match="top_k must be between 1 and 100"):
        SearchQuery(text="test", top_k=0)


def test_search_query_validates_top_k_max():
    """Test top_k maximum validation."""
    with pytest.raises(ValueError, match="top_k must be between 1 and 100"):
        SearchQuery(text="test", top_k=101)
```

**Step 3: Run tests to verify failure**

Run:
```bash
cd services/api && poetry run pytest tests/domain/test_chunk.py tests/domain/test_search_query.py -v
```

Expected: FAIL with "No module named 'app.domain.entities.chunk'"

**Step 4: Implement Chunk entity**

Create `services/api/app/domain/entities/chunk.py`:

```python
"""Chunk domain entity."""
from dataclasses import dataclass, field
from uuid import UUID
from typing import Optional, List, Dict, Any


@dataclass
class Chunk:
    """Chunk entity representing a document fragment.

    Contains text content, token count, and optional embedding vector.
    Chunks are the fundamental unit for vector search and RAG.
    """

    id: UUID
    document_id: UUID
    content: str
    tokens: int
    embedding_vector: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    section_title: Optional[str] = None
    section_level: Optional[int] = None
    page_number: Optional[int] = None

    def has_embedding(self) -> bool:
        """Check if chunk has been embedded.

        Returns:
            True if embedding_vector is present, False otherwise
        """
        return self.embedding_vector is not None and len(self.embedding_vector) > 0
```

**Step 5: Implement SearchQuery value object**

Create `services/api/app/domain/value_objects/__init__.py`:

```python
"""Domain value objects."""
from app.domain.value_objects.search_query import SearchQuery

__all__ = ["SearchQuery"]
```

Create `services/api/app/domain/value_objects/search_query.py`:

```python
"""Search query value object."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchQuery:
    """Immutable search query value object.

    Validates search parameters on creation.
    Being frozen ensures immutability (value object principle).
    """

    text: str
    top_k: int = 5

    def __post_init__(self):
        """Validate search query parameters."""
        if self.top_k < 1 or self.top_k > 100:
            raise ValueError("top_k must be between 1 and 100")
```

**Step 6: Run tests to verify they pass**

Run:
```bash
cd services/api && poetry run pytest tests/domain/ -v
```

Expected: PASS (all domain tests)

**Step 7: Commit domain entities and value objects**

```bash
git add services/api/app/domain/ services/api/tests/domain/
git commit -m "feat(api): add Chunk entity and SearchQuery value object

- Chunk entity with embedding support
- SearchQuery immutable value object with validation
- 100% test coverage for all domain logic"
```

---

## Phase 3: Ports Layer - Interfaces

### Task 5: Define Repository Ports

**Files:**
- Create: `services/api/app/ports/__init__.py`
- Create: `services/api/app/ports/repositories.py`

**Step 1: Create repository port interfaces**

Create `services/api/app/ports/__init__.py`:

```python
"""Ports - interface definitions for dependency inversion."""
```

Create `services/api/app/ports/repositories.py`:

```python
"""Repository port definitions.

Repositories abstract data persistence, following the Repository pattern.
These are interfaces - infrastructure layer provides implementations.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from app.domain.entities.document import Document
from app.domain.entities.chunk import Chunk


class DocumentRepository(ABC):
    """Port for document persistence operations."""

    @abstractmethod
    async def save(self, document: Document) -> Document:
        """Persist document to storage.

        Args:
            document: Document entity to persist

        Returns:
            Persisted document (may have generated fields)
        """
        pass

    @abstractmethod
    async def find_by_id(self, document_id: UUID) -> Optional[Document]:
        """Retrieve document by ID.

        Args:
            document_id: Document UUID

        Returns:
            Document if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_all(self, page: int, limit: int) -> Tuple[List[Document], int]:
        """Retrieve paginated documents.

        Args:
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (documents list, total count)
        """
        pass

    @abstractmethod
    async def delete(self, document_id: UUID) -> None:
        """Delete document from storage.

        Args:
            document_id: Document UUID to delete
        """
        pass


class ChunkRepository(ABC):
    """Port for chunk persistence operations."""

    @abstractmethod
    async def save_batch(self, chunks: List[Chunk]) -> List[Chunk]:
        """Persist multiple chunks atomically.

        Args:
            chunks: List of chunk entities

        Returns:
            Persisted chunks
        """
        pass

    @abstractmethod
    async def find_by_document_id(self, document_id: UUID) -> List[Chunk]:
        """Retrieve all chunks for a document.

        Args:
            document_id: Document UUID

        Returns:
            List of chunks (may be empty)
        """
        pass

    @abstractmethod
    async def delete_by_document_id(self, document_id: UUID) -> None:
        """Delete all chunks for a document.

        Args:
            document_id: Document UUID
        """
        pass
```

**Step 2: Commit repository ports**

```bash
git add services/api/app/ports/
git commit -m "feat(api): add repository port interfaces

- DocumentRepository port for document persistence
- ChunkRepository port for chunk persistence
- Abstractions enable dependency inversion principle"
```

---

### Task 6: Define Service Ports

**Files:**
- Create: `services/api/app/ports/services.py`

**Step 1: Create service port interfaces**

Create `services/api/app/ports/services.py`:

```python
"""Service port definitions for external dependencies.

These ports abstract external services (embedding, generation, vector store),
allowing implementations to be swapped without changing business logic.
"""
from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.domain.entities.chunk import Chunk


class EmbeddingService(ABC):
    """Port for embedding generation service."""

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (one per input text)

        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        pass


class VectorStore(ABC):
    """Port for vector database operations."""

    @abstractmethod
    async def upsert(self, chunks: List[Chunk]) -> None:
        """Insert or update chunk vectors in vector database.

        Args:
            chunks: List of chunks with embedding_vector populated

        Raises:
            VectorStoreError: If upsert operation fails
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        top_k: int,
        document_id: Optional[UUID] = None
    ) -> List[Chunk]:
        """Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            document_id: Optional filter by document

        Returns:
            List of most similar chunks (ordered by similarity)
        """
        pass

    @abstractmethod
    async def delete_by_document(self, document_id: UUID) -> None:
        """Delete all vectors for a document.

        Args:
            document_id: Document UUID

        Raises:
            VectorStoreError: If deletion fails
        """
        pass


class GenerationService(ABC):
    """Port for LLM text generation service."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: List[str],
        model: Optional[str] = None
    ) -> str:
        """Generate text response using LLM.

        Args:
            prompt: User query/prompt
            context: Retrieved context chunks
            model: Optional model identifier

        Returns:
            Generated text response

        Raises:
            GenerationServiceError: If generation fails
        """
        pass


class FileProcessor(ABC):
    """Port for file processing operations."""

    @abstractmethod
    async def extract_text(self, file_content: bytes, file_type: str) -> str:
        """Extract text from file content.

        Args:
            file_content: Raw file bytes
            file_type: File type (pdf, docx, txt, etc.)

        Returns:
            Extracted text content

        Raises:
            FileProcessingError: If text extraction fails
        """
        pass


class TextChunker(ABC):
    """Port for text chunking operations."""

    @abstractmethod
    async def chunk(self, text: str) -> List[str]:
        """Chunk text into semantic segments.

        Args:
            text: Input text to chunk

        Returns:
            List of text chunks

        Raises:
            ChunkingError: If chunking fails
        """
        pass
```

**Step 2: Commit service ports**

```bash
git add services/api/app/ports/services.py
git commit -m "feat(api): add service port interfaces

- EmbeddingService port for vector generation
- VectorStore port for vector DB operations
- GenerationService port for LLM calls
- FileProcessor and TextChunker ports
- Complete dependency inversion for external services"
```

---

## Phase 4: Application Layer - Use Cases

### Task 7: Implement Upload Document Use Case

**Files:**
- Create: `services/api/app/application/__init__.py`
- Create: `services/api/app/application/use_cases/__init__.py`
- Create: `services/api/app/application/use_cases/upload_document.py`
- Create: `services/api/tests/application/__init__.py`
- Create: `services/api/tests/application/test_upload_document.py`

**Step 1: Write test for upload use case**

Create `services/api/tests/application/__init__.py` (empty)

Create `services/api/tests/application/test_upload_document.py`:

```python
"""Tests for UploadDocumentUseCase."""
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from datetime import datetime

from app.application.use_cases.upload_document import (
    UploadDocumentUseCase,
    UploadDocumentCommand
)
from app.domain.entities.document import Document
from app.domain.entities.chunk import Chunk
from app.core.enums import UploadStatus
from app.ports.repositories import DocumentRepository, ChunkRepository
from app.ports.services import EmbeddingService, VectorStore, FileProcessor, TextChunker


@pytest.mark.asyncio
async def test_upload_document_success():
    """Test successful document upload workflow."""
    # Arrange: Create mocks for all dependencies
    mock_doc_repo = Mock(spec=DocumentRepository)
    mock_chunk_repo = Mock(spec=ChunkRepository)
    mock_embedding_service = Mock(spec=EmbeddingService)
    mock_vector_store = Mock(spec=VectorStore)
    mock_file_processor = Mock(spec=FileProcessor)
    mock_chunker = Mock(spec=TextChunker)

    # Configure mock behavior
    mock_doc_repo.save = AsyncMock(side_effect=lambda doc: doc)
    mock_chunk_repo.save_batch = AsyncMock(side_effect=lambda chunks: chunks)
    mock_file_processor.extract_text = AsyncMock(return_value="Sample document text content")
    mock_chunker.chunk = AsyncMock(return_value=["chunk 1 content", "chunk 2 content"])
    mock_embedding_service.generate_embeddings = AsyncMock(
        return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    )
    mock_vector_store.upsert = AsyncMock()

    # Create use case with mocked dependencies
    use_case = UploadDocumentUseCase(
        document_repo=mock_doc_repo,
        chunk_repo=mock_chunk_repo,
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store,
        file_processor=mock_file_processor,
        chunker=mock_chunker
    )

    # Act: Execute use case
    command = UploadDocumentCommand(
        title="Test Document",
        file_name="test.pdf",
        file_content=b"PDF content bytes",
        description="Test description"
    )
    document, chunk_count = await use_case.execute(command)

    # Assert: Verify orchestration
    assert document.title == "Test Document"
    assert document.upload_status == UploadStatus.COMPLETED
    assert chunk_count == 2

    # Verify interactions
    assert mock_doc_repo.save.call_count == 2  # Initial + completion
    assert mock_chunk_repo.save_batch.call_count == 1
    assert mock_embedding_service.generate_embeddings.call_count == 1
    assert mock_vector_store.upsert.call_count == 1

    # Verify final save was with completed status
    final_save_call = mock_doc_repo.save.call_args_list[1]
    saved_doc = final_save_call[0][0]
    assert saved_doc.upload_status == UploadStatus.COMPLETED


@pytest.mark.asyncio
async def test_upload_document_failure_marks_failed():
    """Test that errors mark document as failed."""
    # Arrange
    mock_doc_repo = Mock(spec=DocumentRepository)
    mock_file_processor = Mock(spec=FileProcessor)

    mock_doc_repo.save = AsyncMock(side_effect=lambda doc: doc)
    mock_file_processor.extract_text = AsyncMock(side_effect=Exception("Processing failed"))

    use_case = UploadDocumentUseCase(
        document_repo=mock_doc_repo,
        chunk_repo=Mock(spec=ChunkRepository),
        embedding_service=Mock(spec=EmbeddingService),
        vector_store=Mock(spec=VectorStore),
        file_processor=mock_file_processor,
        chunker=Mock(spec=TextChunker)
    )

    # Act & Assert
    command = UploadDocumentCommand(
        title="Test",
        file_name="test.pdf",
        file_content=b"content"
    )

    with pytest.raises(Exception, match="Processing failed"):
        await use_case.execute(command)

    # Verify document was marked as failed
    assert mock_doc_repo.save.call_count == 2
    failed_call = mock_doc_repo.save.call_args_list[1]
    failed_doc = failed_call[0][0]
    assert failed_doc.upload_status == UploadStatus.FAILED
```

**Step 2: Run test to verify failure**

Run:
```bash
cd services/api && poetry run pytest tests/application/test_upload_document.py -v
```

Expected: FAIL with "No module named 'app.application'"

**Step 3: Implement UploadDocumentUseCase**

Create `services/api/app/application/__init__.py`:

```python
"""Application layer - use cases orchestrating business workflows."""
```

Create `services/api/app/application/use_cases/__init__.py`:

```python
"""Use cases - application services."""
```

Create `services/api/app/application/use_cases/upload_document.py`:

```python
"""Upload document use case."""
from dataclasses import dataclass
from typing import Tuple, Optional
from uuid import UUID, uuid4
from datetime import datetime
import logging

from app.domain.entities.document import Document
from app.domain.entities.chunk import Chunk
from app.core.enums import UploadStatus
from app.ports.repositories import DocumentRepository, ChunkRepository
from app.ports.services import (
    EmbeddingService,
    VectorStore,
    FileProcessor,
    TextChunker
)

logger = logging.getLogger(__name__)


@dataclass
class UploadDocumentCommand:
    """Input DTO for upload document use case."""

    title: str
    file_name: str
    file_content: bytes
    description: Optional[str] = None


class UploadDocumentUseCase:
    """Use case orchestrating document upload workflow.

    Coordinates file processing, chunking, embedding, and persistence.
    Follows single responsibility - orchestration only, no business logic.
    """

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        file_processor: FileProcessor,
        chunker: TextChunker
    ):
        """Initialize use case with injected dependencies (ports)."""
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.file_processor = file_processor
        self.chunker = chunker

    async def execute(self, command: UploadDocumentCommand) -> Tuple[Document, int]:
        """Execute document upload workflow.

        Args:
            command: Upload parameters

        Returns:
            Tuple of (created document, chunk count)

        Raises:
            Various exceptions from ports if operations fail
        """
        # 1. Create domain entity
        document = Document(
            id=uuid4(),
            title=command.title,
            file_name=command.file_name,
            file_type=self._detect_file_type(command.file_name),
            created_at=datetime.utcnow(),
            upload_status=UploadStatus.PROCESSING,
            description=command.description
        )

        # 2. Persist document (initial state)
        document = await self.document_repo.save(document)
        logger.info(f"Created document {document.id} in PROCESSING state")

        try:
            # 3. Extract text from file
            text = await self.file_processor.extract_text(
                command.file_content,
                document.file_type
            )
            logger.debug(f"Extracted {len(text)} characters from {document.file_name}")

            # 4. Chunk text
            chunk_texts = await self.chunker.chunk(text)
            logger.debug(f"Created {len(chunk_texts)} chunks")

            # 5. Create chunk entities
            chunks = [
                Chunk(
                    id=uuid4(),
                    document_id=document.id,
                    content=chunk_text,
                    tokens=self._count_tokens(chunk_text)
                )
                for chunk_text in chunk_texts
            ]

            # 6. Persist chunks
            chunks = await self.chunk_repo.save_batch(chunks)
            logger.debug(f"Persisted {len(chunks)} chunks to database")

            # 7. Generate embeddings
            embeddings = await self.embedding_service.generate_embeddings(
                [c.content for c in chunks]
            )
            logger.debug(f"Generated {len(embeddings)} embeddings")

            # 8. Update chunks with embeddings
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding_vector = embedding

            # 9. Store vectors in vector database
            await self.vector_store.upsert(chunks)
            logger.debug(f"Stored {len(chunks)} vectors in vector DB")

            # 10. Mark document as completed (domain logic)
            document.mark_completed()
            await self.document_repo.save(document)
            logger.info(f"Document {document.id} completed successfully")

            return document, len(chunks)

        except Exception as e:
            # Use domain logic for failure state
            logger.error(f"Document {document.id} processing failed: {e}")
            document.mark_failed()
            await self.document_repo.save(document)
            raise

    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from extension."""
        return filename.rsplit('.', 1)[-1].lower() if '.' in filename else "unknown"

    def _count_tokens(self, text: str) -> int:
        """Estimate token count (simple word-based approximation)."""
        return len(text.split())
```

**Step 4: Run tests to verify they pass**

Run:
```bash
cd services/api && poetry run pytest tests/application/test_upload_document.py -v
```

Expected: PASS (2 tests)

**Step 5: Commit upload use case**

```bash
git add services/api/app/application/ services/api/tests/application/
git commit -m "feat(api): add UploadDocument use case

- Orchestrates upload workflow: file -> chunks -> embeddings -> storage
- Uses domain entities for state transitions
- Depends only on ports (DIP)
- Full test coverage with mocked ports"
```

---

### Task 8: Implement Additional Use Cases

**Files:**
- Create: `services/api/app/application/use_cases/delete_document.py`
- Create: `services/api/app/application/use_cases/search_documents.py`
- Create: `services/api/app/application/use_cases/list_documents.py`
- Create: `services/api/tests/application/test_delete_document.py`
- Create: `services/api/tests/application/test_search_documents.py`

**Step 1: Implement DeleteDocument use case**

Create `services/api/app/application/use_cases/delete_document.py`:

```python
"""Delete document use case."""
from uuid import UUID
import logging

from app.ports.repositories import DocumentRepository, ChunkRepository
from app.ports.services import VectorStore
from app.core.exceptions import DocumentNotFoundError

logger = logging.getLogger(__name__)


class DeleteDocumentUseCase:
    """Use case for deleting documents and associated resources.

    Coordinates deletion across multiple storage layers.
    """

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        vector_store: VectorStore
    ):
        """Initialize with repository and vector store dependencies."""
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self.vector_store = vector_store

    async def execute(self, document_id: UUID) -> None:
        """Delete document and all associated data.

        Args:
            document_id: Document UUID to delete

        Raises:
            DocumentNotFoundError: If document doesn't exist
        """
        # 1. Verify document exists
        document = await self.document_repo.find_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(f"Document {document_id} not found")

        logger.info(f"Deleting document {document_id}")

        # 2. Delete from vector store
        await self.vector_store.delete_by_document(document_id)
        logger.debug(f"Deleted vectors for document {document_id}")

        # 3. Delete chunks (may cascade from document deletion, but explicit is safer)
        await self.chunk_repo.delete_by_document_id(document_id)
        logger.debug(f"Deleted chunks for document {document_id}")

        # 4. Delete document
        await self.document_repo.delete(document_id)
        logger.info(f"Successfully deleted document {document_id}")
```

**Step 2: Implement SearchDocuments use case**

Create `services/api/app/application/use_cases/search_documents.py`:

```python
"""Search documents use case."""
from typing import List
import logging

from app.domain.value_objects.search_query import SearchQuery
from app.domain.entities.chunk import Chunk
from app.ports.services import EmbeddingService, VectorStore

logger = logging.getLogger(__name__)


class SearchDocumentsUseCase:
    """Use case for semantic document search.

    Orchestrates query embedding and vector search.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore
    ):
        """Initialize with embedding and vector store dependencies."""
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    async def execute(self, query: SearchQuery) -> List[Chunk]:
        """Execute semantic search.

        Args:
            query: Search query value object

        Returns:
            List of relevant chunks ordered by similarity
        """
        logger.info(f"Searching for: '{query.text}' (top_k={query.top_k})")

        # 1. Generate query embedding
        query_embeddings = await self.embedding_service.generate_embeddings([query.text])
        query_vector = query_embeddings[0]

        # 2. Search vector store
        results = await self.vector_store.search(
            query_vector=query_vector,
            top_k=query.top_k
        )

        logger.info(f"Found {len(results)} results")
        return results
```

**Step 3: Implement ListDocuments use case**

Create `services/api/app/application/use_cases/list_documents.py`:

```python
"""List documents use case."""
from typing import List, Tuple
import logging

from app.domain.entities.document import Document
from app.ports.repositories import DocumentRepository

logger = logging.getLogger(__name__)


class ListDocumentsUseCase:
    """Use case for paginated document listing."""

    def __init__(self, document_repo: DocumentRepository):
        """Initialize with document repository."""
        self.document_repo = document_repo

    async def execute(self, page: int = 1, limit: int = 20) -> Tuple[List[Document], int]:
        """List documents with pagination.

        Args:
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (documents, total_count)

        Raises:
            ValueError: If page < 1 or limit out of range
        """
        if page < 1:
            raise ValueError("Page must be >= 1")
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")

        logger.debug(f"Listing documents (page={page}, limit={limit})")

        documents, total = await self.document_repo.find_all(page=page, limit=limit)

        logger.info(f"Retrieved {len(documents)} documents (total: {total})")
        return documents, total
```

**Step 4: Write basic tests**

Create `services/api/tests/application/test_delete_document.py`:

```python
"""Tests for DeleteDocumentUseCase."""
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from app.application.use_cases.delete_document import DeleteDocumentUseCase
from app.domain.entities.document import Document
from app.core.enums import UploadStatus
from app.core.exceptions import DocumentNotFoundError
from app.ports.repositories import DocumentRepository, ChunkRepository
from app.ports.services import VectorStore


@pytest.mark.asyncio
async def test_delete_document_success():
    """Test successful document deletion."""
    doc_id = uuid4()
    mock_doc_repo = Mock(spec=DocumentRepository)
    mock_chunk_repo = Mock(spec=ChunkRepository)
    mock_vector_store = Mock(spec=VectorStore)

    # Mock document exists
    mock_doc_repo.find_by_id = AsyncMock(return_value=Document(
        id=doc_id,
        title="Test",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.utcnow(),
        upload_status=UploadStatus.COMPLETED
    ))
    mock_doc_repo.delete = AsyncMock()
    mock_chunk_repo.delete_by_document_id = AsyncMock()
    mock_vector_store.delete_by_document = AsyncMock()

    use_case = DeleteDocumentUseCase(
        document_repo=mock_doc_repo,
        chunk_repo=mock_chunk_repo,
        vector_store=mock_vector_store
    )

    await use_case.execute(doc_id)

    # Verify all deletions occurred
    mock_vector_store.delete_by_document.assert_called_once_with(doc_id)
    mock_chunk_repo.delete_by_document_id.assert_called_once_with(doc_id)
    mock_doc_repo.delete.assert_called_once_with(doc_id)


@pytest.mark.asyncio
async def test_delete_document_not_found():
    """Test deleting non-existent document raises error."""
    doc_id = uuid4()
    mock_doc_repo = Mock(spec=DocumentRepository)
    mock_doc_repo.find_by_id = AsyncMock(return_value=None)

    use_case = DeleteDocumentUseCase(
        document_repo=mock_doc_repo,
        chunk_repo=Mock(spec=ChunkRepository),
        vector_store=Mock(spec=VectorStore)
    )

    with pytest.raises(DocumentNotFoundError):
        await use_case.execute(doc_id)
```

**Step 5: Add missing import and run tests**

Add to `services/api/tests/application/test_delete_document.py`:
```python
from datetime import datetime
```

Run:
```bash
cd services/api && poetry run pytest tests/application/ -v
```

Expected: PASS (all application tests)

**Step 6: Commit additional use cases**

```bash
git add services/api/app/application/use_cases/ services/api/tests/application/
git commit -m "feat(api): add DeleteDocument, SearchDocuments, ListDocuments use cases

- DeleteDocument: coordinates cascade deletion
- SearchDocuments: semantic search workflow
- ListDocuments: paginated retrieval
- All use cases tested with mocked ports"
```

---

## Phase 5: Infrastructure Layer - Database Adapters

### Task 9: Implement SQLAlchemy Repository Adapters

**Files:**
- Create: `services/api/app/infrastructure/__init__.py`
- Create: `services/api/app/infrastructure/db/__init__.py`
- Create: `services/api/app/infrastructure/db/base.py`
- Create: `services/api/app/infrastructure/db/models.py`
- Create: `services/api/app/infrastructure/db/repositories/__init__.py`
- Create: `services/api/app/infrastructure/db/repositories/document_repository_impl.py`
- Create: `services/api/app/infrastructure/db/repositories/chunk_repository_impl.py`

This is a large task - continue in next message for implementation details.

**Step 1: Create database base and models**

Create `services/api/app/infrastructure/__init__.py`:
```python
"""Infrastructure layer - adapters implementing ports."""
```

Create `services/api/app/infrastructure/db/__init__.py`:
```python
"""Database infrastructure."""
```

Create `services/api/app/infrastructure/db/base.py`:
```python
"""SQLAlchemy base setup."""
from sqlalchemy.orm import declarative_base

Base = declarative_base()
```

Create `services/api/app/infrastructure/db/models.py`:
```python
"""SQLAlchemy ORM models (infrastructure concern).

These are NOT domain entities - they're database representations.
Repositories map between these and domain entities.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.infrastructure.db.base import Base
from app.core.enums import UploadStatus


class DocumentModel(Base):
    """SQLAlchemy model for documents table."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(512), nullable=True)
    file_size = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    upload_status = Column(SQLEnum(UploadStatus), nullable=False)
    created_at = Column(DateTime, nullable=False)

    # Relationships
    chunks = relationship(
        "ChunkModel",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class ChunkModel(Base):
    """SQLAlchemy model for chunks table."""

    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    tokens = Column(Integer, nullable=False)
    metadata = Column(JSONB, nullable=False, default=dict)
    section_title = Column(String(255), nullable=True)
    section_level = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)

    # Relationships
    document = relationship("DocumentModel", back_populates="chunks")
```

**Step 2: Run initial commit for models**

```bash
git add services/api/app/infrastructure/db/
git commit -m "feat(api): add SQLAlchemy models for database layer

- DocumentModel and ChunkModel ORM definitions
- Infrastructure layer separate from domain
- Cascade delete configuration"
```

---

Due to length constraints, I'll provide the key remaining tasks in summary form. The full plan would continue with:

## Remaining Tasks Summary

**Task 10-12: Complete Repository Implementations**
- Implement DocumentRepositoryImpl and ChunkRepositoryImpl
- Map between ORM models and domain entities
- Write integration tests with test database

**Task 13-15: Infrastructure Adapters (External Services)**
- Implement QdrantVectorStore adapter
- Implement HTTPEmbeddingService client
- Implement FileProcessor and SemanticChunker

**Task 16-18: HTTP Layer (FastAPI Routes)**
- Implement document upload route
- Implement search route
- Update dependency injection in main.py

**Task 19-21: Testing & Cleanup**
- Write E2E tests for critical workflows
- Delete redundant files
- Run linting and type checking

**Task 22-24: Final Integration**
- Update all imports
- Verify K8s deployments work
- Final testing and documentation

---

Each task would follow the same TDD pattern:
1. Write failing test
2. Verify failure
3. Implement minimal code
4. Verify pass
5. Commit with descriptive message

Total estimated: **40-50 bite-sized tasks** over 2-3 weeks.
