"""Application configuration using Pydantic settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Model Configuration
    default_model: str = "openai:gpt-5-mini"
    max_chunks: int = 5
    temperature: float = 0.1

    # Service Configuration
    port: int = 8002
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Provider Toggles
    enable_openai: bool = True
    enable_anthropic: bool = False
    enable_google: bool = False

    # API Keys (optional)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
