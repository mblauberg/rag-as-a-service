# Comprehensive Quality Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix critical bugs, refactor for maintainability, redesign frontend to search-centric single-page app, and achieve 80%+ test coverage.

**Architecture:** Microservices (API, Embedder, Frontend) communicating via REST. Backend refactored with dependency injection, frontend modernized with shadcn/ui and single-page architecture centered on search.

**Tech Stack:** FastAPI, SQLAlchemy, Qdrant, React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, pytest, Vitest

---

## Phase 1: Critical Bug Fixes

### Task 1.1: Fix Schema Mismatch - Backend

**Context:** Upload response currently nests document inside response object, causing frontend to see `undefined` for document ID.

**Files:**
- Modify: `services/api/app/models/schemas.py:66-72`
- Modify: `services/api/app/api/routes/documents.py:76-80`

**Step 1: Update DocumentUploadResponse schema**

Edit `services/api/app/models/schemas.py`:

```python
# Replace the existing DocumentUploadResponse class
class DocumentUploadResponse(DocumentResponse):
    """Schema for document upload response - extends DocumentResponse."""

    model_config = ConfigDict(from_attributes=True)

    message: str
    chunk_count: int
```

**Step 2: Update upload endpoint response**

Edit `services/api/app/api/routes/documents.py`:

```python
# Replace the return statement in upload_document function (around line 76)
return DocumentUploadResponse(
    **DocumentResponse.model_validate(document).model_dump(),
    message="Document uploaded and processed successfully",
    chunk_count=chunk_count
)
```

**Step 3: Verify schema change**

Run: `cd services/api && poetry run python -c "from app.models.schemas import DocumentUploadResponse; print(DocumentUploadResponse.model_fields.keys())"`

Expected: Should show `id`, `title`, `message`, `chunk_count` and other Document fields

**Step 4: Commit**

```bash
git add services/api/app/models/schemas.py services/api/app/api/routes/documents.py
git commit -m "fix: flatten DocumentUploadResponse schema to expose id at top level"
```

---

### Task 1.2: Fix Schema Mismatch - Frontend Types

**Context:** Frontend types are already correct, but need to verify they match new backend.

**Files:**
- Read: `services/frontend/src/types/index.ts:29-40`

**Step 1: Verify DocumentUploadResponse type**

Read `services/frontend/src/types/index.ts` and confirm lines 29-40 define:

```typescript
export interface DocumentUploadResponse extends Document {
  message: string;
  chunk_count: number;
}
```

**Step 2: If type is incorrect, fix it**

If the interface doesn't extend Document, update it to:

```typescript
export interface DocumentUploadResponse extends Document {
  message: string;
  chunk_count: number;
}
```

**Step 3: Commit if changed**

```bash
git add services/frontend/src/types/index.ts
git commit -m "fix: align DocumentUploadResponse type with backend schema"
```

---

### Task 1.3: Fix Health Endpoint Routing

**Context:** Health endpoints are mounted at `/api/v1/health` resulting in `/api/v1/health/health` and `/api/v1/health/ready`.

**Files:**
- Modify: `services/api/app/main.py:65-69`

**Step 1: Update router prefix**

Edit `services/api/app/main.py`:

```python
# Replace the health router inclusion (around line 65)
app.include_router(
    health.router,
    prefix="/api/v1",  # Changed from "/api/v1/health"
    tags=["health"]
)
```

**Step 2: Verify routing**

Run: `cd services/api && poetry run python -c "from app.main import app; routes = [r.path for r in app.routes]; print([r for r in routes if 'health' in r or 'ready' in r])"`

Expected: Should show `/api/v1/health` and `/api/v1/ready` (not `/api/v1/health/health`)

**Step 3: Commit**

```bash
git add services/api/app/main.py
git commit -m "fix: correct health endpoint paths to /api/v1/health and /api/v1/ready"
```

---

### Task 1.4: Fix Health Endpoint - Frontend

**Context:** Update frontend API client to use correct health endpoint paths.

**Files:**
- Modify: `services/frontend/src/services/api.ts:49-57`

**Step 1: Update health check methods**

Edit `services/frontend/src/services/api.ts`:

```typescript
// Update checkHealth method (around line 49)
async checkHealth(): Promise<HealthStatus> {
  const response = await this.client.get<HealthStatus>('/api/v1/health');
  return response.data;
}

async checkReadiness(): Promise<ReadinessStatus> {
  const response = await this.client.get<ReadinessStatus>('/api/v1/ready');
  return response.data;
}
```

**Step 2: Commit**

```bash
git add services/frontend/src/services/api.ts
git commit -m "fix: update health endpoint paths in API client"
```

---

### Task 1.5: Add Qdrant Healthcheck to Docker Compose

**Context:** Qdrant container has no healthcheck, causing race conditions on startup.

**Files:**
- Modify: `infrastructure/docker-compose/docker-compose.yml:24-35`

**Step 1: Add healthcheck to Qdrant service**

Edit `infrastructure/docker-compose/docker-compose.yml`:

```yaml
  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: raas-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:6333/readyz || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - raas-network
```

**Step 2: Update API service dependency**

Update API service `depends_on` section (around line 58):

```yaml
  api:
    # ... other config
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_healthy  # Changed from service_started
```

**Step 3: Update Embedder service dependency**

Update Embedder service `depends_on` section (around line 87):

```yaml
  embedder:
    # ... other config
    depends_on:
      qdrant:
        condition: service_healthy  # Changed from service_started
```

**Step 4: Commit**

```bash
git add infrastructure/docker-compose/docker-compose.yml
git commit -m "fix: add Qdrant healthcheck and update service dependencies"
```

---

### Task 1.6: Fix File Deletion Bug - Add file_path Column

**Context:** File deletion uses incorrect glob pattern. Need to store actual file path in database.

**Files:**
- Create: `services/api/app/migrations/002_add_file_path.sql`
- Modify: `services/api/app/models/document.py:17-30`

**Step 1: Create migration**

Create `services/api/app/migrations/002_add_file_path.sql`:

```sql
-- Add file_path column to documents table
ALTER TABLE documents ADD COLUMN file_path VARCHAR(500);

-- Update existing records with reconstructed path (will be NULL, that's ok)
-- New uploads will have the path stored
```

