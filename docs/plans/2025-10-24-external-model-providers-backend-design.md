# External Model Providers Backend Design

**Date**: 2025-10-24
**Status**: Design Approved
**Scope**: Backend API provider infrastructure for OpenAI, Anthropic, and Google models

## Overview

This design implements the backend provider abstraction layer to support external LLM APIs (OpenAI, Anthropic, Google) alongside the existing Ollama integration. This provides the backend infrastructure needed by the frontend multi-provider model selector design.

## Goals

1. **Provider Abstraction**: Create a clean interface that any LLM provider can implement
2. **Graceful Degradation**: System works with Ollama alone, enhances as API keys are added
3. **Extensibility**: New providers can be added without modifying existing code
4. **Backend-Only Scope**: Implement backend infrastructure, assuming frontend changes are handled separately
5. **Latest Models**: Support the most recent models available as of October 2025

## Relationship to Other Designs

**Depends on**: None (builds on existing Ollama implementation)

**Enables**: `docs/plans/2025-10-24-multi-provider-model-selector-design.md` (frontend UI enhancements)

**Integration Point**: Frontend will call `/api/v1/models` and `/api/v1/generate` with provider-prefixed model names (e.g., `openai:gpt-5`). Backend routes requests to appropriate provider and returns unified responses.

## Architecture

### Provider Abstraction Layer

**Base Interface** (`app/providers/base.py`):

```python
from abc import ABC, abstractmethod
from typing import List
from app.models.schemas import Model

class ModelProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def list_models(self) -> List[Model]:
        """Return available models from this provider with full metadata."""
        pass

    @abstractmethod
    async def generate(self, model: str, prompt: str, temperature: float = 0.1) -> dict:
        """
        Generate text using provider's API.

        Returns:
            {
                "response": str,  # Generated text
                "prompt_eval_count": int,  # Input tokens (optional)
                "eval_count": int,  # Output tokens (optional)
            }
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and accessible."""
        pass
```

**Concrete Implementations**:
- `OllamaProvider` (refactored from existing `OllamaClient`)
- `OpenAIProvider` (new, uses OpenAI SDK)
- `AnthropicProvider` (new, uses Anthropic SDK)
- `GoogleProvider` (new, uses Google Generative AI SDK)

### Provider Registry

**Location**: `app/providers/registry.py`

```python
class ProviderRegistry:
    """Manages multiple LLM providers and routes requests."""

    def __init__(self):
        self.providers: dict[str, ModelProvider] = {}

    def register(self, name: str, provider: ModelProvider):
        """Register a provider if it's available."""
        if provider.is_available():
            self.providers[name] = provider
            logger.info(f"Registered provider: {name}")
        else:
            logger.warning(f"Provider not available: {name}")

    async def list_all_models(self) -> List[Model]:
        """Aggregate models from all registered providers."""
        models = []
        for provider_name, provider in self.providers.items():
            try:
                provider_models = await provider.list_models()
                models.extend(provider_models)
            except Exception as e:
                logger.error(f"Failed to list models from {provider_name}: {e}")
        return models

    async def generate(self, model_name: str, prompt: str, temperature: float = 0.1) -> dict:
        """Route generation to appropriate provider based on model name."""
        provider_name = self._extract_provider(model_name)

        if provider_name not in self.providers:
            raise ValueError(f"Provider not available: {provider_name}")

        return await self.providers[provider_name].generate(
            model_name, prompt, temperature
        )

    def _extract_provider(self, model_name: str) -> str:
        """Extract provider name from model (e.g., 'openai:gpt-5' -> 'openai')."""
        if ":" in model_name:
            return model_name.split(":")[0]
        return "ollama"  # Default for backward compatibility
```

### Initialization Flow

On startup (`app/main.py`):

```python
from app.providers.registry import ProviderRegistry
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.google_provider import GoogleProvider

# Initialize registry
provider_registry = ProviderRegistry()

# Attempt to register all providers (graceful degradation)
provider_registry.register("ollama", OllamaProvider())
provider_registry.register("openai", OpenAIProvider())
provider_registry.register("anthropic", AnthropicProvider())
provider_registry.register("google", GoogleProvider())
```

Each provider's `is_available()` checks for required API keys. Missing keys result in the provider being skipped (no crash).

## Model Selection (October 2025)

### OpenAI Models

- `openai:gpt-5` - GPT-5 (flagship, released Aug 2025, best overall intelligence)
- `openai:gpt-4-5` - GPT-4.5 (released Feb 2025, strong performance, lower cost)
- `openai:o4-mini` - o4-mini (reasoning model, cost-effective, fast)

