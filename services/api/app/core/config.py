"""Application configuration with nested Pydantic Settings"""

from typing import Any

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import (DEFAULT_CHUNK_MAX_SIZE, DEFAULT_CHUNK_MIN_SIZE,
                                DEFAULT_SEARCH_LIMIT, EMBEDDER_TIMEOUT_SECONDS,
                                GENERATOR_TIMEOUT_SECONDS, MAX_SEARCH_LIMIT,
                                SEMANTIC_BREAKPOINT_PERCENTILE)


class ChunkingConfig(BaseSettings):
    """Chunking configuration - all chunking parameters centralized"""

    strategy: str = Field(
        "semantic", description="Chunking strategy: 'semantic' or 'recursive'"
    )
    min_chunk_size: int = Field(
        DEFAULT_CHUNK_MIN_SIZE, description="Minimum chunk size in characters"
    )
    max_chunk_size: int = Field(
        DEFAULT_CHUNK_MAX_SIZE, description="Maximum chunk size in characters"
    )
    breakpoint_percentile: int = Field(
        SEMANTIC_BREAKPOINT_PERCENTILE,
        description="Percentile for semantic breakpoints",
    )

    @field_validator("breakpoint_percentile")
    @classmethod
    def validate_percentile(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("Percentile must be between 0 and 100")
        return v

    @field_validator("max_chunk_size")
    @classmethod
    def validate_chunk_sizes(cls, v: int, info: ValidationInfo) -> int:
        if "min_chunk_size" in info.data and v <= info.data["min_chunk_size"]:
            raise ValueError("max_chunk_size must be greater than min_chunk_size")
        return v

    model_config = SettingsConfigDict(env_prefix="CHUNKING_", case_sensitive=False)


class SearchConfig(BaseSettings):
    """Search configuration - all search parameters centralized"""

    default_limit: int = Field(
        DEFAULT_SEARCH_LIMIT, description="Default number of results"
    )
    max_limit: int = Field(MAX_SEARCH_LIMIT, description="Maximum allowed results")
    enable_reranking: bool = Field(True, description="Enable cross-encoder reranking")
    enable_query_expansion: bool = Field(True, description="Enable query expansion")
    rrf_weight: float = Field(
        0.5, description="Reciprocal rank fusion weight (0.0-1.0)"
    )

    @field_validator("rrf_weight")
    @classmethod
    def validate_rrf_weight(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("rrf_weight must be between 0.0 and 1.0")
        return v

    model_config = SettingsConfigDict(env_prefix="SEARCH_", case_sensitive=False)


class EmbedderConfig(BaseSettings):
    """Embedder service configuration"""

    url: str = Field(..., description="Embedder service URL")
    batch_size: int = Field(32, description="Batch size for embedding generation")
    timeout: float = Field(
        EMBEDDER_TIMEOUT_SECONDS, description="HTTP timeout in seconds"
    )

    model_config = SettingsConfigDict(env_prefix="EMBEDDER_", case_sensitive=False)


class GeneratorConfig(BaseSettings):
    """Generator service configuration"""

    url: str = Field(..., description="Generator service URL")
    timeout: float = Field(
        GENERATOR_TIMEOUT_SECONDS, description="HTTP timeout in seconds"
    )
    default_model: str = Field("openai:gpt-5-mini", description="Default LLM model to use")

    model_config = SettingsConfigDict(env_prefix="GENERATOR_", case_sensitive=False)


class SearchServiceConfig(BaseSettings):
    """Search service configuration"""

    url: str = Field("http://search:8003", description="Search service URL")
    timeout: float = Field(60.0, description="HTTP timeout in seconds")

    model_config = SettingsConfigDict(env_prefix="SEARCH_SERVICE_", case_sensitive=False)


class Settings(BaseSettings):
    """Application settings - top-level configuration

    Includes nested configurations for different domains.
    All settings can be overridden via environment variables.
    """

    # Database
    database_url: str = Field(..., description="Database connection URL")

    # Vector DB
    qdrant_url: str = Field(..., description="Qdrant vector database URL")

    # Nested configurations
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    embedder: EmbedderConfig = Field(default_factory=EmbedderConfig)
    generator: GeneratorConfig = Field(default_factory=GeneratorConfig)
    search_service: SearchServiceConfig = Field(default_factory=SearchServiceConfig)

    # Application settings
    log_level: str = Field("INFO", description="Logging level")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
        description="Allowed CORS origins"
    )

    # File Upload Configuration
    upload_dir: str = Field("/app/uploads", description="Directory for uploaded files")
    max_upload_size: int = Field(
        104857600, description="Maximum file upload size in bytes (100MB)"
    )

    # API Configuration
    api_host: str = Field("0.0.0.0", description="API host")
    api_port: int = Field(8000, description="API port")
    api_workers: int = Field(4, description="Number of API workers")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


# Singleton instance
settings = Settings()
