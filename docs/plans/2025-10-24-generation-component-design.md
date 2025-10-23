# Generation Component Design

**Date:** 2025-10-24
**Status:** Approved
**Author:** Design Session with Claude Code

## Overview

This design adds the "G" (Generation) to RAAS, transforming it from a pure retrieval system into a full Retrieval-Augmented Generation (RAG) service. The system will generate LLM-based summaries with inline citations from retrieved document chunks.

## Requirements

### Functional Requirements
- Generate summaries from retrieved document chunks with inline citations
- Support multiple LLM models selectable from frontend
- Always show summary at top, followed by cited document chunks
- Citations link to corresponding chunks in results
- Self-hosted LLM (Ollama) with architecture for future cloud API support

### Non-Functional Requirements
- **Priority:** Implementation simplicity - start with self-hosted, add cloud later
- **Architecture:** New Generator microservice following existing pattern
- **UX:** Modern, minimal design with progressive loading states
- **Reliability:** Graceful degradation if generation fails

## Architecture Overview

### High-Level Data Flow

```
Frontend → API → Qdrant (search) → Generator (synthesis) → API → Frontend
                                    ↓
                                  Ollama
```

### Search Flow with Generation

1. **Frontend** sends search query with selected model
2. **API** performs vector search via Qdrant (existing flow)
3. **API** retrieves top-K document chunks with relevance scores
4. **API** sends query + chunks + model to Generator service
5. **Generator** formats chunks with citation markers, calls Ollama, returns synthesis
6. **API** returns response: `{summary, chunks, query, model_used}`
7. **Frontend** displays:
   - Summary at top with inline citation links `[1]`, `[2]`
   - Chunks list below, numbered and clickable from citations

## Component Design

### 1. Generator Service (New)

**Technology:**
- FastAPI (Python) on port 8002
- `ollama` Python client library
- Poetry for dependency management

**Key Endpoints:**

```python
POST /api/v1/generate
Request: {
  query: str,
  chunks: [{text: str, document_id: str, chunk_index: int}],
  model: str
}
Response: {
  summary: str,
  model_used: str,
  tokens_used: int
}

GET /api/v1/models
Response: {
  models: [{name: str, size: str, modified_at: str}]
}

GET /health          # Liveness probe
GET /ready           # Readiness probe (checks Ollama connectivity)
```

**RAG Prompt Template:**

```
You are a helpful assistant. Answer the user's question based ONLY on the provided context.
Cite sources using [1], [2], etc. to reference the document chunks.

Context:
[1] {chunk_1_text}
[2] {chunk_2_text}
...

Question: {user_query}

Answer with inline citations:
```

**Configuration:**
- `OLLAMA_URL` - URL to Ollama server (default: `http://ollama:11434`)
- `DEFAULT_MODEL` - Fallback model (default: `llama3.2`)
- `MAX_CHUNKS` - Max chunks to include in context (default: 5)
- `TEMPERATURE` - LLM temperature (default: 0.1 for factual responses)

**Service Structure:**
```
services/generator/
├── app/
│   ├── main.py                 # FastAPI app
│   ├── api/
│   │   └── routes/
│   │       ├── generate.py     # Generation endpoints
│   │       └── models.py       # Model listing
│   ├── services/
│   │   ├── ollama_client.py    # Ollama API wrapper
│   │   └── prompt_service.py   # Prompt template management
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   └── config.py               # Configuration
├── tests/
├── pyproject.toml
└── Dockerfile
```

### 2. API Service Modifications

**New Environment Variable:**
- `GENERATOR_URL` - URL to Generator service (default: `http://generator:8002`)

**Modified Search Endpoint:**

```python
POST /api/v1/search
Request: {
  query: str,
  limit: int = 10,
  model: str  # NEW: Selected model for generation
}
Response: {
  query: str,
  summary: str | None,        # null if generation failed
  chunks: list[ChunkResult],
  model_used: str | None,
  total_results: int
}
```

**Implementation:**
1. Perform existing Qdrant vector search
2. Call Generator service with query + chunks + model
3. Include summary in response alongside chunks
4. Handle Generator errors gracefully (return chunks without summary if fails)

**New Models Endpoint:**

```python
GET /api/v1/models
Response: {
  models: list[Model]  # Proxied from Generator
}
```

- Proxy to Generator's `/api/v1/models` endpoint
- Cache results for 5 minutes to reduce load

**Error Handling:**
- Generator unavailable → log warning, return chunks only with `summary: null`
- Model not found → use default model, log warning
- Timeout → 30 seconds (configurable)

### 3. Frontend Modifications

**UI Components (Modern, Minimal Design):**

1. **Model Selector:**
   - Single-select dropdown above search bar
   - Label: "Model" with subtle size info (e.g., "llama3.2 • 2GB")
   - Default to last-used model (localStorage) or first available
   - Fetch models from `GET /api/v1/models` on mount

2. **Summary Display (Top Section):**
   - Clean card with larger typography
   - Summary text with inline citation links `[1]`, `[2]` as clickable chips/badges
   - Clicking citation scrolls to and highlights corresponding chunk
   - Footer: "Generated by {model}" (subtle)
   - Loading state: Skeleton placeholder with shimmer effect

3. **Document Chunks (Below Summary):**
   - Each chunk numbered `[1]`, `[2]`, etc. matching citations
   - Card layout: document title, relevance score (subtle), text excerpt
   - Highlight target chunk when clicked from citation
   - Smooth scroll animation

**Loading States:**
- Progressive: "Searching..." → "Generating summary..." status updates
- Skeleton loaders for summary and chunks during generation

**Error States:**
- Summary generation failed → Show chunks only with info banner "Summary unavailable"
- No results → Empty state illustration with helpful message

