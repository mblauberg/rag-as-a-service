# Local Development & Testing (Phase 3)

This document outlines the configuration for local development using Docker Compose and describes the testing strategy for RAAS. Claude Code should follow these guidelines when generating `docker-compose` files and test suites.

## Docker Compose for development

To run all services locally during development, use a Docker Compose configuration similar to the one below.  It defines containers for PostgreSQL, Qdrant, the API service, the embedder service and the frontend.  The file is typically located at `infrastructure/docker-compose/docker-compose.dev.yml`.

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:15-alpine
    container_name: raas-postgres
    environment:
      POSTGRES_DB: raas_dev
      POSTGRES_USER: raas_user
      POSTGRES_PASSWORD: raas_pass_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ../../services/api/app/migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U raas_user -d raas_dev"]
      interval: 5s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: raas-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334

  api:
    build:
      context: ../../services/api
      dockerfile: Dockerfile
    container_name: raas-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://raas_user:raas_pass_dev@postgres:5432/raas_dev
      - QDRANT_URL=http://qdrant:6333
      - EMBEDDER_URL=http://embedder:8001
      - UPLOAD_DIR=/app/uploads
    volumes:
      - ../../services/api:/app
      - upload_data:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_started
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  embedder:
    build:
      context: ../../services/embedder
      dockerfile: Dockerfile
    container_name: raas-embedder
    ports:
      - "8001:8001"
    environment:
      - QDRANT_URL=http://qdrant:6333
      - MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
    volumes:
      - ../../services/embedder:/app
      - model_cache:/root/.cache/torch
    depends_on:
      - qdrant
    command: uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

  frontend:
    build:
      context: ../../services/frontend
      dockerfile: Dockerfile.dev
    container_name: raas-frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ../../services/frontend:/app
      - /app/node_modules
    command: npm run dev

volumes:
  postgres_data:
  qdrant_data:
  upload_data:
  model_cache:
```

## Testing strategy

Testing is critical to ensure reliability.  The following strategies should be adopted:

### Unit tests

- **API service**: Use `pytest` and `pytest-asyncio` to test each endpoint.  Mock external dependencies such as the embedder service and Qdrant.  Aim for at least 70% code coverage.
- **Embedding service**: Test embedding generation and error handling by mocking the Qdrant client.  Verify that embeddings are generated for a sample input and stored successfully.

### Integration tests

Integration tests should simulate the end‑to‑end workflow: uploading a document, triggering embedding, performing a search and verifying that the results contain expected chunks.  Use the actual Docker Compose environment or a test instance of PostgreSQL and Qdrant.  Place these tests under `tests/integration/`.

### Load testing

To demonstrate scalability during the final demo, a simple load test script can perform concurrent uploads and search queries.  An example `tests/load-test.sh` is provided in the PRD.  It uploads multiple documents in parallel and issues numerous search requests, verifying that the API remains responsive.

This file gives Claude Code the context necessary to generate the Docker Compose configuration and to scaffold comprehensive tests.  Remember to follow the guidelines for `CLAUDE.md` when documenting bash commands and testing procedures【860557105589140†L48-L61】.