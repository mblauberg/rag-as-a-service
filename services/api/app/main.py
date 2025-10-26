"""FastAPI application entrypoint."""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import documents, generate, health, models, search
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import RaasException

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting RAAS API service")
    logger.info(
        f"Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}"
    )
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
    lifespan=lifespan,
)

logger = logging.getLogger(__name__)


@app.exception_handler(RaasException)
async def raas_exception_handler(
    request: Request, exc: RaasException
) -> JSONResponse:
    """Handle all RAAS custom exceptions with structured responses."""
    logger.error(
        f"{exc.__class__.__name__}: {exc.message}",
        extra={"path": str(request.url.path), "details": exc.details},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all for unexpected errors."""
    logger.exception("Unexpected error", extra={"path": str(request.url.path)})
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
        },
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
app.include_router(health.router, prefix="/api/v1", tags=["health"])

app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])

app.include_router(search.router, prefix="/api/v1/search", tags=["search"])

app.include_router(models.router, prefix="/api/v1", tags=["models"])

app.include_router(
    generate.router,
    prefix="/api/v1/generate",
    tags=["generate"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "RAAS API Gateway", "version": "0.1.0", "docs": "/docs"}
