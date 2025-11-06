# RAaS – Retrieval-Augmented Generation as a Service

Search documents with natural language and get AI-powered answers with source citations.

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.119-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

![RAaS Demo](docs/images/main-page-example.png)
*Upload documents, ask questions, get AI summaries with citations*

![RAaS Search Demo](docs/images/search-example.gif)
*Retrieve document summaries plus the retrieved, ranked document chunks*

---

## What It Does

Upload PDFs, DOCX, or text files and query them using plain English. RAaS combines vector similarity search with keyword matching, then generates contextual answers with inline citations showing exactly where information came from.

**Example:** Search "contract violations" → Finds "breach of agreement", "non-compliance", etc. → Generates summary: *"The agreement was violated on three occasions [1][2]..."*

### Features

- Semantic search understanding meaning beyond keywords
- Multi-provider LLM support (OpenAI, Anthropic, Google)
- Hybrid retrieval with cross-encoder reranking
- Document format support: PDF, DOCX, TXT, CSV, Markdown
- Kubernetes deployment with autoscaling

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### 1. Set Up API Keys

Run the setup script:
```bash
./scripts/setup-secrets.sh
```

Or manually create `.env`:
```bash
cp .env.template .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Start Services

```bash
docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d
```

Wait 2-3 minutes for services to initialize (downloads ML models on first run).

### 3. Use the Application

Open http://localhost:3000

1. Click "Upload Document" and select a file
2. Wait for processing (a few seconds)
3. Type a question in the search bar
4. Toggle "Generate Summary" for AI answers with citations

**Access points:**
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- API: http://localhost:8000

---

## Architecture

```
┌──────────┐
│ Frontend │ React + TypeScript
│  :3000   │
└────┬─────┘
     │
┌────▼─────┐
│   API    │ Request orchestration
│  :8000   │
└────┬─────┘
     │
     ├─────► Embedder :8001   (Text → Vectors)
     ├─────► Search :8003     (Hybrid search + reranking)
     ├─────► Generator :8002  (AI summaries)
     ├─────► Postgres :5432   (Metadata + chunks)
     └─────► Qdrant :6333     (Vector database)
```

### Services

| Service | Purpose | Key Tech |
|---------|---------|----------|
| **API** | Gateway & orchestration | FastAPI, SQLAlchemy, PostgreSQL |
| **Search** | Hybrid search + reranking | Qdrant, sentence-transformers, cross-encoder |
| **Embedder** | Text embedding generation | all-MiniLM-L6-v2 (384-dim vectors) |
| **Generator** | AI summary generation | OpenAI/Anthropic/Google APIs |
| **Frontend** | User interface | React 18, TypeScript, Tailwind, shadcn/ui |

### Search Pipeline

1. **Query embedding** → 384-dimensional vector
2. **Hybrid retrieval** → Vector search (Qdrant) + keyword search (Postgres)
3. **RRF fusion** → Merge results using Reciprocal Rank Fusion
4. **Cross-encoder reranking** → Score top results for relevance
5. **AI generation** → Summary with inline citations [1][2][3]

---

## API Usage

### Search Documents

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 10}'
```

Response:
```json
{
  "results": [{
    "chunk_id": "abc-123",
    "content": "Machine learning is a subset of AI...",
    "score": 0.89
  }]
}
```

### Generate AI Summary

```bash
curl -X POST http://localhost:8000/api/v1/generate/summary \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "chunk_ids": ["abc-123", "def-456"],
    "model": "gpt-5-mini"
  }'
```

Response:
```json
{
  "summary": "Machine learning enables computers to learn from data [1]...",
  "model_used": "gpt-5-mini"
}
```

See full API reference at http://localhost:8000/docs

---

## Deployment

### Docker Compose (Development)

```bash
# Start
docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d

# Stop
docker-compose -f infrastructure/docker-compose/docker-compose.yml down

# View logs
docker-compose -f infrastructure/docker-compose/docker-compose.yml logs -f
```

### Kubernetes (Production)

```bash
# Automated setup (creates kind cluster, builds images, deploys)
./infrastructure/scripts/setup-kind-full.sh

# Manual deployment
kind create cluster --config infrastructure/kind/kind-config.yaml
docker build -t raas-api:latest -f services/api/Dockerfile services/api
kind load docker-image raas-api:latest
kubectl apply -k infrastructure/k8s/overlays/local/

# Access services
kubectl port-forward svc/frontend 3000:3000 -n raas
kubectl port-forward svc/api 8000:8000 -n raas
```

