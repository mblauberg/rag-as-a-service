# Generator Service

RAG summary generation with multi-provider LLM support.

## Supported Providers

- **OpenAI** (GPT-4o, GPT-4o Mini, GPT-5, GPT-5 Mini) - Recommended for production, requires API key
- **Ollama** (local models like llama3.2, mistral) - Good for development, no API key needed
- **Anthropic** (Claude Opus 4.1, Claude Sonnet 4.5) - Requires API key
- **Google** (Gemini 2.5 Pro, Gemini 2.5 Flash) - Requires API key

## Quick Start

### Local Development

```bash
# Install dependencies
poetry install

# Run service (Ollama only)
poetry run uvicorn app.main:app --reload --port 8002

# Run tests
poetry run pytest
```

### Enabling External Providers

Set environment variables:

```bash
# OpenAI
export ENABLE_OPENAI=true
export OPENAI_API_KEY=sk-...

# Anthropic
export ENABLE_ANTHROPIC=true
export ANTHROPIC_API_KEY=sk-ant-...

# Google
export ENABLE_GOOGLE=true
export GOOGLE_API_KEY=AIza...
```

Restart the service. Providers register automatically if keys are valid.

## API Endpoints

### List Available Models

```bash
GET /api/v1/models

Response:
{
  "models": [
    {
      "name": "llama3.2",
      "display_name": "Llama3.2",
      "provider": "ollama",
      "size": "2.0GB",
      "description": "Local Ollama model",
      "capabilities": ["local"],
      "modified_at": "2025-10-01T12:00:00Z"
    },
    {
      "name": "openai:gpt-5-mini",
      "display_name": "GPT-4o Mini",
      "provider": "openai",
      "size": "N/A",
      "description": "Cost-effective, fast responses",
      "capabilities": ["reasoning", "coding", "fast", "cost-effective"],
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
| `ENABLE_OPENAI` | `true` | Enable OpenAI provider (recommended for production) |
| `OPENAI_API_KEY` | Required | OpenAI API key |
| `ENABLE_OLLAMA` | `false` | Enable Ollama provider (local inference) |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `ENABLE_ANTHROPIC` | `false` | Enable Anthropic provider |
| `ANTHROPIC_API_KEY` | `""` | Anthropic API key (optional) |
| `ENABLE_GOOGLE` | `false` | Enable Google provider |
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

Models are identified by qualified names:

- **Ollama models**: Simple name (e.g., `llama3.2`, `mistral`)
- **API models**: Prefixed with provider (e.g., `openai:gpt-5-mini`, `anthropic:claude-sonnet-4-5`)

The registry routes requests to the appropriate provider based on the prefix.

### Graceful Degradation

- System starts with only Ollama if no API keys configured
- Providers automatically register when API keys added
- Missing API keys logged as warnings, not errors
- Frontend automatically discovers available models via `/api/v1/models`

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

### Ollama Provider

- **Local inference**: No API key required
- **Model management**: Uses Ollama's model registry
- **Availability**: Checks connection to `OLLAMA_URL`
- **Models**: Dynamically fetched from Ollama server

### OpenAI Provider

- **Models**: GPT-4o, GPT-4o Mini, GPT-5, GPT-5 Mini
- **Authentication**: Requires `OPENAI_API_KEY`
- **API**: Uses official `openai` Python SDK
- **Rate limits**: Handled by SDK with exponential backoff
- **Recommended**: Default for production deployments

### Anthropic Provider

- **Models**: Claude Opus 4.1, Claude Sonnet 4.5
- **Authentication**: Requires `ANTHROPIC_API_KEY`
- **API**: Uses official `anthropic` Python SDK
- **Streaming**: Not currently implemented

### Google Provider

- **Models**: Gemini 2.5 Pro, Gemini 2.5 Flash
- **Authentication**: Requires `GOOGLE_API_KEY`
- **API**: Uses `google-generativeai` SDK
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
4. Test with Ollama first to isolate provider issues

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

- Ollama: 1-5 seconds (local inference)
- API providers: 2-10 seconds (network + API latency)

### Scalability

- Ollama: Limited by local GPU/CPU resources
- API providers: Limited by rate limits and quotas
- Consider caching for repeated queries
- Implement request queuing for high load

### Cost Optimization

- Use Ollama for development and testing
- Reserve API providers for production
- Monitor token usage for API providers
- Consider model selection based on task complexity

## License

This service is part of the RAAS platform. See the root LICENSE file for details.
