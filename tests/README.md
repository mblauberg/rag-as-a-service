# RAAS Testing Guide

This directory contains integration tests for the RAAS (Retrieval-Augmented Answer System) platform.

## Directory Structure

```
tests/
├── integration/          # End-to-end integration tests
│   ├── *.py             # Python/Playwright browser tests
│   ├── *.sh             # Shell script integration tests
│   └── upload_test_corpus.py  # Utility to upload test documents
└── debug/               # Debugging utilities (not part of test suite)
    └── debug_dom_structure.py  # DOM inspection tool for test development
```

## Integration Tests

### Python/Playwright Tests

Browser tests for frontend:

- `test_webapp.py` - Basic functionality
- `test_documents_page.py` - Document listing
- `test_upload_search.py` - Upload and search
- `test_ai_summary_placement.py` - AI summaries
- `test_summary_fix.py` - Summary API
- `test_httpx_redirects.py` - HTTP redirects

**Running Playwright tests:**
```bash
# Install dependencies first
pip install playwright httpx pytest pytest-asyncio
playwright install chromium

# Run individual test
python tests/integration/test_webapp.py

# Or with pytest
pytest tests/integration/test_webapp.py -v
```

### Shell Script Tests

End-to-end tests using curl:

- `test_full_workflow.sh` - Upload, search, delete
- `test_generation_flow.sh` - AI generation with citations
- `test_multi_provider.sh` - Multi-provider models

**Running shell tests:**
```bash
# Make executable first
chmod +x tests/integration/*.sh

# Run from repository root
./tests/integration/test_full_workflow.sh
```

## Prerequisites

### For Python Tests
- Python 3.10+
- Playwright: `pip install playwright && playwright install`
- httpx: `pip install httpx`
- pytest: `pip install pytest pytest-asyncio`

### For Shell Tests
- bash
- curl
- jq (for JSON parsing): `brew install jq` or `apt-get install jq`
- Docker and Docker Compose

### Services Must Be Running
All tests require the RAAS services to be running:

```bash
# Start all services
cd infrastructure/docker-compose
docker-compose up -d

# Verify services are ready
curl http://localhost:8000/api/v1/health
curl http://localhost:3000
```

## Test Configuration

### Service URLs
- Frontend: `http://localhost:3000`
- API Service: `http://localhost:8000`
- Embedder Service: `http://localhost:8001`
- Generator Service: `http://localhost:8002`

### Valid Models for Testing

Use these model identifiers in tests:
- `openai:gpt-5-mini` - Latest fast OpenAI model (default, requires API key)
- `openai:gpt-5` - Latest advanced OpenAI model (requires API key)
- `anthropic:claude-sonnet-4-5` - Anthropic Sonnet model (requires API key)
- `anthropic:claude-opus-4-1` - Anthropic Opus model (requires API key)
- `google:gemini-2.5-flash` - Google Flash model (requires API key)
- `google:gemini-2.5-pro` - Google Pro model (requires API key)

**Note:** Always use cloud provider models with appropriate API keys configured for testing.

## Debugging Tools

### debug_dom_structure.py

Not part of the automated test suite. Used for:
- Inspecting frontend DOM structure
- Finding correct Playwright selectors
- Debugging test failures due to UI changes

**Usage:**
```bash
# Ensure frontend is running first
python tests/debug/debug_dom_structure.py
```

## Common Issues

### Tests Fail Immediately
- **Cause:** Services not running
- **Fix:** Start services with `docker-compose up -d`

### Search/Upload Tests Fail
- **Cause:** Services not ready yet
- **Fix:** Wait 30s after starting services for embeddings to initialize

### Model Not Found Errors
- **Cause:** Using invalid model name
- **Fix:** Check available models at `http://localhost:8000/api/v1/models`

### Playwright Browser Not Found
- **Cause:** Browser binaries not installed
- **Fix:** Run `playwright install chromium`

## Writing New Tests

### Python/Playwright Test Template
```python
#!/usr/bin/env python3
"""Test description."""
import asyncio
from playwright.async_api import async_playwright

async def test_your_feature():
    """Test your feature description."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto('http://localhost:3000')
        # Your test logic here

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_your_feature())
```

### Shell Test Template
```bash
#!/bin/bash
set -e

echo "Testing feature..."
response=$(curl -s http://localhost:8000/api/v1/endpoint)

if echo "$response" | grep -q "expected"; then
    echo "✓ Test passed"
else
    echo "✗ Test failed"
    exit 1
fi
```

## Best Practices

1. **Test Independence** – Each test should clean up after itself
2. **Timeouts** – Use appropriate timeouts for async operations (default: 60s)
3. **Model Selection** – Use `openai:gpt-5-mini` for speed, only use larger models when necessary
4. **Error Messages** – Include descriptive output for debugging failures
5. **Service Health** – Check service health before running tests

## Unit Tests

For service-specific unit tests, see:
- `services/api/tests/` - API service unit tests
- `services/generator/tests/` - Generator service unit tests
- `services/embedder/tests/` - Embedder service unit tests

Each service has its own test suite with pytest configuration.