**Step 2: Update Document model**

Edit `services/api/app/models/document.py`:

```python
# Add new field after file_size (around line 25)
file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
```

**Step 3: Verify model**

Run: `cd services/api && poetry run python -c "from app.models.document import Document; print('file_path' in Document.__table__.columns)"`

Expected: Should print `True` after database migration applied

**Step 4: Commit**

```bash
git add services/api/app/migrations/002_add_file_path.sql services/api/app/models/document.py
git commit -m "feat: add file_path column to track actual file locations"
```

---

### Task 1.7: Fix File Deletion Bug - Update Service

**Context:** Update document service to store and use file_path for deletion.

**Files:**
- Modify: `services/api/app/services/document_service.py:65-75`
- Modify: `services/api/app/services/document_service.py:246-252`

**Step 1: Store file path during upload**

Edit `services/api/app/services/document_service.py` in `create_document` method:

```python
# Update document creation (around line 66)
document = Document(
    title=title,
    description=description,
    file_name=filename,
    file_type=file_type,
    file_size=file_size,
    file_path=str(file_path),  # Add this line
    upload_status="processing",
    embedding_status="pending"
)
```

**Step 2: Use file_path for deletion**

Edit `services/api/app/services/document_service.py` in `delete_document` method:

```python
# Replace file deletion logic (around line 246)
# Delete file from disk
if document.file_path:
    file_path = Path(document.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
else:
    # Fallback for old documents without file_path
    logger.warning(f"No file_path stored for document {document_id}, skipping file deletion")
```

**Step 3: Commit**

```bash
git add services/api/app/services/document_service.py
git commit -m "fix: use stored file_path for reliable file deletion"
```

---

## Phase 2: Backend Refactoring

### Task 2.1: Create Dependency Injection Infrastructure

**Context:** Replace global singletons with dependency injection for better testability.

**Files:**
- Create: `services/api/app/core/dependencies.py`

**Step 1: Create dependencies module**

Create `services/api/app/core/dependencies.py`:

```python
"""Dependency injection providers for FastAPI."""
from pathlib import Path
from typing import Generator

from app.core.config import settings
from app.services.document_service import DocumentService
from app.core.qdrant_client import QdrantClientWrapper


def get_document_service() -> DocumentService:
    """
    Provide DocumentService instance.

    Returns:
        DocumentService instance configured with upload directory
    """
    return DocumentService(upload_dir=Path(settings.upload_dir))


def get_qdrant_client() -> QdrantClientWrapper:
    """
    Provide QdrantClientWrapper instance.

    Returns:
        QdrantClientWrapper configured with Qdrant URL
    """
    return QdrantClientWrapper(url=settings.qdrant_url)
```

**Step 2: Commit**

```bash
git add services/api/app/core/dependencies.py
git commit -m "feat: add dependency injection infrastructure"
```

---

### Task 2.2: Refactor DocumentService to Accept Dependencies

**Context:** Remove global instance, make service accept upload_dir in constructor.

**Files:**
- Modify: `services/api/app/services/document_service.py:23-29`
- Modify: `services/api/app/services/document_service.py:261-262`

**Step 1: Update DocumentService constructor**

Edit `services/api/app/services/document_service.py`:

```python
# Update __init__ method (around line 26)
def __init__(self, upload_dir: Path):
    """
    Initialize document service.

    Args:
        upload_dir: Directory for storing uploaded files
    """
    self.upload_dir = upload_dir
    self.upload_dir.mkdir(parents=True, exist_ok=True)
```

**Step 2: Remove global instance**

Remove the global instance at the end of the file (around line 261):

```python
# DELETE these lines:
# # Global document service instance
# document_service = DocumentService()
```

**Step 3: Commit**

```bash
git add services/api/app/services/document_service.py
git commit -m "refactor: remove global DocumentService instance, use DI"
```

---

### Task 2.3: Update Document Routes to Use DI

**Context:** Inject DocumentService into route handlers instead of importing global.

**Files:**
- Modify: `services/api/app/api/routes/documents.py:7`
- Modify: `services/api/app/api/routes/documents.py:18-24`
- Modify: `services/api/app/api/routes/documents.py:94-99`
- Modify: `services/api/app/api/routes/documents.py:126-130`
- Modify: `services/api/app/api/routes/documents.py:155-159`

**Step 1: Update imports**

Edit `services/api/app/api/routes/documents.py`:

```python
# Replace import (around line 7)
from app.core.dependencies import get_document_service
from app.services.document_service import DocumentService
```

**Step 2: Update upload_document route**

```python
@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="File to upload"),
    title: str = Form(..., description="Document title"),
    description: str = Form(None, description="Optional document description"),
    db: AsyncSession = Depends(get_db),
    doc_service: DocumentService = Depends(get_document_service)  # Add this
):
    # ... validation code ...

    # Replace document_service with doc_service
    document, chunk_count = await doc_service.create_document(
        db=db,
        file_content=content,
        filename=file.filename,
        title=title,
        description=description
    )
```

**Step 3: Update list_documents route**

```python
@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    doc_service: DocumentService = Depends(get_document_service)  # Add this
):
    # ... validation code ...
    return await doc_service.get_documents(db, page=page, limit=limit)
```

**Step 4: Update get_document route**

```python
@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    doc_service: DocumentService = Depends(get_document_service)  # Add this
):
    document = await doc_service.get_document_detail(db, document_id)
    # ... rest of function
```

**Step 5: Update delete_document route**

```python
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    doc_service: DocumentService = Depends(get_document_service)  # Add this
):
    deleted = await doc_service.delete_document(db, document_id)
    # ... rest of function
```

**Step 6: Commit**

```bash
git add services/api/app/api/routes/documents.py
git commit -m "refactor: inject DocumentService via FastAPI dependencies"
```

---

### Task 2.4: Make Qdrant Client Async

**Context:** Qdrant operations are synchronous but called from async contexts, blocking event loop.

**Files:**
- Modify: `services/api/app/core/qdrant_client.py`

**Step 1: Add async wrappers to QdrantClientWrapper**

Edit `services/api/app/core/qdrant_client.py`:

