"""FastAPI application entrypoint for Generator service."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.services.generation_service as gen_service
from app.api.routes import generate, health, models
from app.core.config import settings
from app.core.exceptions import RaasException
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.google_provider import GoogleProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.registry import ProviderRegistry

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize provider registry
provider_registry = ProviderRegistry()
provider_registry.register("openai", OpenAIProvider())
provider_registry.register("anthropic", AnthropicProvider())
provider_registry.register("google", GoogleProvider())

# Set global registry
gen_service.provider_registry = provider_registry

logger.info(f"Registered providers: {list(provider_registry.providers.keys())}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting RAAS Generator service")

    # Validate required API keys
    try:
        settings.validate_required_keys()
    except ValueError as e:
        logger.error(str(e))
        raise  # Re-raise to fail startup

    logger.info(f"Default model: {settings.default_model}")
    logger.info(f"Max chunks: {settings.max_chunks}")
    logger.info(f"Temperature: {settings.temperature}")
    logger.info(f"Available providers: {list(provider_registry.providers.keys())}")

    yield

    # Shutdown
    logger.info("Shutting down RAAS Generator service")


# Create FastAPI application
app = FastAPI(
    title="RAAS Generator",
    description="Retrieval-Augmented Generation as a Service - Generator Service",
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

# Include routers
app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["health"]
)

app.include_router(
    generate.router,
    prefix="/api/v1/generate",
    tags=["generation"]
)

app.include_router(
    models.router,
    prefix="/api/v1/models",
    tags=["models"]
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "RAAS Generator Service",
        "version": "0.1.0",
        "docs": "/docs"
    }
