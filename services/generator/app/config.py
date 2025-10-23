"""Application configuration."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Ollama Configuration
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    enable_ollama: bool = os.getenv("ENABLE_OLLAMA", "true").lower() == "true"

    # OpenAI Configuration
    enable_openai: bool = os.getenv("ENABLE_OPENAI", "false").lower() == "true"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Anthropic Configuration
    enable_anthropic: bool = os.getenv("ENABLE_ANTHROPIC", "false").lower() == "true"
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Google Configuration
    enable_google: bool = os.getenv("ENABLE_GOOGLE", "false").lower() == "true"
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")

    class Config:
        env_file = ".env"


settings = Settings()
