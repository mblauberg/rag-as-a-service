# RAAS Embedder Service

Vector embedding generation service using sentence-transformers for the RAAS platform.

## Overview

The embedder service generates 384-dimensional vector embeddings from text chunks and search queries using the `all-MiniLM-L6-v2` model from sentence-transformers. It stores the embeddings in Qdrant vector database for semantic search.

## Features

- **Batch Embedding**: Process multiple text chunks efficiently in configurable batches
- **Query Embedding**: Generate embeddings for search queries
- **Qdrant Integration**: Automatic collection initialization and vector storage
- **Health Checks**: Liveness and readiness probes for Kubernetes
- **Async Architecture**: Non-blocking operations for better performance

## Requirements

- Python 3.11+
- Qdrant vector database
- ~500MB for the sentence-transformers model

## Installation

### Using Poetry

```bash
cd services/embedder
poetry install
```

### Using Docker

```bash
docker build -t raas-embedder:latest .
```

## Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_URL` | `http://qdrant:6333` | Qdrant server URL |
| `MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `MODEL_DIMENSION` | `384` | Embedding vector dimension |
| `BATCH_SIZE` | `32` | Number of texts to process per batch |
| `COLLECTION_NAME` | `documents` | Qdrant collection name |
| `LOG_LEVEL` | `INFO` | Logging level |

## Running the Service

### Local Development

```bash
poetry run uvicorn app.main:app --reload --port 8001
```

### Docker

```bash
docker run -p 8001:8001 \
  -e QDRANT_URL=http://qdrant:6333 \
  raas-embedder:latest
```

## API Endpoints

### POST /api/v1/embed

Generate embeddings for text chunks and store in Qdrant.

**Request:**
```json
{
  "chunks": [
    {
      "id": "uuid-string",
      "text": "Text content to embed",
      "metadata": {
        "document_id": "doc-uuid",
        "chunk_index": 0
      }
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "count": 1,
  "message": "Successfully embedded and stored 1 chunks"
}
```

### POST /api/v1/embed-query

Generate embedding for a search query.

**Request:**
```json
{
  "query": "What is machine learning?"
}
```

**Response:**
```json
{
  "embedding": [0.123, -0.456, 0.789, ...]
}
```

### POST /api/v1/generate-embeddings

Generate embeddings for a batch of texts without storing them in Qdrant. This endpoint is used by the API service which handles its own vector storage.

**Request:**
```json
{
  "texts": [
    "First text to embed",
    "Second text to embed",
    "Third text to embed"
  ]
}
```

**Response:**
```json
{
  "embeddings": [
    [0.123, -0.456, 0.789, ...],
    [0.234, -0.567, 0.890, ...],
    [0.345, -0.678, 0.901, ...]
  ]
}
```

### GET /api/v1/health

Basic health check.

**Response:**
```json
{
  "status": "healthy"
}
```

### GET /api/v1/ready

Readiness check (indicates model loading status).

**Response:**
```json
{
  "status": "ready",
  "model_loaded": true
}
```

## Testing

Run the test suite:

```bash
poetry run pytest
```

With coverage:

```bash
poetry run pytest --cov=app tests/
```

## Integration with API Service

The API service calls this embedder service:

1. **After document upload**: API sends chunks to `/api/v1/embed` endpoint
2. **During search**: API sends query to `/api/v1/embed-query` endpoint

## Model Information

- **Model**: `all-MiniLM-L6-v2`
- **Dimension**: 384
- **Max Tokens**: 256
- **Framework**: sentence-transformers (PyTorch-based)
- **Download Size**: ~90MB
- **Memory Usage**: ~500MB when loaded

## Performance

- Batch processing: ~32 chunks per batch (configurable)
- Embedding speed: ~100-200 texts/second on CPU
- GPU support: Automatic if available

## Troubleshooting

### Model fails to load

- Ensure sufficient disk space (~500MB)
- Check internet connection for first-time model download
- Verify Python version is 3.11+

### Qdrant connection errors

- Verify Qdrant is running and accessible
- Check `QDRANT_URL` environment variable
- Ensure Qdrant is on version 1.15.1+ (matches client version)

### Memory issues

- Reduce `BATCH_SIZE` in configuration
- Ensure sufficient RAM (2GB+ recommended)
- Consider using GPU for better performance

## License

Part of the RAAS platform.
