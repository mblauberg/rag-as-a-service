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
from app.application.use_cases.list_documents import ListDocumentsUseCase
from app.application.use_cases.search_documents import SearchDocumentsUseCase

# Domain & Use Cases
from app.application.use_cases.upload_document import UploadDocumentUseCase
from app.core.config import settings
from app.core.database import get_db
from app.core.qdrant_client import qdrant_client
from app.infrastructure.db.repositories.chunk_repository_impl import ChunkRepositoryImpl

# Infrastructure - Repositories
from app.infrastructure.db.repositories.document_repository_impl import DocumentRepositoryImpl
from app.infrastructure.processing.file_processor import FileProcessorImpl
from app.infrastructure.processing.semantic_chunker import SemanticChunkerImpl

# Infrastructure - Services
from app.infrastructure.services.embedding_service import HTTPEmbeddingService
from app.infrastructure.services.generation_service import HTTPGenerationService
from app.infrastructure.vector_store.qdrant_store import QdrantVectorStoreImpl

# Infrastructure - Search
from app.infrastructure.search.postgres_keyword_store import PostgresKeywordStoreImpl
from app.infrastructure.search.rrf_fusion_service import RRFFusionServiceImpl

# Infrastructure - Query Augmentation
from app.infrastructure.generation.llm_query_augmenter import LLMQueryAugmenterImpl

# Ports
from app.ports.services import KeywordStore, FusionService, EmbeddingService, VectorStore, GenerationService, QueryAugmenter


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
    db: AsyncSession = Depends(get_db)
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
        client=qdrant_client.client,
        collection_name="documents"
    )
    file_processor = FileProcessorImpl()
    chunker = SemanticChunkerImpl(
        min_chunk_size=settings.chunking.min_chunk_size,
        max_chunk_size=settings.chunking.max_chunk_size,
        breakpoint_percentile=settings.chunking.breakpoint_percentile
    )

    return UploadDocumentUseCase(
        document_repo=document_repo,
        chunk_repo=chunk_repo,
        embedding_service=embedding_service,
        vector_store=vector_store,
        file_processor=file_processor,
        chunker=chunker
    )


# List Documents Use Case
def get_list_documents_use_case(
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
        client=qdrant_client.client,
        collection_name="documents"
    )

    return DeleteDocumentUseCase(
        document_repo=document_repo,
        chunk_repo=chunk_repo,
        vector_store=vector_store
    )


# Keyword Store
def get_keyword_store(
    db: AsyncSession = Depends(get_db)
) -> KeywordStore:
    """Create PostgreSQL keyword store instance."""
    return PostgresKeywordStoreImpl(db)


# Fusion Service
def get_fusion_service() -> FusionService:
    """Create RRF fusion service instance."""
    return RRFFusionServiceImpl()


# Generation Service
def get_generation_service() -> GenerationService:
    """Create HTTP generation service instance."""
    return HTTPGenerationService(settings.generator.url)


# Query Augmenter
def get_query_augmenter(
    generation_service: GenerationService = Depends(get_generation_service)
) -> QueryAugmenter:
    """Create LLM query augmenter instance."""
    return LLMQueryAugmenterImpl(generation_service)


# Search Documents Use Case
def get_search_documents_use_case(
    embedding_service: EmbeddingService = Depends(lambda: HTTPEmbeddingService(settings.embedder.url)),
    vector_store: VectorStore = Depends(lambda: QdrantVectorStoreImpl(
        client=qdrant_client.client,
        collection_name="documents"
    )),
    keyword_store: KeywordStore = Depends(get_keyword_store),
    fusion_service: FusionService = Depends(get_fusion_service),
    query_augmenter: QueryAugmenter = Depends(get_query_augmenter)
) -> SearchDocumentsUseCase:
    """Factory for SearchDocumentsUseCase with hybrid capabilities and query expansion.

    Args:
        embedding_service: Service for generating embeddings
        vector_store: Store for semantic search
        keyword_store: Store for BM25 keyword search
        fusion_service: Service for result fusion
        query_augmenter: Service for query expansion

    Returns:
        Fully configured SearchDocumentsUseCase instance with hybrid search and query expansion support
    """
    return SearchDocumentsUseCase(
        embedding_service=embedding_service,
        vector_store=vector_store,
        keyword_store=keyword_store,
        fusion_service=fusion_service,
        query_augmenter=query_augmenter
    )
