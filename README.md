# RAaS – Retrieval-Augmented Generation as a Service

A microservices-based document search platform that combines vector embeddings with LLM-powered summarization.

> Academic project for INFS3208 (Cloud Computing), University of Queensland, 2025

## What it does

RAaS lets you upload documents and search them semantically. Instead of just matching keywords, it understands meaning and generates AI summaries with citations.

- Hybrid search using vector similarity and keyword matching (RRF fusion)
- AI-generated summaries from OpenAI, Anthropic, or Google models with inline citations
- Upload PDFs, DOCX, or TXT files with automatic text chunking
- Cross-encoder reranking for improved result relevance
- React frontend with real-time search UI

## Architecture

```
        ┌──────────┐
        │ Frontend │ :3000
        └─────┬────┘
              │
        ┌─────▼─────┐
        │    API    │
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
        │  :6333  │
        └─────────┘
```

Services:
- API (FastAPI) - orchestrates requests, manages document CRUD
- Search (FastAPI) - hybrid retrieval with cross-encoder reranking
- Embedder (FastAPI) - generates vectors using sentence-transformers
- Generator (FastAPI) - creates summaries via OpenAI/Anthropic/Google
- Frontend (React) - single-page app with live search

Infrastructure:
- PostgreSQL stores document metadata
- Qdrant handles vector storage and similarity search
- Runs on Docker Compose or Kubernetes

## Tech Stack

Backend: Python 3.13, FastAPI, SQLAlchemy, Pydantic v2, sentence-transformers, Qdrant, httpx

Frontend: React 18, TypeScript, Vite, React Query, Tailwind CSS, shadcn/ui, Radix UI

## Quick Start

### Prerequisites

- Docker 24.0+ with Docker Compose 2.0+
- OpenAI API key (get one at https://platform.openai.com/api-keys)
- Optional: Python 3.13+ + Poetry, Node.js 18+ for local development

### Setup

1. Configure API keys

```bash
cp infrastructure/docker-compose/.env.example infrastructure/docker-compose/.env
# Edit .env and set OPENAI_API_KEY=sk-your-key-here
# (Optional: ANTHROPIC_API_KEY, GOOGLE_API_KEY for other providers)
```

2. Start services

```bash
docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d

# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

For local development:

```bash
# Backend services
cd services/api && poetry install && poetry run uvicorn app.main:app --reload

# Frontend
cd services/frontend && npm install && npm run dev
```

## Usage

Once running, visit http://localhost:3000 to upload documents and search. The API is available at http://localhost:8000/docs for direct testing.

Key endpoints:
- `POST /api/v1/documents` - upload PDF/DOCX/TXT
- `POST /api/v1/search` - search with optional AI summary
- `GET /api/v1/models` - list available LLM models

Example search request:

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "what is machine learning?",
    "limit": 10,
    "model": "openai:gpt-4o-mini"
  }'
```

Returns chunks with an AI-generated summary and inline citations like [1] [2].

## Configuration

Provider settings in `infrastructure/docker-compose/.env`:

```bash
# Required
OPENAI_API_KEY=sk-your-key
DEFAULT_MODEL=openai:gpt-4o-mini

# Optional providers
ANTHROPIC_API_KEY=sk-ant-your-key
GOOGLE_API_KEY=your-key
```

Each service has its own `.env.example` with detailed options.

## Testing

Unit tests per service:

```bash
cd services/api && poetry run pytest
cd services/embedder && poetry run pytest
cd services/generator && poetry run pytest
cd services/search && poetry run pytest
cd services/frontend && npm test
```

Full integration test:

```bash
./tests/integration/test_full_workflow.sh
```

## Kubernetes

For local Kubernetes deployment with kind:

```bash
./infrastructure/scripts/setup-kind-full.sh
# or manually: kubectl apply -k infrastructure/k8s/overlays/local/

kubectl port-forward svc/frontend 3000:80 -n raas
kubectl port-forward svc/api 8000:8000 -n raas
```

More details in [infrastructure/k8s/README.md](infrastructure/k8s/README.md).

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

## Extending

To add a new LLM provider:

1. Create provider class in `services/generator/app/providers/`
2. Implement the `ModelProvider` interface
3. Register it in `app/main.py`
4. Add credentials to `.env`

Check [services/generator/README.md](services/generator/README.md) for examples.

## Troubleshooting

Services won't start? Check logs:
```bash
docker-compose -f infrastructure/docker-compose/docker-compose.yml logs -f
```

No search results? Verify embeddings were created:
```bash
curl http://localhost:8000/api/v1/documents | jq '.[] | {id, title}'
curl http://localhost:6333/collections/documents | jq '.result'
```

Database connection issues:
```bash
docker exec -it raas-postgres psql -U raasuser -d raasdb -c '\dt'
```

## License

Academic project - INFS3208, University of Queensland, 2025.
