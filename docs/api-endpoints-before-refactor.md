# API Endpoints Before Refactor

**Date:** 2025-01-26
**Purpose:** Document current API structure before legacy cleanup refactoring

## Overview

This document captures the current dual-architecture state of the RAAS API, which has both legacy facade-based routes and modern hexagonal architecture routes. The legacy routes will be removed, and the hexagonal routes will be promoted to the primary paths.

---

## Legacy Routes (TO BE REMOVED)

These routes use the legacy facade pattern with `DocumentService` and direct database access:

### Documents (Legacy)

**Base Path:** `/api/v1/documents`
**Implementation:** `services/api/app/api/routes/documents.py` (~184 lines)
**Architecture:** Facade pattern with `DocumentService`

- **POST `/api/v1/documents/upload`**
  - Upload a document file
  - Multipart form data: file, title, description (optional)
  - Returns: Document details and chunk count
  - Uses: `DocumentService.create_document()`

- **GET `/api/v1/documents`**
  - List all documents (paginated)
  - Query params: `page` (default: 1), `limit` (default: 20, max: 100)
  - Returns: Paginated list of documents with metadata
  - Uses: `DocumentService.get_documents()`

- **GET `/api/v1/documents/{document_id}`**
  - Get detailed document information including chunks
  - Path param: `document_id` (UUID)
  - Returns: Document with chunks array
  - Uses: `DocumentService.get_document_detail()`

- **DELETE `/api/v1/documents/{document_id}`**
  - Delete document and all associated data
  - Path param: `document_id` (UUID)
  - Returns: 204 No Content on success
  - Uses: `DocumentService.delete_document()`

### Search (Legacy)

**Base Path:** `/api/v1/search`
**Implementation:** `services/api/app/api/routes/search.py` (~433 lines)
**Architecture:** Direct database access, mixed concerns

- **POST `/api/v1/search`**
  - Perform semantic vector search across documents
  - Request body: `query` (string), `limit` (int), `document_ids` (optional), `model` (optional for summary)
  - Returns: Search results with chunks and optional AI summary
  - Uses: Direct Qdrant search + PostgreSQL joins
  - Retrieval method: `vector` (semantic only)

- **POST `/api/v1/search/hybrid`**
  - Hybrid search combining BM25 (lexical) and vector (semantic) retrieval
  - Request body: Same as `/search`
  - Returns: RRF-fused results from BM25 + vector search
  - Uses: `HybridSearchService` (stub implementation)
  - Expected improvement: 18-22% over vector-only
  - Retrieval method: `hybrid` with metadata

- **POST `/api/v1/search/advanced`**
  - Advanced search with query expansion + hybrid retrieval
  - Request body: Same as `/search`
  - Pipeline: Query expansion (LLM) -> Hybrid search -> Multi-set RRF
  - Returns: Expanded queries + fused results + metadata
  - Expected improvement: 25-40% over baseline (cumulative)
  - Retrieval method: `hybrid_expanded` with expanded_queries metadata

---

## Modern Routes (TO BE PROMOTED)

These routes follow hexagonal architecture with use cases, ports, and adapters:

### Documents (Hexagonal)

**Base Path:** `/api/v1/hexagonal/documents`
**Implementation:** `services/api/app/api/routes/hexagonal_documents.py` (~234 lines)
**Architecture:** Hexagonal with use cases and dependency injection

- **POST `/api/v1/hexagonal/documents/upload`**
  - Upload a document file with hexagonal architecture
  - Multipart form data: file, title, description (optional)
  - Returns: Document details and chunk count
  - Uses: `UploadDocumentUseCase` with proper error handling
  - Complete workflow: Validation -> Extraction -> Semantic chunking -> Embedding -> Vector storage -> Metadata persistence
  - Domain exceptions: `FileProcessingError`, `ChunkingError`, `EmbeddingServiceError`, `VectorStoreError`

- **GET `/api/v1/hexagonal/documents`**
  - Get paginated list of documents
  - Query params: `page` (default: 1), `limit` (default: 20, max: 100)
  - Returns: Paginated list with total count
  - Uses: `ListDocumentsUseCase`
  - Validation in use case layer

- **DELETE `/api/v1/hexagonal/documents/{document_id}`**
  - Delete document and all associated data
  - Path param: `document_id` (UUID)
  - Returns: 204 No Content on success
  - Uses: `DeleteDocumentUseCase`
  - Removes: PostgreSQL metadata/chunks + Qdrant vectors
  - Domain exceptions: `DocumentNotFoundError`, `VectorStoreError`

### Search (Hexagonal)

**Base Path:** `/api/v1/hexagonal/search`
**Implementation:** `services/api/app/api/routes/hexagonal_search.py` (~131 lines)
**Architecture:** Hexagonal with use cases and ports

- **POST `/api/v1/hexagonal/search`**
  - Perform document search with hybrid retrieval (RECOMMENDED)
  - Request body: `query` (string), `top_k` (int, default: 10)
  - Query params:
    - `mode`: `vector` | `keyword` | `hybrid` (default: `hybrid`)
    - `use_expansion`: boolean (default: `true`) - Multi-query expansion for +15-20% recall
    - `use_reranking`: boolean (default: `true`) - Cross-encoder reranking for +8-12% precision@10
  - Returns: Ranked chunks with search results
  - Uses: `SearchDocumentsUseCase` with mode selection
  - Search modes:
    - `VECTOR`: Pure semantic search using embeddings
    - `KEYWORD`: Pure lexical/BM25 search using PostgreSQL FTS
    - `HYBRID`: RRF fusion of both (RECOMMENDED, +18-22% accuracy)
  - Domain exceptions: `EmbeddingServiceError`, `VectorStoreError`
  - Workflow:
    1. Generate query embedding (if vector/hybrid)
    2. Search Qdrant for semantic matches (if vector/hybrid)
    3. Search PostgreSQL FTS for keyword matches (if keyword/hybrid)
    4. Fuse results using Reciprocal Rank Fusion (if hybrid)
    5. Optionally rerank with cross-encoder for precision
    6. Return top-k ranked results

