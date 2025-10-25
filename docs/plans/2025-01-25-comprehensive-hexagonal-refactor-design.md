# Comprehensive Hexagonal Architecture Refactor Design

**Date:** 2025-01-25
**Type:** Architecture Refactor
**Status:** Approved for Implementation

## Executive Summary

This design document outlines a comprehensive refactoring of the RAAS (Retrieval-Augmented-Generation as a Service) project to adopt **Hexagonal Architecture (Ports & Adapters)** within each microservice. The refactor prioritizes code quality, maintainability, and SOLID principles while maintaining all existing functionality and Type I project requirements.

**Primary Goals:**
- Apply hexagonal architecture within all 4 microservices
- Achieve full SOLID principles compliance
- Update all packages for Python 3.13 compatibility
- Improve testing with focused critical path coverage (60-80%)
- Simplify project structure and remove redundancy
- Maintain all Type I requirements (scalability, reliability, orchestration)

**Timeline Estimate:** 2-3 weeks
**Risk Level:** Medium (significant restructuring but no feature changes)

---

## 1. Architecture Overview

### 1.1 High-Level Structure

The project maintains **4 independent microservices** (Type I requirement):

1. **API Service** - Gateway coordinating RAG workflows
2. **Embedder Service** - Vector embedding generation
3. **Generator Service** - LLM-based answer generation
4. **Frontend Service** - React UI for user interaction

Each backend service (API, Embedder, Generator) adopts **hexagonal architecture** internally:

```
services/<service-name>/
├── domain/          # Core business logic (entities, value objects, domain services)
├── application/     # Use cases / application services (orchestration)
├── infrastructure/  # Adapters (DB, HTTP, external APIs, vector stores)
├── ports/           # Interface definitions (repositories, external services)
└── main.py          # Dependency injection container and app wiring
```

### 1.2 Dependency Flow

**Dependencies point inward** (Dependency Inversion Principle):

```
Infrastructure → Ports ← Application ← Domain
     ↓            ↑          ↓           ↓
  Adapters    Interfaces  Use Cases   Entities
```

- **Domain**: Zero external dependencies (pure Python)
- **Ports**: Define interfaces (abstract base classes)
- **Application**: Depends on ports, orchestrates workflows
- **Infrastructure**: Implements ports, handles external concerns

---

## 2. Layer-by-Layer Design

### 2.1 Domain Layer

**Purpose:** Pure business logic with no infrastructure dependencies.

**Components:**

```python
# domain/entities/document.py
@dataclass
class Document:
    """Core document entity with business rules."""
    id: UUID
    title: str
    file_name: str
    file_type: str
    created_at: datetime
    upload_status: UploadStatus

    def mark_completed(self) -> None:
        """Transition to completed state (business rule)."""
        self.upload_status = UploadStatus.COMPLETED

    def mark_failed(self) -> None:
        """Transition to failed state (business rule)."""
        self.upload_status = UploadStatus.FAILED

# domain/entities/chunk.py
@dataclass
class Chunk:
    """Chunk entity representing a document fragment."""
    id: UUID
    document_id: UUID
    content: str
    tokens: int
    embedding_vector: Optional[List[float]] = None

    def has_embedding(self) -> bool:
        """Check if chunk has been embedded."""
        return self.embedding_vector is not None

# domain/value_objects/search_query.py
@dataclass(frozen=True)
class SearchQuery:
    """Immutable search query with validation."""
    text: str
    top_k: int = 5

    def __post_init__(self):
        if self.top_k < 1 or self.top_k > 100:
            raise ValueError("top_k must be between 1 and 100")
```

**Principles:**
- Entities contain business logic and state transitions
- Value objects are immutable and self-validating
- No imports from infrastructure or application layers
- Testable without any mocks or setup

### 2.2 Ports Layer (Interfaces)

**Purpose:** Define contracts between application and infrastructure layers.

**Repository Ports:**

```python
# ports/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from domain.entities.document import Document
from domain.entities.chunk import Chunk

class DocumentRepository(ABC):
    """Interface for document persistence."""

    @abstractmethod
    async def save(self, document: Document) -> Document:
        """Persist document."""
        pass

    @abstractmethod
    async def find_by_id(self, document_id: UUID) -> Optional[Document]:
        """Retrieve document by ID."""
        pass

    @abstractmethod
    async def find_all(self, page: int, limit: int) -> tuple[List[Document], int]:
        """Paginated document retrieval."""
        pass

    @abstractmethod
    async def delete(self, document_id: UUID) -> None:
        """Delete document."""
        pass

class ChunkRepository(ABC):
    """Interface for chunk persistence."""

    @abstractmethod
    async def save_batch(self, chunks: List[Chunk]) -> List[Chunk]:
        """Persist multiple chunks."""
        pass

    @abstractmethod
    async def find_by_document_id(self, document_id: UUID) -> List[Chunk]:
        """Retrieve chunks for a document."""
        pass
```

**Service Ports:**

