"""Configuration settings loaded from environment variables."""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    database_url: str

    # Qdrant Configuration
    qdrant_url: str

    # Embedder Service Configuration
    embedder_url: str

    # Generator Service Configuration
    generator_url: str = "http://localhost:8002"

    # File Upload Configuration
    upload_dir: str = "/app/uploads"
    max_upload_size: int = 104857600  # 100MB

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4

    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost"]

    # Logging
    log_level: str = "INFO"

    # Chunking Configuration
    CHUNKING_STRATEGY: str = "semantic"  # semantic | recursive
    SEMANTIC_MIN_CHUNK_SIZE: int = 128
    SEMANTIC_MAX_CHUNK_SIZE: int = 512
    SEMANTIC_BREAKPOINT_PERCENTILE: float = 95.0

    # Legacy chunking (for backward compatibility)
    CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 80

    # Reranker settings
    RERANKER_MODEL: str = Field(
        default="BAAI/bge-reranker-v2-m3",
        description="Cross-encoder model for reranking"
    )
    RERANKER_TOP_K: int = Field(
        default=10,
        description="Number of results to return after reranking"
    )
    RERANKER_CANDIDATE_MULTIPLIER: int = Field(
        default=5,
        description="Retrieve N*top_k candidates before reranking"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
