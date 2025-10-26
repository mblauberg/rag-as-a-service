# RAAS Search Service

Intelligent search and retrieval service for RAG-as-a-Service.

## Features

- **Hybrid Search**: Combines semantic (vector) and lexical (keyword) search
- **Reciprocal Rank Fusion**: Merges multiple result sets intelligently
- **Cross-Encoder Reranking**: Improves precision with query-document relevance scoring
- **Query Expansion**: LLM-based multi-query generation for better recall
- **Flexible Modes**: Vector-only, keyword-only, or hybrid retrieval

## API Endpoints

- `POST /api/v1/search` - Hybrid search with all features
- `GET /api/v1/health` - Health check
- `GET /api/v1/ready` - Readiness check

## Tech Stack

- FastAPI for async HTTP API
- Qdrant for vector similarity search
- PostgreSQL FTS for keyword search
- Cross-encoder models for reranking
