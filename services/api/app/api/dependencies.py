"""Dependency injection factory functions for hexagonal architecture.

These factory functions wire up the hexagonal architecture dependencies:
- Ports (interfaces) are implemented by Infrastructure layer adapters
- Use cases depend on ports (dependency inversion principle)
- FastAPI routes depend on use cases via these factories
"""
from fastapi import Depends
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.delete_document import DeleteDocumentUseCase
from app.application.use_cases.get_document import GetDocumentUseCase
from app.application.use_cases.list_documents import ListDocumentsUseCase

# Domain & Use Cases
from app.application.use_cases.upload_document import UploadDocumentUseCase
from app.core.config import settings
from app.core.database import get_db
from app.core.qdrant_client import qdrant_client
from app.infrastructure.db.repositories.chunk_repository_impl import ChunkRepositoryImpl

# Infrastructure - Repositories
from app.infrastructure.db.repositories.document_repository_impl import DocumentRepositoryImpl

# Infrastructure - Query Augmentation
from app.infrastructure.generation.llm_query_augmenter import LLMQueryAugmenterImpl
from app.infrastructure.processing.file_processor import FileProcessorImpl
from app.infrastructure.processing.semantic_chunker import SemanticChunkerImpl

# Infrastructure - Services
from app.infrastructure.services.embedding_service import HTTPEmbeddingService
from app.infrastructure.services.generation_service import HTTPGenerationService
from app.infrastructure.services.search_service import SearchServiceClient
from app.infrastructure.vector_store.qdrant_store import QdrantVectorStoreImpl

# Ports
from app.ports.repositories import ChunkRepository
from app.ports.services import GenerationService, QueryAugmenter


# Qdrant Client Dependency
async def get_qdrant_client() -> AsyncQdrantClient:
    """Get Qdrant async client instance.

    Returns singleton Qdrant client from global wrapper.
    Ensures collection is initialized on first use.
    """
    await qdrant_client._ensure_collection()
    return qdrant_client.client


# Upload Document Use Case
def get_upload_document_use_case(
    db: AsyncSession = Depends(get_db),
) -> UploadDocumentUseCase:
    """Factory for UploadDocumentUseCase with all dependencies wired.

    Creates a new use case instance with:
    - Document and chunk repositories (PostgreSQL)
    - Embedding service (HTTP client to embedder microservice)
    - Vector store (Qdrant)
    - File processor (PDF/TXT extraction)
    - Text chunker (semantic chunking)

    Args:
        db: Database session from FastAPI dependency

    Returns:
        Fully configured UploadDocumentUseCase instance
    """
    # Repositories
    document_repo = DocumentRepositoryImpl(db)
    chunk_repo = ChunkRepositoryImpl(db)

    # Services
    embedding_service = HTTPEmbeddingService(settings.embedder.url)
    vector_store = QdrantVectorStoreImpl(
        client=qdrant_client.client, collection_name="documents"
    )
    file_processor = FileProcessorImpl()
    chunker = SemanticChunkerImpl(
        min_chunk_size=settings.chunking.min_chunk_size,
        max_chunk_size=settings.chunking.max_chunk_size,
        breakpoint_percentile=settings.chunking.breakpoint_percentile,
    )

    return UploadDocumentUseCase(
        document_repo=document_repo,
        chunk_repo=chunk_repo,
        embedding_service=embedding_service,
        vector_store=vector_store,
        file_processor=file_processor,
        chunker=chunker,
    )


# List Documents Use Case
def get_list_documents_use_case(
    db: AsyncSession = Depends(get_db),
) -> ListDocumentsUseCase:
    """Factory for ListDocumentsUseCase.

    Args:
        db: Database session from FastAPI dependency

    Returns:
        Fully configured ListDocumentsUseCase instance
    """
    document_repo = DocumentRepositoryImpl(db)
    return ListDocumentsUseCase(document_repo=document_repo)


# Delete Document Use Case
def get_delete_document_use_case(
    db: AsyncSession = Depends(get_db),
) -> DeleteDocumentUseCase:
    """Factory for DeleteDocumentUseCase.

    Args:
        db: Database session from FastAPI dependency

    Returns:
        Fully configured DeleteDocumentUseCase instance
    """
    document_repo = DocumentRepositoryImpl(db)
    chunk_repo = ChunkRepositoryImpl(db)
    vector_store = QdrantVectorStoreImpl(
        client=qdrant_client.client, collection_name="documents"
    )

    return DeleteDocumentUseCase(
        document_repo=document_repo, chunk_repo=chunk_repo, vector_store=vector_store
    )


# Get Document Use Case
def get_get_document_use_case(db: AsyncSession = Depends(get_db)) -> GetDocumentUseCase:
    """Factory for GetDocumentUseCase.

    Args:
        db: Database session from FastAPI dependency

    Returns:
        Fully configured GetDocumentUseCase instance
    """
    document_repo = DocumentRepositoryImpl(db)
    chunk_repo = ChunkRepositoryImpl(db)

    return GetDocumentUseCase(document_repo=document_repo, chunk_repo=chunk_repo)


# Generation Service
def get_generation_service() -> GenerationService:
    """Create HTTP generation service instance."""
    return HTTPGenerationService(settings.generator.url)


# Search Service Client
def get_search_service_client() -> SearchServiceClient:
    """Create search service HTTP client."""
    return SearchServiceClient(
        search_url=settings.search_service.url,
        timeout=settings.search_service.timeout
    )


# Query Augmenter
def get_query_augmenter(
    generation_service: GenerationService = Depends(get_generation_service),
) -> QueryAugmenter:
    """Create LLM query augmenter instance."""
    return LLMQueryAugmenterImpl(generation_service)


# Chunk Repository
async def get_chunk_repository(
    session: AsyncSession = Depends(get_db),
) -> ChunkRepository:
    """Get chunk repository instance."""
    return ChunkRepositoryImpl(session)