```python
# ports/services.py
class EmbeddingService(ABC):
    """Interface for embedding generation."""

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for texts."""
        pass

class VectorStore(ABC):
    """Interface for vector database operations."""

    @abstractmethod
    async def upsert(self, chunks: List[Chunk]) -> None:
        """Insert or update vectors."""
        pass

    @abstractmethod
    async def search(self, query_vector: List[float], top_k: int) -> List[Chunk]:
        """Search for similar vectors."""
        pass

    @abstractmethod
    async def delete_by_document(self, document_id: UUID) -> None:
        """Delete all vectors for a document."""
        pass

class GenerationService(ABC):
    """Interface for LLM text generation."""

    @abstractmethod
    async def generate(self, prompt: str, context: List[str]) -> str:
        """Generate text from prompt and context."""
        pass
```

**Benefits:**
- Application layer depends on abstractions (DIP)
- Easy to mock for testing
- Implementations can be swapped without touching business logic
- Clear contracts prevent coupling

### 2.3 Application Layer (Use Cases)

**Purpose:** Orchestrate business workflows using domain entities and ports.

**Example Use Case:**

```python
# application/use_cases/upload_document.py
from dataclasses import dataclass
from typing import Tuple, Optional
from uuid import UUID, uuid4
from datetime import datetime

from domain.entities.document import Document
from domain.entities.chunk import Chunk
from domain.enums import UploadStatus
from ports.repositories import DocumentRepository, ChunkRepository
from ports.services import EmbeddingService, VectorStore

@dataclass
class UploadDocumentCommand:
    """Input data transfer object."""
    title: str
    file_name: str
    file_content: bytes
    description: Optional[str] = None

class UploadDocumentUseCase:
    """Orchestrates document upload workflow."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        file_processor: FileProcessor,
        chunker: TextChunker
    ):
        """Inject all dependencies via constructor."""
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.file_processor = file_processor
        self.chunker = chunker

    async def execute(self, command: UploadDocumentCommand) -> Tuple[Document, int]:
        """Execute upload workflow.

        Returns:
            Tuple of (created document, chunk count)
        """
        # 1. Create domain entity
        document = Document(
            id=uuid4(),
            title=command.title,
            file_name=command.file_name,
            file_type=self._detect_type(command.file_name),
            created_at=datetime.utcnow(),
            upload_status=UploadStatus.PROCESSING
        )

        # 2. Persist document
        document = await self.document_repo.save(document)

        try:
            # 3. Process file and create chunks
            text = await self.file_processor.extract_text(command.file_content)
            chunk_texts = await self.chunker.chunk(text)

            chunks = [
                Chunk(
                    id=uuid4(),
                    document_id=document.id,
                    content=chunk_text,
                    tokens=self._count_tokens(chunk_text)
                )
                for chunk_text in chunk_texts
            ]

            # 4. Persist chunks
            chunks = await self.chunk_repo.save_batch(chunks)

            # 5. Generate embeddings
            embeddings = await self.embedding_service.generate_embeddings(
                [c.content for c in chunks]
            )

            # 6. Update chunks with embeddings
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding_vector = embedding

            # 7. Store in vector database
            await self.vector_store.upsert(chunks)

            # 8. Update document status (domain logic)
            document.mark_completed()
            await self.document_repo.save(document)

            return document, len(chunks)

        except Exception as e:
            # Use domain logic for failure
            document.mark_failed()
            await self.document_repo.save(document)
            raise

    def _detect_type(self, filename: str) -> str:
        """Detect file type from extension."""
        return filename.split('.')[-1].lower()

    def _count_tokens(self, text: str) -> int:
        """Count tokens (simplified)."""
        return len(text.split())
```

**Other Use Cases:**
- `SearchDocumentsUseCase` - Hybrid search orchestration
- `DeleteDocumentUseCase` - Cascade deletion workflow
- `GenerateAnswerUseCase` - RAG pipeline orchestration
- `ListDocumentsUseCase` - Paginated document retrieval

**Principles:**
- Use cases orchestrate, don't contain business rules
- Single responsibility - one workflow per use case
- Depend only on ports (abstractions)
- Fully testable with mocked ports

### 2.4 Infrastructure Layer (Adapters)

**Purpose:** Implement ports with concrete technologies (DB, HTTP, external APIs).

**Database Adapters:**