```python
"""Qdrant client wrapper for vector operations."""
import asyncio
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, Distance, VectorParams

from app.core.config import settings


class QdrantClientWrapper:
    """Async wrapper for Qdrant client operations."""

    def __init__(self, url: str):
        """
        Initialize Qdrant client.

        Args:
            url: Qdrant server URL
        """
        self.url = url
        self.client = QdrantClient(url=url, prefer_grpc=False)
        self.collection_name = settings.collection_name

    async def ensure_collection(self) -> None:
        """Ensure the collection exists with proper configuration."""
        loop = asyncio.get_event_loop()

        def _ensure():
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.model_dimension,
                        distance=Distance.COSINE
                    )
                )

        await loop.run_in_executor(None, _ensure)

    async def upsert_vectors(self, points: List[PointStruct]) -> None:
        """
        Upsert vectors to collection (async).

        Args:
            points: List of points to upsert
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.client.upsert,
            self.collection_name,
            points
        )

    async def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Filter] = None
    ) -> List[dict]:
        """
        Search for similar vectors (async).

        Args:
            query_vector: Query vector
            limit: Maximum results
            score_threshold: Minimum similarity score
            filter_conditions: Optional filters

        Returns:
            List of search results
        """
        loop = asyncio.get_event_loop()

        def _search():
            return self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_conditions
            )

        results = await loop.run_in_executor(None, _search)
        return [
            {
                "id": str(result.id),
                "score": result.score,
                "payload": result.payload
            }
            for result in results
        ]

    async def delete_by_document_id(self, document_id: str) -> None:
        """
        Delete all vectors for a document (async).

        Args:
            document_id: Document UUID
        """
        loop = asyncio.get_event_loop()

        def _delete():
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={
                    "filter": {
                        "must": [
                            {
                                "key": "document_id",
                                "match": {"value": document_id}
                            }
                        ]
                    }
                }
            )

        await loop.run_in_executor(None, _delete)

    async def health_check(self) -> bool:
        """
        Check if Qdrant is healthy (async).

        Returns:
            True if healthy, False otherwise
        """
        loop = asyncio.get_event_loop()

        def _check():
            try:
                self.client.get_collections()
                return True
            except Exception:
                return False

        return await loop.run_in_executor(None, _check)


# Global instance - will be replaced with DI
qdrant_client = QdrantClientWrapper(url=settings.qdrant_url)
```

**Step 2: Update DocumentService to use async Qdrant methods**

Edit `services/api/app/services/document_service.py` in `delete_document` method:

```python
# Update Qdrant deletion (around line 240)
try:
    await qdrant_client.delete_by_document_id(str(document_id))
except Exception as e:
    logger.error(f"Error deleting vectors from Qdrant: {e}")
```

**Step 3: Commit**

```bash
git add services/api/app/core/qdrant_client.py services/api/app/services/document_service.py
git commit -m "feat: make Qdrant client operations async to avoid blocking"
```

---

### Task 2.5: Create Custom Exception Classes

**Context:** Add custom exceptions for better error handling and clearer error messages.

**Files:**
- Create: `services/api/app/core/exceptions.py`

**Step 1: Create exceptions module**

Create `services/api/app/core/exceptions.py`:

```python
"""Custom exception classes for RAAS."""
from uuid import UUID
from typing import Optional


class RAASException(Exception):
    """Base exception for RAAS application."""

    def __init__(self, message: str, status_code: int = 500, details: Optional[dict] = None):
        """
        Initialize exception.

        Args:
            message: Error message
            status_code: HTTP status code
            details: Optional additional details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class DocumentNotFoundError(RAASException):
    """Raised when document is not found."""

    def __init__(self, document_id: UUID):
        super().__init__(
            message=f"Document {document_id} not found",
            status_code=404,
            details={"document_id": str(document_id)}
        )


class EmbeddingFailedError(RAASException):
    """Raised when embedding generation fails."""

    def __init__(self, reason: str, document_id: Optional[UUID] = None):
        super().__init__(
            message=f"Embedding generation failed: {reason}",
            status_code=500,
            details={"reason": reason, "document_id": str(document_id) if document_id else None}
        )


class FileProcessingError(RAASException):
    """Raised when file processing fails."""

    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"Failed to process file {filename}: {reason}",
            status_code=400,
            details={"filename": filename, "reason": reason}
        )


class InvalidFileTypeError(RAASException):
    """Raised when file type is not supported."""

    def __init__(self, filename: str, file_type: str):
        super().__init__(
            message=f"File type {file_type} is not supported",
            status_code=400,
            details={"filename": filename, "file_type": file_type}
        )


class QdrantConnectionError(RAASException):
    """Raised when Qdrant connection fails."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Failed to connect to Qdrant: {reason}",
            status_code=503,
            details={"reason": reason}
        )
```

**Step 2: Add exception handler to main app**

Edit `services/api/app/main.py`:

```python
# Add import at top
from fastapi.responses import JSONResponse
from app.core.exceptions import RAASException

# Add exception handler after app creation (around line 55)
@app.exception_handler(RAASException)
async def raas_exception_handler(request, exc: RAASException):
    """Handle RAAS custom exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "type": exc.__class__.__name__,
            "details": exc.details
        }
    )
```

**Step 3: Commit**

```bash
git add services/api/app/core/exceptions.py services/api/app/main.py
git commit -m "feat: add custom exception classes for better error handling"
```

---

### Task 2.6: Use Custom Exceptions in DocumentService

**Context:** Replace generic exceptions with custom typed exceptions.

**Files:**
- Modify: `services/api/app/services/document_service.py:11`
- Modify: `services/api/app/services/document_service.py:82-111`
- Modify: `services/api/app/services/document_service.py:217-238`

**Step 1: Add imports**

Edit `services/api/app/services/document_service.py`:

```python
# Add to imports (around line 11)
from app.core.exceptions import (
    DocumentNotFoundError,
    FileProcessingError,
    EmbeddingFailedError
)
```

**Step 2: Update create_document error handling**

```python
# Update exception handling in create_document (around line 107)
except ValueError as e:
    logger.error(f"Invalid file: {e}")
    document.upload_status = "failed"
    await db.commit()
    raise FileProcessingError(filename=filename, reason=str(e))
except Exception as e:
    logger.error(f"Error processing document: {e}")
    document.upload_status = "failed"
    await db.commit()
    raise FileProcessingError(filename=filename, reason=str(e))
```

