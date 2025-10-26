# RAAS – Retrieval-Augmented Generation as a Service

A production-ready microservices platform for semantic document search, powered by vector embeddings and modern web technologies.

## Overview

RAAS enables intelligent document search through semantic understanding. Upload documents, and the system automatically chunks them, generates vector embeddings, and provides lightning-fast semantic search capabilities. Built with scalability, observability, and user experience in mind.

## Key Features

### Core Functionality
- **Semantic Search**: Find documents by meaning, not just keywords
- **AI-Generated Summaries**: Get instant AI-powered summaries of search results with clickable citations
- **Enhanced Document Navigation**: Click search results or summary citations to jump directly to specific chunks in documents
- **Vector Embeddings**: 384-dimensional embeddings using sentence-transformers (all-MiniLM-L6-v2)
- **Intelligent Chunking**: Automatic text segmentation for optimal retrieval
- **Multi-format Support**: Upload TXT, PDF, DOCX, and more
- **Real-time Processing**: Asynchronous document processing with status tracking

### Modern UI/UX
- **Search-Centric Interface**: Single-page application focused on discovery
- **Drag-and-Drop Upload**: Intuitive file upload with visual feedback
- **Instant Results**: Real-time search as you type
- **Responsive Design**: Optimized for desktop, tablet, and mobile
- **Accessibility**: WCAG-compliant with semantic HTML and ARIA labels
- **Dark Mode Ready**: Built with shadcn/ui components and Tailwind CSS

### Developer Experience
- **Comprehensive Testing**: Unit, integration, and component tests
- **Type Safety**: Full TypeScript coverage with strict mode
- **Dependency Injection**: Clean architecture with testable services
- **Error Handling**: Custom exceptions with proper HTTP status codes
- **API Documentation**: Interactive OpenAPI (Swagger) docs for all endpoints
- **Health Checks**: Liveness and readiness probes for Kubernetes

### Production-Ready
- **Horizontal Scaling**: Kubernetes HPA for API and embedder services
- **High Availability**: PostgreSQL and Qdrant with persistent volumes
- **Observability**: Structured JSON logging throughout
- **CORS Support**: Configurable cross-origin resource sharing
- **Resource Limits**: Memory and CPU constraints for stability
- **Container Orchestration**: Docker Compose for local dev, Kubernetes for production

## Architecture

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
       │                                           ▲
       │                                           │
       ├──────────────────────────────────────────┘
       │             ┌─────────────┐
       │             │  Embedder   │
       │             │  Port 8001  │
       │             └─────────────┘
       │
       ├──────────────────────────────────┐
       │             ┌─────────────┐      │
       └────────────▶│  Generator  │      │
                     │  Port 8002  │      │
                     └──────┬──────┘      │
                            │             │
                            ▼             │
                     ┌─────────────┐      │
                     │   Ollama    │◀─────┘
                     │ Port 11434  │
                     └─────────────┘
```

### Technology Stack

**Backend:**
- FastAPI (async Python web framework)
- SQLAlchemy with asyncpg (PostgreSQL ORM)
- Qdrant Python client (vector database)
- sentence-transformers (ML embeddings)
- Pydantic v2 (data validation)

**Frontend:**
- React 18 with TypeScript
- Vite (build tool)
- React Query (server state management)
- React Router (SPA routing)
- Tailwind CSS (styling)
- shadcn/ui (component library)
- Axios (HTTP client)

**Infrastructure:**
- Docker & Docker Compose
- Kubernetes with Kustomize
- NGINX (ingress & reverse proxy)
- PostgreSQL 15
- Qdrant vector database

### Data Flow

**Document Upload:**
1. User uploads file via frontend
2. API stores metadata in PostgreSQL
3. API chunks document and stores chunks
4. API sends chunks to embedder service
5. Embedder generates vectors and stores in Qdrant
6. Status updated to 'completed'

**Search Query:**
1. User enters search query
2. API forwards query to embedder
3. Embedder generates query vector
4. Qdrant performs vector similarity search
5. API joins results with PostgreSQL metadata
6. Results returned to frontend with scores

## Quick Start

### Prerequisites

- Docker 24.0+ and Docker Compose 2.0+
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Poetry 1.5+ (Python dependency management)

### Local Development with Docker Compose

```bash
# Clone the repository
git clone <repository-url>
cd raas

# Start all services
docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d --build

