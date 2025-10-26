# Generator Service Tests

## Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── providers/           # Provider implementation tests
│   ├── services/            # Service layer tests
│   ├── clients/             # Client tests
│   ├── test_config.py       # Configuration tests
│   └── test_schemas.py      # Schema validation tests
```

## Best Practices

### AAA Pattern
All tests follow Arrange-Act-Assert:
```python
def test_feature():
    # Arrange - setup
    # Act - perform action
    # Assert - verify result
```

### Naming Convention
`test_<method>_<scenario>_<expected_outcome>`

Examples:
- `test_generate_with_valid_prompt_returns_response`
- `test_list_models_when_provider_unavailable_returns_empty_list`

### Fixtures
Common fixtures in `conftest.py`:
- `mock_llm_response` - Standard LLM response
- `test_generation_config` - Test configuration
- `mock_anthropic_client`, `mock_openai_client`, `mock_google_client` - Mock API clients
- Provider instance fixtures for each provider type

### Mocking Strategy
- Mock external APIs (Anthropic, OpenAI, Google, Ollama)
- Test real provider logic
- No mocking internal business logic

### Running Tests

```bash
# All tests
poetry run pytest -v

# Specific provider
poetry run pytest tests/unit/providers/test_anthropic_provider.py -v

# Random order (verify independence)
poetry run pytest --random-order -v
```

## Test Coverage

- **Total Tests**: 44
- **Providers**: 27 tests (Anthropic, OpenAI, Google, Ollama, Base, Registry)
- **Services**: 7 tests (Generation, Prompt)
- **Clients**: 4 tests (Ollama client)
- **Config/Schemas**: 6 tests

All tests are independent and can run in any order.
