# RAAS Comprehensive Quality Improvements

**Date:** 2025-10-23
**Status:** Approved
**Scope:** All three microservices (API, Embedder, Frontend)

## Executive Summary

This design addresses critical bugs, structural issues, and user experience in the RAAS platform. The improvements focus on ensuring bug-free operation, proper project structure, and modern UX design while maintaining pragmatic simplicity.

## Goals

1. **Bug-Free Operation** - Fix all identified bugs and prevent future issues
2. **Code Quality** - Improve maintainability through proper structure and patterns
3. **Modern UX** - Transform into a search-centric, single-page application
4. **Comprehensive Testing** - Achieve 80%+ test coverage across all services
5. **Production Readiness** - Ensure reliable deployment with proper health checks

## Issues Identified

### Critical Bugs

1. **Schema Mismatch (P0)** - `DocumentUploadResponse` structure differs between frontend and backend
   - Backend: `{document: {...}, message, chunk_count}`
   - Frontend expects: `{id, title, ..., message, chunk_count}`
   - Impact: Upload navigation broken, shows `/documents/undefined`

2. **Health Endpoint Path (P1)** - Inconsistent API paths
   - Current: `/api/v1/health/health` and `/api/v1/health/ready`
   - Expected: `/api/v1/health` and `/api/v1/ready`

3. **Missing Qdrant Healthcheck (P0)** - Services start before Qdrant ready
   - docker-compose.yml missing healthcheck for Qdrant
   - API/Embedder use `service_started` instead of `service_healthy`
   - Impact: Race condition on startup

4. **File Deletion Bug (P1)** - Document files not properly deleted
   - `document_service.py:247` uses incorrect glob pattern
   - Pattern `{document_id}*` doesn't match stored filename format

### Backend Structural Issues

5. **Global Singletons** - Services instantiated at module level
   - `document_service = DocumentService()` in `services/document_service.py`
   - `embedding_service = EmbeddingService()` in `services/embedding_service.py`
   - Impact: Difficult to test, hidden dependencies

6. **Blocking Qdrant Operations** - Synchronous calls in async contexts
   - `qdrant_client.upsert_vectors()` is sync but called from async functions
   - Blocks event loop during vector operations

7. **Weak Error Handling** - Generic exceptions without context
   - No custom exception classes
   - Inconsistent error logging
   - Missing request tracing

### Frontend Quality Issues

8. **Code Duplication** - Utility functions repeated across components
   - `formatDate`, `formatFileSize`, `getStatusBadge` duplicated
   - Located in: `DocumentCard.tsx`, `DocumentDetailPage.tsx`

9. **Type Mismatches** - TypeScript types don't match backend schemas
   - `ReadinessStatus` expects different structure than API returns

10. **Missing Drag-and-Drop** - Upload form shows "drag and drop" but doesn't work
    - Only file input button functional

11. **No Error Boundary** - React errors cause white screen
    - No top-level error handling

12. **Dated UX Design** - Multi-page navigation with friction
    - Search buried on separate page
    - Upload requires navigation away
    - Standard card/form design

## Design Solutions

### Section 1: Critical Bug Fixes

#### 1.1 Schema Alignment

**Backend Changes:**
```python
# Before (schemas.py)
class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    message: str
    chunk_count: int

# After (schemas.py)
class DocumentUploadResponse(DocumentResponse):
    """Flat response extending DocumentResponse."""
    message: str
    chunk_count: int
```

**Endpoint Update:**
```python
# documents.py
return DocumentUploadResponse(
    **DocumentResponse.model_validate(document).model_dump(),
    message="Document uploaded and processed successfully",
    chunk_count=chunk_count
)
```

**Frontend Update:**
```typescript
// types/index.ts - Already correct, just needs backend fix
export interface DocumentUploadResponse extends Document {
  message: string;
  chunk_count: number;
}
```

#### 1.2 Health Endpoint Restructuring

**Backend Changes:**
```python
# main.py
# Before
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])

# After
app.include_router(health.router, prefix="/api/v1", tags=["health"])
```