# Wait for services to be healthy (30-60 seconds)
# Check status
docker-compose -f infrastructure/docker-compose/docker-compose.yml ps

# Access the application
open http://localhost:3000
```

**Service URLs:**
- Frontend: http://localhost:3000
- API: http://localhost:8000/docs
- Embedder: http://localhost:8001/docs
- Generator: http://localhost:8002/docs
- Qdrant Dashboard: http://localhost:6333/dashboard
- Ollama: http://localhost:11434

### Kubernetes Deployment (Local with Kind)

```bash
# Create local Kind cluster and deploy all services
./infrastructure/scripts/setup-kind-full.sh

# Check deployment status
kubectl get pods -n raas
kubectl get svc -n raas

# Access via port-forward
kubectl port-forward svc/frontend 3000:80 -n raas
kubectl port-forward svc/api 8000:8000 -n raas
```

### Service-Specific Development

#### API Service

```bash
cd services/api

# Install dependencies
poetry install

# Run locally (requires PostgreSQL and Qdrant running)
poetry run uvicorn app.main:app --reload --port 8000

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_documents.py -v
```

#### Embedder Service

```bash
cd services/embedder

# Install dependencies
poetry install

# Run locally (requires Qdrant running)
poetry run uvicorn app.main:app --reload --port 8001

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app --cov-report=html
```

#### Generator Service

```bash
cd services/generator

# Install dependencies
poetry install

# Run locally (requires Ollama running)
poetry run uvicorn app.main:app --reload --port 8002

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app --cov-report=html
```

#### Frontend

```bash
cd services/frontend

# Install dependencies
npm install

# Run dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Type check
npx tsc --noEmit

# Lint
npm run lint
```

## Testing

### Running All Tests

```bash
# Backend tests (API)
cd services/api && poetry run pytest

# Backend tests (Embedder)
cd services/embedder && poetry run pytest

# Backend tests (Generator)
cd services/generator && poetry run pytest

# Frontend tests
cd services/frontend && npm test

# Integration tests
./tests/integration/test_full_workflow.sh
./tests/integration/test_generation_flow.sh
```

### Integration Test Suite

The integration test script tests the complete workflow:

```bash
# Run from repository root
./tests/integration/test_full_workflow.sh
```

**What it tests:**
- Health endpoints for all services
- Document upload via API
- Document retrieval
- Semantic search functionality
- Document deletion
- Frontend accessibility

**Features:**
- Colorized output with progress indicators
- Automatic service startup and health checks
- Comprehensive test coverage
- Interactive cleanup options
- Exit codes for CI/CD integration

### Test Coverage

**API Service:**
- Unit tests for all routes and services
- Integration tests with test database
- Mock tests for external dependencies
- Exception handling tests
- Database transaction tests

**Embedder Service:**
- Unit tests for embedding generation
- Qdrant integration tests
- Batch processing tests
- Model loading tests

**Frontend:**
- Component unit tests with Vitest
- React Testing Library for UI tests
- Hook testing with custom utilities
- Mock API responses

## API Documentation

### Core Endpoints

#### Health & Status

```bash
# Check API health (liveness)
GET /api/v1/health

# Check API readiness
GET /api/v1/health/ready
```

#### Documents

```bash
# Upload document
POST /api/v1/documents
Content-Type: multipart/form-data
Body: file, title (optional), description (optional)

# List all documents
GET /api/v1/documents

# Get document by ID
GET /api/v1/documents/{id}

# Delete document
DELETE /api/v1/documents/{id}
```

#### Search

```bash
# Semantic search
POST /api/v1/search
Content-Type: application/json
Body: {
  "query": "search query text",
  "limit": 10,  // optional, default 10
  "model": "llama3.2"  // optional, enables generation
}
```

#### Models

```bash
# List available LLM models
GET /api/v1/models
```

#### Summary Generation

```bash
# Generate AI summary from search result chunks
POST /api/v1/generate/summary
Content-Type: application/json
Body: {
  "query": "what is semantic search?",
  "chunk_ids": ["uuid1", "uuid2", ...],
  "model": "gpt-5-mini"
}

# Response:
{
  "summary": "Based on your documents, semantic search uses embeddings...",
  "model_used": "gpt-5-mini"
}

