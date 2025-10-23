# API Service Specification (Phase 1)

This document describes the requirements and structure of the FastAPI gateway service for RAAS.  It defines the endpoints, models, and overall architecture that Claude Code should implement. Use this as a reference when generating or reviewing API code.

## Overview

The API service acts as the gateway for the RAAS platform.  It handles file uploads, manages document metadata in PostgreSQL, interacts with the embedder service to generate vector embeddings, and performs semantic search queries using Qdrant.  The service is written in Python 3.11 with FastAPI and uses asynchronous database access via `asyncpg` and SQLAlchemy.

## Directory structure

The API service should be organised according to the following layout:

```
services/api/
├── app/
│   ├── main.py               # FastAPI entrypoint
│   ├── api/
│   │   ├── routes/
│   │   │   ├── documents.py  # Document upload, listing, detail and deletion
│   │   │   ├── search.py     # Semantic search endpoint
│   │   │   └── health.py     # Health and readiness probes
│   ├── core/
│   │   ├── config.py         # Settings loaded from environment variables
│   │   ├── database.py       # Async database connection and session
│   │   └── qdrant_client.py  # Qdrant client wrapper
│   ├── models/
│   │   ├── document.py       # SQLAlchemy models
│   │   └── schemas.py        # Pydantic request/response models
│   ├── services/
│   │   ├── document_service.py  # Document processing logic
│   │   ├── chunking_service.py   # Text chunking utility
│   │   └── embedder_client.py    # Async client for the embedder service
│   └── utils/
│       └── file_processing.py    # File type detection and text extraction
├── tests/                   # Unit tests for API functionality
├── Dockerfile               # Container definition
├── pyproject.toml           # Poetry configuration
├── poetry.lock              # Frozen dependency versions
└── .env.example             # Example environment variables
```

## Endpoints

Implement the following REST endpoints under the `/api/v1` prefix.  Use Pydantic v2 for request and response models.  Add proper error handling and validation.

| Method & path | Description |
|---|---|
| `POST /api/v1/documents/upload` | Accepts a multipart file upload along with optional title and description.  Saves the file to disk, extracts text, chunks it, stores document metadata and chunks in PostgreSQL, and triggers embedding generation.  Returns document details and processing status. |
| `GET /api/v1/documents` | Returns a paginated list of documents with metadata such as title, filename, size, chunk count, embedding status and creation date.  Supports `page` and `limit` query parameters. |
| `GET /api/v1/documents/{id}` | Retrieves details of a single document by UUID, including its chunks. |
| `DELETE /api/v1/documents/{id}` | Deletes a document: removes vectors from Qdrant, deletes the file from disk and removes records from the database. |
| `POST /api/v1/search` | Performs a semantic search.  Accepts a query string and optional list of document IDs to filter.  Sends the query to the embedder service to generate an embedding, queries Qdrant for similar vectors, joins results with PostgreSQL metadata, and returns ranked chunks. |
| `GET /api/v1/health` | Health probe returning `status: healthy` if the service is running. |
| `GET /api/v1/health/ready` | Readiness probe that checks connectivity to the database, Qdrant and the embedder service, returning detailed status for each. |

## Database schema

Define the initial PostgreSQL schema in `services/api/app/migrations/001_initial.sql`:

```sql
-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    file_name VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    upload_status VARCHAR(50) DEFAULT 'pending',
    embedding_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chunks table
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    qdrant_point_id UUID,
    token_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

-- Indexes for efficient queries
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_documents_status ON documents(embedding_status);
CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_qdrant_id ON document_chunks(qdrant_point_id);

-- Trigger to update the `updated_at` column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Technical guidelines

- Use asynchronous database access (e.g. `asyncpg` with SQLAlchemy).  Avoid blocking calls in the event loop.
- Use Pydantic models for input validation and typed responses.  Include descriptive docstrings for all functions.
- Log requests and responses in JSON format to stdout; avoid printing to stderr.
- Implement proper exception handlers that return useful HTTP status codes and messages.
- Expose an OpenAPI specification automatically via FastAPI's built‑in docs (`/docs`).

This specification will be used by Claude Code to scaffold the API service and generate initial code.  Make sure to refer back to the PRD for further detail on data flow and service responsibilities.