**Frontend Update:**
```typescript
// api.ts
async checkHealth(): Promise<HealthStatus> {
  const response = await this.client.get<HealthStatus>('/api/v1/health');
  return response.data;
}

async checkReadiness(): Promise<ReadinessStatus> {
  const response = await this.client.get<ReadinessStatus>('/api/v1/ready');
  return response.data;
}
```

#### 1.3 Docker Compose Reliability

**Qdrant Healthcheck:**
```yaml
qdrant:
  image: qdrant/qdrant:v1.7.4
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:6333/readyz || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 30s
```

**Service Dependencies:**
```yaml
api:
  depends_on:
    postgres:
      condition: service_healthy
    qdrant:
      condition: service_healthy  # Changed from service_started

embedder:
  depends_on:
    qdrant:
      condition: service_healthy  # Changed from service_started
```

#### 1.4 File Deletion Fix

**Track File Path in Database:**
```python
# document.py - Add column
file_path: Mapped[str] = mapped_column(String, nullable=True)

# document_service.py - Store path
document = Document(
    # ... existing fields
    file_path=str(file_path)
)

# Delete using stored path
if document.file_path:
    file_path = Path(document.file_path)
    if file_path.exists():
        file_path.unlink()
```

### Section 2: Backend Refactoring

#### 2.1 Dependency Injection

**Service Factory Functions:**
```python
# services/document_service.py
class DocumentService:
    def __init__(self, upload_dir: Path):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

# New dependencies.py
from app.core.config import settings

def get_document_service() -> DocumentService:
    return DocumentService(upload_dir=Path(settings.upload_dir))

def get_embedding_service() -> EmbeddingService:
    service = EmbeddingService()
    if not service.model_loaded:
        service.load_model()
    return service
```

**Route Updates:**
```python
# routes/documents.py
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    db: AsyncSession = Depends(get_db),
    doc_service: DocumentService = Depends(get_document_service)
):
    document, chunk_count = await doc_service.create_document(...)
```

#### 2.2 Async Qdrant Operations

**Make Qdrant Client Async:**
```python
# core/qdrant_client.py
class QdrantClientWrapper:
    def __init__(self, url: str):
        self.client = QdrantClient(url=url, prefer_grpc=False)

    async def upsert_vectors(self, points: List[PointStruct]) -> None:
        """Async wrapper for upsert."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.client.upsert,
            settings.collection_name,
            points
        )

    async def health_check(self) -> bool:
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, self.client.get_collections)
            return True
        except Exception:
            return False
```

#### 2.3 Custom Exceptions

**New exceptions.py:**
```python
# core/exceptions.py
class RAASException(Exception):
    """Base exception for RAAS."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class DocumentNotFoundError(RAASException):
    def __init__(self, document_id: UUID):
        super().__init__(
            f"Document {document_id} not found",
            status_code=404
        )

class EmbeddingFailedError(RAASException):
    def __init__(self, reason: str):
        super().__init__(
            f"Embedding generation failed: {reason}",
            status_code=500
        )

class FileProcessingError(RAASException):
    def __init__(self, filename: str, reason: str):
        super().__init__(
            f"Failed to process file {filename}: {reason}",
            status_code=400
        )
```

**Exception Handler:**
```python
# main.py
@app.exception_handler(RAASException)
async def raas_exception_handler(request: Request, exc: RAASException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "type": exc.__class__.__name__
        }
    )
```

#### 2.4 Structured Logging

**Add Request ID Middleware:**
```python
# middleware/request_id.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# main.py
app.add_middleware(RequestIDMiddleware)
```

**Structured Logger:**
```python
# core/logging.py
import logging
import json
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id', default='')

class StructuredLogger(logging.Logger):
    def _log(self, level, msg, args, **kwargs):
        extra = kwargs.get('extra', {})
        extra['request_id'] = request_id_var.get()
        kwargs['extra'] = extra
        super()._log(level, msg, args, **kwargs)
```

### Section 3: Frontend Refactoring

#### 3.1 Shared Utilities