# Error Codes:
# - 404: Chunk IDs not found
# - 503: Generator service unavailable
```

### Response Examples

**Document Upload Response:**
```json
{
  "id": 1,
  "title": "My Document",
  "description": "Optional description",
  "filename": "document.txt",
  "file_size": 1024,
  "upload_status": "completed",
  "embedding_status": "processing",
  "created_at": "2025-10-24T12:00:00Z",
  "updated_at": "2025-10-24T12:00:00Z"
}
```

**Search Response:**
```json
{
  "query": "search query text",
  "summary": "Generated summary with citations [1] [2].",
  "chunks": [
    {
      "document_id": "uuid",
      "document_title": "My Document",
      "text": "Relevant text chunk...",
      "score": 0.85,
      "chunk_index": 0
    }
  ],
  "model_used": "llama3.2",
  "total_results": 1
}
```

### Interactive Documentation

Visit the API docs for interactive testing:
- API Service: http://localhost:8000/docs
- Embedder Service: http://localhost:8001/docs
- Generator Service: http://localhost:8002/docs

## Multi-Provider Model Support

The system supports multiple LLM providers for summary generation:

- **OpenAI** (GPT-4o, GPT-4o-mini, default)
- **Ollama** (local models - llama3.2, mistral, etc.)
- **Anthropic** (Claude models)
- **Google** (Gemini models)

To enable additional providers, configure environment variables in `services/generator/.env`:

```bash
# OpenAI (recommended, enabled by default)
ENABLE_OPENAI=true
OPENAI_API_KEY=sk-...
DEFAULT_MODEL=openai:gpt-4o-mini

# Ollama (optional, for local models)
ENABLE_OLLAMA=true
OLLAMA_URL=http://localhost:11434

# Anthropic (optional)
ENABLE_ANTHROPIC=true
ANTHROPIC_API_KEY=sk-ant-...

# Google (optional)
ENABLE_GOOGLE=true
GOOGLE_API_KEY=...
```

Models from all enabled providers appear automatically in the frontend dropdown.

## Configuration

### Environment Variables

#### API Service

```bash
DATABASE_URL=postgresql+asyncpg://raasuser:raaspass@postgres:5432/raasdb
QDRANT_URL=http://qdrant:6333
EMBEDDER_URL=http://embedder:8001
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=104857600
CORS_ORIGINS=["http://localhost:3000"]
LOG_LEVEL=INFO
```

#### Embedder Service

```bash
QDRANT_URL=http://qdrant:6333
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
MODEL_DIMENSION=384
BATCH_SIZE=32
COLLECTION_NAME=documents
LOG_LEVEL=INFO
```

#### Generator Service

```bash
# OpenAI Configuration (default)
ENABLE_OPENAI=true
OPENAI_API_KEY=your-openai-api-key-here
DEFAULT_MODEL=openai:gpt-4o-mini

# Ollama Configuration (optional)
OLLAMA_URL=http://localhost:11434
ENABLE_OLLAMA=false