---

## Unchanged Routes

These routes will remain unchanged during refactoring:

### Health Checks

**Base Path:** `/api/v1`
**Implementation:** `services/api/app/api/routes/health.py` (~112 lines)

- **GET `/api/v1/health`**
  - Basic health check endpoint
  - Returns: `{"status": "healthy"}`
  - No dependencies

- **GET `/api/v1/ready`**
  - Readiness check validating connectivity to dependencies
  - Returns: Overall status + service status array
  - Checks: PostgreSQL, Qdrant, Embedder service
  - Status values: `ready` | `not_ready`

### Models

**Base Path:** `/api/v1`
**Implementation:** `services/api/app/api/routes/models.py` (~32 lines)

- **GET `/api/v1/models`**
  - List available LLM models from Generator service
  - Returns: `{"models": [...]}`
  - Uses: `GeneratorClient.list_models()`

### Root

**Base Path:** `/`
**Implementation:** `services/api/app/main.py` (root endpoint)

- **GET `/`**
  - Root endpoint with API metadata
  - Returns: Service name, version, docs URL
  - No dependencies

---

## Route Registration (Current State)

**File:** `services/api/app/main.py`

```python
# Legacy routes (lines 73-89)
app.include_router(
    documents.router,
    prefix="/api/v1/documents",
    tags=["documents"]
)

app.include_router(
    search.router,
    prefix="/api/v1/search",
    tags=["search"]
)

# Hexagonal routes (lines 92-102)
app.include_router(
    hexagonal_documents.router,
    prefix="/api/v1/hexagonal/documents",
    tags=["hexagonal-documents"]
)

app.include_router(
    hexagonal_search.router,
    prefix="/api/v1/hexagonal/search",
    tags=["hexagonal-search"]
)
```

---

## Architectural Differences

### Legacy Routes

**Pattern:** Facade + Service Layer
**Dependencies:** `app.core.dependencies`, `app.services.*`
**Database Access:** Mixed (some direct queries, some via service)
**Error Handling:** HTTPException with generic messages
**Code Characteristics:**
- God object facades (`DocumentService`)
- Mixed concerns in route handlers
- Direct database queries in search.py
- Tight coupling to implementation details
- SOLID violations (SRP, DIP)

### Modern Hexagonal Routes

**Pattern:** Hexagonal Architecture (Ports & Adapters)
**Dependencies:** `app.api.dependencies`, `app.application.use_cases.*`
**Database Access:** Through repository ports
**Error Handling:** Domain-specific exceptions with proper HTTP status mapping
**Code Characteristics:**
- Use cases orchestrate business logic
- Ports define contracts (repositories, services)
- Adapters implement external integrations
- Domain-driven design with value objects
- SOLID principles throughout
- Dependency injection at all layers
- Clean separation of concerns

---

## Response Schema Comparison

### Legacy Response Models

**Location:** `app.models.schemas`

- `DocumentUploadResponse`: Document data + message + chunk_count
- `DocumentResponse`: Document data only
- `DocumentDetailResponse`: Document + chunks array
- `DocumentListResponse`: Documents array + pagination
- `SearchRequest`: Query + filters + model
- `SearchResponse`: Query + summary + chunks + model_used + total_results + retrieval_method + metadata + expanded_queries
- `SearchResultItem`: Chunk data + document metadata + score

### Modern Response Models

**Location:** `app.api.models`

- `UploadDocumentResponse`: document (nested) + chunk_count + message
- `DocumentResponse`: id + title + filename + description + created_at + updated_at
- `ListDocumentsResponse`: documents (array) + total + page + limit
- `SearchRequest`: query + top_k
- `SearchResponse`: query + results (array) + total_results
- `ChunkSearchResult`: chunk_id + document_id + document_title + chunk_text + chunk_index + score + section_title + page_number + metadata

**Key Difference:** Modern schemas use nested DTOs and separate concerns better (document as nested object vs flat structure).

---

## Summary

**Total Legacy Routes to Remove:** 7 endpoints across 2 files
**Total Modern Routes to Promote:** 4 endpoints across 2 files
**Unchanged Routes:** 4 endpoints across 2 files
**Code to Delete:** ~617 lines (documents.py + search.py)
**Code to Promote:** ~365 lines (hexagonal_documents.py + hexagonal_search.py)

**Expected Outcome After Refactor:**
- Single source of truth for document and search operations
- All routes at `/api/v1/*` (no `/hexagonal/` prefix)
- Clean hexagonal architecture throughout
- Improved maintainability and testability
- SOLID principles enforced
- ~900 lines of legacy code removed (including services)

---

## Next Steps

1. Remove legacy route files: `documents.py`, `search.py`
2. Remove legacy service facades: `DocumentService`, `HybridSearchService` (stub)
3. Rename hexagonal routes to primary: `hexagonal_documents.py` -> `documents.py`, `hexagonal_search.py` -> `search.py`
4. Update route registration in `main.py` to use `/api/v1/*` paths
5. Remove legacy dependencies: `app.core.dependencies.py`, `app.models.schemas.py`
6. Update tests and documentation
7. Verify all functionality preserved