### Anthropic Models

- `anthropic:claude-opus-4-1` - Claude Opus 4.1 (most powerful, released Aug 2025)
- `anthropic:claude-sonnet-4-5` - Claude Sonnet 4.5 (best coding, released Sep 2025)
- `anthropic:claude-haiku-4-5` - Claude Haiku 4.5 (fastest/cheapest, released Oct 2025)

### Google Models

- `google:gemini-2-5-pro` - Gemini 2.5 Pro (2M context, adaptive thinking)
- `google:gemini-2-5-flash` - Gemini 2.5 Flash (efficient, low-cost)

### Model Metadata Schema

Enhanced `Model` schema in `app/models/schemas.py`:

```python
class Model(BaseModel):
    name: str              # Qualified name: "openai:gpt-5", "llama3.2"
    display_name: str      # Human-readable: "GPT-5", "Llama 3.2"
    provider: str          # "ollama", "openai", "anthropic", "google"
    size: str              # "70B", "N/A" (for API models)
    description: str       # Capability description
    capabilities: List[str] = []  # ["reasoning", "coding", "fast"]
    modified_at: str = ""  # ISO timestamp (Ollama) or release date
```

## Configuration

### Environment Variables

Extend `app/core/config.py`:

```python
class Settings(BaseSettings):
    # Existing Ollama config
    ollama_url: str = "http://localhost:11434"
    default_model: str = "llama3.2"

    # Provider toggles
    enable_ollama: bool = True
    enable_openai: bool = False
    enable_anthropic: bool = False
    enable_google: bool = False

    # API keys (optional)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # Existing settings
    max_chunks: int = 5
    temperature: float = 0.1
    port: int = 8002
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
```

### Docker Compose Example

```yaml
generator:
  environment:
    # Ollama (default enabled)
    - OLLAMA_URL=http://host.docker.internal:11434
    - ENABLE_OLLAMA=true

    # OpenAI (optional)
    - ENABLE_OPENAI=false
    - OPENAI_API_KEY=${OPENAI_API_KEY}

    # Anthropic (optional)
    - ENABLE_ANTHROPIC=false
    - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

    # Google (optional)
    - ENABLE_GOOGLE=false
    - GOOGLE_API_KEY=${GOOGLE_API_KEY}
```

## Error Handling

### Provider Availability
- **Missing API Key**: Provider's `is_available()` returns `False`, not registered, logged as info
- **Invalid API Key**: Provider initialization fails, logged as warning, not registered
- **Network Failures**: Caught during `is_available()` check, provider skipped

### Generation Failures
- **Rate Limiting**: Provider catches rate limit exceptions, raises `ValueError` with message
- **Timeouts**: Each provider implements 30s timeout, raises `TimeoutError`
- **Invalid Model**: Registry checks if provider exists, raises `ValueError` if not found
- **API Errors**: Provider logs error, re-raises with context

### Graceful Degradation
1. System starts with only Ollama if no API keys configured
2. Users add API keys via environment variables
3. Restart service to register new providers
4. Frontend automatically shows new models (fetches `/models` on mount)

## Data Flow

### Model List Request

```
Frontend → GET /api/v1/models → Generator Service
  ↓
ProviderRegistry.list_all_models()
  ↓
[OllamaProvider.list_models(), OpenAIProvider.list_models(), ...]
  ↓
Aggregate and return List[Model]
  ↓
Frontend displays in dropdown (grouped by provider)
```

### Generation Request

```
Frontend → POST /api/v1/search {model: "openai:gpt-5", query: "...", chunks: [...]}
  ↓
API Service → POST /generate {model: "openai:gpt-5", ...}
  ↓
GenerationService.generate_summary(model="openai:gpt-5", ...)
  ↓
ProviderRegistry.generate("openai:gpt-5", prompt, temperature)
  ↓
Extract provider: "openai"
  ↓
OpenAIProvider.generate(model="openai:gpt-5", prompt, temp)
  ↓
OpenAI API call
  ↓
Return {response: "...", prompt_eval_count: X, eval_count: Y}
  ↓
GenerationService builds GenerateResponse(summary, model_used, tokens_used)
  ↓
API Service returns to frontend
```

## Testing Strategy

### Unit Tests (`tests/unit/providers/`)