# Generation Settings
MAX_CHUNKS=5
TEMPERATURE=0.1
MAX_TOKENS=2000
TIMEOUT=30
LOG_LEVEL=INFO
```

#### Frontend

```bash
VITE_API_URL=http://localhost:8000
```

### Configuration Files

- `services/api/.env.example` - API environment template
- `services/embedder/.env.example` - Embedder environment template
- `services/frontend/.env.example` - Frontend environment template
- `infrastructure/k8s/base/` - Kubernetes base configurations
- `infrastructure/k8s/overlays/` - Environment-specific overlays

## Project Structure

```
raas/
├── services/
│   ├── api/                    # FastAPI gateway service
│   │   ├── app/
│   │   │   ├── api/           # Route handlers
│   │   │   ├── core/          # Config and dependencies
│   │   │   ├── models/        # SQLAlchemy and Pydantic models
│   │   │   ├── services/      # Business logic
│   │   │   ├── exceptions.py  # Custom exceptions
│   │   │   └── main.py        # Application entry point
│   │   ├── tests/             # API tests
│   │   ├── pyproject.toml     # Poetry dependencies
│   │   └── Dockerfile
│   │
│   ├── embedder/              # Embedding generation service
│   │   ├── app/
│   │   │   ├── api/           # Route handlers
│   │   │   ├── core/          # Config and dependencies
│   │   │   ├── services/      # Embedding logic
│   │   │   └── main.py        # Application entry point
│   │   ├── tests/             # Embedder tests
│   │   ├── pyproject.toml     # Poetry dependencies
│   │   └── Dockerfile
│   │
│   ├── generator/             # LLM generation service
│   │   ├── app/
│   │   │   ├── api/           # Route handlers
│   │   │   ├── core/          # Config and dependencies
│   │   │   ├── models/        # Pydantic schemas
│   │   │   ├── services/      # Generation logic
│   │   │   └── main.py        # Application entry point
│   │   ├── tests/             # Generator tests
│   │   ├── pyproject.toml     # Poetry dependencies
│   │   └── Dockerfile
│   │
│   └── frontend/              # React SPA
│       ├── src/
│       │   ├── components/    # React components
│       │   ├── hooks/         # Custom hooks
│       │   ├── services/      # API client
│       │   ├── types/         # TypeScript types
│       │   ├── App.tsx        # Main app component
│       │   └── main.tsx       # Entry point
│       ├── tests/             # Frontend tests
│       ├── package.json       # npm dependencies
│       ├── vite.config.ts     # Vite configuration
│       ├── tsconfig.json      # TypeScript configuration
│       └── Dockerfile
│
├── infrastructure/
│   ├── docker-compose/        # Local development
│   │   ├── docker-compose.yml
│   │   └── .env.example
│   ├── k8s/                   # Kubernetes manifests
│   │   ├── base/              # Base configurations
│   │   ├── overlays/          # Environment overlays
│   │   │   ├── local/
│   │   │   └── production/
│   │   └── scripts/           # Deployment scripts
│   │       └── deploy-local.sh
│   ├── kind/                  # Kind cluster config
│   │   └── kind-config.yaml
│   └── scripts/               # Infrastructure scripts
│       ├── init-ollama.sh
│       ├── setup-kind-full.sh
│       ├── test-rollout-rollback.sh
│       ├── test-scalability-reliability.sh
│       └── verify-type1-requirements.sh
│
├── tests/
│   └── integration/           # Integration tests
│       ├── test_full_workflow.sh
│       └── test_generation_flow.sh
│
├── docs/                      # Documentation
├── data/                      # Data directory
│   └── uploads/              # Uploaded files
├── CLAUDE.md                 # Claude Code instructions
└── README.md                 # This file
```

## Architecture Details

### Dependency Injection Pattern

The API service uses FastAPI's dependency injection for clean, testable code:

```python
# app/core/dependencies.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_document_service(
    db: AsyncSession = Depends(get_db)
) -> DocumentService:
    return DocumentService(db)

# app/api/routes/documents.py
@router.post("/documents")
async def upload_document(
    service: DocumentService = Depends(get_document_service)
):
    return await service.upload_document(...)
```

### Async Qdrant Client

The embedder service uses asynchronous Qdrant operations for optimal performance:

```python
# Non-blocking vector operations
async with AsyncQdrantClient(url=qdrant_url) as client:
    await client.upsert(
        collection_name="documents",
        points=[...]
    )
```

### Custom Exception Handling

Structured exceptions with proper HTTP status codes:

```python
# app/exceptions.py
class DocumentNotFoundException(HTTPException):
    def __init__(self, document_id: int):
        super().__init__(
            status_code=404,
            detail=f"Document with id {document_id} not found"
        )
```

### Frontend Component Architecture

The frontend follows React best practices with custom hooks:

```typescript
// Custom hook for data fetching
export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: fetchDocuments,
    staleTime: 5000,
  });
}

// Usage in components
function DocumentList() {
  const { data, isLoading, error } = useDocuments();
  // ... render logic
}
```

## Kubernetes Deployment

### Resource Requirements

**API Service:**
- Requests: 256Mi memory, 0.25 CPU
- Limits: 512Mi memory, 0.5 CPU
- Replicas: 2-5 (HPA)

**Embedder Service:**
- Requests: 512Mi memory, 0.5 CPU
- Limits: 1Gi memory, 1 CPU
- Replicas: 1-3 (HPA)

**Frontend:**
- Requests: 64Mi memory, 0.1 CPU
- Limits: 128Mi memory, 0.2 CPU
- Replicas: 2

### Horizontal Pod Autoscaling

```yaml
# HPA targets
API: 70% CPU, 80% memory
Embedder: 70% CPU, 80% memory
```

### Persistent Storage

```yaml
PostgreSQL: 10Gi PVC
Qdrant: 5Gi PVC
```

## Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check Docker daemon
docker info

# Check logs
docker-compose -f infrastructure/docker-compose/docker-compose.yml logs -f

# Restart services
docker-compose -f infrastructure/docker-compose/docker-compose.yml restart
```

