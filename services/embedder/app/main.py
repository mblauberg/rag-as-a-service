"""FastAPI application entrypoint for the embedder service."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import RaasException
from app.services.embedding_service import embedding_service
from app.models.schemas import (
    EmbedRequest,
    EmbedResponse,
    EmbedQueryRequest,
    EmbedQueryResponse,
    GenerateEmbeddingsRequest,
    GenerateEmbeddingsResponse,
    HealthResponse,
    ReadinessResponse
)

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
    logger.info("Starting RAAS Embedder Service")
    logger.info(f"Model: {settings.model_name}")
    logger.info(f"Qdrant URL: {settings.qdrant_url}")
    logger.info(f"Batch size: {settings.batch_size}")

    try:
        # Load the embedding model
        embedding_service.load_model()
        logger.info("Embedder service ready")
    except Exception as e:
        logger.error(f"Failed to initialize embedder service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down RAAS Embedder Service")


# Create FastAPI application
app = FastAPI(
    title="RAAS Embedder Service",
    description="Vector embedding generation service using sentence-transformers",
    version="0.1.0",
    lifespan=lifespan
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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RAAS Embedder Service",
        "version": "0.1.0",
        "model": settings.model_name
    }


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.

    Returns:
        Health status
    """
    return HealthResponse(status="healthy")


@app.get("/api/v1/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check that validates model loading.

    Returns:
        Readiness status with model loading state
    """
    model_loaded = embedding_service.model_loaded

    status_value = "ready" if model_loaded else "not_ready"

    return ReadinessResponse(
        status=status_value,
        model_loaded=model_loaded
    )


@app.post("/api/v1/embed", response_model=EmbedResponse, status_code=status.HTTP_200_OK)
async def embed_chunks(request: EmbedRequest):
    """
    Generate embeddings for text chunks and store in Qdrant.

    Accepts a list of chunks with text and metadata, generates embeddings
    in batches, and stores them in the Qdrant vector database.

    Args:
        request: Embedding request with list of chunks

    Returns:
        Success status and count of processed chunks

    Raises:
        HTTPException: If embedding generation or storage fails
    """
    try:
        logger.info(f"Received embedding request for {len(request.chunks)} chunks")

        success = await embedding_service.embed_and_store_chunks(request.chunks)

        if success:
            return EmbedResponse(
                success=True,
                count=len(request.chunks),
                message=f"Successfully embedded and stored {len(request.chunks)} chunks"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to embed and store chunks"
            )

    except Exception as e:
        logger.error(f"Error in embed endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding operation failed: {str(e)}"
        )


@app.post("/api/v1/embed-query", response_model=EmbedQueryResponse)
async def embed_query(request: EmbedQueryRequest):
    """
    Generate embedding for a search query.

    Args:
        request: Query embedding request with query text

    Returns:
        Query embedding vector

    Raises:
        HTTPException: If embedding generation fails
    """
    try:
        logger.info(f"Generating embedding for query: {request.query[:50]}...")

        embedding = embedding_service.embed_query(request.query)

        return EmbedQueryResponse(embedding=embedding)

    except RuntimeError as e:
        logger.error(f"Model not ready: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded yet. Please wait for service to be ready."
        )
    except Exception as e:
        logger.error(f"Error in embed-query endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query embedding failed: {str(e)}"
        )


@app.post("/api/v1/generate-embeddings", response_model=GenerateEmbeddingsResponse)
async def generate_embeddings(request: GenerateEmbeddingsRequest):
    """
    Generate embeddings for a batch of texts without storing them.

    This endpoint is designed for use by the API service which handles
    its own vector storage. It only generates and returns embeddings.

    Args:
        request: Batch embedding request with list of texts

    Returns:
        List of embedding vectors (one per input text)

    Raises:
        HTTPException: If embedding generation fails
    """
    try:
        logger.info(f"Generating embeddings for {len(request.texts)} texts")

        embeddings = embedding_service.generate_embeddings(request.texts)

        return GenerateEmbeddingsResponse(embeddings=embeddings)

    except RuntimeError as e:
        logger.error(f"Model not ready: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded yet. Please wait for service to be ready."
        )
    except Exception as e:
        logger.error(f"Error in generate-embeddings endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {str(e)}"
        )
