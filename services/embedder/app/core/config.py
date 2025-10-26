"""Configuration settings loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Qdrant Configuration
    qdrant_url: str

    # Model Configuration
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    model_dimension: int = 384
    batch_size: int = 32

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    api_workers: int = 2

    # Qdrant Collection
    collection_name: str = "documents"

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings(qdrant_url="")
