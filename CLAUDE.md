# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAAS (Retrieval-Augmented Generation as a Service) is a microservices-based platform for semantic document search. The system ingests documents, chunks them, generates vector embeddings, and enables semantic search queries.

### Architecture

The platform consists of four microservices that communicate asynchronously:

1. **API Service** (`services/api/`) - FastAPI gateway (port 8000)
   - Handles document uploads, metadata storage in PostgreSQL
   - Manages search requests and coordinates with embedder service
   - Stores document chunks in PostgreSQL and references Qdrant point IDs

2. **Embedder Service** (`services/embedder/`) - Embedding generation (port 8001)
   - Generates 384-dimensional vectors using sentence-transformers (`all-MiniLM-L6-v2`)
   - Stores embeddings in Qdrant vector database
   - Processes chunks in batches (default 32) for optimal performance

3. **Generator Service** (`services/generator/`) - RAG summary generation (port 8002)
   - Multi-provider LLM support (OpenAI, Anthropic, Google, Ollama)
   - Generates summaries from retrieved document chunks
   - Configurable models with graceful degradation

4. **Frontend** (`services/frontend/`) - React SPA (port 3000)
   - Built with React 18, TypeScript, Vite, Tailwind CSS
   - Uses React Query for state management and caching
   - Served via NGINX in production

### Data Flow

- **Upload**: Frontend → API → PostgreSQL (metadata + chunks) → Embedder → Qdrant (vectors)
- **Search**: Frontend → API → Embedder (query embedding) → Qdrant (vector search) → API (join with PostgreSQL) → Frontend

### Storage

- **PostgreSQL**: Document metadata (`documents` table) and text chunks (`document_chunks` table)
- **Qdrant**: Vector embeddings in a collection named `documents` (384-dim, cosine distance)
- **Filesystem**: Uploaded files stored in `data/uploads/` (local dev) or persistent volumes (k8s)

## Development Commands

### Local Development (Docker Compose)

```bash
# Start all services locally
docker-compose -f infrastructure/docker-compose/docker-compose.yml up

# Build and restart specific service
docker-compose -f infrastructure/docker-compose/docker-compose.yml up --build api

# View logs
docker-compose -f infrastructure/docker-compose/docker-compose.yml logs -f api
```

### Kubernetes (Kind)

```bash
# Create local Kind cluster
./infrastructure/scripts/setup-kind.sh

# Build and deploy all services
./infrastructure/scripts/build-and-deploy.sh v1

# Deploy with specific version tag
./infrastructure/scripts/build-and-deploy.sh v2

# Apply Kustomize overlays
kubectl apply -k infrastructure/k8s/overlays/local/

# Check deployment status
kubectl rollout status deployment/api -n raas
kubectl get pods -n raas
kubectl get svc -n raas
kubectl get ingress -n raas

# Destroy cluster
kind delete cluster --name raas-cluster
```

### Service-Specific Commands

#### API Service
```bash
cd services/api

# Install dependencies with Poetry
poetry install

# Run locally
poetry run uvicorn app.main:app --reload --port 8000

# Run tests
poetry run pytest

# Run specific test
poetry run pytest tests/test_documents.py::test_upload_document -v
```

#### Embedder Service
```bash
cd services/embedder

# Install dependencies
poetry install

# Run locally
poetry run uvicorn app.main:app --reload --port 8001

# Run tests
poetry run pytest
```

#### Generator Service
```bash
cd services/generator

# Install dependencies
poetry install

# Run locally
poetry run uvicorn app.main:app --reload --port 8002

# Run tests
poetry run pytest
```

#### Frontend
```bash
cd services/frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint and type-check
npm run lint
npx tsc --noEmit
```

### Database Operations

```bash
# Connect to PostgreSQL in Docker
docker exec -it raas-postgres psql -U raasuser -d raasdb

# In Kubernetes
kubectl exec -it <postgres-pod> -n raas -- psql -U raasuser -d raasdb

# Apply initial migration
psql -U raasuser -d raasdb -f services/api/app/migrations/001_initial.sql
```

## Key Technical Details

### API Service Architecture

- **Async-first**: Uses `asyncpg` with SQLAlchemy for non-blocking database operations
- **Database schema**: Two main tables (`documents` and `document_chunks`) with cascading deletes
- **Status tracking**: Documents have `upload_status` and `embedding_status` fields
- **Chunking**: Text is split into manageable chunks using SemanticChunker (implementation in `services/api/app/services/chunking/`)
- **Error handling**: Returns proper HTTP status codes with descriptive error messages
- **Logging**: JSON-formatted logs to stdout

### Embedder Service Architecture

