"""FastAPI application entrypoint for Generator service."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import generate, models, health
from app.providers.registry import ProviderRegistry
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.google_provider import GoogleProvider
import app.services.generation_service as gen_service

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
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting RAAS Generator service")
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
async def root():
    """Root endpoint."""
    return {
        "message": "RAAS Generator Service",
        "version": "0.1.0",
        "docs": "/docs"
    }