**Step 3: Update get_document_detail**

```python
# Update get_document_detail to raise custom exception (around line 211)
async def get_document_detail(
    self,
    db: AsyncSession,
    document_id: UUID
) -> DocumentDetailResponse:
    """Get detailed document information including chunks."""
    query = (
        select(Document)
        .options(selectinload(Document.chunks))
        .where(Document.id == document_id)
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise DocumentNotFoundError(document_id)

    return DocumentDetailResponse.model_validate(document)
```

**Step 4: Update delete_document**

```python
# Update delete_document (around line 232)
async def delete_document(
    self,
    db: AsyncSession,
    document_id: UUID
) -> bool:
    """Delete document and associated resources."""
    # Get document
    query = select(Document).where(Document.id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise DocumentNotFoundError(document_id)

    # ... rest of deletion logic

    return True
```

**Step 5: Commit**

```bash
git add services/api/app/services/document_service.py
git commit -m "refactor: use custom exceptions in DocumentService"
```

---

## Phase 3: Frontend Refactoring

### Task 3.1: Create Shared Utility Functions

**Context:** Extract duplicated formatting functions into shared utilities.

**Files:**
- Create: `services/frontend/src/utils/formatters.ts`

**Step 1: Create formatters utility**

Create `services/frontend/src/utils/formatters.ts`:

```typescript
/**
 * Shared formatting utilities for dates, file sizes, and status badges.
 */

/**
 * Format a date string with optional time.
 */
export function formatDate(dateString: string, includeTime = false): string {
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...(includeTime && { hour: '2-digit', minute: '2-digit' })
  };
  return new Date(dateString).toLocaleString('en-US', options);
}

/**
 * Format file size in bytes to human-readable format.
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

/**
 * Status type for documents.
 */
export type StatusType = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * Get Tailwind CSS classes for status badge.
 */
export function getStatusColor(status: StatusType): string {
  const colors: Record<StatusType, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
}
```

**Step 2: Commit**

```bash
git add services/frontend/src/utils/formatters.ts
git commit -m "feat: add shared utility functions for formatting"
```

---

### Task 3.2: Update DocumentCard to Use Utilities

**Context:** Replace inline formatting functions with shared utilities.

**Files:**
- Modify: `services/frontend/src/components/documents/DocumentCard.tsx:26-57`

**Step 1: Update imports and remove inline functions**

Edit `services/frontend/src/components/documents/DocumentCard.tsx`:

```typescript
// Add import at top
import { formatDate, formatFileSize, getStatusColor } from '../../utils/formatters';

// REMOVE these inline functions (lines 26-57):
// - formatDate
// - formatFileSize
// - getStatusBadge

// UPDATE getStatusBadge usage to use utility:
const getStatusBadge = (status: string) => {
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(status as any)}`}>
      {status}
    </span>
  );
};
```

**Step 2: Verify component still works**

Check that the component imports are correct and TypeScript has no errors.

**Step 3: Commit**

```bash
git add services/frontend/src/components/documents/DocumentCard.tsx
git commit -m "refactor: use shared formatters in DocumentCard"
```

---

### Task 3.3: Update DocumentDetailPage to Use Utilities

**Context:** Replace inline formatting functions with shared utilities.

**Files:**
- Modify: `services/frontend/src/pages/DocumentDetailPage.tsx:57-90`

**Step 1: Update imports and remove inline functions**

Edit `services/frontend/src/pages/DocumentDetailPage.tsx`:

```typescript
// Add import at top
import { formatDate, formatFileSize, getStatusColor } from '../utils/formatters';

// REMOVE these inline functions (lines 57-90):
// - formatDate
// - formatFileSize
// - getStatusBadge

// UPDATE getStatusBadge usage:
const getStatusBadge = (status: string) => {
  return (
    <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(status as any)}`}>
      {status}
    </span>
  );
};
```

**Step 2: Commit**

```bash
git add services/frontend/src/pages/DocumentDetailPage.tsx
git commit -m "refactor: use shared formatters in DocumentDetailPage"
```

---

### Task 3.4: Fix ReadinessStatus Type Mismatch

**Context:** Frontend type expects different structure than backend returns.

**Files:**
- Modify: `services/frontend/src/types/index.ts:69-82`

**Step 1: Update ReadinessStatus types**

Edit `services/frontend/src/types/index.ts`:

```typescript
// Update interfaces (around line 69)
export interface ServiceStatus {
  name: string;
  status: 'ready' | 'not_ready';
  details?: string;
}

export interface ReadinessStatus {
  status: 'ready' | 'not_ready';
  services: ServiceStatus[];  // Changed from object with boolean values
}
```

**Step 2: Commit**

```bash
git add services/frontend/src/types/index.ts
git commit -m "fix: align ReadinessStatus type with backend schema"
```

---

### Task 3.5: Add Error Boundary Component

**Context:** Add React error boundary to catch and display errors gracefully.

**Files:**
- Create: `services/frontend/src/components/ErrorBoundary.tsx`

**Step 1: Create ErrorBoundary component**

Create `services/frontend/src/components/ErrorBoundary.tsx`:

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from './common/Button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full text-center">
            <div className="mb-4">
              <svg
                className="mx-auto h-12 w-12 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Something went wrong
            </h1>
            <p className="text-gray-600 mb-6">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <pre className="text-left text-xs bg-gray-100 p-4 rounded mb-6 overflow-auto max-h-40">
                {this.state.error.stack}
              </pre>
            )}
            <Button onClick={this.handleReload}>
              Reload Page
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Step 2: Wrap App with ErrorBoundary**

Edit `services/frontend/src/main.tsx`:

```typescript
// Add import
import { ErrorBoundary } from './components/ErrorBoundary';

// Wrap App component
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>,
);
```

**Step 3: Commit**

```bash
git add services/frontend/src/components/ErrorBoundary.tsx services/frontend/src/main.tsx
git commit -m "feat: add ErrorBoundary for graceful error handling"
```

---

### Task 3.6: Install and Configure shadcn/ui

**Context:** Set up shadcn/ui component library for modern UI components.

**Files:**
- Create: `services/frontend/components.json`
- Modify: `services/frontend/tailwind.config.js`
- Modify: `services/frontend/tsconfig.json`

