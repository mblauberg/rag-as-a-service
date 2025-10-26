"""Application configuration using Pydantic settings."""
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"
    default_model: str = "openai:gpt-5-mini"
    max_chunks: int = 5
    temperature: float = 0.1

    # Service Configuration
    port: int = 8002
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Provider Toggles
    enable_ollama: bool = False
    enable_openai: bool = True
    enable_anthropic: bool = False
    enable_google: bool = False

    # API Keys (optional)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
