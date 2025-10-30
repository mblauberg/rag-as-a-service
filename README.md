# RAaS – Retrieval-Augmented Generation as a Service

> Microservices platform for semantic document search with AI-generated summaries

![Project Status](https://img.shields.io/badge/status-portfolio%20project-blue)
[![Tech Stack](https://img.shields.io/badge/Python-3.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.119-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Table of Contents

- [Overview](#overview)
- [Demo](#demo)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Development](#development)
- [Kubernetes Deployment](#kubernetes-deployment)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact--links)

## Overview

RAaS is a document search platform that combines semantic understanding with AI-generated summaries. Upload documents, search using natural language, and receive contextual answers with citations.

Built with a microservices architecture that scales compute-intensive operations independently.

**API Docs:** `http://localhost:8000/docs` (when running locally)

## Demo

![Search Interface](docs/images/search-interface.png)
*Semantic search with AI-powered summaries and inline citations*

![Search Demo](docs/images/search-demo.gif)
*Real-time document search and answer generation*

### Key Features

- **Semantic Search** – Understands meaning, not just keywords. Search for "contract breach" and find "agreement violation"
- **Hybrid Retrieval** – Combines vector similarity with keyword matching using Reciprocal Rank Fusion (RRF)
- **AI Summarization** – Generate contextual answers with inline citations from OpenAI, Anthropic, or Google models
- **Multi-Format Support** – Upload PDFs, DOCX, TXT, CSV, and Markdown files
- **Cross-Encoder Reranking** – Improves result relevance with precision scoring
- **Production-Ready** – Kubernetes deployment with auto-scaling, health checks, and zero-downtime updates

---

## Architecture

```
        ┌──────────┐
        │ Frontend │ :3000
        └─────┬────┘
              │
        ┌─────▼─────┐
        │    API    │  ←─ Gateway & Orchestration
        │   :8000   │
        └─────┬─────┘
              │
    ┌─────────┼─────────┬──────────┐
    │         │         │          │
┌───▼────┐ ┌─▼────┐ ┌──▼─────┐ ┌──▼──────┐
│Embedder│ │Search│ │Generator│ │Postgres │
│ :8001  │ │:8003 │ │ :8002  │ │ :5432   │
└───┬────┘ └─┬────┘ └─────────┘ └─────────┘
    │        │
    │   ┌────▼────┐
    └───► Qdrant  │
        │  :6333  │  ←─ Vector Database
        └─────────┘
```

### Microservices

| Service | Responsibility | Tech Stack |
|---------|----------------|------------|
| **API Gateway** | Request orchestration, document CRUD, business logic | FastAPI, SQLAlchemy, PostgreSQL |
| **Search** | Hybrid retrieval (vector + keyword), cross-encoder reranking | FastAPI, Qdrant, sentence-transformers |
| **Embedder** | 384-dimensional vector generation | sentence-transformers (all-MiniLM-L6-v2) |
| **Generator** | AI summaries with citations | OpenAI/Anthropic/Google APIs |
| **Frontend** | Real-time search UI | React 18, TypeScript, Tailwind CSS, shadcn/ui |

### Infrastructure

- **PostgreSQL** – Document metadata and text chunks
- **Qdrant** – Vector storage with HNSW indexing
- **Docker Compose** – Local development
- **Kubernetes** – Production deployment with HPA, rolling updates, health probes

---

## Tech Stack

**Backend:**
- Python 3.13 with async/await patterns
- FastAPI 0.119 for high-performance APIs
- SQLAlchemy 2.0 with asyncpg
- Pydantic v2 for data validation
- sentence-transformers for embeddings
- Qdrant vector database

**Frontend:**
- React 18 with TypeScript
- Vite for fast builds
- React Query for server state
- Tailwind CSS + shadcn/ui components
- Radix UI primitives

**Infrastructure:**
- Docker 24.0+ with multi-stage builds
- Kubernetes with Kustomize
- NGINX Ingress Controller
- Horizontal Pod Autoscaler (HPA)
- Persistent Volumes for stateful services

---

## Quick Start

### Prerequisites

- Docker 24.0+ with Docker Compose 2.0+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- Optional: Python 3.13+ + Poetry, Node.js 18+ for local development

### Setup

1. **Clone and configure**

```bash
# TODO: Replace YOUR_USERNAME with your GitHub username before publishing
git clone https://github.com/YOUR_USERNAME/raas.git
cd raas

# Set up environment variables
cp infrastructure/docker-compose/.env.example infrastructure/docker-compose/.env
# Edit .env and add your API keys:
# OPENAI_API_KEY=sk-your-key-here
# Optional: ANTHROPIC_API_KEY, GOOGLE_API_KEY
```

2. **Start all services**

```bash
docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d

# Wait ~30 seconds for services to initialize
# Then visit:
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

3. **Upload a document and search**

```bash
# Upload a document
curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@example.pdf" \
  -F "title=Example Document"

# Search with AI summary
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key findings?",
    "limit": 10,
    "model": "openai:gpt-4o-mini"
  }'
```

---

## Development

### Local Development Setup

```bash
# Backend (API service)
cd services/api
poetry install
poetry run uvicorn app.main:app --reload --port 8000

# Frontend
cd services/frontend
npm install
npm run dev  # Runs on http://localhost:3000
```

### Running Tests

```bash
# Unit tests per service
cd services/api && poetry run pytest
cd services/embedder && poetry run pytest
cd services/generator && poetry run pytest
cd services/search && poetry run pytest
cd services/frontend && npm test

# Integration test (full workflow)
./tests/integration/test_full_workflow.sh
```

### Code Quality

```bash
# Type checking
cd services/api && poetry run mypy app/

# Linting
cd services/api && poetry run ruff check app/

# Frontend type checking
cd services/frontend && npx tsc --noEmit
```

---

## Kubernetes Deployment

Deploy to a local Kubernetes cluster using [kind](https://kind.sigs.k8s.io/):

```bash
# Automated setup (creates cluster, builds images, deploys)
./infrastructure/scripts/setup-kind-full.sh

# Access services
kubectl port-forward svc/frontend 3000:80 -n raas
kubectl port-forward svc/api 8000:8000 -n raas
```

### Manual Deployment

```bash
# Create kind cluster
kind create cluster --config infrastructure/kind/kind-config.yaml

# Build and load images
docker build -t raas-api:latest -f services/api/Dockerfile services/api
kind load docker-image raas-api:latest

# Deploy with Kustomize
kubectl apply -k infrastructure/k8s/overlays/local/

# Verify deployment
kubectl get pods -n raas
kubectl logs -f deployment/api -n raas
```

See [infrastructure/k8s/README.md](infrastructure/k8s/README.md) for production deployment instructions.

---

## API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/documents` | Upload PDF/DOCX/TXT/CSV/MD file |
| `GET` | `/api/v1/documents` | List all documents |
| `GET` | `/api/v1/documents/{id}` | Get document details |
| `DELETE` | `/api/v1/documents/{id}` | Delete document and vectors |
| `POST` | `/api/v1/search` | Search with optional AI summary |
| `GET` | `/api/v1/models` | List available LLM models |
| `GET` | `/health` | Health check endpoint |

### Example: Search with AI Summary

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "limit": 10,
    "model": "openai:gpt-4o-mini",
    "include_summary": true
  }'
```

Response:
```json
{
  "chunks": [
    {
      "id": "chunk-123",
      "document_id": "doc-456",
      "text": "Machine learning is a subset of AI...",
      "score": 0.89,
      "metadata": {"page": 1, "section": "Introduction"}
    }
  ],
  "summary": "Machine learning is an AI approach... [1] [2]",
  "total": 42
}
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for GPT models |
| `ANTHROPIC_API_KEY` | No | - | Anthropic API key for Claude models |
| `GOOGLE_API_KEY` | No | - | Google API key for Gemini models |
| `DEFAULT_MODEL` | No | `openai:gpt-4o-mini` | Default model for summaries |
| `DATABASE_URL` | No | Auto-generated | PostgreSQL connection string |
| `QDRANT_URL` | No | `http://qdrant:6333` | Qdrant vector database URL |

See individual service `.env.example` files for complete configuration options.

---

## Project Structure

```
raas/
├── services/
│   ├── api/              # FastAPI gateway service
│   │   ├── app/
│   │   │   ├── api/      # Route handlers
│   │   │   ├── domain/   # Business logic
│   │   │   ├── models/   # SQLAlchemy models
│   │   │   └── repositories/  # Data access layer
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── embedder/         # Vector generation service
│   ├── generator/        # LLM summarization service
│   ├── search/           # Hybrid search service
│   └── frontend/         # React SPA
│       ├── src/
│       │   ├── components/
│       │   ├── hooks/
│       │   └── services/
│       └── package.json
├── infrastructure/
│   ├── docker-compose/   # Local development
│   │   ├── docker-compose.yml
│   │   └── .env.example
│   ├── k8s/              # Kubernetes manifests
│   │   ├── base/
│   │   └── overlays/
│   ├── kind/             # Local Kubernetes setup
│   └── scripts/
└── tests/
    └── integration/
```

---

## Extending the Platform

### Adding a New LLM Provider

1. Create a provider class in `services/generator/app/providers/`:

```python
from app.providers.base import ModelProvider

class MyProvider(ModelProvider):
    async def generate(self, prompt: str, **kwargs) -> str:
        # Implementation here
        pass
```

2. Register in `services/generator/app/main.py`:

```python
from app.providers.my_provider import MyProvider

providers = {
    "my-provider": MyProvider(api_key=os.getenv("MY_PROVIDER_API_KEY"))
}
```

3. Add credentials to `.env`:

```bash
MY_PROVIDER_API_KEY=your-key-here
```

See [services/generator/README.md](services/generator/README.md) for detailed examples.

---

## Performance & Scaling

### Benchmarks

- **Search latency**: <100ms for hybrid search (p95)
- **Embedding generation**: ~50ms per 512-token chunk
- **AI summary generation**: 2-5s depending on provider and model
- **Throughput**: 100+ concurrent search requests (with HPA)

### Horizontal Pod Autoscaler

Services automatically scale based on resource utilization:

```yaml
# Example HPA configuration
minReplicas: 2
maxReplicas: 5
targetCPUUtilizationPercentage: 70
targetMemoryUtilizationPercentage: 80
```

---

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose -f infrastructure/docker-compose/docker-compose.yml logs -f

# Restart individual service
docker-compose restart api
```

### No search results

```bash
# Verify documents were uploaded
curl http://localhost:8000/api/v1/documents | jq

# Check Qdrant collection
curl http://localhost:6333/collections/documents | jq '.result'
```

### Database connection issues

```bash
# Access PostgreSQL
docker exec -it raas-postgres psql -U raasuser -d raasdb

# List tables
\dt

# Check documents
SELECT id, title, status FROM documents;
```

### Kubernetes pod crashes

```bash
# Check pod status
kubectl get pods -n raas

# View logs
kubectl logs -f deployment/api -n raas

# Describe pod for events
kubectl describe pod <pod-name> -n raas
```

---

## Technical Highlights

### Architecture Decisions

- **Microservices**: Independent scaling of compute-intensive services (embedder, search)
- **Async/Await**: Non-blocking I/O throughout the stack for high concurrency
- **Repository Pattern**: Clean separation of data access from business logic
- **Type Safety**: Pydantic v2 + TypeScript for compile-time guarantees
- **Health Probes**: Kubernetes liveness/readiness checks for automatic recovery
- **Rolling Updates**: Zero-downtime deployments with automatic rollback

### Search Algorithm

1. **Query Embedding**: Convert search query to 384-dimensional vector
2. **Hybrid Retrieval**:
   - Vector search (Qdrant HNSW index)
   - Keyword search (PostgreSQL full-text)
3. **RRF Fusion**: Combine rankings using Reciprocal Rank Fusion
4. **Cross-Encoder Reranking**: Precision scoring for top-k results
5. **AI Summarization**: Generate contextual answer with citations

---

## Testing

- **47 test files** across all services
- **Unit tests** with pytest and Jest
- **Integration tests** for end-to-end workflows
- **Type checking** with mypy (strict mode)
- **Linting** with Ruff and ESLint

```bash
# Run all tests
./tests/integration/test_full_workflow.sh

# With coverage
cd services/api && poetry run pytest --cov=app --cov-report=html
```

---

## Contributing

This is a portfolio/academic project created as a final university assignment. While active development is not planned, contributions for bug fixes, documentation improvements, and educational enhancements are welcome!

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests
4. Run tests: `poetry run pytest` (backend) or `npm test` (frontend)
5. Commit changes: `git commit -am 'feat: add my feature'`
6. Push to branch: `git push origin feature/my-feature`
7. Open a Pull Request

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Contact & Links

<!-- TODO: Update with your actual contact information before publishing -->

**Author:** Michael Blauberg
**Email:** mblauberg@outlook.com
**LinkedIn:** [linkedin.com/in/mblauberg](https://linkedin.com/in/mblauberg)

**Project Links:**
- [Report Issues](../../issues)
- [Security Policy](SECURITY.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), and [Kubernetes](https://kubernetes.io/)
- Vector search powered by [Qdrant](https://qdrant.tech/)
- Embeddings from [sentence-transformers](https://www.sbert.net/)
- UI components from [shadcn/ui](https://ui.shadcn.com/)