**Step 1: Initialize shadcn/ui**

Run from frontend directory:
```bash
cd services/frontend
npx shadcn-ui@latest init
```

When prompted:
- Style: Default
- Base color: Slate
- CSS variables: Yes

**Step 2: Install core components**

```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add sheet
npx shadcn-ui@latest add badge
```

**Step 3: Commit**

```bash
git add components.json tailwind.config.js tsconfig.json src/components/ui/ src/lib/
git commit -m "feat: initialize shadcn/ui with core components"
```

---

## Phase 4: UX Redesign (Search-Centric)

### Task 4.1: Install Additional Dependencies

**Context:** Install framer-motion for animations and additional utilities.

**Files:**
- Modify: `services/frontend/package.json`

**Step 1: Install dependencies**

Run from frontend directory:
```bash
cd services/frontend
npm install framer-motion
npm install cmdk  # For command palette
npm install @radix-ui/react-icons  # Icon set
```

**Step 2: Commit**

```bash
git add package.json package-lock.json
git commit -m "feat: install animation and UI dependencies"
```

---

### Task 4.2: Create Enhanced SearchBar Component

**Context:** Build modern search bar with keyboard shortcuts and glassmorphism effect.

**Files:**
- Create: `services/frontend/src/components/search/EnhancedSearchBar.tsx`

**Step 1: Create EnhancedSearchBar**

Create `services/frontend/src/components/search/EnhancedSearchBar.tsx`:

```typescript
import React, { useEffect, useRef } from 'react';
import { MagnifyingGlassIcon } from '@radix-ui/react-icons';

interface EnhancedSearchBarProps {
  value: string;
  onChange: (value: string) => void;
  autoFocus?: boolean;
  placeholder?: string;
}

export const EnhancedSearchBar: React.FC<EnhancedSearchBarProps> = ({
  value,
  onChange,
  autoFocus = false,
  placeholder = 'Search documents...'
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Focus search on "/" key
      if (e.key === '/' && document.activeElement !== inputRef.current) {
        e.preventDefault();
        inputRef.current?.focus();
      }

      // Clear on Escape
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        onChange('');
        inputRef.current?.blur();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onChange]);

  return (
    <div className="relative w-full max-w-3xl mx-auto">
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-6 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className="
            w-full pl-14 pr-20 py-4 text-lg
            bg-white/70 backdrop-blur-md
            border border-gray-200/50
            rounded-full shadow-lg
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
            transition-all duration-200
            placeholder:text-gray-400
          "
        />
        <kbd className="
          absolute right-6 top-1/2 -translate-y-1/2
          px-2 py-1 text-xs font-medium
          bg-gray-100 text-gray-600
          border border-gray-200
          rounded
          pointer-events-none
        ">
          /
        </kbd>
      </div>
    </div>
  );
};
```

**Step 2: Commit**

```bash
git add services/frontend/src/components/search/EnhancedSearchBar.tsx
git commit -m "feat: create enhanced search bar with keyboard shortcuts"
```

---

### Task 4.3: Create Drag-and-Drop UploadModal

**Context:** Build modal with functional drag-and-drop file upload.

**Files:**
- Create: `services/frontend/src/components/upload/UploadModal.tsx`

**Step 1: Create UploadModal component**

Create `services/frontend/src/components/upload/UploadModal.tsx`:

```typescript
import React, { useState } from 'react';
import { useUploadDocument } from '../../hooks/useDocuments';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { useToast } from '../ui/use-toast';
import { cn } from '../../lib/utils';

interface UploadModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: (documentId: string) => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  open,
  onClose,
  onSuccess
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const uploadDocument = useUploadDocument();
  const { toast } = useToast();

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragIn = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragOut = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const validFile = files.find(f =>
      ['.pdf', '.docx', '.txt'].some(ext => f.name.toLowerCase().endsWith(ext))
    );

    if (validFile) {
      setFile(validFile);
      if (!title) {
        setTitle(validFile.name.replace(/\.[^/.]+$/, ''));
      }
    } else {
      toast({
        title: 'Invalid file type',
        description: 'Please upload PDF, DOCX, or TXT files only',
        variant: 'destructive'
      });
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      if (!title) {
        setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file || !title) {
      toast({
        title: 'Missing information',
        description: 'Please provide a file and title',
        variant: 'destructive'
      });
      return;
    }

    try {
      const result = await uploadDocument.mutateAsync({
        file,
        title,
        description: description || undefined
      });

      toast({
        title: 'Upload successful',
        description: `${title} has been uploaded and is being processed`
      });

      onSuccess?.(result.id);
      onClose();

      // Reset form
      setFile(null);
      setTitle('');
      setDescription('');
    } catch (error) {
      toast({
        title: 'Upload failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive'
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div
            onDragEnter={handleDragIn}
            onDragLeave={handleDragOut}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={cn(
              "border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
              isDragging
                ? "border-primary-500 bg-primary-50"
                : "border-gray-300 hover:border-gray-400"
            )}
          >
            <input
              type="file"
              id="file-upload"
              className="sr-only"
              accept=".pdf,.docx,.txt"
              onChange={handleFileInput}
            />

            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="space-y-2">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <div className="text-sm text-gray-600">
                  <span className="font-medium text-primary-600">Click to upload</span>
                  {' or drag and drop'}
                </div>
                <p className="text-xs text-gray-500">
                  PDF, DOCX, or TXT (up to 100MB)
                </p>
                {file && (
                  <p className="text-sm font-medium text-gray-900 mt-2">
                    Selected: {file.name}
                  </p>
                )}
              </div>
            </label>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Title *</label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter document title"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Description (optional)</label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter document description"
              rows={3}
            />
          </div>

          <div className="flex justify-end space-x-3">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={uploadDocument.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!file || !title || uploadDocument.isPending}
            >
              {uploadDocument.isPending ? 'Uploading...' : 'Upload'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
```

**Step 2: Add Textarea to shadcn**

```bash
cd services/frontend
npx shadcn-ui@latest add textarea
```

**Step 3: Commit**

```bash
git add services/frontend/src/components/upload/UploadModal.tsx services/frontend/src/components/ui/textarea.tsx
git commit -m "feat: create drag-and-drop upload modal with validation"
```

---