```python
# infrastructure/db/models.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from infrastructure.db.base import Base

class DocumentModel(Base):
    """SQLAlchemy ORM model for documents."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    upload_status = Column(Enum(UploadStatus), nullable=False)
    created_at = Column(DateTime, nullable=False)

    chunks = relationship("ChunkModel", back_populates="document", cascade="all, delete-orphan")

# infrastructure/db/repositories/document_repository_impl.py
from typing import Optional, List, Callable
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ports.repositories import DocumentRepository
from domain.entities.document import Document
from infrastructure.db.models import DocumentModel

class SQLDocumentRepository(DocumentRepository):
    """SQLAlchemy implementation of DocumentRepository port."""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        """Inject session factory for async DB access."""
        self.session_factory = session_factory

    async def save(self, document: Document) -> Document:
        """Persist document to PostgreSQL."""
        async with self.session_factory() as session:
            # Map domain entity to ORM model
            db_model = DocumentModel(
                id=document.id,
                title=document.title,
                file_name=document.file_name,
                file_type=document.file_type,
                upload_status=document.upload_status,
                created_at=document.created_at
            )
            session.add(db_model)
            await session.commit()
            return document

    async def find_by_id(self, document_id: UUID) -> Optional[Document]:
        """Retrieve document by ID."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == document_id)
            )
            db_model = result.scalar_one_or_none()

            if not db_model:
                return None

            # Map ORM model to domain entity
            return Document(
                id=db_model.id,
                title=db_model.title,
                file_name=db_model.file_name,
                file_type=db_model.file_type,
                created_at=db_model.created_at,
                upload_status=db_model.upload_status
            )

    async def find_all(self, page: int, limit: int) -> tuple[List[Document], int]:
        """Retrieve paginated documents."""
        async with self.session_factory() as session:
            # Get total count
            count_result = await session.execute(select(func.count(DocumentModel.id)))
            total = count_result.scalar()

            # Get paginated results
            offset = (page - 1) * limit
            result = await session.execute(
                select(DocumentModel)
                .order_by(DocumentModel.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            db_models = result.scalars().all()

            # Map to domain entities
            documents = [
                Document(
                    id=m.id,
                    title=m.title,
                    file_name=m.file_name,
                    file_type=m.file_type,
                    created_at=m.created_at,
                    upload_status=m.upload_status
                )
                for m in db_models
            ]

            return documents, total

    async def delete(self, document_id: UUID) -> None:
        """Delete document (cascades to chunks)."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == document_id)
            )
            db_model = result.scalar_one_or_none()

            if db_model:
                await session.delete(db_model)
                await session.commit()
```

**HTTP Adapters (FastAPI Routes):**

```python
# infrastructure/http/routes/documents.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from uuid import UUID

from infrastructure.http.schemas import DocumentUploadResponse
from application.use_cases.upload_document import UploadDocumentUseCase, UploadDocumentCommand

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    use_case: UploadDocumentUseCase = Depends(get_upload_use_case)
):
    """HTTP adapter for document upload.

    Maps HTTP request to use case command and response.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )

    # Create command from HTTP request
    command = UploadDocumentCommand(
        title=title,
        file_name=file.filename,
        file_content=content,
        description=description
    )

    try:
        # Execute use case
        document, chunk_count = await use_case.execute(command)

        # Map domain entity to HTTP response
        return DocumentUploadResponse(
            id=str(document.id),
            title=document.title,
            file_name=document.file_name,
            chunk_count=chunk_count,
            message="Document uploaded successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
```

**External Service Adapters:**

```python
# infrastructure/external/embedder_client.py
import httpx
from typing import List

from ports.services import EmbeddingService

class HTTPEmbeddingService(EmbeddingService):
    """HTTP client adapter for embedding service."""

    def __init__(self, base_url: str, http_client: httpx.AsyncClient):
        self.base_url = base_url
        self.client = http_client

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Call embedder microservice via HTTP."""
        response = await self.client.post(
            f"{self.base_url}/embed",
            json={"texts": texts}
        )
        response.raise_for_status()
        return response.json()["embeddings"]

# infrastructure/vector/qdrant_adapter.py
from typing import List
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from ports.services import VectorStore
from domain.entities.chunk import Chunk

class QdrantVectorStore(VectorStore):
    """Qdrant adapter implementing VectorStore port."""

    def __init__(self, client: QdrantClient, collection_name: str):
        self.client = client
        self.collection = collection_name

    async def upsert(self, chunks: List[Chunk]) -> None:
        """Store chunk vectors in Qdrant."""
        points = [
            PointStruct(
                id=str(chunk.id),
                vector=chunk.embedding_vector,
                payload={
                    "document_id": str(chunk.document_id),
                    "content": chunk.content,
                    "tokens": chunk.tokens
                }
            )
            for chunk in chunks
            if chunk.has_embedding()
        ]

        self.client.upsert(
            collection_name=self.collection,
            points=points
        )

    async def search(self, query_vector: List[float], top_k: int) -> List[Chunk]:
        """Search for similar vectors."""
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k
        )

        # Map Qdrant results to domain chunks
        return [
            Chunk(
                id=UUID(hit.id),
                document_id=UUID(hit.payload["document_id"]),
                content=hit.payload["content"],
                tokens=hit.payload["tokens"],
                embedding_vector=hit.vector
            )
            for hit in results
        ]

    async def delete_by_document(self, document_id: UUID) -> None:
        """Delete all vectors for a document."""
        self.client.delete(
            collection_name=self.collection,
            points_selector={
                "filter": {
                    "must": [
                        {
                            "key": "document_id",
                            "match": {"value": str(document_id)}
                        }
                    ]
                }
            }
        )
```

### 2.5 Dependency Injection & Wiring

**Purpose:** Wire all layers together in the composition root.

