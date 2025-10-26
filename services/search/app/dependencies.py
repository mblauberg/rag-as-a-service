"""Dependency injection for FastAPI."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.services.vector_search import VectorSearchService
from app.services.keyword_search import KeywordSearchService
from app.services.fusion import RRFFusionService
from app.services.reranker import CrossEncoderReranker
from app.services.search_orchestrator import SearchOrchestrator, EmbedderClient

# Database engine
engine = create_async_engine(settings.database_url, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """Get database session."""
    async with async_session_maker() as session:
        yield session


# Singleton services (loaded once at startup)
_vector_service: VectorSearchService | None = None
_keyword_service: KeywordSearchService | None = None
_fusion_service: RRFFusionService | None = None
_reranker: CrossEncoderReranker | None = None
_embedder_client: EmbedderClient | None = None
_orchestrator: SearchOrchestrator | None = None


def get_vector_service() -> VectorSearchService:
    """Get vector search service."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorSearchService(
            qdrant_url=settings.qdrant_url,
            collection_name=settings.qdrant_collection
        )
    return _vector_service


def get_keyword_service() -> KeywordSearchService:
    """Get keyword search service."""
    global _keyword_service
    if _keyword_service is None:
        _keyword_service = KeywordSearchService()
    return _keyword_service


def get_fusion_service() -> RRFFusionService:
    """Get RRF fusion service."""
    global _fusion_service
    if _fusion_service is None:
        _fusion_service = RRFFusionService(k=settings.rrf_k)
    return _fusion_service


def get_reranker() -> CrossEncoderReranker:
    """Get cross-encoder reranker."""
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoderReranker(model_name=settings.reranking_model)
    return _reranker


def get_embedder_client() -> EmbedderClient:
    """Get embedder service client."""
    global _embedder_client
    if _embedder_client is None:
        _embedder_client = EmbedderClient(embedder_url=settings.embedder_url)
    return _embedder_client


def get_search_orchestrator() -> SearchOrchestrator:
    """Get search orchestrator with all dependencies."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SearchOrchestrator(
            vector_service=get_vector_service(),
            keyword_service=get_keyword_service(),
            fusion_service=get_fusion_service(),
            reranker=get_reranker(),
            embedder_client=get_embedder_client(),
        )
    return _orchestrator
