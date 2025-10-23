"""FastAPI application entrypoint for Generator service."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings as core_settings
from app.config import settings
from app.api.routes import generate, models, health
from app.providers.registry import ProviderRegistry
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.google_provider import GoogleProvider

# Configure logging
logging.basicConfig(
    level=core_settings.log_level,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global provider registry
provider_registry = ProviderRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting RAAS Generator service")
    logger.info(f"Ollama URL: {core_settings.ollama_url}")
    logger.info(f"Default model: {core_settings.default_model}")
    logger.info(f"Max chunks: {core_settings.max_chunks}")
    logger.info(f"Temperature: {core_settings.temperature}")

    # Initialize provider registry
    logger.info("Initializing provider registry...")

    # Register Ollama if enabled
    if settings.enable_ollama:
        try:
            ollama = OllamaProvider(base_url=settings.ollama_base_url)
            provider_registry.register("ollama", ollama)
            logger.info("Registered Ollama provider")
        except Exception as e:
            logger.warning(f"Failed to register Ollama: {e}")

    # Register OpenAI if enabled
    if settings.enable_openai:
        try:
            openai = OpenAIProvider()
            provider_registry.register("openai", openai)
            logger.info("Registered OpenAI provider")
        except Exception as e:
            logger.warning(f"Failed to register OpenAI: {e}")

    # Register Anthropic if enabled
    if settings.enable_anthropic:
        try:
            anthropic = AnthropicProvider()
            provider_registry.register("anthropic", anthropic)
            logger.info("Registered Anthropic provider")
        except Exception as e:
            logger.warning(f"Failed to register Anthropic: {e}")

    # Register Google if enabled
    if settings.enable_google:
        try:
            google = GoogleProvider()
            provider_registry.register("google", google)
            logger.info("Registered Google provider")
        except Exception as e:
            logger.warning(f"Failed to register Google: {e}")

    active_providers = list(provider_registry.providers.keys())
    logger.info(f"Provider registry initialized with: {active_providers}")

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
    allow_origins=core_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    health.router,
    prefix="/health",
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