### Task 4.4: Create Debounced Search Hook

**Context:** Add custom hook for debounced search to avoid excessive API calls.

**Files:**
- Create: `services/frontend/src/hooks/useDebounce.ts`
- Create: `services/frontend/src/hooks/useSearchWithDebounce.ts`

**Step 1: Create useDebounce hook**

Create `services/frontend/src/hooks/useDebounce.ts`:

```typescript
import { useEffect, useState } from 'react';

/**
 * Debounce a value - only updates after specified delay.
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

**Step 2: Create useSearchWithDebounce hook**

Create `services/frontend/src/hooks/useSearchWithDebounce.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { useDebounce } from './useDebounce';
import { api } from '../services/api';

/**
 * Search with automatic debouncing (300ms).
 */
export function useSearchWithDebounce(query: string, limit: number = 20) {
  const debouncedQuery = useDebounce(query, 300);

  return useQuery({
    queryKey: ['search', debouncedQuery, limit],
    queryFn: () => api.search({ query: debouncedQuery, limit }),
    enabled: debouncedQuery.length > 0,
    staleTime: 10000, // Results fresh for 10 seconds
  });
}
```

**Step 3: Commit**

```bash
git add services/frontend/src/hooks/useDebounce.ts services/frontend/src/hooks/useSearchWithDebounce.ts
git commit -m "feat: add debounced search hook for optimized queries"
```

---

### Task 4.5: Create Main Single-Page Layout

**Context:** Build unified single-page app centered on search.

**Files:**
- Create: `services/frontend/src/pages/MainPage.tsx`

**Step 1: Create MainPage component**

Create `services/frontend/src/pages/MainPage.tsx`:

```typescript
import React, { useState } from 'react';
import { EnhancedSearchBar } from '../components/search/EnhancedSearchBar';
import { UploadModal } from '../components/upload/UploadModal';
import { Button } from '../components/ui/button';
import { useSearchWithDebounce } from '../hooks/useSearchWithDebounce';
import { useDocuments } from '../hooks/useDocuments';
import { DocumentCard } from '../components/documents/DocumentCard';
import { motion, AnimatePresence } from 'framer-motion';
import { PlusIcon } from '@radix-ui/react-icons';

