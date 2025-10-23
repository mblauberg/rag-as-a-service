# Embedding Service Specification (Phase 1)

This document outlines the requirements for the embedding service, which is responsible for generating vector representations of text chunks and search queries using a sentence‑transformers model, and storing them in Qdrant. It should be implemented as a separate FastAPI service.

## Overview

The embedding service exposes endpoints that accept text chunks or queries, generates dense embeddings using a pre‑trained sentence‑transformers model (for example, `all-MiniLM-L6-v2`), and communicates with Qdrant to store or search vectors. It is a standalone microservice listening on port 8001. The API service will call this service to embed document chunks after upload and to embed user queries during search.

## Directory structure

The service should follow this structure:

```
services/embedder/
├── app/
│   ├── main.py                # FastAPI application entrypoint
│   ├── core/
│   │   ├── config.py          # Settings (Qdrant URL, model name, batch size)
│   │   ├── model.py           # Model loading logic (optional separation)
│   │   └── qdrant_client.py   # Qdrant client and collection initialization
│   ├── services/
│   │   └── embedding_service.py  # Embedding logic and Qdrant upsert/delete
│   ├── models/
│   │   └── schemas.py         # Pydantic request/response models
├── tests/
│   └── test_embeddings.py      # Unit tests for embedding endpoints
├── Dockerfile                 # Container definition
├── pyproject.toml             # Poetry configuration
└── .env.example              # Example environment variables
```

## Endpoints

| Method & path | Description |
|---|---|
| `POST /embed` | Accepts a JSON body containing a list of text chunks with metadata. Generates embeddings in batches, stores them in a Qdrant collection named `documents`, and returns `success: true` with the count of processed chunks. |
| `POST /embed-query` | Accepts a JSON body with a `query` string. Returns the embedding vector as a list of floats, which the API service uses for searching. |
| `GET /health` | Returns `status: healthy` if the service is running. |
| `GET /ready` | Returns `status: ready` when the model has finished loading. This is used as a readiness probe in Kubernetes. |

## Qdrant collection schema

The embedder should ensure that a collection named `documents` exists in Qdrant with 384‑dimensional vectors and cosine distance. This can be done at startup:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

def initialize_collection(client: QdrantClient, collection_name: str = "documents"):
    collections = client.get_collections().collections
    if collection_name not in [c.name for c in collections]:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )
```

## Technical guidelines

- Load the sentence‑transformers model (for example `all-MiniLM-L6-v2`) once at startup to avoid repeated downloads. The model dimension is 384.
- Process chunks in batches (e.g. 32 at a time) to optimise performance.
- When storing vectors in Qdrant, include metadata payloads for `document_id`, `chunk_index` and the original text, using `PointStruct` for upsert operations.
- Provide endpoints for health and readiness so Kubernetes can manage the service.
- Use a proper logging mechanism and avoid printing to stdout, as writing to stdout can corrupt JSON‑RPC messages when building MCP servers【292313839669692†L118-L130】.

This specification provides the context Claude Code needs to implement the embedder service correctly. Refer back to the PRD for more details on integration with other components.