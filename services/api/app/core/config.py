"""Configuration settings loaded from environment variables."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    database_url: str

    # Qdrant Configuration
    qdrant_url: str

    # Embedder Service Configuration
    embedder_url: str

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