**Create utils/formatters.ts:**
```typescript
// utils/formatters.ts
export function formatDate(dateString: string, includeTime = false): string {
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...(includeTime && { hour: '2-digit', minute: '2-digit' })
  };
  return new Date(dateString).toLocaleString('en-US', options);
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

export type StatusType = 'pending' | 'processing' | 'completed' | 'failed';

export function getStatusColor(status: StatusType): string {
  const colors = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
}
```

#### 3.2 Type Safety

**Auto-generate types from OpenAPI schema:**
```bash
# Add to package.json scripts
"generate-types": "openapi-typescript http://localhost:8000/openapi.json -o src/types/api.ts"
```

**Or manually align types:**
```typescript
// types/index.ts
export interface ServiceStatus {
  name: string;
  status: 'ready' | 'not_ready';
  details?: string;
}

export interface ReadinessStatus {
  status: 'ready' | 'not_ready';
  services: ServiceStatus[];  // Fixed: was expecting booleans
}
```

#### 3.3 Error Boundary

**Create ErrorBoundary component:**
```typescript
// components/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Something went wrong
            </h1>
            <p className="text-gray-600 mb-4">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-primary-600 text-white rounded-md"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Section 4: Modern UX Redesign

#### 4.1 Single-Page Architecture

**New Component Structure:**
```
src/
├── pages/
│   └── MainPage.tsx              # Single unified page
├── components/
│   ├── search/
│   │   ├── SearchBar.tsx         # Hero search (always visible)
│   │   ├── SearchResults.tsx     # Results list
│   │   └── SearchFilters.tsx     # Side panel filters
│   ├── documents/
│   │   ├── DocumentGrid.tsx      # Grid view (when no search)
│   │   ├── DocumentCard.tsx      # Compact card
│   │   └── DocumentSlideOver.tsx # Detail slide-over panel
│   ├── upload/
│   │   └── UploadModal.tsx       # Modal with drag-drop
│   └── layout/
│       ├── Header.tsx            # Minimal header
│       └── CommandPalette.tsx    # Cmd+K interface
```

**Main Page Layout:**
```typescript
// pages/MainPage.tsx
export const MainPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <Header onUploadClick={() => setUploadOpen(true)} />

      <main className="container mx-auto px-4 py-8">
        {/* Hero Search */}
        <div className="max-w-3xl mx-auto mb-12">
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            autoFocus
          />
        </div>

        {/* Results or Document Grid */}
        {searchQuery ? (
          <SearchResults
            query={searchQuery}
            onDocumentClick={setSelectedDoc}
          />
        ) : (
          <DocumentGrid onDocumentClick={setSelectedDoc} />
        )}
      </main>

      {/* Modals & Slide-overs */}
      <UploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />
      <DocumentSlideOver
        documentId={selectedDoc}
        onClose={() => setSelectedDoc(null)}
      />

      <CommandPalette />
    </div>
  );
};
```

#### 4.2 shadcn/ui Integration

**Installation:**
```bash
cd services/frontend
npx shadcn-ui@latest init
```

**Install Components:**
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add sheet  # For slide-over
npx shadcn-ui@latest add command  # For command palette
```

**Component Migration:**
- Replace `components/common/Button.tsx` with shadcn Button
- Replace `components/common/Card.tsx` with shadcn Card
- Replace `components/common/Input.tsx` with shadcn Input
- Replace `components/common/Modal.tsx` with shadcn Dialog
- Add Toast notifications for feedback

#### 4.3 Drag-and-Drop Implementation

**UploadModal with Drag-Drop:**
```typescript
// components/upload/UploadModal.tsx
export const UploadModal: React.FC<Props> = ({ open, onClose }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);

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
      ['.pdf', '.docx', '.txt'].some(ext => f.name.endsWith(ext))
    );

    if (validFile) {
      setFile(validFile);
    } else {
      toast.error('Please upload PDF, DOCX, or TXT files only');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
        </DialogHeader>

        <div
          onDragEnter={handleDragIn}
          onDragLeave={handleDragOut}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={cn(
            "border-2 border-dashed rounded-lg p-8 text-center transition-colors",
            isDragging ? "border-primary-500 bg-primary-50" : "border-gray-300"
          )}
        >
          {/* Upload UI */}
        </div>
      </DialogContent>
    </Dialog>
  );
};
```

