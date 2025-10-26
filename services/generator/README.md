# Generator Service

RAG summary generation with multi-provider LLM support.

## Supported Providers

All providers are cloud-based for production reliability, scalability, and consistent performance:

- **OpenAI** (GPT-4o, GPT-4o Mini, GPT-5, GPT-5 Mini) - Primary provider, recommended for production
- **Anthropic** (Claude Opus 4.1, Claude Sonnet 4.5) - Alternative provider for graceful degradation
- **Google** (Gemini 2.5 Pro, Gemini 2.5 Flash) - Alternative provider for vendor flexibility

## Quick Start

### Local Development

```bash
# Install dependencies
poetry install

# Set up environment (copy .env.example to .env and add API keys)
cp .env.example .env

# Run service
poetry run uvicorn app.main:app --reload --port 8002

# Run tests
poetry run pytest
```

### Configuring Providers

Set environment variables:

```bash
# OpenAI (Primary)
export ENABLE_OPENAI=true
export OPENAI_API_KEY=sk-...

# Anthropic (Optional - for fallback/alternative)
export ENABLE_ANTHROPIC=true
export ANTHROPIC_API_KEY=sk-ant-...

# Google (Optional - for fallback/alternative)
export ENABLE_GOOGLE=true
export GOOGLE_API_KEY=AIza...
```

Providers register automatically if API keys are valid. At least one provider must be configured for the service to function.

## API Endpoints

### List Available Models

```bash
GET /api/v1/models

Response:
{
  "models": [
    {
      "name": "openai:gpt-5-mini",
      "display_name": "GPT-5 Mini",
      "provider": "openai",
      "size": "N/A",
      "description": "Cost-effective, fast responses with reasoning",
      "capabilities": ["reasoning", "coding", "fast", "cost-effective"],
      "modified_at": "2025-10-24T12:00:00Z"
    },
    {
      "name": "anthropic:claude-sonnet-4-5",
      "display_name": "Claude Sonnet 4.5",
      "provider": "anthropic",
      "size": "N/A",
      "description": "Balanced performance and intelligence",
      "capabilities": ["reasoning", "coding", "analysis"],
      "modified_at": "2025-10-24T12:00:00Z"
    }
  ]
}
```

### Generate Summary

```bash
POST /api/v1/generate
{
  "query": "What is cloud computing?",
  "chunks": [...],
  "model": "openai:gpt-5-mini"  # Optional, defaults to DEFAULT_MODEL
}

Response:
{
  "summary": "Cloud computing provides...",
  "model_used": "openai:gpt-5-mini",
  "tokens_used": 0
}
```

## Configuration

Environment variables:

| Variable | Default (.env.example) | Description |
|----------|---------|-------------|
| `DEFAULT_MODEL` | `openai:gpt-5-mini` | Default model if not specified in request |
| `ENABLE_OPENAI` | `true` | Enable OpenAI provider (primary) |
| `OPENAI_API_KEY` | Required | OpenAI API key |
| `ENABLE_ANTHROPIC` | `false` | Enable Anthropic provider (optional) |
| `ANTHROPIC_API_KEY` | `""` | Anthropic API key (optional) |
| `ENABLE_GOOGLE` | `false` | Enable Google provider (optional) |
| `GOOGLE_API_KEY` | `""` | Google API key (optional) |
| `MAX_CHUNKS` | `5` | Maximum document chunks to include in context |
| `TEMPERATURE` | `0.1` | Generation temperature (0.0-1.0) |
| `MAX_TOKENS` | `2000` | Maximum tokens in generated response |
| `TIMEOUT` | `30` | Request timeout in seconds |

## Architecture

### Provider Abstraction

All providers implement the `ModelProvider` interface:

```python
class ModelProvider(ABC):
    async def list_models() -> List[Model]
    async def generate(model: str, prompt: str, context: str) -> str
    def is_available() -> bool
```

### Provider Registry

The `ProviderRegistry` manages all providers:

- Registers providers at startup if `is_available()` returns True
- Routes generation requests based on model name prefix
- Aggregates models from all registered providers

### Model Naming Convention

All models use qualified names with provider prefixes:

- **Format**: `provider:model-name`
- **Examples**: `openai:gpt-5-mini`, `anthropic:claude-sonnet-4-5`, `google:gemini-2.5-pro`

The registry routes requests to the appropriate provider based on the prefix.

### Graceful Degradation

