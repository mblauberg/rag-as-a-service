"""Dependency injection for FastAPI endpoints."""
import httpx

from app.core.qdrant_client import QdrantClientWrapper, qdrant_client
from app.services.chunking_orchestrator import ChunkingOrchestrator
from app.services.document_metadata_service import DocumentMetadataService
from app.services.document_service import DocumentService
from app.services.document_upload_service import DocumentUploadService
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


async def get_http_client():
    """
    Provide HTTP client for service-to-service communication.

    Creates an async HTTP client with appropriate timeout settings
    for communicating with embedder and generator services.

    Yields:
        httpx.AsyncClient: Async HTTP client instance
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


def get_document_upload_service() -> DocumentUploadService:
    """
    Provide DocumentUploadService instance.

    Returns a new instance for handling file I/O operations.
    This service has no external dependencies.

    Returns:
        DocumentUploadService: Service for file operations
    """
    return DocumentUploadService()


def get_document_metadata_service() -> DocumentMetadataService:
    """
    Provide DocumentMetadataService instance.

    Returns a new instance for handling database CRUD operations.
    This service receives database session as parameter in methods.

    Returns:
        DocumentMetadataService: Service for database operations
    """
    return DocumentMetadataService()


def get_chunking_orchestrator(
    metadata_service: DocumentMetadataService = None
) -> ChunkingOrchestrator:
    """
    Provide ChunkingOrchestrator instance.

    Returns a new instance for orchestrating chunking workflows.
    Injects DocumentMetadataService dependency.

    Args:
        metadata_service: Optional DocumentMetadataService (created if not provided)

    Returns:
        ChunkingOrchestrator: Service for chunking orchestration
    """
    if metadata_service is None:
        metadata_service = get_document_metadata_service()
    return ChunkingOrchestrator(metadata_service=metadata_service)


def get_document_service(
    upload_service: DocumentUploadService = None,
    metadata_service: DocumentMetadataService = None,
    chunking_orchestrator: ChunkingOrchestrator = None,
    qdrant_client: QdrantClientWrapper = None
) -> DocumentService:
    """
    Provide DocumentService facade instance.

    Returns a new instance coordinating all specialized services.
    Creates dependencies if not provided.

    Args:
        upload_service: Optional DocumentUploadService
        metadata_service: Optional DocumentMetadataService
        chunking_orchestrator: Optional ChunkingOrchestrator
        qdrant_client: Optional QdrantClientWrapper

    Returns:
        DocumentService: Facade service coordinating document operations
    """
    if upload_service is None:
        upload_service = get_document_upload_service()
    if metadata_service is None:
        metadata_service = get_document_metadata_service()
    if chunking_orchestrator is None:
        chunking_orchestrator = get_chunking_orchestrator(metadata_service)
    if qdrant_client is None:
        qdrant_client = get_qdrant_client()

    return DocumentService(
        upload_service=upload_service,
        metadata_service=metadata_service,
        chunking_orchestrator=chunking_orchestrator,
        qdrant_client=qdrant_client
    )