- **Model loading**: Sentence-transformers model loaded once at startup to avoid repeated downloads
- **Batch processing**: Processes embeddings in configurable batches (typically 32)
- **Qdrant integration**: Stores vectors with metadata payloads including `document_id`, `chunk_index`, and original text
- **Collection initialization**: Ensures `documents` collection exists with 384-dim vectors and cosine distance
- **Readiness probe**: `/ready` endpoint indicates when model has finished loading

### Frontend Architecture

- **API client**: Centralized in `src/services/api.ts` using Axios
- **State management**: React Query for server state, caching, and automatic refetching
- **Custom hooks**: `useDocuments` and `useSearch` wrap API calls with loading/error states
- **TypeScript types**: Shared types in `src/types/index.ts` matching backend Pydantic models
- **Routing**: React Router for SPA navigation
- **Styling**: Tailwind CSS with semantic HTML and ARIA labels

### Generator Service Architecture

- **Multi-provider support**: Abstraction layer supporting OpenAI, Anthropic, Google, and Ollama
- **Provider registry**: Dynamic registration based on available API keys and configuration
- **Model selection**: Configurable default model with per-request overrides
- **Graceful degradation**: Falls back to Ollama when API providers unavailable
- **Prompt engineering**: Structured prompts combining query context with retrieved chunks
- **Configuration**: Environment-based provider enablement with `.env` files

### Kubernetes Deployment

- **Namespace**: All resources deployed to `raas` namespace
- **Kustomize structure**: Base manifests in `infrastructure/k8s/base/` with overlays for `local` and `gcp`
- **Autoscaling**: HPA configured for API and embedder based on CPU (70%) and memory (80%)
- **Ingress**: NGINX ingress routes `/` to frontend and `/api` to API service
- **Persistent storage**: PVCs for PostgreSQL and Qdrant data
- **Secrets**: PostgreSQL credentials stored in `postgres-secret.yaml`

### Environment Variables

Each service expects specific environment variables. Examples are provided in `.env.example` files:

- **API**: `DATABASE_URL`, `QDRANT_URL`, `EMBEDDER_URL`, `GENERATOR_URL`, `UPLOAD_DIR`
- **Embedder**: `QDRANT_URL`, `MODEL_NAME`, `BATCH_SIZE`
- **Generator**: `DEFAULT_MODEL`, `ENABLE_OPENAI`, `OPENAI_API_KEY`, `ENABLE_OLLAMA`, `OLLAMA_URL`, `ENABLE_ANTHROPIC`, `ANTHROPIC_API_KEY`, `ENABLE_GOOGLE`, `GOOGLE_API_KEY`
- **Frontend**: `VITE_API_URL`

## Common Tasks

### Adding a New API Endpoint

1. Define Pydantic request/response schemas in `services/api/app/models/schemas.py`
2. Implement route handler in appropriate file under `services/api/app/api/routes/`
3. Add business logic in `services/api/app/services/`
4. Include router in `services/api/app/main.py`
5. Add tests in `services/api/tests/`

### Modifying Database Schema

1. Create new migration SQL file in `services/api/app/migrations/`
2. Update SQLAlchemy models in `services/api/app/models/document.py`
3. Update Pydantic schemas in `services/api/app/models/schemas.py`
4. Apply migration manually or via initialization script

### Adding a New Frontend Page

1. Create page component in `services/frontend/src/pages/`
2. Add route in `services/frontend/src/App.tsx`
3. Create necessary hooks in `services/frontend/src/hooks/`
4. Add API methods in `services/frontend/src/services/api.ts`
5. Define TypeScript types in `services/frontend/src/types/index.ts`

### Debugging Services

- **Check service health**: `curl http://localhost:8000/api/v1/health`
- **Check readiness**: `curl http://localhost:8000/api/v1/health/ready`
- **View Qdrant collections**: Navigate to `http://localhost:6333/dashboard` in browser
- **Check logs in k8s**: `kubectl logs -f deployment/api -n raas`
- **Port-forward for debugging**: `kubectl port-forward svc/api 8000:8000 -n raas`

## Testing Strategy

- **Unit tests**: Test individual functions and classes in isolation
- **Integration tests**: Test service interactions (API ↔ Database, API ↔ Embedder)
- **Load tests**: Located in `tests/` directory
- **Health checks**: Both `/health` (liveness) and `/ready` (readiness) probes for each service

## Important Implementation Notes

- Avoid blocking operations in FastAPI async endpoints - use async database clients and HTTP clients
- When logging in MCP servers or background services, avoid writing to stdout as it can corrupt JSON-RPC messages
- Use Pydantic v2 for all request/response models with descriptive docstrings
- Frontend should display loading states and handle errors gracefully with user-friendly messages
- Delete operations should cascade: remove from Qdrant, delete file from disk, then remove from PostgreSQL
- Qdrant point IDs should be stored in `document_chunks.qdrant_point_id` for reference during deletion
