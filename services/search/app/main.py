"""FastAPI application for search service."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.schemas import (
    SearchRequest,
    SearchResponse,
    ChunkResult,
    HealthResponse,
    ReadinessResponse,
)
from app.services.search_orchestrator import SearchOrchestrator
from app.dependencies import get_db, get_search_orchestrator, get_reranker

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting RAAS Search Service")
    logger.info(f"Qdrant URL: {settings.qdrant_url}")
    logger.info(f"Database URL: {settings.database_url}")

    try:
        # Load reranking model at startup
        reranker = get_reranker()
        logger.info("Search service ready")
    except Exception as e:
        logger.error(f"Failed to initialize search service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down RAAS Search Service")


# Create FastAPI application
app = FastAPI(
    title="RAAS Search Service",
    description="Intelligent search and retrieval service with hybrid search and reranking",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RAAS Search Service",
        "version": "0.1.0",
        "features": ["vector", "keyword", "hybrid", "reranking"]
    }


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy")


@app.get("/api/v1/ready", response_model=ReadinessResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check endpoint."""
    try:
        # Check if reranker is loaded
        reranker = get_reranker()
        models_loaded = reranker.model is not None

        # Check database connection
        database_connected = False
        try:
            # Execute simple query to verify database connectivity
            from sqlalchemy import text
            await db.execute(text("SELECT 1"))
            database_connected = True
        except Exception as db_error:
            logger.warning(f"Database connection check failed: {db_error}")

        status_value = "ready" if (models_loaded and database_connected) else "not_ready"

        return ReadinessResponse(
            status=status_value,
            models_loaded=models_loaded,
            database_connected=database_connected
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return ReadinessResponse(
            status="not_ready",
            models_loaded=False,
            database_connected=False
        )


@app.post("/api/v1/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    orchestrator: SearchOrchestrator = Depends(get_search_orchestrator),
):
    """Execute intelligent search with hybrid retrieval and reranking.

    Supports three modes:
    - VECTOR: Pure semantic search using embeddings
    - KEYWORD: Pure lexical search using PostgreSQL FTS
    - HYBRID: Combines both with RRF fusion (RECOMMENDED)

    Args:
        request: Search request with query and parameters
        db: Database session
        orchestrator: Search orchestrator service

    Returns:
        Search results with ranked chunks
    """
    try:
        logger.info(
            f"Search request: query='{request.query[:50]}', mode={request.mode}, "
            f"top_k={request.top_k}, reranking={request.use_reranking}"
        )

        # Execute search
        chunks = await orchestrator.search(
            query=request.query,
            mode=request.mode,
            top_k=request.top_k,
            use_reranking=request.use_reranking,
            use_expansion=request.use_expansion,
            document_id=request.document_id,
            db_session=db,
        )

        # Convert to response DTOs
        results = [
            ChunkResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                content=chunk.content,
                score=chunk.score or 0.0,
                chunk_index=chunk.chunk_index,
            )
            for chunk in chunks
        ]

        logger.info(f"Search returned {len(results)} results")

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            mode_used=request.mode,
            reranking_applied=request.use_reranking,
            expansion_applied=request.use_expansion,
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
