"""FastAPI application entrypoint."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, hexagonal_documents, hexagonal_search, models, search
from app.core.config import settings
from app.core.database import init_db

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting RAAS API service")
    logger.info(f"Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
    logger.info(f"Qdrant URL: {settings.qdrant_url}")
    logger.info(f"Embedder URL: {settings.embedder.url}")
    logger.info(f"Generator URL: {settings.generator.url}")

    # Initialize database tables (in production, use proper migrations)
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield

    # Shutdown
    logger.info("Shutting down RAAS API service")


# Create FastAPI application
app = FastAPI(
    title="RAAS API",
    description="Retrieval-Augmented Generation as a Service - API Gateway",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["health"]
)

# LEGACY ROUTE - REMOVED
# app.include_router(
#     documents.router,
#     prefix="/api/v1/documents",
#     tags=["documents"]
# )

app.include_router(
    search.router,
    prefix="/api/v1/search",
    tags=["search"]
)

app.include_router(
    models.router,
    prefix="/api/v1",
    tags=["models"]
)

# Hexagonal architecture routes (new clean architecture implementation)
app.include_router(
    hexagonal_documents.router,
    prefix="/api/v1/hexagonal/documents",
    tags=["hexagonal-documents"]
)

app.include_router(
    hexagonal_search.router,
    prefix="/api/v1/hexagonal/search",
    tags=["hexagonal-search"]
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RAAS API Gateway",
        "version": "0.1.0",
        "docs": "/docs"
    }
