# API Service Tests

## Overview

This test suite covers the RAAS API service using pytest and follows hexagonal architecture patterns.

## Running Tests

### All Tests
```bash
poetry run pytest tests/ -v
```

### Specific Test Categories
```bash
# Unit tests only
poetry run pytest tests/unit/ -v

# Integration tests only
poetry run pytest tests/integration/ -v

# Domain tests
poetry run pytest tests/domain/ -v

# Infrastructure tests
poetry run pytest tests/infrastructure/ -v

# Application tests
poetry run pytest tests/application/ -v
```

### With Coverage
```bash
poetry run pytest tests/ --cov=app --cov-report=html
```

## Test Organization

```
tests/
├── api/              # API endpoint tests
├── application/      # Application layer use cases
├── domain/           # Domain model tests
├── infrastructure/   # Infrastructure implementations
├── integration/      # End-to-end integration tests
├── ports/            # Port interface tests
├── services/         # Service layer tests
├── unit/             # Unit tests for core components
└── utils/            # Utility function tests
```

## Key Testing Patterns

### Async Tests
Tests use `pytest-asyncio` for async operations:
```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result is not None
```

### Mocking
Use `pytest-mock` for dependency injection:
```python
def test_with_mock(mocker):
    mock_repo = mocker.Mock()
    service = MyService(mock_repo)
    # test logic
```

### Fixtures
Common fixtures defined in `conftest.py`:
- `db_session`: Database session for tests
- `test_client`: FastAPI test client
- `mock_qdrant_client`: Mocked vector store

## Current Status

**Baseline Results (2025-10-26):**
- Total: 297 tests
- Passed: 256
- Failed: 30
- Errors: 11

Main issues:
- Database constraint failures (missing file_size in fixtures)
- Service unavailability in some integration tests

## Dependencies

Tests require:
- Python 3.13+
- pytest 8.3.0+
- pytest-asyncio 0.24.0+
- pytest-mock 3.14.0+

Install with:
```bash
poetry install --with dev
```

## Notes

- Integration tests may require running services (Qdrant, Generator)
- Use `.env.test` for test-specific configuration
- Model references use current OpenAI models (gpt-4, gpt-4o-mini)
