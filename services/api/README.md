# RAAS API Service

FastAPI gateway service for RAAS (Retrieval-Augmented Generation as a Service).

## Features

- Document upload with text extraction (PDF, DOCX, TXT)
- Automatic text chunking and embedding generation
- Semantic search across documents
- PostgreSQL for metadata and chunks
- Qdrant for vector storage
- Async operations throughout

## Setup

### Prerequisites

- Python 3.11+
- Poetry
- PostgreSQL
- Qdrant
- Embedder service running

### Installation

```bash
# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
```

### Database Setup

Apply the initial migration:

```bash
psql -U raasuser -d raasdb -f app/migrations/001_initial.sql
```

Or let the application create tables automatically on startup (development only).

## Database Migrations

To add full-text search support for hybrid search:

```bash
cd services/api
DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db" poetry run python scripts/run_migration.py add_fts_index.sql
```

This adds a `text_search_vector` column and GIN index to `document_chunks` table for BM25-like lexical search.

## Running

### Development

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

### Production

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```bash
# Build image
docker build -t raas-api:latest .

# Run container
docker run -p 8000:8000 --env-file .env raas-api:latest
```

## API Endpoints

### Documents

- `POST /api/v1/documents` - Upload a document with automatic chunking and embedding
- `GET /api/v1/documents` - List all documents (paginated)
- `GET /api/v1/documents/{id}` - Get document details with chunks
- `DELETE /api/v1/documents/{id}` - Delete document and all associated data

### Search

- `POST /api/v1/search` - Hybrid semantic + keyword search with optional AI summarization

### Models

- `GET /api/v1/models` - List available LLM models from all enabled providers

### Health

- `GET /api/v1/health` - Liveness check
- `GET /api/v1/health/ready` - Readiness check

## Documentation

Interactive API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run specific test
poetry run pytest tests/test_documents.py -v
```

## Environment Variables

See `.env.example` for all available configuration options.

Required variables:
- `DATABASE_URL` - PostgreSQL connection string
- `QDRANT_URL` - Qdrant server URL
- `EMBEDDER_URL` - Embedder service URL
- `GENERATOR_URL` - Generator service URL (for RAG responses)

## Architecture

This service follows **Hexagonal Architecture** (Ports and Adapters):

**Layers:**
- **Domain** (`app/domain/`): Core business entities (Document, Chunk) and value objects (SearchQuery)
- **Application** (`app/application/`): Use cases orchestrating business logic
  - `UploadDocumentUseCase`: Handle document upload, chunking, embedding
  - `SearchDocumentsUseCase`: Execute hybrid search with optional summarization
  - `ListDocumentsUseCase`: Retrieve paginated document list
  - `DeleteDocumentUseCase`: Remove documents and cleanup
- **Infrastructure** (`app/infrastructure/`): External system adapters
  - Repositories: PostgreSQL data access
  - Services: Embedder/Generator HTTP clients
  - Vector Store: Qdrant integration
- **API** (`app/api/`): HTTP routes and DTOs
- **Ports** (`app/ports/`): Interface definitions for external dependencies

**Benefits:**
- Testable: Business logic independent of frameworks
- Flexible: Swap implementations via dependency injection
- SOLID: Single Responsibility, Dependency Inversion throughout

For comprehensive architecture details, see the root [README.md](../../README.md).