**TypeScript Types:**

```typescript
interface SearchResponse {
  query: string
  summary: string | null
  chunks: ChunkResult[]
  model_used: string | null
  total_results: number
}

interface ChunkResult {
  id: number
  text: string
  document_id: string
  document_title: string
  score: number
}

interface Model {
  name: string
  size: string
  modified_at: string
}
```

## Infrastructure & Deployment

### Docker Compose

**New Services:**

```yaml
ollama:
  image: ollama/ollama:latest
  ports:
    - "11434:11434"
  volumes:
    - ollama-data:/root/.ollama  # Persist downloaded models
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
    interval: 10s
    timeout: 5s
    retries: 5

generator:
  build: ./services/generator
  ports:
    - "8002:8002"
  environment:
    - OLLAMA_URL=http://ollama:11434
    - DEFAULT_MODEL=llama3.2
    - MAX_CHUNKS=5
    - TEMPERATURE=0.1
  depends_on:
    ollama:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
    interval: 10s
    timeout: 5s
    retries: 3

volumes:
  ollama-data:  # Store downloaded models
```

**API Service Update:**
```yaml
api:
  environment:
    - GENERATOR_URL=http://generator:8002
```

### Kubernetes

**New Resources:**

1. **Ollama Deployment:**
   - PVC for model storage (10Gi)
   - Resource limits: 4 CPU, 8Gi memory (GPU optional for production)
   - Service: ClusterIP on port 11434

2. **Generator Deployment:**
   - HPA: 2-10 replicas based on CPU (70%) and memory (80%)
   - Resource requests: 500m CPU, 1Gi memory
   - Service: ClusterIP on port 8002
   - ConfigMap for settings (default model, temperature, etc.)

3. **Model Initialization:**
   - Init container to pull default models on first startup
   - Environment variable: `MODELS_TO_PRELOAD=llama3.2,mistral`
   - Generator waits for at least one model before marking ready

**File Structure:**
```
infrastructure/k8s/base/
├── generator/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml
│   └── configmap.yaml
└── ollama/
    ├── deployment.yaml
    ├── service.yaml
    └── pvc.yaml
```

## Testing Strategy

### Unit Tests

**Generator Service:**
- Prompt template formatting
- Citation marker injection
- Model validation logic
- Configuration parsing

**API Service:**
- Search endpoint with model parameter
- Generator client error handling
- Model listing with caching

### Integration Tests

**Generator Service:**
- Mock Ollama responses
- Test error handling: missing model, timeout, malformed chunks
- Readiness probe with Ollama connectivity

**API Service:**
- End-to-end search with generation
- Graceful degradation when Generator unavailable
- Model listing endpoint behavior

### Frontend Tests

**Component Tests:**
- Model selector state management
- Citation link click → scroll to chunk
- Loading/error states rendering

**Integration:**
- Search flow with model selection
- Citation highlighting and scroll behavior

### End-to-End Test

```bash
1. Upload test document
2. Perform search with generation (model: llama3.2)
3. Verify summary contains citations [1], [2], etc.
4. Click citation [1]
5. Verify scroll to chunk #1 with highlight
6. Verify model_used in response
```

## Error Handling

### Error Scenarios & Responses

| Scenario | Handling | User Experience |
|----------|----------|-----------------|
| Generator unavailable | Return chunks only, `summary: null` | Show chunks with banner "Summary unavailable" |
| Model not found | Fall back to default model, log warning | Generate with default, show which model used |
| Ollama timeout (30s) | Return error to API | Show chunks with error banner |
| No chunks found | Skip generation | Empty state message |
| Invalid citations in summary | Display as-is, log warning | Summary shown with malformed citations |

### Logging & Monitoring

**Generator Service Metrics:**
- Generation requests: query, model, token count, latency
- Success/failure rates by model
- Ollama model loading times
- Error types and frequencies

**API Service Metrics:**
- Generator availability
- Request latency (with vs without generation)
- Cache hit rates for model listing

## Future Enhancements (Out of Scope)

1. **Cloud API Support:**
   - Add OpenAI/Anthropic provider alongside Ollama
   - Abstract LLM client interface
   - Configuration-based provider selection

2. **Response Caching:**
   - Cache generated summaries (keyed by query + chunks)
   - Redis/in-memory cache with TTL
   - Reduce redundant generation costs

3. **Streaming Responses:**
   - SSE/WebSocket for progressive summary display
   - Better UX for long generations

4. **Advanced Features:**
   - Multi-turn conversations with context
   - Clarifying questions before synthesis
   - Custom prompt templates per use case

## Implementation Phases

### Phase 1: Core Generation (MVP)
- Implement Generator service with Ollama integration
- Add `/generate` endpoint with basic prompt template
- Update API search endpoint to call Generator
- Docker Compose setup with Ollama

### Phase 2: Frontend Integration
- Add model selector to search interface
- Implement summary display with citations
- Add citation click → scroll behavior
- Loading and error states

### Phase 3: Kubernetes & Production
- Create K8s manifests for Generator and Ollama
- Set up HPA and resource management
- Add monitoring and logging
- Integration tests

### Phase 4: Polish & Testing
- Comprehensive error handling
- End-to-end tests
- Performance optimization
- Documentation updates

## Success Criteria

- [ ] Users can select LLM model from frontend dropdown
- [ ] Search results show summary with inline citations at top
- [ ] Citations link to and highlight corresponding chunks
- [ ] System degrades gracefully if generation fails (shows chunks)
- [ ] Generator service follows existing microservice pattern
- [ ] Docker Compose and Kubernetes deployments working
- [ ] End-to-end tests passing
- [ ] Performance: Search + generation completes in <10s for typical query
