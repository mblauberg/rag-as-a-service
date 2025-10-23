# Generator Service

LLM-based text generation service for RAAS using Ollama.

## Features

- Generate summaries from document chunks
- Support multiple Ollama models
- RAG-specific prompt engineering
- Inline citation generation

## Development

```bash
poetry install
poetry run uvicorn app.main:app --reload --port 8002
```

## Testing

```bash
poetry run pytest
```

## Environment Variables

See `.env.example` for configuration options.