#### 4.4 Modern Visual Design

**Glassmorphism Search Bar:**
```typescript
// components/search/SearchBar.tsx
<div className="relative">
  <input
    type="text"
    placeholder="Search documents..."
    className="
      w-full px-6 py-4 text-lg
      bg-white/70 backdrop-blur-md
      border border-gray-200/50
      rounded-full shadow-lg
      focus:outline-none focus:ring-2 focus:ring-primary-500
      transition-all duration-200
    "
  />
  <kbd className="absolute right-4 top-4 px-2 py-1 text-xs bg-gray-100 rounded">
    /
  </kbd>
</div>
```

**Smooth Animations:**
```typescript
// Add framer-motion
import { motion, AnimatePresence } from 'framer-motion';

<AnimatePresence>
  {results.map((result, i) => (
    <motion.div
      key={result.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ delay: i * 0.05 }}
    >
      <DocumentCard document={result} />
    </motion.div>
  ))}
</AnimatePresence>
```

**Dark Mode:**
```typescript
// Add next-themes
import { ThemeProvider } from 'next-themes';

// main.tsx
<ThemeProvider attribute="class" defaultTheme="system">
  <App />
</ThemeProvider>

// tailwind.config.js - Already configured by shadcn
```

#### 4.5 UX Enhancements

**Search-as-you-type with Debouncing:**
```typescript
// hooks/useSearch.ts
import { useDebounce } from '@/hooks/useDebounce';

export function useSearchResults(query: string) {
  const debouncedQuery = useDebounce(query, 300);

  return useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: () => api.search({ query: debouncedQuery, limit: 20 }),
    enabled: debouncedQuery.length > 0,
  });
}
```

**Keyboard Navigation:**
```typescript
// components/search/SearchResults.tsx
const [selectedIndex, setSelectedIndex] = useState(0);

useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      setSelectedIndex(i => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      setSelectedIndex(i => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      onDocumentClick(results[selectedIndex].id);
    }
  };

  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [selectedIndex, results]);
```

**Empty States:**
```typescript
// components/documents/EmptyState.tsx
export const EmptyState: React.FC<{ type: 'no-documents' | 'no-results' }> = ({ type }) => {
  const content = {
    'no-documents': {
      icon: <FileIcon className="w-16 h-16 text-gray-400" />,
      title: 'No documents yet',
      description: 'Upload your first document to get started',
      action: <Button onClick={onUpload}>Upload Document</Button>
    },
    'no-results': {
      icon: <SearchIcon className="w-16 h-16 text-gray-400" />,
      title: 'No results found',
      description: 'Try adjusting your search query',
    }
  };

  return (
    <div className="text-center py-12">
      {content[type].icon}
      <h3 className="text-xl font-semibold mt-4">{content[type].title}</h3>
      <p className="text-gray-600 mt-2">{content[type].description}</p>
      {content[type].action && <div className="mt-6">{content[type].action}</div>}
    </div>
  );
};
```

### Section 5: Testing Strategy

#### 5.1 Backend Tests

**Test Structure:**
```
services/api/tests/
├── conftest.py              # Fixtures
├── unit/
│   ├── test_services.py     # Service layer
│   ├── test_chunking.py     # Chunking logic
│   └── test_schemas.py      # Pydantic validation
├── integration/
│   ├── test_documents.py    # Document endpoints
│   ├── test_search.py       # Search endpoints
│   └── test_health.py       # Health endpoints
└── e2e/
    └── test_pipeline.py     # Full upload→search flow
```

**Fixtures (conftest.py):**
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from httpx import AsyncClient
from app.main import app
from app.core.database import Base

