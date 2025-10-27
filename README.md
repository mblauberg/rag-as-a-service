# RAAS – Retrieval-Augmented Generation as a Service

Microservices platform for semantic document search using vector embeddings.

**Academic Project**
Course: INFS3208 - Cloud Computing
Institution: University of Queensland
Year: 2025

## Features

- **Hybrid Search**: Vector similarity + keyword search with RRF fusion
- **AI Summaries**: LLM-generated summaries with citations (OpenAI, Anthropic, Google)
- **Multi-format Upload**: PDF, DOCX, TXT with automatic chunking
- **Cross-Encoder Reranking**: Two-stage retrieval for better precision
- **Responsive UI**: React + TypeScript with shadcn/ui

## Architecture

```
┌──────────┐
│ Frontend │ :3000
└────┬─────┘
     │
┌────▼────┐     ┌──────────┐     ┌────────┐
│   API   │────▶│ Postgres │     │ Qdrant │
│  :8000  │     │  :5432   │     │ :6333  │
└────┬────┘     └──────────┘     └───┬────┘
     │                                │
     ├─────┬─────┬─────┐             │
     │     │     │     │             │
┌────▼──┐ │     │ ┌───▼────┐        │
│ Search│◀┘     │ │Embedder│◀───────┘
│ :8003 │       │ │ :8001  │
└───────┘       │ └────────┘
             ┌──▼───────┐
             │Generator │
             │  :8002   │
             └──────────┘
```

**Services:**
- **API** (FastAPI): Orchestration, document CRUD
- **Search** (FastAPI): Hybrid retrieval with reranking
- **Embedder** (FastAPI): Vector generation (sentence-transformers)
- **Generator** (FastAPI): LLM summaries (multi-provider)
- **Frontend** (React): SPA with real-time search

**Infrastructure:**
- PostgreSQL for metadata
- Qdrant for vector storage
- Docker Compose / Kubernetes

## Tech Stack

**Backend:**
- Python 3.13
- FastAPI, SQLAlchemy, Pydantic v2
- sentence-transformers, Qdrant, httpx

**Frontend:**
- React 18, TypeScript
- Vite, React Query, Tailwind CSS
- shadcn/ui, Radix UI

## Quick Start

### Local Development

```bash
# Start all services
docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d

# Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Service-Specific Development

```bash
# API
cd services/api
poetry install
poetry run uvicorn app.main:app --reload --port 8000

# Frontend
cd services/frontend
npm install
npm run dev
```

## API Endpoints

### Documents
- `POST /api/v1/documents` - Upload document
- `GET /api/v1/documents` - List documents
- `GET /api/v1/documents/{id}` - Get document
- `DELETE /api/v1/documents/{id}` - Delete document

### Search
- `POST /api/v1/search` - Hybrid search with optional AI summary

**Request:**
```json
{
  "query": "what is machine learning?",
  "limit": 10,
  "model": "openai:gpt-5-mini"
}
```

**Response:**
```json
{
  "query": "what is machine learning?",
  "summary": "Machine learning is... [1] [2]",
  "chunks": [...],
  "model_used": "openai:gpt-5-mini"
}
```

### Models
- `GET /api/v1/models` - List available LLM models

### Health
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/ready` - Readiness check

## Configuration

### Generator Service

```bash
# OpenAI (primary)
ENABLE_OPENAI=true
OPENAI_API_KEY=sk-...
DEFAULT_MODEL=openai:gpt-5-mini

# Anthropic (optional)
ENABLE_ANTHROPIC=true
ANTHROPIC_API_KEY=sk-ant-...

# Google (optional)
ENABLE_GOOGLE=true
GOOGLE_API_KEY=...
```

See `services/*/. env.example` for full config options.

## Testing

```bash
# Backend tests
cd services/api && poetry run pytest
cd services/embedder && poetry run pytest
cd services/generator && poetry run pytest
cd services/search && poetry run pytest

# Frontend tests
cd services/frontend && npm test

# Integration tests
./tests/integration/test_full_workflow.sh
```

## Kubernetes Deployment

```bash
# Local (Kind)
./infrastructure/scripts/setup-kind-full.sh

# Or manual
kubectl apply -k infrastructure/k8s/overlays/local/

# Access
kubectl port-forward svc/frontend 3000:80 -n raas
kubectl port-forward svc/api 8000:8000 -n raas
```

See [infrastructure/k8s/README.md](infrastructure/k8s/README.md) for details.

## Project Structure

```
raas/
├── services/
│   ├── api/         # FastAPI gateway
│   ├── embedder/    # Vector generation
│   ├── generator/   # LLM summaries
│   ├── search/      # Hybrid retrieval
│   └── frontend/    # React SPA
├── infrastructure/
│   ├── docker-compose/
│   └── k8s/         # Kubernetes manifests
└── tests/
    └── integration/
```

## Development

### Prerequisites

- Docker 24.0+ and Docker Compose 2.0+
- Python 3.13+ and Poetry (for local dev)
- Node.js 18+ (for frontend dev)

### Adding a New LLM Provider

1. Create provider class in `services/generator/app/providers/`
2. Implement `ModelProvider` interface
3. Register in `app/main.py`
4. Add config to `.env`

See [services/generator/README.md](services/generator/README.md) for details.

## Troubleshooting

**Services not starting:**
```bash
docker-compose -f infrastructure/docker-compose/docker-compose.yml logs -f
```

**Database issues:**
```bash
docker exec -it raas-postgres psql -U raasuser -d raasdb -c '\dt'
```

**No search results:**
```bash
# Check embeddings
curl http://localhost:8000/api/v1/documents | jq '.[] | {id, embedding_status}'

# Check Qdrant
curl http://localhost:6333/collections/documents | jq
```

## License

Academic project for INFS3208.