**Test Files**:
- `test_base_provider.py` - Test abstract base class contract
- `test_ollama_provider.py` - Test refactored Ollama provider
- `test_openai_provider.py` - Mock OpenAI API, test error handling
- `test_anthropic_provider.py` - Mock Anthropic API, test error handling
- `test_google_provider.py` - Mock Google API, test error handling
- `test_registry.py` - Test registration, routing, aggregation logic

**Coverage**:
- Provider `is_available()` with missing/invalid API keys
- Model list parsing and metadata extraction
- Generation with various temperature settings
- Error handling (timeouts, rate limits, invalid responses)
- Provider routing based on model name prefix

### Integration Tests (`tests/integration/`)

**Test Files**:
- `test_provider_initialization.py` - Test startup with various env var combinations
- `test_models_endpoint.py` - Test `/models` aggregates from all providers
- `test_generation_routing.py` - Test end-to-end generation with different providers

**Scenarios**:
- Start with only Ollama (no API keys)
- Start with Ollama + OpenAI
- Start with all providers enabled
- Handle provider failures gracefully
- Validate response schemas

### Mocking Strategy

Use `pytest-httpx` to mock external API calls:
- OpenAI API responses
- Anthropic API responses
- Google API responses

This allows testing without real API keys and avoids costs.

## Implementation Phases

### Phase 1: Backend Foundation
1. Update this design doc with latest model information
2. Create `ModelProvider` abstract base class (`app/providers/base.py`)
3. Create `ProviderRegistry` class (`app/providers/registry.py`)
4. Refactor `OllamaClient` → `OllamaProvider` implementing `ModelProvider`
5. Update `GenerationService` to use `ProviderRegistry`
6. Update `Settings` in `config.py` with new environment variables
7. Enhance `Model` schema in `schemas.py` with provider metadata fields
8. Update `/models` endpoint to call `registry.list_all_models()`
9. Write unit tests for base abstractions

### Phase 2: OpenAI Provider (Validate Architecture)
10. Add `openai` SDK to `pyproject.toml`
11. Implement `OpenAIProvider` in `app/providers/openai_provider.py`
12. Add hardcoded model metadata for GPT-5, GPT-4.5, o4-mini
13. Implement error handling (rate limits, timeouts, invalid keys)
14. Write unit tests with mocked API
15. Test end-to-end generation with OpenAI (if API key available)

### Phase 3: Anthropic & Google Providers
16. Add `anthropic` SDK to `pyproject.toml`
17. Implement `AnthropicProvider` with Claude Opus 4.1, Sonnet 4.5, Haiku 4.5
18. Add `google-generativeai` SDK to `pyproject.toml`
19. Implement `GoogleProvider` with Gemini 2.5 Pro, Flash
20. Write unit tests for both providers
21. Write comprehensive integration tests
22. Update Docker Compose with example environment variables
23. Update README with provider configuration instructions

## Dependencies

### Backend (Generator Service)

**New Python Packages** (add to `pyproject.toml`):
```toml
[tool.poetry.dependencies]
openai = "^1.50.0"  # OpenAI SDK
anthropic = "^0.36.0"  # Anthropic SDK
google-generativeai = "^0.8.0"  # Google Generative AI SDK
```

**Existing Dependencies**:
- `ollama` (already installed)
- `fastapi`, `pydantic`, `uvicorn` (already installed)

## Backward Compatibility

### Existing Deployments
- Deployments without new environment variables continue working (Ollama only)
- Existing model names (e.g., `llama3.2`) work without provider prefix
- Default behavior unchanged when no API keys configured

### Migration Path
1. Deploy backend with provider abstraction (no breaking changes)
2. Existing frontend continues working with Ollama-only responses
3. Optionally add API keys via environment variables
4. Deploy frontend UI enhancements (separate implementation)
5. Users gain access to external models through updated UI

## Success Metrics

- Provider abstraction allows adding new provider in <2 hours
- System gracefully handles 0, 1, 2, 3, or 4 active providers
- `/models` endpoint responds in <500ms with all provider models aggregated
- Generation requests route correctly based on model name prefix
- No performance regression for Ollama-only deployments
- All tests pass with mocked external APIs (no real API keys needed for CI)

## Future Enhancements

- **Provider Health Monitoring**: Track availability and latency per provider
- **Automatic Fallback**: If primary provider fails, try alternate model
- **Cost Tracking**: Log token usage and estimated costs per provider
- **Custom Models**: Allow users to configure custom fine-tuned models
- **Streaming Responses**: Support streaming generation for long outputs
- **Provider-Specific Features**: Leverage unique capabilities (e.g., Google's 2M context)
