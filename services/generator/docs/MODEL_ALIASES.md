# Model Alias Support

## Overview

The generator service supports user-friendly model aliases that automatically map to provider-specific API model names.

## Supported Aliases

| Alias | Provider | Actual API Name |
|-------|----------|-----------------|
| gpt-5 | OpenAI | gpt-5 |
| gpt-5-mini | OpenAI | gpt-5-mini |
| sonnet-4.5 | Anthropic | claude-sonnet-4-5-20250929 |
| opus-4.1 | Anthropic | claude-opus-4-1-20250805 |
| haiku-4.5 | Anthropic | claude-haiku-4-5-20251001 |
| gemini-flash-2.5 | Google | gemini-2.5-flash |
| gemini-pro-2.5 | Google | gemini-2.5-pro |

## Usage

### Using Aliases

```bash
curl -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "your query",
    "chunks": [...],
    "model": "sonnet-4.5"
  }'
```

### Using Provider:Model Format (Backward Compatible)

```bash
curl -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "your query",
    "chunks": [...],
    "model": "anthropic:claude-sonnet-4-5-20250929"
  }'
```

## Provider Configuration

At least **one** provider API key must be configured:

- `OPENAI_API_KEY` - for gpt-5, gpt-5-mini, gpt-4o models
- `ANTHROPIC_API_KEY` - for sonnet-4.5, opus-4.1, haiku-4.5 models
- `GOOGLE_API_KEY` - for gemini-flash-2.5, gemini-pro-2.5 models

## Error Handling

If you request a model whose provider isn't configured:

```json
{
  "error": "Provider 'openai' not available (no API key configured). Available providers: ['anthropic', 'google']"
}
```

## Adding New Aliases

To add new model aliases:

1. Add to `MODEL_ALIASES` in `app/providers/registry.py`
2. Add corresponding entry to provider's `MODELS` list
3. Update this documentation
4. Add tests to `tests/unit/providers/test_registry.py`