- At least one provider (OpenAI recommended) must be configured
- Additional providers register automatically when API keys are valid
- Missing optional API keys logged as warnings, not errors
- Frontend automatically discovers available models via `/api/v1/models`
- Provider abstraction enables switching between vendors without code changes

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=term-missing

# Run specific test file
poetry run pytest tests/unit/providers/test_openai_provider.py -v

# Run integration tests only
poetry run pytest tests/integration/ -v
```

## Provider Details

### OpenAI Provider (Primary)

- **Models**: GPT-4o, GPT-4o Mini, GPT-5, GPT-5 Mini (default: gpt-5-mini)
- **Authentication**: Requires `OPENAI_API_KEY`
- **API**: Uses official `openai` Python SDK
- **Rate limits**: Handled by SDK with exponential backoff
- **Status**: Primary provider for production deployments

### Anthropic Provider (Alternative)

- **Models**: Claude Opus 4.1, Claude Sonnet 4.5
- **Authentication**: Requires `ANTHROPIC_API_KEY`
- **API**: Uses official `anthropic` Python SDK
- **Status**: Optional fallback provider
- **Streaming**: Not currently implemented

### Google Provider (Alternative)

- **Models**: Gemini 2.5 Pro, Gemini 2.5 Flash
- **Authentication**: Requires `GOOGLE_API_KEY`
- **API**: Uses `google-generativeai` SDK
- **Status**: Optional fallback provider
- **Safety settings**: Configured to block only high-risk content

## Adding a New Provider

1. **Create provider class** in `app/providers/your_provider.py`:

```python
from app.providers.base import ModelProvider
from app.models.schemas import Model

class YourProvider(ModelProvider):
    async def list_models(self) -> List[Model]:
        # Return list of available models
        pass

    async def generate(self, model: str, prompt: str, context: str) -> str:
        # Generate text using the provider's API
        pass

    def is_available(self) -> bool:
        # Check if API key is configured
        pass
```

2. **Add configuration** to `app/core/config.py`:

```python
class Settings(BaseSettings):
    enable_yourprovider: bool = False
    yourprovider_api_key: str = ""
```

3. **Register provider** in `app/main.py`:

```python
from app.providers.your_provider import YourProvider

provider_registry.register("yourprovider", YourProvider())
```

4. **Write tests** in `tests/unit/providers/test_your_provider.py`:

```python
import pytest
from app.providers.your_provider import YourProvider

@pytest.mark.asyncio
async def test_list_models():
    provider = YourProvider()
    if provider.is_available():
        models = await provider.list_models()
        assert len(models) > 0
```

## Troubleshooting

### Provider not registering

Check startup logs for warnings:
```
WARNING: OpenAI provider not available - missing API key
```

Ensure environment variables are set correctly and service is restarted.

### Models not appearing

1. Check provider is enabled: `ENABLE_<PROVIDER>=true`
2. Verify API key is valid
3. Check logs for provider initialization errors
4. Test provider availability: `curl http://localhost:8002/api/v1/models`

### Generation failures

1. Check model name is correctly prefixed (e.g., `openai:gpt-5-mini`)
2. Verify API key has sufficient credits/quota
3. Review logs for detailed error messages
4. Try alternative provider to isolate provider-specific issues

## Development Guidelines

### Code Style

- Follow PEP 8 conventions
- Use type hints for all function signatures
- Add docstrings to all public methods
- Keep functions focused and single-purpose

### Testing

- Write unit tests for all providers
- Mock external API calls in tests
- Test both success and failure scenarios
- Maintain test coverage above 80%

### Error Handling

- Catch provider-specific exceptions
- Return descriptive error messages
- Log errors with appropriate severity
- Don't expose API keys in logs or responses

## Performance Considerations

### Response Times

- Cloud API providers: 2-10 seconds (network + API latency + generation time)
- Varies by model size and complexity
- Consider using faster models (gpt-5-mini, gemini-2.5-flash) for time-sensitive queries

### Scalability

- Cloud providers scale automatically with demand
- Limited by API rate limits and quotas
- Consider caching for repeated queries
- Implement request queuing for high load
- Monitor concurrent request limits

### Cost Optimization

- Default to cost-effective models (gpt-5-mini) for most queries
- Reserve premium models (gpt-5, claude-opus-4-1) for complex analysis
- Monitor token usage across all providers
- Implement response caching to reduce API calls
- Consider model selection based on task complexity and budget

## License

This service is part of the RAAS platform. See the root LICENSE file for details.