```python
# main.py
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import httpx
from qdrant_client import QdrantClient

from core.config import Settings
from infrastructure.db.repositories.document_repository_impl import SQLDocumentRepository
from infrastructure.db.repositories.chunk_repository_impl import SQLChunkRepository
from infrastructure.external.embedder_client import HTTPEmbeddingService
from infrastructure.external.generator_client import HTTPGenerationService
from infrastructure.vector.qdrant_adapter import QdrantVectorStore
from infrastructure.processing.file_processor import FileProcessorService
from infrastructure.processing.semantic_chunker import SemanticChunker
from application.use_cases.upload_document import UploadDocumentUseCase
from application.use_cases.search_documents import SearchDocumentsUseCase
from application.use_cases.delete_document import DeleteDocumentUseCase
from infrastructure.http.routes import documents, search, health

class Container:
    """Dependency injection container (composition root)."""

    def __init__(self, settings: Settings):
        # Infrastructure resources (singletons)
        self.engine = create_async_engine(settings.database_url, echo=settings.db_echo)
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.qdrant_client = QdrantClient(url=settings.qdrant_url)

        # Repositories (adapters implementing ports)
        self.document_repo = SQLDocumentRepository(self.session_factory)
        self.chunk_repo = SQLChunkRepository(self.session_factory)

        # External services (adapters)
        self.embedding_service = HTTPEmbeddingService(
            settings.embedder_url,
            self.http_client
        )
        self.generation_service = HTTPGenerationService(
            settings.generator_url,
            self.http_client
        )
        self.vector_store = QdrantVectorStore(
            self.qdrant_client,
            settings.collection_name
        )

        # Domain/infrastructure services
        self.file_processor = FileProcessorService()
        self.chunker = SemanticChunker(
            min_chunk_size=settings.min_chunk_size,
            max_chunk_size=settings.max_chunk_size
        )

    def get_upload_use_case(self) -> UploadDocumentUseCase:
        """Factory for upload use case with dependencies."""
        return UploadDocumentUseCase(
            document_repo=self.document_repo,
            chunk_repo=self.chunk_repo,
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
            file_processor=self.file_processor,
            chunker=self.chunker
        )

    def get_search_use_case(self) -> SearchDocumentsUseCase:
        """Factory for search use case."""
        return SearchDocumentsUseCase(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
            chunk_repo=self.chunk_repo
        )

    def get_delete_use_case(self) -> DeleteDocumentUseCase:
        """Factory for delete use case."""
        return DeleteDocumentUseCase(
            document_repo=self.document_repo,
            vector_store=self.vector_store,
            file_processor=self.file_processor
        )

    async def close(self):
        """Cleanup resources."""
        await self.http_client.aclose()
        await self.engine.dispose()

# Application setup
settings = Settings()
container = Container(settings)
app = FastAPI(title="RAAS API", version="1.0.0")

# Dependency providers for FastAPI
def get_upload_use_case() -> UploadDocumentUseCase:
    return container.get_upload_use_case()

def get_search_use_case() -> SearchDocumentsUseCase:
    return container.get_search_use_case()

def get_delete_use_case() -> DeleteDocumentUseCase:
    return container.get_delete_use_case()

# Register routes
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(health.router)

# Lifecycle events
@app.on_event("shutdown")
async def shutdown_event():
    await container.close()
```

**Benefits:**
- Single location for all dependency wiring
- Easy to swap implementations (change container)
- Clear dependency graph visibility
- Testable (create test container with mocks)

---

## 3. Testing Strategy

### 3.1 Test Pyramid

```
        /\
       /E2E\      <- End-to-end (few, critical paths)
      /------\
     /Integr-\    <- Integration (adapters with real infrastructure)
    /----------\
   /   Unit     \  <- Unit (many, fast, isolated)
  /--------------\
```

### 3.2 Layer-by-Layer Testing

**Domain Tests (Pure Unit - No Mocks):**

```python
# tests/domain/test_document.py
import pytest
from datetime import datetime
from uuid import uuid4

from domain.entities.document import Document
from domain.enums import UploadStatus

def test_document_mark_completed():
    """Domain logic is tested without any infrastructure."""
    document = Document(
        id=uuid4(),
        title="Test Document",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.utcnow(),
        upload_status=UploadStatus.PROCESSING
    )

    document.mark_completed()

    assert document.upload_status == UploadStatus.COMPLETED

def test_document_mark_failed():
    """Test failure state transition."""
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

**Use Case Tests (Mock Ports Only):**

```python
# tests/application/test_upload_document_use_case.py
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from application.use_cases.upload_document import UploadDocumentUseCase, UploadDocumentCommand
from ports.repositories import DocumentRepository, ChunkRepository
from ports.services import EmbeddingService, VectorStore

@pytest.mark.asyncio
async def test_upload_document_success():
    """Test use case orchestration with mocked ports."""
    # Arrange: Create mocks for all ports
    mock_doc_repo = Mock(spec=DocumentRepository)
    mock_chunk_repo = Mock(spec=ChunkRepository)
    mock_embedding_service = Mock(spec=EmbeddingService)
    mock_vector_store = Mock(spec=VectorStore)
    mock_file_processor = Mock()
    mock_chunker = Mock()

    # Configure mock behavior
    mock_doc_repo.save = AsyncMock(side_effect=lambda doc: doc)
    mock_chunk_repo.save_batch = AsyncMock(side_effect=lambda chunks: chunks)
    mock_file_processor.extract_text = AsyncMock(return_value="Sample document text")
    mock_chunker.chunk = AsyncMock(return_value=["chunk 1", "chunk 2"])
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
        title="Test Upload",
        file_name="test.pdf",
        file_content=b"PDF content here"
    )
    document, chunk_count = await use_case.execute(command)

    # Assert: Verify orchestration
    assert document.title == "Test Upload"
    assert chunk_count == 2
    assert mock_doc_repo.save.call_count == 2  # Initial + completion
    assert mock_chunk_repo.save_batch.call_count == 1
    assert mock_embedding_service.generate_embeddings.call_count == 1
    assert mock_vector_store.upsert.call_count == 1