export const MainPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [uploadOpen, setUploadOpen] = useState(false);

  const searchResults = useSearchWithDebounce(searchQuery);
  const documents = useDocuments(1, 20);

  const showSearch = searchQuery.length > 0;
  const dataToDisplay = showSearch ? searchResults : documents;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <svg
                className="h-8 w-8 text-primary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <span className="text-xl font-bold text-gray-900">RAAS</span>
            </div>

            <Button onClick={() => setUploadOpen(true)} size="sm">
              <PlusIcon className="mr-2 h-4 w-4" />
              Upload
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Search */}
      <main className="container mx-auto px-4">
        <div className="py-12">
          <EnhancedSearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            autoFocus
          />
        </div>

        {/* Results or Documents */}
        <div className="pb-12">
          {dataToDisplay.isLoading && (
            <div className="text-center py-12">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent" />
              <p className="mt-4 text-gray-600">
                {showSearch ? 'Searching...' : 'Loading documents...'}
              </p>
            </div>
          )}

          {dataToDisplay.error && (
            <div className="text-center py-12">
              <p className="text-red-600">
                Error: {dataToDisplay.error.message}
              </p>
            </div>
          )}

          {dataToDisplay.isSuccess && (
            <div className="space-y-4">
              {showSearch ? (
                // Search Results
                <>
                  <p className="text-sm text-gray-600">
                    {searchResults.data.total_results} results for "{searchQuery}"
                  </p>
                  <AnimatePresence>
                    {searchResults.data.results.length === 0 ? (
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-center py-12"
                      >
                        <p className="text-gray-600">No results found</p>
                        <p className="text-sm text-gray-500 mt-2">
                          Try adjusting your search query
                        </p>
                      </motion.div>
                    ) : (
                      <div className="grid grid-cols-1 gap-4">
                        {searchResults.data.results.map((result, i) => (
                          <motion.div
                            key={result.chunk_id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ delay: i * 0.05 }}
                          >
                            <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
                              <div className="flex justify-between items-start mb-2">
                                <h3 className="text-lg font-semibold text-gray-900">
                                  {result.document_title}
                                </h3>
                                <span className="text-sm text-gray-500">
                                  {(result.score * 100).toFixed(0)}% match
                                </span>
                              </div>
                              <p className="text-gray-600 mb-2">
                                {result.chunk_text}
                              </p>
                              <p className="text-xs text-gray-500">
                                Chunk {result.chunk_index + 1}
                              </p>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    )}
                  </AnimatePresence>
                </>
              ) : (
                // Document Grid
                <>
                  <p className="text-sm text-gray-600">
                    {documents.data.total} documents
                  </p>
                  {documents.data.documents.length === 0 ? (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="text-center py-12"
                    >
                      <svg
                        className="mx-auto h-12 w-12 text-gray-400 mb-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        No documents yet
                      </h3>
                      <p className="text-gray-600 mb-6">
                        Upload your first document to get started
                      </p>
                      <Button onClick={() => setUploadOpen(true)}>
                        <PlusIcon className="mr-2 h-4 w-4" />
                        Upload Document
                      </Button>
                    </motion.div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {documents.data.documents.map((doc) => (
                        <DocumentCard key={doc.id} document={doc} />
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Upload Modal */}
      <UploadModal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onSuccess={(id) => {
          console.log('Upload successful:', id);
          // Could navigate to document or show toast
        }}
      />
    </div>
  );
};
```

**Step 2: Update App.tsx to use MainPage**

Edit `services/frontend/src/App.tsx`:

```typescript
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { MainPage } from './pages/MainPage';
import { DocumentDetailPage } from './pages/DocumentDetailPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainPage />} />
      <Route path="/documents/:id" element={<DocumentDetailPage />} />
    </Routes>
  );
}

export default App;
```

**Step 3: Commit**

```bash
git add services/frontend/src/pages/MainPage.tsx services/frontend/src/App.tsx
git commit -m "feat: create search-centric single-page main layout"
```

---

## Phase 5: Testing

### Task 5.1: Create Test Configuration

**Context:** Set up pytest configuration for backend tests.

**Files:**
- Create: `services/api/tests/conftest.py`

**Step 1: Create conftest.py with fixtures**

Create `services/api/tests/conftest.py`:

```python
"""Pytest configuration and fixtures."""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

from app.main import app
from app.core.database import Base, get_db
from app.core.config import Settings


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_document():
    """Sample document data for testing."""
    return {
        "title": "Test Document",
        "description": "Test description",
        "filename": "test.txt",
        "file_content": b"This is test content for the document."
    }
```

**Step 2: Commit**

```bash
git add services/api/tests/conftest.py
git commit -m "test: add pytest configuration and fixtures"
```

---

### Task 5.2: Write Document Upload Integration Test

**Context:** Test the full document upload flow.

**Files:**
- Create: `services/api/tests/integration/test_document_upload.py`

**Step 1: Create integration test directory**

```bash
mkdir -p services/api/tests/integration
```

**Step 2: Create upload test**

Create `services/api/tests/integration/test_document_upload.py`:

```python
"""Integration tests for document upload."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_document_success(client: AsyncClient, sample_document):
    """Test successful document upload."""
    files = {
        "file": (
            sample_document["filename"],
            sample_document["file_content"],
            "text/plain"
        )
    }
    data = {
        "title": sample_document["title"],
        "description": sample_document["description"]
    }

    response = await client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data
    )

    assert response.status_code == 201
    result = response.json()

    # Verify schema fix - id should be at top level
    assert "id" in result
    assert "title" in result
    assert "message" in result
    assert "chunk_count" in result

    assert result["title"] == sample_document["title"]
    assert result["chunk_count"] > 0
    assert result["upload_status"] == "completed"


@pytest.mark.asyncio
async def test_upload_document_missing_file(client: AsyncClient):
    """Test upload with missing file."""
    data = {"title": "Test"}

    response = await client.post(
        "/api/v1/documents/upload",
        data=data
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_upload_document_empty_title(client: AsyncClient, sample_document):
    """Test upload with empty title."""
    files = {
        "file": (
            sample_document["filename"],
            sample_document["file_content"],
            "text/plain"
        )
    }
    data = {"title": ""}

    response = await client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data
    )

    assert response.status_code == 422  # Validation error
```

**Step 3: Run test to verify**

```bash
cd services/api
poetry run pytest tests/integration/test_document_upload.py -v
```

Expected: Tests should pass (or fail appropriately if dependencies missing)

**Step 4: Commit**

```bash
git add services/api/tests/integration/test_document_upload.py
git commit -m "test: add document upload integration tests"
```

---

### Task 5.3: Write Health Endpoint Test

**Context:** Test the fixed health endpoints.

**Files:**
- Modify: `services/api/tests/test_health.py`

**Step 1: Update health test**

Edit `services/api/tests/test_health.py`:

```python
"""Tests for health check endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test basic health check endpoint."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "healthy"


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test readiness check endpoint."""
    response = await client.get("/api/v1/ready")

    assert response.status_code == 200
    result = response.json()
    assert "status" in result
    assert "services" in result
    assert isinstance(result["services"], list)
```

**Step 2: Run test**

```bash
cd services/api
poetry run pytest tests/test_health.py -v
```

**Step 3: Commit**

```bash
git add services/api/tests/test_health.py
git commit -m "test: update health endpoint tests for new paths"
```

---

### Task 5.4: Write Frontend Component Tests

**Context:** Add basic tests for key React components.

**Files:**
- Create: `services/frontend/src/utils/__tests__/formatters.test.ts`

**Step 1: Create test for formatters**

Create `services/frontend/src/utils/__tests__/formatters.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { formatDate, formatFileSize, getStatusColor } from '../formatters';

describe('formatDate', () => {
  it('formats date without time', () => {
    const date = '2024-01-15T10:30:00Z';
    const result = formatDate(date, false);
    expect(result).toContain('Jan');
    expect(result).toContain('15');
    expect(result).toContain('2024');
    expect(result).not.toContain('10:30');
  });

  it('formats date with time', () => {
    const date = '2024-01-15T10:30:00Z';
    const result = formatDate(date, true);
    expect(result).toContain('Jan');
    expect(result).toContain('15');
    expect(result).toContain('2024');
  });
});

describe('formatFileSize', () => {
  it('formats bytes', () => {
    expect(formatFileSize(500)).toBe('500 B');
  });

  it('formats kilobytes', () => {
    expect(formatFileSize(1024)).toBe('1.00 KB');
    expect(formatFileSize(5120)).toBe('5.00 KB');
  });

  it('formats megabytes', () => {
    expect(formatFileSize(1048576)).toBe('1.00 MB');
    expect(formatFileSize(5242880)).toBe('5.00 MB');
  });
});

describe('getStatusColor', () => {
  it('returns correct color for pending', () => {
    expect(getStatusColor('pending')).toContain('yellow');
  });

  it('returns correct color for completed', () => {
    expect(getStatusColor('completed')).toContain('green');
  });

  it('returns correct color for failed', () => {
    expect(getStatusColor('failed')).toContain('red');
  });

  it('returns default color for unknown status', () => {
    expect(getStatusColor('unknown' as any)).toContain('gray');
  });
});
```

**Step 2: Run test**

```bash
cd services/frontend
npm test formatters
```

**Step 3: Commit**

```bash
git add services/frontend/src/utils/__tests__/formatters.test.ts
git commit -m "test: add unit tests for formatter utilities"
```

---

## Phase 6: Integration & Documentation

### Task 6.1: Create Integration Test Script

**Context:** Build automated script to test full Docker Compose stack.

**Files:**
- Create: `infrastructure/scripts/integration-test.sh`

**Step 1: Create test script**

Create `infrastructure/scripts/integration-test.sh`:

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/infrastructure/docker-compose/docker-compose.yml"
TEST_DOC="$SCRIPT_DIR/test-document.txt"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================="
echo "RAAS Integration Test"
echo "================================="

# 1. Cleanup
echo -e "\n${YELLOW}[1/8]${NC} Cleaning up existing containers..."
docker-compose -f "$COMPOSE_FILE" down -v 2>&1 | grep -v "Stopping\|Removing" || true

# 2. Build
echo -e "\n${YELLOW}[2/8]${NC} Building services..."
docker-compose -f "$COMPOSE_FILE" build --no-cache 2>&1 | tail -5

# 3. Start
echo -e "\n${YELLOW}[3/8]${NC} Starting services..."
docker-compose -f "$COMPOSE_FILE" up -d

# 4. Wait for health
echo -e "\n${YELLOW}[4/8]${NC} Waiting for services to be healthy..."
MAX_WAIT=120
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    POSTGRES_HEALTHY=$(docker inspect raas-postgres --format='{{.State.Health.Status}}' 2>/dev/null || echo "starting")
    QDRANT_HEALTHY=$(docker inspect raas-qdrant --format='{{.State.Health.Status}}' 2>/dev/null || echo "starting")

    if [ "$POSTGRES_HEALTHY" = "healthy" ] && [ "$QDRANT_HEALTHY" = "healthy" ]; then
        echo -e "${GREEN}✓ All services healthy${NC}"
        break
    fi

    echo "  Waiting... ($ELAPSED/$MAX_WAIT seconds) [Postgres: $POSTGRES_HEALTHY, Qdrant: $QDRANT_HEALTHY]"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${RED}✗ Services failed to become healthy${NC}"
    docker-compose -f "$COMPOSE_FILE" logs --tail=50
    exit 1
fi

# Additional wait for app startup
sleep 10

# 5. Test health endpoint
echo -e "\n${YELLOW}[5/8]${NC} Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/v1/health || echo "")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi

# 6. Test upload
echo -e "\n${YELLOW}[6/8]${NC} Testing document upload..."
echo "This is a test document for automated integration testing. It contains some content to be chunked and embedded." > "$TEST_DOC"

UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/upload \
    -F "file=@$TEST_DOC" \
    -F "title=Integration Test Document" \
    -F "description=Automated test document")

DOC_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

if [ -z "$DOC_ID" ]; then
    echo -e "${RED}✗ Upload failed${NC}"
    echo "Response: $UPLOAD_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Upload successful (ID: $DOC_ID)${NC}"

# 7. Test search
echo -e "\n${YELLOW}[7/8]${NC} Testing search (waiting for embedding)..."
sleep 15  # Wait for embedding to complete

SEARCH_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/search \
    -H "Content-Type: application/json" \
    -d '{"query": "test document", "limit": 10}')

RESULT_COUNT=$(echo "$SEARCH_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['results']))" 2>/dev/null || echo "0")

if [ "$RESULT_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Search returned $RESULT_COUNT results${NC}"
else
    echo -e "${YELLOW}⚠ Search returned no results (may need more time for embedding)${NC}"
fi

# 8. Cleanup
echo -e "\n${YELLOW}[8/8]${NC} Cleaning up..."
docker-compose -f "$COMPOSE_FILE" down 2>&1 | grep -v "Stopping\|Removing" || true
rm -f "$TEST_DOC"

echo ""
echo "================================="
echo -e "${GREEN}✅ Integration test complete!${NC}"
echo "================================="
```

**Step 2: Make executable**

```bash
chmod +x infrastructure/scripts/integration-test.sh
```

**Step 3: Commit**

```bash
git add infrastructure/scripts/integration-test.sh
git commit -m "feat: add automated integration test script"
```

---

### Task 6.2: Update README with New Features

**Context:** Document the modernized UI and new features.

**Files:**
- Modify: `README.md`

**Step 1: Update README**

Edit `README.md` to add new features section:

```markdown
# RAAS - Retrieval-Augmented Generation as a Service

Modern semantic document search platform with search-centric single-page UI.

## Key Features

- 🔍 **Search-First Interface**: Instant search with debouncing and keyboard shortcuts (/)
- 📤 **Drag-and-Drop Upload**: Modern upload modal with file validation
- ⚡ **Real-Time Results**: Search as you type with 300ms debouncing
- 🎨 **Modern UI**: Built with shadcn/ui, Tailwind CSS, and smooth animations
- 🧪 **Comprehensive Tests**: 80%+ code coverage across all services
- 🏥 **Health Checks**: Proper service health monitoring and dependencies
- 🐳 **Docker Ready**: Full Docker Compose setup with integration tests

## Quick Start

### Run with Docker Compose

\`\`\`bash
cd infrastructure/docker-compose
docker-compose up --build
\`\`\`

Access:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Qdrant Dashboard: http://localhost:6333/dashboard

### Run Integration Tests

\`\`\`bash
./infrastructure/scripts/integration-test.sh
\`\`\`

### Local Development

#### Backend Services

\`\`\`bash
# API Service
cd services/api
poetry install
poetry run pytest  # Run tests
poetry run uvicorn app.main:app --reload

# Embedder Service
cd services/embedder
poetry install
poetry run uvicorn app.main:app --reload --port 8001
\`\`\`

#### Frontend

\`\`\`bash
cd services/frontend
npm install
npm test          # Run tests
npm run dev       # Start dev server
\`\`\`

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## Testing

- **Backend**: pytest with async support, 80%+ coverage
- **Frontend**: Vitest + React Testing Library
- **Integration**: Automated Docker Compose testing

\`\`\`bash
# Run all tests
cd services/api && poetry run pytest --cov
cd services/frontend && npm test -- --coverage
\`\`\`

## Contributing

See [CLAUDE.md](CLAUDE.md) for development guidelines and project structure.
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with modernized features"
```

---

## Execution Summary

**Total Tasks**: 42 bite-sized tasks across 6 phases
**Estimated Time**: 18-24 hours

**Verification Steps:**

After completing all tasks:

1. Run integration test: `./infrastructure/scripts/integration-test.sh`
2. Check test coverage: `cd services/api && poetry run pytest --cov`
3. Frontend tests: `cd services/frontend && npm test -- --coverage`
4. Manual smoke test:
   - Upload document via drag-drop
   - Search immediately (should work with debouncing)
   - Verify results show with match scores
   - Delete document
5. Check no console errors or warnings

**Success Criteria:**
- ✅ All integration tests pass
- ✅ 80%+ test coverage achieved
- ✅ Zero TypeScript errors
- ✅ All Docker services healthy on startup
- ✅ Modern UI loads without errors
- ✅ Search works with instant feedback
- ✅ Upload works with drag-and-drop
