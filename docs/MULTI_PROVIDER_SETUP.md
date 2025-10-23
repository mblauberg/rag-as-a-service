# Multi-Provider Setup Guide

## Overview

The generator service supports multiple LLM providers:
- **Ollama** (local models, default enabled)
- **OpenAI** (GPT-5, GPT-4.1, requires API key)
- **Anthropic** (Claude models, requires API key)
- **Google** (Gemini models, requires API key)

## Configuration

### Environment Variables

Set these in your `.env` file or docker-compose:

```bash
# Ollama (enabled by default)
ENABLE_OLLAMA=true
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI (optional)
ENABLE_OPENAI=true
OPENAI_API_KEY=sk-...

# Anthropic (optional)
ENABLE_ANTHROPIC=true
ANTHROPIC_API_KEY=sk-ant-...

# Google (optional)
ENABLE_GOOGLE=true
GOOGLE_API_KEY=AIza...
```

### Docker Compose

Update `infrastructure/docker-compose/docker-compose.yml`:

```yaml
generator:
  environment:
    - ENABLE_OLLAMA=true
    - ENABLE_OPENAI=${ENABLE_OPENAI:-false}
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - ENABLE_ANTHROPIC=${ENABLE_ANTHROPIC:-false}
    - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    - ENABLE_GOOGLE=${ENABLE_GOOGLE:-false}
    - GOOGLE_API_KEY=${GOOGLE_API_KEY}
```

## Testing

### Test Individual Providers

```bash
# List all available models
curl http://localhost:8002/models | jq

# Generate with specific model
curl -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai:gpt-5",
    "prompt": "Summarize this",
    "context": "Context text here"
  }' | jq
```

## Frontend Integration

The model dropdown in the search bar automatically displays all available models grouped by provider. No frontend configuration needed.

## Troubleshooting

### Provider Not Showing Up

1. Check environment variable is set: `echo $OPENAI_API_KEY`
2. Check logs: `docker-compose logs generator`
3. Verify API key is valid

### Generation Failing

1. Check provider is registered: Look for "Registered X provider" in logs
2. Test API key directly with provider's CLI
3. Check rate limits on provider account