@pytest.mark.asyncio
async def test_upload_document_failure_marks_failed():
    """Test error handling marks document as failed."""
    # Arrange
    mock_doc_repo = Mock(spec=DocumentRepository)
    mock_chunk_repo = Mock(spec=ChunkRepository)
    mock_file_processor = Mock()

    mock_doc_repo.save = AsyncMock(side_effect=lambda doc: doc)
    mock_file_processor.extract_text = AsyncMock(side_effect=Exception("Processing error"))

    use_case = UploadDocumentUseCase(
        document_repo=mock_doc_repo,
        chunk_repo=mock_chunk_repo,
        embedding_service=Mock(),
        vector_store=Mock(),
        file_processor=mock_file_processor,
        chunker=Mock()
    )

    # Act & Assert
    command = UploadDocumentCommand(
        title="Test",
        file_name="test.pdf",
        file_content=b"content"
    )

    with pytest.raises(Exception, match="Processing error"):
        await use_case.execute(command)

    # Verify document was marked as failed
    assert mock_doc_repo.save.call_count == 2
    failed_call = mock_doc_repo.save.call_args_list[1]
    assert failed_call[0][0].upload_status == UploadStatus.FAILED
```

**Integration Tests (Real Adapters):**

```python
# tests/infrastructure/test_sql_document_repository.py
import pytest
from uuid import uuid4
from datetime import datetime

from infrastructure.db.repositories.document_repository_impl import SQLDocumentRepository
from domain.entities.document import Document
from domain.enums import UploadStatus

@pytest.mark.asyncio
async def test_save_and_retrieve_document(test_db_session_factory):
    """Test repository with real SQLAlchemy and test database."""
    repo = SQLDocumentRepository(test_db_session_factory)

    # Create domain entity
    document = Document(
        id=uuid4(),
        title="Integration Test",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.utcnow(),
        upload_status=UploadStatus.COMPLETED
    )

    # Test save
    saved = await repo.save(document)
    assert saved.id == document.id

    # Test retrieve
    found = await repo.find_by_id(document.id)
    assert found is not None
    assert found.id == document.id
    assert found.title == "Integration Test"
    assert found.upload_status == UploadStatus.COMPLETED

@pytest.mark.asyncio
async def test_delete_document_cascades_to_chunks(test_db_session_factory):
    """Test deletion cascade."""
    # ... test implementation
