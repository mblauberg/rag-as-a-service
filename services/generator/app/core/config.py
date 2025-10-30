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

    def validate_required_keys(self) -> None:
        """Validate that required API keys are present based on enabled providers."""
        errors = []

        if self.enable_openai and not self.openai_api_key:
            errors.append(
                "OPENAI_API_KEY is required when ENABLE_OPENAI=true\n"
                "  → Get your key from: https://platform.openai.com/api-keys\n"
                "  → Run: ./scripts/setup-secrets.sh\n"
                "  → Or set manually in .env file"
            )

        if self.enable_anthropic and not self.anthropic_api_key:
            errors.append(
                "ANTHROPIC_API_KEY is required when ENABLE_ANTHROPIC=true\n"
                "  → Get your key from: https://console.anthropic.com/\n"
                "  → Run: ./scripts/setup-secrets.sh\n"
                "  → Or set manually in .env file"
            )

        if self.enable_google and not self.google_api_key:
            errors.append(
                "GOOGLE_API_KEY is required when ENABLE_GOOGLE=true\n"
                "  → Get your key from: https://makersuite.google.com/app/apikey\n"
                "  → Run: ./scripts/setup-secrets.sh\n"
                "  → Or set manually in .env file"
            )

        if errors:
            error_message = "\n\n❌ Configuration Error - Missing Required API Keys:\n\n" + "\n\n".join(errors)
            raise ValueError(error_message)


# Global settings instance
settings = Settings()
