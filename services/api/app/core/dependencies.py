"""Dependency injection for FastAPI endpoints."""
from typing import AsyncGenerator
import httpx

from app.core.qdrant_client import qdrant_client, QdrantClientWrapper
from app.services.generator_client import GeneratorClient


def get_qdrant_client() -> QdrantClientWrapper:
    """
    Provide Qdrant client singleton instance.

    Returns the global QdrantClientWrapper instance that manages
    vector operations for document embeddings. The wrapper ensures the
    collection exists and provides methods for search and deletion.

    Returns:
        QdrantClientWrapper: Qdrant client wrapper singleton
    """
    return qdrant_client


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Provide async HTTP client for external service communication.

    This dependency creates a new httpx.AsyncClient for each request,
    ensuring proper connection management and cleanup. Primarily used
    for communication with the embedder service.

    Configuration:
    - Base timeout: 30 seconds (can be overridden per-request)
    - Automatic connection pooling and reuse within request lifecycle
    - Proper cleanup on request completion

    Yields:
        httpx.AsyncClient: HTTP client for the request
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


def get_generator_client() -> GeneratorClient:
    """
    Provide Generator service client instance.

    Returns a new GeneratorClient instance for each request. The client
    handles communication with the Generator service for LLM-based tasks
    such as query expansion and summary generation.

    Returns:
        GeneratorClient: Generator service client
    """
    return GeneratorClient()