**Note:** Services use ClusterIP by default. Use `kubectl port-forward` or setup an ingress controller for external access.

See [infrastructure/k8s/README.md](infrastructure/k8s/README.md) for production deployment.

---

## Development

### Local Setup

```bash
# Backend
cd services/api
poetry install
poetry run uvicorn app.main:app --reload

# Frontend
cd services/frontend
npm install
npm run dev
```

### Testing

```bash
# Unit tests
cd services/api && poetry run pytest
cd services/frontend && npm test

# Integration test (full workflow)
./tests/integration/test_full_workflow.sh

# Type checking
cd services/api && poetry run mypy app/
cd services/frontend && npx tsc --noEmit
```

### Project Structure

```
raas/
├── services/
│   ├── api/          FastAPI gateway
│   ├── embedder/     Vector generation
│   ├── generator/    LLM summaries
│   ├── search/       Hybrid search
│   └── frontend/     React UI
├── infrastructure/
│   ├── docker-compose/
│   └── k8s/          Kubernetes manifests
└── tests/
    └── integration/
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | - | Anthropic API key |
| `GOOGLE_API_KEY` | No | - | Google API key |
| `DEFAULT_MODEL` | No | `gpt-5-mini` | Default LLM model |
| `DATABASE_URL` | No | Auto | PostgreSQL connection |
| `QDRANT_URL` | No | `http://qdrant:6333` | Vector DB URL |

### Generator Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CHUNKS` | `5` | Max chunks for context |
| `TEMPERATURE` | `0.1` | LLM temperature (0.0-1.0) |
| `MAX_TOKENS` | `2000` | Max response tokens |
| `TIMEOUT` | `30` | API timeout (seconds) |

---

## Troubleshooting

**Services won't start**
```bash
# Check logs
docker-compose -f infrastructure/docker-compose/docker-compose.yml logs -f

# Verify .env file exists and has valid keys
cat .env
```

**"OPENAI_API_KEY is required" error**
```bash
# Run setup script
./scripts/setup-secrets.sh

# Or manually check .env file
grep OPENAI_API_KEY .env
```

**No search results**
```bash
# Verify documents uploaded
curl http://localhost:8000/api/v1/documents | jq

# Check Qdrant collection
curl http://localhost:6333/collections/documents | jq
```

**Kubernetes pod crashes**
```bash
kubectl get pods -n raas
kubectl logs -f deployment/api -n raas
kubectl describe pod <pod-name> -n raas
```

---

## Performance

- **Search latency:** <100ms (95th percentile)
- **Embedding:** ~50ms per 512-token chunk
- **AI generation:** 2-5 seconds (model dependent)
- **Throughput:** 100+ concurrent searches with autoscaling

Kubernetes deployment includes Horizontal Pod Autoscalers for API, embedder, generator, and search services.

---

## Extending

### Add a New LLM Provider

1. Create provider class in `services/generator/app/providers/`:

```python
from app.providers.base import ModelProvider

class MyProvider(ModelProvider):
    async def generate(self, prompt: str, **kwargs) -> str:
        # Implementation
        pass
```

2. Register in `services/generator/app/main.py`:

```python
providers = {
    "my-provider": MyProvider(api_key=os.getenv("MY_PROVIDER_KEY"))
}
```

3. Add credentials to `.env`:

```bash
MY_PROVIDER_KEY=your-key-here
```

See [services/generator/README.md](services/generator/README.md) for details.

---

## Contributing

This is a portfolio and academic project, but contributions are welcome. Focus areas:

- Bug fixes
- Documentation improvements
- Educational enhancements

### Steps

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests for changes
4. Run tests: `poetry run pytest` or `npm test`
5. Commit: `git commit -am 'Add feature'`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Contact

**Michael Blauberg**
- Email: mblauberg@outlook.com
- LinkedIn: [linkedin.com/in/mblauberg](https://linkedin.com/in/mblauberg)

**Project Links**
- [Report Issues](../../issues)
- [Security Policy](SECURITY.md)