```

**End-to-End Tests:**

```python
# tests/e2e/test_upload_workflow.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_complete_upload_workflow(
    test_app,
    test_db,
    test_qdrant_collection
):
    """Test full upload workflow through HTTP API."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Upload document
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", b"PDF content")},
            data={"title": "E2E Test Document"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "E2E Test Document"
        assert data["chunk_count"] > 0

        document_id = data["id"]

        # Verify document is retrievable
        response = await client.get(f"/api/documents/{document_id}")
        assert response.status_code == 200

        # Verify vectors were stored (check Qdrant)
        # ... additional assertions
```

### 3.3 Test Organization

```
tests/
├── domain/                     # Pure unit tests (no setup needed)
│   ├── test_document.py
│   ├── test_chunk.py
│   └── test_search_query.py
│
├── application/                # Use case tests (mocked ports)
│   ├── test_upload_document_use_case.py
│   ├── test_search_documents_use_case.py
│   └── test_delete_document_use_case.py
│
├── infrastructure/             # Integration tests (real adapters)
│   ├── db/
│   │   └── test_sql_document_repository.py
│   ├── http/
│   │   └── test_document_routes.py
│   └── external/
│       └── test_embedder_client.py
│
├── e2e/                       # End-to-end tests
│   ├── test_upload_workflow.py
│   ├── test_search_workflow.py
│   └── test_rag_workflow.py
│
└── conftest.py                # Shared fixtures
```

### 3.4 Coverage Targets

- **Domain layer**: 100% (easy, pure functions)
- **Use cases**: 80%+ (critical business logic)
- **Infrastructure**: 60%+ (key adapters)
- **Overall**: 60-80% (focused on critical paths)

**Critical Paths to Cover:**
1. Document upload → chunking → embedding → vector storage
2. Search → retrieval → reranking
3. RAG generation → context retrieval → LLM call
4. Document deletion → cascade to chunks and vectors
5. Error handling in all use cases

---

## 4. Package Updates for Python 3.13

### 4.1 Version Requirements

**Based on compatibility research (2025):**

```toml
# API Service
[tool.poetry.dependencies]
python = "^3.13"

# Core (Python 3.13 compatible versions)
fastapi = "^0.115.0"           # >=0.115.x required
uvicorn = {extras = ["standard"], version = "^0.32.0"}
pydantic = "^2.8.0"            # >=2.8.0 CRITICAL for Python 3.13
pydantic-settings = "^2.6.0"

# Database
sqlalchemy = "^2.0.36"         # Latest 2.0.x
asyncpg = "^0.30.0"
alembic = "^1.14.0"

# HTTP
httpx = "^0.27.0"

# Vector DB
qdrant-client = "^1.12.0"

# File processing (updated versions)
pypdf = "^5.1.0"               # Major update from 3.x
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

# Dev dependencies
[tool.poetry.group.dev.dependencies]
pytest = "^8.3.0"
pytest-asyncio = "^0.24.0"
pytest-cov = "^6.0.0"
pytest-mock = "^3.14.0"
mypy = "^1.13.0"
ruff = "^0.8.0"               # Modern linter/formatter
```

**Similar updates for Embedder and Generator services.**

### 4.2 Breaking Changes to Address

1. **Pydantic 2.8+**
   - Ensure all v2 migration complete
   - Use `model_validate()` instead of `parse_obj()`
   - Use `model_dump()` instead of `dict()`

2. **sentence-transformers 3.x**
   - API changes in model loading
   - Embedding method signatures updated

3. **pypdf 5.x**
   - Import changes from `pypdf` (not `PyPDF2`)
   - Method name updates

### 4.3 Migration Steps

1. Update `pyproject.toml` with new versions
2. Run `poetry lock --no-update` to regenerate locks
3. Run `poetry install` in each service
4. Update code for breaking changes
5. Run test suites to verify compatibility
6. Update Dockerfiles with Python 3.13 base image

---

## 5. Code Quality Standards

### 5.1 Comment Philosophy

**Best Practices:**

```python
# ❌ BAD: Obvious noise
class Document:
    title: str  # The document title
    id: UUID    # The document ID

# ✅ GOOD: Self-documenting code
class Document:
    """Domain entity for uploaded documents.

    Enforces lifecycle transitions: processing -> completed/failed.
    """
    title: str
    id: UUID

    def mark_completed(self) -> None:
        """Transition to completed state after successful processing."""
        self.upload_status = UploadStatus.COMPLETED
```

**When to Comment:**

1. **Module docstrings**: Purpose and key exports
2. **Class docstrings**: Responsibility and usage
3. **Method docstrings**: Non-obvious behavior, side effects, gotchas
4. **Inline comments**: Complex algorithms, business rules, workarounds
5. **Type hints**: Preferred over comments for types

**When NOT to Comment:**

- Self-explanatory variable names
- Obvious CRUD operations
- Simple getters/setters
- Restating what code clearly does

### 5.2 Linting & Formatting

**Use Ruff (modern, fast replacement for flake8 + isort + black):**

```toml
# pyproject.toml
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
```

### 5.3 Type Checking

**Use mypy for static type checking:**

```toml
[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true
```

---

## 6. Project Structure Cleanup

### 6.1 Files to Delete

**Redundant/obsolete files:**

```bash
# Test file consolidation
services/api/tests/services/test_semantic_chunker.py      # Move to unit/services/
services/api/tests/test_reranker.py                       # Move to unit/services/
services/api/tests/test_generator_client.py               # Move to unit/services/
services/api/tests/test_health.py                         # Move to unit/routes/

# Integration test deduplication
services/api/tests/integration/test_document_upload_async.py  # Merge
services/api/tests/test_upload_integration.py                 # Merge

# Already deleted (clean up from git)
services/api/tests/unit/test_config.py
docs/plans/2025-10-24-advanced-rag-improvements-*.md
docs/plans/2025-10-25-frontend-quick-cleanup-*.md
```

### 6.2 Final Directory Structure

**API Service (Primary Example):**

```
services/api/
├── app/
│   ├── domain/                        # Pure business logic
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── document.py
│   │   │   └── chunk.py
│   │   ├── value_objects/
│   │   │   ├── __init__.py
│   │   │   └── search_query.py
│   │   └── services/                  # Domain services (if complex logic)
│   │       └── __init__.py
│   │
│   ├── application/                   # Use cases
│   │   ├── __init__.py
│   │   └── use_cases/
│   │       ├── __init__.py
│   │       ├── upload_document.py
│   │       ├── search_documents.py
│   │       ├── delete_document.py
│   │       ├── list_documents.py
│   │       └── generate_answer.py
│   │
│   ├── ports/                         # Interfaces
│   │   ├── __init__.py
│   │   ├── repositories.py
│   │   └── services.py
│   │
│   ├── infrastructure/                # Adapters
│   │   ├── __init__.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── models.py
│   │   │   └── repositories/
│   │   │       ├── __init__.py
│   │   │       ├── document_repository_impl.py
│   │   │       └── chunk_repository_impl.py
│   │   ├── http/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── documents.py
│   │   │   │   ├── search.py
│   │   │   │   ├── health.py
│   │   │   │   └── models.py
│   │   │   └── schemas.py
│   │   ├── external/
│   │   │   ├── __init__.py
│   │   │   ├── embedder_client.py
│   │   │   └── generator_client.py
│   │   ├── vector/
│   │   │   ├── __init__.py
│   │   │   └── qdrant_adapter.py
│   │   └── processing/
│   │       ├── __init__.py
│   │       ├── file_processor.py
│   │       ├── semantic_chunker.py
│   │       ├── processors/
│   │       │   ├── __init__.py
│   │       │   ├── base.py
│   │       │   ├── pdf_processor.py
│   │       │   ├── docx_processor.py
│   │       │   └── text_processor.py
│   │       └── search/
│   │           ├── __init__.py
│   │           ├── hybrid_search.py
│   │           ├── bm25.py
│   │           └── reranker.py
│   │
│   ├── core/                          # Shared utilities
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── enums.py
│   │   └── exceptions.py
│   │
│   └── main.py                        # Application entry + DI
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures
│   ├── domain/                        # Pure unit tests
│   │   ├── __init__.py
│   │   ├── test_document.py
│   │   └── test_chunk.py
│   ├── application/                   # Use case tests
│   │   ├── __init__.py
│   │   ├── test_upload_document.py
│   │   └── test_search_documents.py
│   ├── infrastructure/                # Integration tests
│   │   ├── __init__.py
│   │   ├── db/
│   │   │   └── test_repositories.py
│   │   ├── http/
│   │   │   └── test_routes.py
│   │   └── external/
│   │       └── test_clients.py
│   └── e2e/                          # End-to-end tests
│       ├── __init__.py
│       ├── test_upload_workflow.py
│       └── test_rag_workflow.py
│
├── alembic/                          # Database migrations
├── Dockerfile
├── pyproject.toml
├── poetry.lock
└── README.md
```

**Similar structure for Embedder and Generator services** (simpler, fewer layers needed).

### 6.3 Simplification Principles

1. **Max 3 directory levels** (avoid deep nesting)
2. **Colocate related code** (repositories together, routes together)
3. **Clear layer boundaries** (domain/application/infrastructure/ports)
4. **Single import path** (no circular dependencies)
5. **Self-documenting structure** (names indicate purpose)

---

## 7. SOLID Principles Compliance

### 7.1 Single Responsibility Principle (SRP)

**Before:**
```python
# DocumentService did: file I/O, DB ops, chunking, embedding coordination
class DocumentService:
    async def create_document(...):
        # Save file
        # Create DB record
        # Process file
        # Chunk text
        # Call embedder
        # Store vectors
```

**After:**
```python
# Each class has ONE reason to change

class UploadDocumentUseCase:
    """Orchestrates upload workflow only"""

class DocumentRepository:
    """Document persistence only"""

class FileProcessor:
    """File I/O only"""

class SemanticChunker:
    """Text chunking only"""
```

### 7.2 Open/Closed Principle (OCP)

**Example: Adding new vector store**

```python
# Add Pinecone without modifying use cases
class PineconeVectorStore(VectorStore):
    """New implementation of VectorStore port"""
    async def upsert(self, chunks): ...
    async def search(self, query_vector, top_k): ...

# Change only in DI container
container.vector_store = PineconeVectorStore(...)  # Not QdrantVectorStore
```

### 7.3 Liskov Substitution Principle (LSP)

All implementations honor port contracts:

```python
# Any VectorStore works identically in use cases
vector_store: VectorStore = QdrantVectorStore(...)  # OR
vector_store: VectorStore = PineconeVectorStore(...)  # OR
vector_store: VectorStore = InMemoryVectorStore(...)  # for tests

# No type checking needed in use cases
await vector_store.upsert(chunks)  # Always works the same
```

### 7.4 Interface Segregation Principle (ISP)

**Focused interfaces, not fat ones:**

```python
# GOOD: Clients only depend on methods they use
class DocumentRepository(ABC):
    @abstractmethod
    async def save(self, document: Document): ...
    @abstractmethod
    async def find_by_id(self, id: UUID): ...
    @abstractmethod
    async def delete(self, id: UUID): ...

# NOT: DocumentAndChunkAndVectorRepository with 20 methods
```

### 7.5 Dependency Inversion Principle (DIP)

**High-level modules depend on abstractions:**

```python
# Use case depends on PORT (abstraction)
class UploadDocumentUseCase:
    def __init__(self, document_repo: DocumentRepository):  # ← Interface
        self.repo = document_repo

# Infrastructure implements port
class SQLDocumentRepository(DocumentRepository):  # ← Concrete
    async def save(self, document): ...

# Wired in DI container
use_case = UploadDocumentUseCase(
    document_repo=SQLDocumentRepository(...)  # Inject concrete
)
```

**Dependency direction:**
```
Infrastructure → Ports ← Application ← Domain
 (concrete)   implements   depends on   (pure)
```

---

## 8. Type I Requirements Compliance

### 8.1 Requirements Matrix

| Requirement | Implementation | Status | Marks |
|-------------|---------------|--------|-------|
| **Frontend UI** | React with interactive components | ✅ Maintained | 1 |
| **Backend DB** | PostgreSQL + Qdrant (enhanced with clean repos) | ✅ Improved | 1 |
| **≥4 Functionalities** | Upload, Search, Delete, List, Generate, Multi-LLM | ✅ 6 total | 1 |
| **Microservices** | 4 services with hexagonal architecture | ✅ Enhanced | 2 |
| **Scalability** | Horizontal scaling via K8s | ✅ Maintained | 1 |
| **Reliability** | Health checks, error handling | ✅ Improved | 1 |
| **Load Balancing** | K8s service LB + Ingress | ✅ Maintained | 1 |
| **Orchestration (K8s)** | Deployments, Services, ConfigMaps | ✅ Maintained | 3 |
| **Rollout/Rollback** | Rolling updates with history | ✅ Maintained | 1 |
| **Originality** | Hexagonal arch + SOLID + Advanced RAG | ✅ **Enhanced** | 3 |
| **Total** | | | **15/15** |

### 8.2 Demonstration Points

**For presentation, emphasize:**

1. **Architecture sophistication**: Hexagonal architecture within microservices (industry best practice 2025)
2. **SOLID compliance**: Concrete examples of each principle
3. **Testability**: Show domain tests (no mocks), use case tests (mocked ports), integration tests
4. **Scalability**: K8s scaling of independent services
5. **Code quality**: Clean structure, type hints, focused comments

---

## 9. Migration & Implementation Strategy

### 9.1 Implementation Phases

**Phase 1: Foundation (Week 1)**
1. Set up new directory structure
2. Create domain entities and value objects
3. Define all ports (interfaces)
4. Update packages to Python 3.13 compatible versions
5. Create DI container skeleton

**Phase 2: Core Infrastructure (Week 1-2)**
1. Implement database adapters (SQLAlchemy repositories)
2. Implement vector store adapter (Qdrant)
3. Implement HTTP adapters (FastAPI routes)
4. Implement external service adapters (Embedder, Generator clients)
5. Wire up DI container

**Phase 3: Application Layer (Week 2)**
1. Implement use cases (UploadDocument, SearchDocuments, etc.)
2. Connect use cases to ports
3. Migrate business logic from old services to use cases
4. Remove old service layer

**Phase 4: Testing (Week 2-3)**
1. Write domain tests (100% coverage target)
2. Write use case tests with mocks (80% coverage)
3. Write integration tests for adapters (60% coverage)
4. Write E2E tests for critical paths
5. Update existing tests to new structure

**Phase 5: Cleanup & Documentation (Week 3)**
1. Delete redundant files
2. Update all docstrings and comments
3. Run linting and type checking
4. Verify all K8s deployments work
5. Final testing and validation

### 9.2 Risk Mitigation

**Risks:**

1. **Breaking existing functionality**
   - Mitigation: Comprehensive test coverage, incremental migration

2. **Package compatibility issues**
   - Mitigation: Test packages early, have rollback plan

3. **DI container complexity**
   - Mitigation: Start simple, refactor as needed

4. **Timeline overrun**
   - Mitigation: Prioritize core paths, defer nice-to-haves

### 9.3 Rollback Plan

If critical issues arise:
1. Maintain current implementation in separate branch
2. Use feature flags for gradual rollout
3. Git worktree allows easy comparison
4. Can revert entire refactor if needed (unlikely)

---

## 10. Success Criteria

### 10.1 Functional Requirements

- ✅ All existing features work identically
- ✅ All API endpoints respond correctly
- ✅ Upload → embedding → search workflow functional
- ✅ RAG generation workflow functional
- ✅ K8s deployment successful with scaling
- ✅ Rolling updates and rollback demonstrated

### 10.2 Quality Requirements

- ✅ 60-80% test coverage (focused on critical paths)
- ✅ All SOLID principles demonstrable
- ✅ Zero circular dependencies
- ✅ Type checking passes (mypy)
- ✅ Linting passes (ruff)
- ✅ Python 3.13 compatibility verified

### 10.3 Documentation Requirements

- ✅ This design document complete
- ✅ Updated README with architecture explanation
- ✅ Code comments follow standards
- ✅ All ports and use cases documented
- ✅ Deployment instructions updated

---

## 11. References & Resources

### 11.1 Architecture Patterns

- Hexagonal Architecture (Ports & Adapters): Alistair Cockburn
- Clean Architecture: Robert C. Martin
- Domain-Driven Design: Eric Evans

### 11.2 Python 3.13 Compatibility

- Pydantic 2.8+ required for Python 3.13
- FastAPI 0.115+ compatible
- SQLAlchemy 2.0.36+ tested with Python 3.13

### 11.3 RAG Best Practices (2025)

- Hybrid search (vector + BM25)
- Semantic chunking with embeddings
- Reranking for improved relevance
- Async processing for performance

---

## Appendix A: Glossary

- **Port**: Interface definition (abstract base class)
- **Adapter**: Concrete implementation of a port
- **Use Case**: Application service orchestrating a business workflow
- **Entity**: Domain object with identity and lifecycle
- **Value Object**: Immutable domain object defined by attributes
- **Repository**: Port for data persistence operations
- **DI Container**: Composition root for dependency wiring

---

## Appendix B: Example File Mappings

### Current → New Structure

```
# Old location → New location

app/services/document_service.py
  → application/use_cases/upload_document.py
  → application/use_cases/delete_document.py

app/services/document_metadata_service.py
  → infrastructure/db/repositories/document_repository_impl.py

app/core/qdrant_client.py
  → infrastructure/vector/qdrant_adapter.py

app/models/document.py (SQLAlchemy)
  → infrastructure/db/models.py

# New files (domain layer)
domain/entities/document.py (NEW)
domain/entities/chunk.py (NEW)
ports/repositories.py (NEW)
ports/services.py (NEW)
```

---

**End of Design Document**

This comprehensive refactor will transform RAAS into a maintainable, testable, SOLID-compliant codebase following 2025 industry best practices while maintaining all Type I project requirements for maximum marks.
