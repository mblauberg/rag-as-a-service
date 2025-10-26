"""Configuration settings for search service."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Search service configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Service Info
    service_name: str = "raas-search"
    api_host: str = Field("0.0.0.0", description="API host")
    api_port: int = Field(8003, description="API port")
    api_workers: int = Field(2, description="Number of worker processes")
    log_level: str = Field("INFO", description="Logging level")

    # Database (PostgreSQL for keyword search)
    database_url: str = Field(
        "postgresql+asyncpg://raasuser:raaspass@postgres:5432/raasdb",
        description="PostgreSQL connection URL"
    )

    # Vector Database (Qdrant)
    qdrant_url: str = Field(
        "http://qdrant:6333",
        description="Qdrant vector database URL"
    )
    qdrant_collection: str = Field(
        "documents",
        description="Qdrant collection name"
    )

    # Embedder Service (for query embedding)
    embedder_url: str = Field(
        "http://embedder:8001",
        description="Embedder service URL"
    )

    # Generator Service (for query expansion)
    generator_url: str = Field(
        "http://generator:8002",
        description="Generator service URL for query expansion"
    )

    # Search Configuration
    default_search_mode: str = Field("hybrid", description="Default search mode")
    default_top_k: int = Field(10, ge=1, le=100, description="Default number of results")
    enable_query_expansion: bool = Field(True, description="Enable query expansion")
    enable_reranking: bool = Field(True, description="Enable reranking")
    rerank_candidates: int = Field(50, description="Candidates to retrieve for reranking")

    # Reranking Model
    reranking_model: str = Field(
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Cross-encoder model for reranking"
    )

    # RRF Configuration
    rrf_k: int = Field(60, description="RRF constant (research-proven default: 60)")

    # Query Expansion
    query_expansion_variants: int = Field(2, description="Number of query variants to generate")


# Global settings instance
settings = Settings()