@pytest.fixture
async def db_session():
    """Test database session."""
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_raas")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client():
    """Test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sample_document():
    """Factory for test documents."""
    return {
        "title": "Test Document",
        "description": "Test description",
        "file_content": b"Test content",
        "filename": "test.txt"
    }
```

**Unit Test Example:**
```python
# tests/unit/test_services.py
@pytest.mark.asyncio
async def test_create_document(db_session, sample_document):
    service = DocumentService(upload_dir=Path("/tmp/test"))

    document, chunk_count = await service.create_document(
        db=db_session,
        **sample_document
    )

    assert document.title == "Test Document"
    assert document.upload_status == "completed"
    assert chunk_count > 0
```

**Integration Test Example:**
```python
# tests/integration/test_documents.py
@pytest.mark.asyncio
async def test_upload_document_endpoint(client):
    files = {"file": ("test.txt", b"Test content", "text/plain")}
    data = {"title": "Test", "description": "Description"}

    response = await client.post("/api/v1/documents/upload", files=files, data=data)

    assert response.status_code == 201
    result = response.json()
    assert result["title"] == "Test"
    assert result["chunk_count"] > 0
    assert "id" in result  # Check schema fix
```

**E2E Test Example:**
```python
# tests/e2e/test_pipeline.py
@pytest.mark.asyncio
async def test_full_pipeline(client):
    # 1. Upload
    upload_response = await client.post("/api/v1/documents/upload", ...)
    doc_id = upload_response.json()["id"]

    # 2. Wait for embedding
    for _ in range(30):
        doc = await client.get(f"/api/v1/documents/{doc_id}")
        if doc.json()["embedding_status"] == "completed":
            break
        await asyncio.sleep(1)

    # 3. Search
    search_response = await client.post("/api/v1/search", json={"query": "test"})
    results = search_response.json()["results"]

    # 4. Verify document in results
    assert any(r["document_id"] == doc_id for r in results)

    # 5. Delete
    delete_response = await client.delete(f"/api/v1/documents/{doc_id}")
    assert delete_response.status_code == 204
```

#### 5.2 Frontend Tests

**Test Structure:**
```
services/frontend/src/
├── __tests__/
│   ├── components/
│   │   ├── SearchBar.test.tsx
│   │   ├── DocumentCard.test.tsx
│   │   └── UploadModal.test.tsx
│   ├── hooks/
│   │   ├── useDocuments.test.ts
│   │   └── useSearch.test.ts
│   └── utils/
│       └── formatters.test.ts
└── e2e/
    └── main-flow.spec.ts
```

**Component Test Example:**
```typescript
// __tests__/components/SearchBar.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SearchBar } from '@/components/search/SearchBar';

describe('SearchBar', () => {
  it('calls onChange with debounced value', async () => {
    const onChange = vi.fn();
    render(<SearchBar value="" onChange={onChange} />);

    const input = screen.getByPlaceholderText('Search documents...');
    fireEvent.change(input, { target: { value: 'test query' } });

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('test query');
    }, { timeout: 500 });
  });

  it('focuses on "/" key press', () => {
    render(<SearchBar value="" onChange={() => {}} />);

    fireEvent.keyDown(document, { key: '/' });

    expect(screen.getByPlaceholderText('Search documents...')).toHaveFocus();
  });
});
```

**Hook Test Example:**
```typescript
// __tests__/hooks/useDocuments.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useDocuments } from '@/hooks/useDocuments';
import { api } from '@/services/api';

vi.mock('@/services/api');

describe('useDocuments', () => {
  it('fetches documents successfully', async () => {
    const mockDocuments = { documents: [], total: 0, page: 1, limit: 20 };
    vi.mocked(api.listDocuments).mockResolvedValue(mockDocuments);

    const wrapper = ({ children }) => (
      <QueryClientProvider client={new QueryClient()}>
        {children}
      </QueryClientProvider>
    );

    const { result } = renderHook(() => useDocuments(1, 20), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockDocuments);
  });
});
```

**E2E Test Example:**
```typescript
// e2e/main-flow.spec.ts
import { test, expect } from '@playwright/test';

test('full user flow', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Upload document
  await page.click('button:has-text("Upload")');
  await page.setInputFiles('input[type="file"]', 'test-document.txt');
  await page.fill('input[placeholder="Enter document title"]', 'Test Doc');
  await page.click('button:has-text("Upload")');

  // Wait for success
  await expect(page.locator('text=Upload successful')).toBeVisible();

  // Search for document
  await page.fill('input[placeholder="Search documents..."]', 'test');
  await expect(page.locator('text=Test Doc')).toBeVisible();

  // Click to view details
  await page.click('text=Test Doc');
  await expect(page.locator('text=Document Information')).toBeVisible();
});
```

#### 5.3 Test Commands

**Backend:**
```bash
# Run all tests
cd services/api
poetry run pytest

# With coverage
poetry run pytest --cov=app --cov-report=html --cov-report=term

# Specific test
poetry run pytest tests/integration/test_documents.py::test_upload -v

# Watch mode
poetry run ptw -- --testmon
```

**Frontend:**
```bash
# Unit tests
cd services/frontend
npm test

# Coverage
npm test -- --coverage

# E2E tests
npm run test:e2e

# Watch mode
npm test -- --watch
```

### Section 6: Integration Testing

#### 6.1 Docker Compose Test Script

**Create infrastructure/scripts/integration-test.sh:**
```bash
#!/bin/bash
set -e

COMPOSE_FILE="infrastructure/docker-compose/docker-compose.yml"
TEST_DOC="infrastructure/scripts/test-document.txt"

echo "🧪 Starting RAAS Integration Test"
echo "================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Cleanup
echo "📦 Cleaning up existing containers..."
docker-compose -f $COMPOSE_FILE down -v

# 2. Build
echo "🔨 Building services..."
docker-compose -f $COMPOSE_FILE build --no-cache

# 3. Start services
echo "🚀 Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# 4. Wait for health checks
echo "⏳ Waiting for services to be healthy..."
MAX_WAIT=120
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    HEALTH=$(docker-compose -f $COMPOSE_FILE ps | grep -c "healthy" || echo "0")
    if [ "$HEALTH" -ge 3 ]; then
        echo -e "${GREEN}✓ All services healthy${NC}"
        break
    fi
    echo "  Waiting... ($ELAPSED/$MAX_WAIT seconds)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${RED}✗ Services failed to become healthy${NC}"
    docker-compose -f $COMPOSE_FILE logs
    exit 1
fi

# 5. Run tests
echo "🧪 Running integration tests..."

# Test 1: Health check
echo "  - Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/v1/health)
if echo $HEALTH_RESPONSE | grep -q "healthy"; then
    echo -e "    ${GREEN}✓ Health check passed${NC}"
else
    echo -e "    ${RED}✗ Health check failed${NC}"
    exit 1
fi

# Test 2: Upload document
echo "  - Testing document upload..."
echo "This is a test document for integration testing." > $TEST_DOC
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/upload \
    -F "file=@$TEST_DOC" \
    -F "title=Integration Test Document" \
    -F "description=Test document for automated integration testing")

DOC_ID=$(echo $UPLOAD_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

if [ -z "$DOC_ID" ]; then
    echo -e "    ${RED}✗ Upload failed${NC}"
    echo "    Response: $UPLOAD_RESPONSE"
    exit 1
fi
echo -e "    ${GREEN}✓ Upload successful (ID: $DOC_ID)${NC}"

# Test 3: Wait for embedding
echo "  - Waiting for embedding generation..."
MAX_EMBED_WAIT=60
EMBED_ELAPSED=0

while [ $EMBED_ELAPSED -lt $MAX_EMBED_WAIT ]; do
    DOC_STATUS=$(curl -s http://localhost:8000/api/v1/documents/$DOC_ID | \
        python3 -c "import sys, json; print(json.load(sys.stdin)['embedding_status'])" 2>/dev/null || echo "")

    if [ "$DOC_STATUS" = "completed" ]; then
        echo -e "    ${GREEN}✓ Embedding completed${NC}"
        break
    fi
    sleep 2
    EMBED_ELAPSED=$((EMBED_ELAPSED + 2))
done

if [ "$DOC_STATUS" != "completed" ]; then
    echo -e "    ${RED}✗ Embedding did not complete in time${NC}"
    exit 1
fi

# Test 4: Search
echo "  - Testing search..."
SEARCH_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/search \
    -H "Content-Type: application/json" \
    -d '{"query": "integration testing", "limit": 10}')

RESULT_COUNT=$(echo $SEARCH_RESPONSE | python3 -c "import sys, json; print(len(json.load(sys.stdin)['results']))" 2>/dev/null || echo "0")

if [ "$RESULT_COUNT" -gt 0 ]; then
    echo -e "    ${GREEN}✓ Search returned $RESULT_COUNT results${NC}"
else
    echo -e "    ${RED}✗ Search returned no results${NC}"
    exit 1
fi

# Test 5: Delete document
echo "  - Testing document deletion..."
DELETE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
    http://localhost:8000/api/v1/documents/$DOC_ID)

if [ "$DELETE_RESPONSE" = "204" ]; then
    echo -e "    ${GREEN}✓ Document deleted${NC}"
else
    echo -e "    ${RED}✗ Delete failed (HTTP $DELETE_RESPONSE)${NC}"
    exit 1
fi

# Test 6: Verify deletion
echo "  - Verifying document was removed..."
VERIFY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    http://localhost:8000/api/v1/documents/$DOC_ID)

if [ "$VERIFY_RESPONSE" = "404" ]; then
    echo -e "    ${GREEN}✓ Document not found (correctly deleted)${NC}"
else
    echo -e "    ${RED}✗ Document still exists${NC}"
    exit 1
fi

# 7. Check logs for errors
echo "🔍 Checking logs for errors..."
ERROR_COUNT=$(docker-compose -f $COMPOSE_FILE logs | grep -i "error" | grep -v "ERROR_" | wc -l || echo "0")

if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${RED}⚠ Found $ERROR_COUNT error messages in logs${NC}"
    docker-compose -f $COMPOSE_FILE logs | grep -i "error" | grep -v "ERROR_"
else
    echo -e "${GREEN}✓ No errors in logs${NC}"
fi

# 8. Cleanup
echo "🧹 Cleaning up..."
docker-compose -f $COMPOSE_FILE down
rm -f $TEST_DOC

echo ""
echo "================================="
echo -e "${GREEN}✅ All integration tests passed!${NC}"
echo "================================="
```

**Make executable:**
```bash
chmod +x infrastructure/scripts/integration-test.sh
```

### Section 7: Documentation

#### 7.1 API Documentation

**Enhance OpenAPI with examples:**
```python
# routes/documents.py
@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Document uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "My Document",
                        "file_name": "document.pdf",
                        "message": "Document uploaded and processed successfully",
                        "chunk_count": 15,
                        "embedding_status": "pending"
                    }
                }
            }
        },
        400: {"description": "Invalid file or parameters"},
        500: {"description": "Server error during processing"}
    }
)
async def upload_document(...):
```

#### 7.2 Architecture Documentation

**Create docs/architecture.md:**
```markdown
# RAAS Architecture

## Overview
RAAS is a microservices-based semantic document search platform.

## Services

### API Service (Port 8000)
- **Technology:** FastAPI, SQLAlchemy, asyncpg
- **Responsibilities:**
  - Document upload and metadata storage
  - Orchestration between embedder and search
  - RESTful API gateway

### Embedder Service (Port 8001)
- **Technology:** FastAPI, sentence-transformers, Qdrant
- **Responsibilities:**
  - Generate 384-dim embeddings using all-MiniLM-L6-v2
  - Store vectors in Qdrant
  - Provide query embedding for search

### Frontend (Port 3000)
- **Technology:** React 18, TypeScript, Vite, Tailwind, shadcn/ui
- **Responsibilities:**
  - Single-page search-centric interface
  - Document upload via drag-drop
  - Real-time search with debouncing

## Data Flow

[Include the ASCII diagram of upload and search flow]

## Deployment

[Docker Compose and Kubernetes details]
```

#### 7.3 Developer Guide

**Update README.md:**
```markdown
# RAAS - Retrieval-Augmented Generation as a Service

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### Run with Docker Compose
\`\`\`bash
cd infrastructure/docker-compose
docker-compose up --build
\`\`\`

Services:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Qdrant Dashboard: http://localhost:6333/dashboard

### Run Integration Tests
\`\`\`bash
./infrastructure/scripts/integration-test.sh
\`\`\`

### Local Development

#### Backend
\`\`\`bash
cd services/api
poetry install
poetry run pytest  # Run tests
poetry run uvicorn app.main:app --reload
\`\`\`

#### Frontend
\`\`\`bash
cd services/frontend
npm install
npm test  # Run tests
npm run dev
\`\`\`

## Key Features
- 🔍 Search-centric single-page interface
- 📤 Drag-and-drop document upload
- ⚡ Real-time search with instant feedback
- 🎨 Modern UI with dark mode support
- ⌨️ Keyboard-first navigation (/, Cmd+K)
- 🧪 Comprehensive test coverage (80%+)

## Architecture
See [docs/architecture.md](docs/architecture.md)

## Contributing
See [docs/contributing.md](docs/contributing.md)
```

## Implementation Priority

### Phase 1: Critical Bug Fixes (Immediate)
1. Schema mismatch fix
2. Health endpoint restructuring
3. Docker Compose reliability
4. File deletion bug

**Timeline:** 1-2 hours
**Success Criteria:** All services start cleanly, upload works end-to-end

### Phase 2: Backend Refactoring (High Priority)
1. Dependency injection
2. Async Qdrant operations
3. Custom exceptions
4. Structured logging

**Timeline:** 3-4 hours
**Success Criteria:** No global singletons, proper error handling, traceable logs

### Phase 3: Frontend Refactoring (High Priority)
1. Shared utilities
2. Type safety fixes
3. Error boundary
4. shadcn/ui integration

**Timeline:** 2-3 hours
**Success Criteria:** No code duplication, types aligned, better error UX

### Phase 4: UX Redesign (Medium Priority)
1. Single-page architecture
2. Modern search bar
3. Drag-and-drop upload
4. Slide-over panels
5. Keyboard navigation

**Timeline:** 4-6 hours
**Success Criteria:** Search-centric interface, 0-click search, smooth animations

### Phase 5: Testing (Medium Priority)
1. Backend unit tests
2. Backend integration tests
3. Frontend component tests
4. E2E tests

**Timeline:** 4-5 hours
**Success Criteria:** 80%+ coverage, all tests passing

### Phase 6: Integration & Documentation (Low Priority)
1. Integration test script
2. API documentation
3. Architecture docs
4. Developer guide

**Timeline:** 2-3 hours
**Success Criteria:** Integration test passes, docs complete

## Total Estimated Timeline
18-24 hours of development work

## Success Metrics
- ✅ All identified bugs fixed
- ✅ Zero global singletons
- ✅ 80%+ test coverage
- ✅ Integration test passes
- ✅ Modern search-centric UI
- ✅ Complete documentation
- ✅ No TypeScript/Python type errors
- ✅ All Docker Compose services healthy on startup

## Risks & Mitigations

### Risk: UX redesign breaks existing functionality
**Mitigation:** Implement incrementally, keep existing pages until new UI tested

### Risk: Type generation from OpenAPI may fail
**Mitigation:** Manual type alignment as backup plan

### Risk: Test coverage takes longer than expected
**Mitigation:** Prioritize critical path tests first (upload → search)

### Risk: shadcn/ui migration breaks styling
**Mitigation:** Migrate one component at a time, keep Tailwind classes

## Post-Implementation Verification

1. Run integration test script - must pass
2. Run all unit/integration tests - must pass
3. Manual smoke test:
   - Upload document via drag-drop
   - Search immediately
   - View document details in slide-over
   - Delete document
   - Verify dark mode works
4. Check logs for errors
5. Review test coverage report

## Conclusion

This comprehensive design addresses all identified issues while modernizing the UX and ensuring long-term maintainability. The phased approach allows for incremental progress with verification at each step.
