"""Application configuration using Pydantic settings."""
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"
    default_model: str = "llama3.2"
    max_chunks: int = 5
    temperature: float = 0.1

    # Service Configuration
    port: int = 8002
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