**Database connection errors:**
```bash
# Verify PostgreSQL is running
docker exec -it raas-postgres psql -U raasuser -d raasdb -c '\l'

# Check migrations
docker exec -it raas-postgres psql -U raasuser -d raasdb -c '\dt'
```

**Embedder model download issues:**
```bash
# Model downloads on first start (may take 1-2 minutes)
# Check embedder logs
docker-compose -f infrastructure/docker-compose/docker-compose.yml logs embedder

# Manually download model (optional)
docker exec -it raas-embedder python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

**Frontend build errors:**
```bash
# Clear cache and reinstall
cd services/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

**Search returns no results:**
```bash
# Check if embeddings are completed
curl http://localhost:8000/api/v1/documents | jq '.[] | {id, embedding_status}'

# Check Qdrant collection
curl http://localhost:6333/collections/documents | jq

# Verify vector count
curl http://localhost:6333/collections/documents | jq '.result.points_count'
```

### Debug Mode

**API Service:**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
poetry run uvicorn app.main:app --reload --log-level debug
```

**Frontend:**
```bash
# Enable React DevTools
npm run dev
# Open browser DevTools
```

### Port Forwarding (Kubernetes)

```bash
# Access services locally
kubectl port-forward svc/api 8000:8000 -n raas
kubectl port-forward svc/embedder 8001:8001 -n raas
kubectl port-forward svc/frontend 3000:80 -n raas
kubectl port-forward svc/qdrant 6333:6333 -n raas
kubectl port-forward svc/postgres 5432:5432 -n raas
```

## Performance Considerations

### Embedding Generation

- **Batch Size**: Default 32 chunks per batch (configurable)
- **Model Size**: 384 dimensions (lightweight, fast)
- **Processing Time**: ~50-100ms per batch on CPU
- **GPU Support**: Can enable GPU for faster processing

### Vector Search

- **Search Latency**: <50ms for 10k vectors
- **Index Type**: HNSW (Hierarchical Navigable Small World)
- **Distance Metric**: Cosine similarity

### Database

- **Connection Pool**: 20 connections (asyncpg)
- **Query Optimization**: Indexed foreign keys
- **Cascading Deletes**: Automatic cleanup

## Security Considerations

### API Security

- CORS configuration for frontend origins
- File upload validation (size, type)
- SQL injection prevention (SQLAlchemy ORM)
- Input validation (Pydantic models)

### Kubernetes Security

- Non-root containers
- Resource limits to prevent DoS
- Network policies (optional)
- Secret management for credentials

### File Storage

- Uploaded files stored outside web root
- File type validation
- Size limits enforced

## Contributing

### Development Workflow

1. Create feature branch
2. Make changes with tests
3. Run test suite
4. Update documentation
5. Submit pull request

### Code Style

**Python:**
- Follow PEP 8
- Use type hints
- Max line length: 100
- Use Black formatter

**TypeScript:**
- ESLint configuration provided
- Prettier for formatting
- Strict mode enabled

### Commit Messages

```
feat: add new feature
fix: bug fix
test: add tests
docs: documentation
refactor: code refactoring
chore: maintenance
```

## Kubernetes Deployment

The RAAS platform can be deployed to Kubernetes for production-grade orchestration, scalability, and reliability.

### Quick Start (Local)

```bash
# Deploy to local Kind cluster
./infrastructure/k8s/scripts/deploy-local.sh

# Access services
kubectl port-forward svc/api 8000:8000 -n raas
kubectl port-forward svc/frontend 3000:3000 -n raas
```

### Full Documentation

See [infrastructure/k8s/README.md](infrastructure/k8s/README.md) for:
- Architecture overview
- Production deployment
- Scaling and HPA
- Rollout and rollback procedures
- Troubleshooting guide

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [Your Repo URL]
- Documentation: See `docs/` directory
- CLAUDE.md: Instructions for AI assistants

## Acknowledgments

- sentence-transformers for embedding models
- Qdrant for vector database
- FastAPI for Python web framework
- React team for frontend framework
- shadcn/ui for component library
