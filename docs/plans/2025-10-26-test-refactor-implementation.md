# Comprehensive Test Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor all test files across services to remove obsolete tests, enforce best practices, and establish consistent patterns.

**Architecture:** Service-by-service deep clean starting with Generator (pilot), then API, Frontend, Embedder, and finally root integration tests. Each service goes through Audit → Cleanup → Restructure → Validate → Document phases.

**Tech Stack:** pytest, Vitest, Playwright, Python, TypeScript

---

## Phase 1: Generator Service (Pilot Refactor)

### Task 1: Baseline - Capture Current Test State

**Files:**
- Read: `services/generator/tests/`
- Create: `.test-refactor-baseline-generator.txt`

**Step 1: Run current test suite and capture results**

```bash
cd services/generator
poetry install
poetry run pytest -v --tb=short > ../../.test-refactor-baseline-generator.txt 2>&1
```

Expected: Capture all test results (pass/fail counts)

**Step 2: Review baseline**

```bash
cat ../../.test-refactor-baseline-generator.txt | grep -E "passed|failed|error"
```

Expected: See summary like "X passed, Y failed"

**Step 3: Commit baseline**

```bash
git add .test-refactor-baseline-generator.txt
git commit -m "test(generator): capture baseline test results before refactor"
```

### Task 2: Audit - Inventory Test Files

**Files:**
- Read: `services/generator/tests/`
- Create: `.generator-test-audit.md`

**Step 1: List all test files with line counts**

```bash
cd services/generator/tests
find . -name "*.py" -type f | xargs wc -l | sort -rn > ../../../.generator-test-audit.md
```

**Step 2: Document current structure**

Append to `.generator-test-audit.md`:
```markdown
## Current Structure
- Root level: test_generation_service.py, test_ollama_client.py, test_prompt_service.py, test_schemas.py
- unit/providers/: test_anthropic.py, test_google.py, test_openai.py, test_ollama.py, test_base.py
- unit/: test_config.py, test_registry.py

## Issues Found
- [ ] Tests outside unit/ directory
- [ ] Check for outdated model references
- [ ] Check fixture organization
```

**Step 3: Commit audit**

```bash
git add .generator-test-audit.md
git commit -m "test(generator): audit current test structure"
```

### Task 3: Restructure - Move Root Tests to Unit Directory

**Files:**
- Move: `services/generator/tests/test_generation_service.py` → `services/generator/tests/unit/services/test_generation_service.py`
- Move: `services/generator/tests/test_ollama_client.py` → `services/generator/tests/unit/clients/test_ollama_client.py`
- Move: `services/generator/tests/test_prompt_service.py` → `services/generator/tests/unit/services/test_prompt_service.py`
- Move: `services/generator/tests/test_schemas.py` → `services/generator/tests/unit/test_schemas.py`

**Step 1: Create new directory structure**

```bash
cd services/generator/tests
mkdir -p unit/services unit/clients
```

**Step 2: Move files**

```bash
mv test_generation_service.py unit/services/
mv test_ollama_client.py unit/clients/
mv test_prompt_service.py unit/services/
mv test_schemas.py unit/
```

**Step 3: Verify tests still work**

```bash
cd ..
poetry run pytest -v
```

Expected: Same number of tests pass as baseline

**Step 4: Commit restructure**

```bash
git add tests/
git commit -m "test(generator): reorganize tests into unit/ subdirectories"
```

### Task 4: Centralize Fixtures in conftest.py

**Files:**
- Create: `services/generator/tests/conftest.py`
- Read: All test files to identify common fixtures

**Step 1: Create conftest.py with common fixtures**

```python
# services/generator/tests/conftest.py
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_llm_response():
    """Standard mock LLM response for testing."""
    return {
        "id": "test-completion-id",
        "choices": [{"message": {"content": "Test response"}}],
        "model": "test-model",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20}
    }

@pytest.fixture
def test_generation_config():
    """Test configuration for generation service."""
    return {
        "provider": "ollama",
        "model": "llama2",
        "temperature": 0.7,
        "max_tokens": 100
    }

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    client = Mock()
    client.messages = Mock()
    client.messages.create = AsyncMock()
    return client

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = AsyncMock()
    return client

@pytest.fixture
def mock_google_client():
    """Mock Google client."""
    client = Mock()
    client.generate_content = AsyncMock()
    return client
```

**Step 2: Run tests to verify fixtures work**

```bash
cd services/generator
poetry run pytest -v
```

Expected: Tests still pass with centralized fixtures

**Step 3: Commit conftest**

```bash
git add tests/conftest.py
git commit -m "test(generator): centralize common fixtures in conftest.py"
```

### Task 5: Enforce AAA Pattern - Provider Tests

**Files:**
- Modify: `services/generator/tests/unit/providers/test_anthropic.py`
- Modify: `services/generator/tests/unit/providers/test_openai.py`
- Modify: `services/generator/tests/unit/providers/test_google.py`
- Modify: `services/generator/tests/unit/providers/test_ollama.py`

**Step 1: Review one provider test for AAA pattern**

Read `services/generator/tests/unit/providers/test_anthropic.py` and check each test follows:
```python
def test_feature_scenario_outcome():
    # Arrange - setup test data
    provider = AnthropicProvider(config)
    request = GenerationRequest(...)

    # Act - perform the action
    result = await provider.generate(request)

    # Assert - verify expectations
    assert result.content == expected
```

**Step 2: Refactor tests to enforce AAA with comments**

For each test that doesn't follow AAA, add clear section comments:

```python
@pytest.mark.asyncio
async def test_generate_with_valid_request_returns_response(mock_anthropic_client):
    # Arrange
    provider = AnthropicProvider(client=mock_anthropic_client)
    request = GenerationRequest(prompt="test", model="claude-3")
    mock_anthropic_client.messages.create.return_value = Mock(content=[Mock(text="response")])

    # Act
    result = await provider.generate(request)

    # Assert
    assert result.content == "response"
    mock_anthropic_client.messages.create.assert_called_once()
```

**Step 3: Run tests**

```bash
poetry run pytest tests/unit/providers/ -v
```

Expected: All provider tests pass

**Step 4: Commit AAA enforcement**

```bash
git add tests/unit/providers/
git commit -m "test(generator): enforce AAA pattern in provider tests"
```

### Task 6: Improve Test Names - Follow Convention

**Files:**
- Modify: All test files in `services/generator/tests/`

**Step 1: Review test naming convention**

Target format: `test_<method>_<scenario>_<expected_outcome>`

Examples:
- `test_generate_with_invalid_provider_raises_error`
- `test_register_provider_with_duplicate_name_raises_error`
- `test_create_prompt_with_system_message_includes_system_role`

**Step 2: Rename vague test names**

Find and rename tests like:
- `test_1` → `test_generate_with_valid_request_returns_response`
- `test_success` → `test_register_provider_with_unique_name_succeeds`
- `test_error` → `test_generate_with_missing_model_raises_value_error`

**Step 3: Run tests**

```bash
poetry run pytest -v
```

Expected: All tests pass with descriptive names

**Step 4: Commit naming improvements**

```bash
git add tests/
git commit -m "test(generator): improve test names following convention"
```

### Task 7: Remove Over-Mocking - Test Real Logic

**Files:**
- Review: All test files for over-mocking

**Step 1: Identify over-mocked tests**

Look for tests that mock everything including the logic being tested:
```python
# BAD - testing mock behavior
def test_process():
    processor = Mock()
    processor.process.return_value = "mocked"
    assert processor.process() == "mocked"  # Just testing mock!
```

**Step 2: Refactor to test real implementations**

```python
# GOOD - testing real logic
def test_process_with_valid_input_returns_formatted_output():
    # Arrange
    processor = RealProcessor()  # Real implementation
    mock_external_api = Mock()   # Only mock external deps
    processor.api_client = mock_external_api

    # Act
    result = processor.process("input")

    # Assert - verify real processing logic
    assert result == expected_transformation("input")
```

**Step 3: Run tests**

```bash
poetry run pytest -v
```

Expected: Tests still pass, now testing real behavior

**Step 4: Commit mock reduction**

```bash
git add tests/
git commit -m "test(generator): reduce over-mocking, test real implementations"
```

### Task 8: Add Missing Coverage - Error Handling

**Files:**
- Modify: `services/generator/tests/unit/providers/test_base.py`
- Modify: `services/generator/tests/unit/test_registry.py`

**Step 1: Write failing test for error handling**

```python
# services/generator/tests/unit/providers/test_base.py

@pytest.mark.asyncio
async def test_generate_with_network_error_raises_generation_error():
    # Arrange
    provider = BaseProvider()
    provider._make_api_call = AsyncMock(side_effect=ConnectionError("Network down"))

    # Act & Assert
    with pytest.raises(GenerationError, match="Network down"):
        await provider.generate(request)
```

**Step 2: Run test to verify it fails or passes**

```bash
poetry run pytest tests/unit/providers/test_base.py::test_generate_with_network_error_raises_generation_error -v
```

Expected: Test either passes (coverage exists) or fails (needs implementation)

**Step 3: If needed, implement error handling**

Only if test fails - add proper error handling to source code.

**Step 4: Run full suite**

```bash
poetry run pytest -v
```

Expected: All tests pass including new error handling tests

**Step 5: Commit coverage additions**

```bash
git add tests/ services/generator/
git commit -m "test(generator): add error handling test coverage"
```

### Task 9: Validate - Full Generator Test Suite

**Files:**
- Read: `.test-refactor-baseline-generator.txt`

**Step 1: Run full test suite**

```bash
cd services/generator
poetry run pytest -v --tb=short
```

Expected: All tests pass

**Step 2: Compare with baseline**

```bash
poetry run pytest -v | grep -E "passed|failed|error"
cat ../../.test-refactor-baseline-generator.txt | grep -E "passed|failed|error"
```

Expected: Same or more tests passing, none failing

**Step 3: Run tests in random order**

```bash
poetry run pytest --random-order -v
```

Expected: All tests pass (no interdependencies)

**Step 4: Commit validation success**

```bash
git commit --allow-empty -m "test(generator): validate refactor - all tests passing"
```

### Task 10: Document - Update Generator Testing Guidelines

**Files:**
- Create: `services/generator/tests/README.md`

**Step 1: Write testing guidelines**

```markdown
# Generator Service Tests

## Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── providers/           # Provider implementation tests
│   ├── services/            # Service layer tests
│   ├── clients/             # Client tests
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

### Fixtures
Common fixtures in `conftest.py`:
- `mock_llm_response` - Standard LLM response
- `test_generation_config` - Test configuration
- `mock_anthropic_client`, `mock_openai_client`, etc.

### Mocking Strategy
- Mock external APIs (Anthropic, OpenAI, Google)
- Test real provider logic
- No mocking internal business logic

### Running Tests
```bash
# All tests
poetry run pytest -v

# Specific provider
poetry run pytest tests/unit/providers/test_anthropic.py -v

# Random order (verify independence)
poetry run pytest --random-order -v
```
```

**Step 2: Commit documentation**

```bash
git add tests/README.md
git commit -m "docs(generator): add testing guidelines"
```

---

## Phase 2: API Service Refactor

### Task 11: Baseline - Capture API Test State

**Files:**
- Create: `.test-refactor-baseline-api.txt`

**Step 1: Run current test suite**

```bash
cd services/api
poetry install
poetry run pytest -v --tb=short > ../../.test-refactor-baseline-api.txt 2>&1
```

**Step 2: Review baseline**

```bash
cat ../../.test-refactor-baseline-api.txt | tail -20
```

**Step 3: Commit baseline**

```bash
git add .test-refactor-baseline-api.txt
git commit -m "test(api): capture baseline test results before refactor"
```

### Task 12: Cleanup - Remove Orphaned .pyc Files

**Files:**
- Delete: Orphaned `__pycache__` entries

**Step 1: Find orphaned .pyc files**

```bash
cd services/api/tests
find . -name "*.pyc" | while read pyc; do
    py="${pyc%.pyc}.py"
    py="${py//__pycache__\//}"
    py="${py//.cpython-*/}"
    if [ ! -f "$py" ]; then
        echo "Orphaned: $pyc (no $py)"
    fi
done
```

**Step 2: Remove orphaned cache directories**

```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
```

**Step 3: Verify tests still work**

```bash
cd ..
poetry run pytest -v | head -50
```

Expected: Tests run cleanly without old cache

**Step 4: Commit cleanup**

```bash
git add -A
git commit -m "test(api): remove orphaned pycache files"
```

### Task 13: Audit - Review Test-to-Code Alignment

**Files:**
- Read: `services/api/tests/infrastructure/`
- Read: `services/api/app/infrastructure/`

**Step 1: List test files and corresponding source files**

```bash
cd services/api
find tests/ -name "test_*.py" | sort > /tmp/test-files.txt
find app/ -name "*.py" | grep -v __pycache__ | sort > /tmp/source-files.txt
```

**Step 2: Check for tests without corresponding source**

For each test file, verify corresponding source exists. Document any mismatches in `.api-test-audit.md`

**Step 3: Identify deprecated feature tests**

Look for test files testing old features (check git history if needed):
```bash
git log --all --oneline --source --grep="remove\|deprecate\|delete" -- services/api/ | head -20
```

**Step 4: Document findings**

Create `.api-test-audit.md` with findings and commit.

```bash
git add .api-test-audit.md
git commit -m "test(api): audit test-to-code alignment"
```

### Task 14: Fixture Consolidation - Review conftest.py Hierarchy

**Files:**
- Read: `services/api/tests/conftest.py`
- Read: `services/api/tests/*/conftest.py`

**Step 1: List all conftest files**

```bash
cd services/api/tests
find . -name "conftest.py"
```

**Step 2: Identify duplicate fixtures**

```bash
for conf in $(find . -name "conftest.py"); do
    echo "=== $conf ==="
    grep "@pytest.fixture" "$conf" | sed 's/def //' | sed 's/(.*//'
done
```

**Step 3: Move common fixtures to root conftest**

If fixtures are duplicated across multiple conftest files, consolidate them into the root `tests/conftest.py`.

**Step 4: Run tests**

```bash
cd ..
poetry run pytest -v | tail -20
```

Expected: All tests pass with consolidated fixtures

**Step 5: Commit consolidation**

```bash
git add tests/
git commit -m "test(api): consolidate duplicate fixtures to root conftest"
```

### Task 15: Integration Tests - Verify Cross-Boundary Testing

**Files:**
- Read: `services/api/tests/integration/`

**Step 1: Review integration tests**

Check each integration test actually tests cross-boundary interactions (not just unit behavior with real DB).

**Step 2: Ensure proper markers**

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_document_stores_in_qdrant_and_db():
    # This should test API → Qdrant + DB interaction
    pass
```

**Step 3: Run only integration tests**

```bash
cd services/api
poetry run pytest -v -m integration
```

Expected: Integration tests pass

**Step 4: Commit any marker corrections**

```bash
git add tests/integration/
git commit -m "test(api): verify integration test markers and scope"
```

### Task 16: Apply AAA Pattern - API Layer Tests

**Files:**
- Modify: `services/api/tests/api/`

**Step 1: Review API endpoint tests**

```bash
cd services/api/tests/api
ls -la
```

**Step 2: Enforce AAA in endpoint tests**

Example:
```python
@pytest.mark.asyncio
async def test_health_endpoint_returns_200_with_status_ok():
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:

        # Act
        response = await client.get("/health")

        # Assert
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
```

**Step 3: Run API tests**

```bash
cd ../..
poetry run pytest tests/api/ -v
```

Expected: All API tests pass with AAA structure

**Step 4: Commit AAA enforcement**

```bash
git add tests/api/
git commit -m "test(api): enforce AAA pattern in API endpoint tests"
```

### Task 17: Apply AAA Pattern - Application Layer Tests

**Files:**
- Modify: `services/api/tests/application/`

**Step 1: Review use case tests**

```bash
cd services/api/tests/application
ls -la
```

**Step 2: Enforce AAA in use case tests**

**Step 3: Run application tests**

```bash
cd ../..
poetry run pytest tests/application/ -v
```

Expected: All application tests pass

**Step 4: Commit AAA enforcement**

```bash
git add tests/application/
git commit -m "test(api): enforce AAA pattern in application layer tests"
```

### Task 18: Apply AAA Pattern - Domain Layer Tests

**Files:**
- Modify: `services/api/tests/domain/`

**Step 1: Review domain entity tests**

**Step 2: Enforce AAA in domain tests**

**Step 3: Run domain tests**

```bash
poetry run pytest tests/domain/ -v
```

Expected: All domain tests pass

**Step 4: Commit AAA enforcement**

```bash
git add tests/domain/
git commit -m "test(api): enforce AAA pattern in domain layer tests"
```

### Task 19: Apply AAA Pattern - Infrastructure Layer Tests

**Files:**
- Modify: `services/api/tests/infrastructure/`

**Step 1: Review infrastructure tests**

**Step 2: Enforce AAA in infrastructure tests**

**Step 3: Run infrastructure tests**

```bash
poetry run pytest tests/infrastructure/ -v
```

Expected: All infrastructure tests pass

**Step 4: Commit AAA enforcement**

```bash
git add tests/infrastructure/
git commit -m "test(api): enforce AAA pattern in infrastructure layer tests"
```

### Task 20: Improve Test Names - API Service

**Files:**
- Modify: All test files in `services/api/tests/`

**Step 1: Find vague test names**

```bash
cd services/api/tests
grep -r "def test_[0-9]" . || echo "No numeric tests found"
grep -r "def test_success" . || echo "No vague 'success' tests"
grep -r "def test_error" . || echo "No vague 'error' tests"
```

**Step 2: Rename to follow convention**

`test_<method>_<scenario>_<expected_outcome>`

**Step 3: Run tests**

```bash
cd ..
poetry run pytest -v | head -100
```

Expected: Descriptive test names in output

**Step 4: Commit naming improvements**

```bash
git add tests/
git commit -m "test(api): improve test names following convention"
```

### Task 21: Validate - Full API Test Suite

**Files:**
- Read: `.test-refactor-baseline-api.txt`

**Step 1: Run full test suite**

```bash
cd services/api
poetry run pytest -v --tb=short
```

Expected: All tests pass

**Step 2: Compare with baseline**

```bash
poetry run pytest -v 2>&1 | grep -E "passed|failed|error"
cat ../../.test-refactor-baseline-api.txt | grep -E "passed|failed|error"
```

Expected: Same or more tests passing

**Step 3: Verify test independence**

```bash
poetry run pytest --random-order -v | tail -50
```

Expected: All tests pass in random order

**Step 4: Commit validation**

```bash
git commit --allow-empty -m "test(api): validate refactor - all tests passing"
```

### Task 22: Document - Update API Testing Guidelines

**Files:**
- Modify: `services/api/tests/README.md` (or create if missing)

**Step 1: Document test organization**

```markdown
# API Service Tests

## Architecture

Tests follow hexagonal/clean architecture:

```
tests/
├── conftest.py              # Shared fixtures
├── api/                     # API endpoints (HTTP layer)
├── application/             # Use cases (business logic)
├── domain/                  # Entities, value objects
├── infrastructure/          # External integrations (DB, Qdrant, etc)
├── ports/                   # Port/interface contract tests
├── services/                # Document processors
├── unit/                    # Unit tests (config, models, utils)
└── integration/             # Cross-boundary integration tests
```

## Best Practices

[Same as Generator service: AAA, naming, fixtures, mocking strategy]

## Running Tests

```bash
# All tests
poetry run pytest -v

# Specific layer
poetry run pytest tests/application/ -v

# Unit tests only
poetry run pytest -v -m unit

# Integration tests only
poetry run pytest -v -m integration

# Random order
poetry run pytest --random-order -v
```
```

**Step 2: Commit documentation**

```bash
git add tests/README.md
git commit -m "docs(api): update testing guidelines"
```

---

## Phase 3: Frontend Service Refactor

### Task 23: Baseline - Capture Frontend Test State

**Files:**
- Create: `.test-refactor-baseline-frontend.txt`

**Step 1: Run frontend tests**

```bash
cd services/frontend
npm install
npm test > ../../.test-refactor-baseline-frontend.txt 2>&1
```

**Step 2: Review baseline**

```bash
cat ../../.test-refactor-baseline-frontend.txt | tail -30
```

**Step 3: Commit baseline**

```bash
git add .test-refactor-baseline-frontend.txt
git commit -m "test(frontend): capture baseline test results before refactor"
```

### Task 24: Enforce AAA Pattern - Component Tests

**Files:**
- Modify: `services/frontend/src/components/**/__tests__/*.test.tsx`

**Step 1: Review component test structure**

Read `services/frontend/src/components/documents/__tests__/DocumentCard.test.tsx`

**Step 2: Apply AAA pattern**

```typescript
describe('DocumentCard', () => {
  it('renders document title and metadata correctly', () => {
    // Arrange
    const mockDocument = {
      id: '123',
      title: 'Test Document',
      createdAt: '2025-01-01'
    };

    // Act
    render(<DocumentCard document={mockDocument} />);

    // Assert
    expect(screen.getByText('Test Document')).toBeInTheDocument();
    expect(screen.getByText('2025-01-01')).toBeInTheDocument();
  });
});
```

**Step 3: Run component tests**

```bash
npm test -- components/documents
```

Expected: Component tests pass

**Step 4: Commit AAA enforcement**

```bash
git add src/components/
git commit -m "test(frontend): enforce AAA pattern in component tests"
```

### Task 25: Review Mocking Strategy - Child Components

**Files:**
- Modify: Component test files

**Step 1: Identify over-mocked child components**

Look for tests that mock child components unnecessarily.

**Step 2: Test components with real children where appropriate**

Only mock external dependencies (APIs, routers) and complex children. Simple child components should be real.

**Step 3: Run tests**

```bash
npm test
```

Expected: Tests pass with improved mocking strategy

**Step 4: Commit mocking improvements**

```bash
git add src/
git commit -m "test(frontend): improve component mocking strategy"
```

### Task 26: Ensure Proper Cleanup - afterEach Hooks

**Files:**
- Modify: All test files

**Step 1: Add cleanup hooks where needed**

```typescript
import { cleanup } from '@testing-library/react';

afterEach(() => {
  cleanup();
});
```

**Step 2: Run tests**

```bash
npm test
```

Expected: No memory leaks, clean test runs

**Step 3: Commit cleanup additions**

```bash
git add src/
git commit -m "test(frontend): add proper cleanup in afterEach hooks"
```

### Task 27: Verify Type Safety - Test Assertions

**Files:**
- Review: All `.test.ts` and `.test.tsx` files

**Step 1: Run type checking on tests**

```bash
npm run type-check
```

Expected: No type errors in tests

**Step 2: Fix any type errors**

Add proper types to test fixtures and assertions.

**Step 3: Commit type safety improvements**

```bash
git add src/
git commit -m "test(frontend): ensure type safety in test assertions"
```

### Task 28: Standardize Mock Data Creation

**Files:**
- Create: `services/frontend/src/test-utils/mocks.ts`

**Step 1: Create centralized mock data**

```typescript
// src/test-utils/mocks.ts
export const mockDocument = {
  id: 'test-doc-1',
  title: 'Test Document',
  content: 'Test content',
  createdAt: '2025-01-01T00:00:00Z',
  fileType: 'pdf' as const
};

export const mockSearchResult = {
  documents: [mockDocument],
  total: 1,
  query: 'test query'
};

export const mockModel = {
  id: 'openai:gpt-4',
  name: 'GPT-4',
  provider: 'openai' as const
};
```

**Step 2: Update tests to use centralized mocks**

Replace inline mock data with imported mocks.

**Step 3: Run tests**

```bash
npm test
```

Expected: All tests pass with centralized mocks

**Step 4: Commit mock standardization**

```bash
git add src/
git commit -m "test(frontend): standardize mock data creation"
```

### Task 29: Validate - Full Frontend Test Suite

**Files:**
- Read: `.test-refactor-baseline-frontend.txt`

**Step 1: Run full test suite**

```bash
cd services/frontend
npm test
```

Expected: All tests pass

**Step 2: Compare with baseline**

```bash
npm test 2>&1 | grep -E "Tests|passed"
cat ../../.test-refactor-baseline-frontend.txt | grep -E "Tests|passed"
```

Expected: Same or more tests passing

**Step 3: Run type checking**

```bash
npm run type-check
```

Expected: No type errors

**Step 4: Commit validation**

```bash
git commit --allow-empty -m "test(frontend): validate refactor - all tests passing"
```

### Task 30: Document - Frontend Testing Guidelines

**Files:**
- Create: `services/frontend/src/__tests__/README.md`

**Step 1: Write testing guidelines**

```markdown
# Frontend Tests

## Structure

```
src/
├── components/
│   └── **/__tests__/       # Component tests
├── utils/
│   └── __tests__/          # Utility function tests
└── test-utils/
    └── mocks.ts            # Centralized mock data
```

## Best Practices

### AAA Pattern
```typescript
it('test description', () => {
  // Arrange
  // Act
  // Assert
});
```

### Mocking Strategy
- Mock external APIs
- Mock complex child components
- Use real implementations for simple components
- Centralized mocks in `test-utils/mocks.ts`

### Cleanup
Always cleanup after each test:
```typescript
afterEach(() => {
  cleanup();
});
```

### Type Safety
All test fixtures and assertions should be type-safe.

## Running Tests

```bash
# All tests
npm test

# Specific component
npm test -- DocumentCard

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```
```

**Step 2: Commit documentation**

```bash
git add src/__tests__/README.md
git commit -m "docs(frontend): add testing guidelines"
```

---

## Phase 4: Embedder Service (Minimal)

### Task 31: Baseline - Capture Embedder Test State

**Files:**
- Create: `.test-refactor-baseline-embedder.txt`

**Step 1: Run embedder tests**

```bash
cd services/embedder
poetry install
poetry run pytest -v > ../../.test-refactor-baseline-embedder.txt 2>&1
```

**Step 2: Review baseline**

```bash
cat ../../.test-refactor-baseline-embedder.txt
```

**Step 3: Commit baseline**

```bash
git add .test-refactor-baseline-embedder.txt
git commit -m "test(embedder): capture baseline test results before refactor"
```

### Task 32: Apply AAA Pattern - Embedder Tests

**Files:**
- Modify: `services/embedder/tests/test_embeddings.py`

**Step 1: Review current tests**

Read `services/embedder/tests/test_embeddings.py`

**Step 2: Apply AAA pattern**

```python
@pytest.mark.asyncio
async def test_health_endpoint_returns_healthy_status():
    # Arrange
    async with AsyncClient(app=app, base_url="http://test") as client:

        # Act
        response = await client.get("/health")

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

**Step 3: Run tests**

```bash
poetry run pytest -v
```

Expected: All tests pass

**Step 4: Commit AAA enforcement**

```bash
git add tests/
git commit -m "test(embedder): enforce AAA pattern"
```

### Task 33: Verify Endpoint Tests Match Current API

**Files:**
- Read: `services/embedder/tests/test_embeddings.py`
- Read: `services/embedder/app/main.py`

**Step 1: List tested endpoints**

```bash
grep "client\\.get\\|client\\.post" tests/test_embeddings.py
```

**Step 2: List actual endpoints**

```bash
grep "@app\\." app/main.py
```

**Step 3: Verify alignment**

Ensure all endpoints are tested and no tests for non-existent endpoints.

**Step 4: Update tests if needed**

If misalignment found, update tests to match current API.

**Step 5: Commit verification**

```bash
git add tests/
git commit -m "test(embedder): verify endpoint tests match current API"
```

### Task 34: Validate - Embedder Test Suite

**Files:**
- Read: `.test-refactor-baseline-embedder.txt`

**Step 1: Run full test suite**

```bash
cd services/embedder
poetry run pytest -v
```

Expected: All tests pass

**Step 2: Compare with baseline**

```bash
poetry run pytest -v 2>&1 | grep -E "passed|failed"
cat ../../.test-refactor-baseline-embedder.txt | grep -E "passed|failed"
```

Expected: Same results

**Step 3: Commit validation**

```bash
git commit --allow-empty -m "test(embedder): validate refactor - all tests passing"
```

---

## Phase 5: Root Integration Tests

### Task 35: Baseline - Capture Integration Test State

**Files:**
- Create: `.test-refactor-baseline-integration.txt`

**Step 1: Run integration tests**

```bash
cd tests
poetry install 2>/dev/null || pip install -r requirements.txt
pytest -v > ../.test-refactor-baseline-integration.txt 2>&1
```

**Step 2: Review baseline**

```bash
cat ../.test-refactor-baseline-integration.txt | tail -50
```

**Step 3: Commit baseline**

```bash
git add .test-refactor-baseline-integration.txt
git commit -m "test(integration): capture baseline test results before refactor"
```

### Task 36: Consolidate Playwright Setup Code

**Files:**
- Review: `tests/test_webapp.py`, `tests/test_upload_search.py`, `tests/test_documents_page.py`

**Step 1: Identify duplicate setup**

Look for repeated Playwright setup code across test files.

**Step 2: Create shared fixtures**

```python
# tests/conftest.py
import pytest
from playwright.async_api import async_playwright

@pytest.fixture
async def browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        yield browser
        await browser.close()

@pytest.fixture
async def page(browser):
    context = await browser.new_context()
    page = await context.new_page()
    yield page
    await context.close()
```

**Step 3: Update tests to use shared fixtures**

**Step 4: Run tests**

```bash
pytest -v
```

Expected: Tests pass with consolidated setup

**Step 5: Commit consolidation**

```bash
git add tests/
git commit -m "test(integration): consolidate Playwright setup code"
```

### Task 37: Remove or Relocate Debug Utilities

**Files:**
- Review: `tests/debug_dom_structure.py`

**Step 1: Determine if debug utility is still needed**

Check git history and recent usage.

**Step 2: Either remove or move to dev tools**

If not needed:
```bash
git rm tests/debug_dom_structure.py
```

If needed for development, move to a `dev-tools/` directory.

**Step 3: Commit cleanup**

```bash
git commit -m "test(integration): remove unused debug utilities"
```

### Task 38: Standardize Test Data Setup

**Files:**
- Review: `tests/upload_test_corpus.py`
- Modify: Create standardized approach

**Step 1: Review current test data approach**

Read `upload_test_corpus.py` to understand test data management.

**Step 2: Create fixture for test data**

```python
# tests/conftest.py
import pytest

@pytest.fixture
def test_documents():
    """Standard test document corpus."""
    return [
        {"filename": "test.pdf", "content": "PDF content"},
        {"filename": "test.csv", "content": "col1,col2\nval1,val2"},
        {"filename": "test.txt", "content": "Plain text content"}
    ]

@pytest.fixture
async def uploaded_test_documents(page, test_documents):
    """Upload test documents and return their IDs."""
    doc_ids = []
    for doc in test_documents:
        # Upload document
        await page.goto("http://localhost:3000/upload")
        await page.set_input_files("input[type=file]", doc["filename"])
        await page.click("button:has-text('Upload')")
        # Capture doc ID from response
        doc_id = await page.locator("[data-doc-id]").get_attribute("data-doc-id")
        doc_ids.append(doc_id)
    return doc_ids
```

**Step 3: Update tests to use standardized fixtures**

**Step 4: Run tests**

```bash
pytest -v
```

Expected: Tests pass with standardized test data

**Step 5: Commit standardization**

```bash
git add tests/
git commit -m "test(integration): standardize test data setup"
```

### Task 39: Update Outdated Model References

**Files:**
- Modify: `tests/test_summary_fix.py`

**Step 1: Find outdated model references**

```bash
grep -r "gpt-5" tests/
grep -r "gpt-4-mini" tests/
```

**Step 2: Update to valid model names**

Replace `gpt-5-mini` with valid model (e.g., `gpt-4` or `gpt-3.5-turbo`).

**Step 3: Run tests**

```bash
pytest tests/test_summary_fix.py -v
```

Expected: Test passes with valid model

**Step 4: Commit model updates**

```bash
git add tests/
git commit -m "test(integration): update outdated model references"
```

### Task 40: Add Timeout Handling and Retry Logic

**Files:**
- Modify: E2E test files

**Step 1: Add timeout configuration**

```python
@pytest.mark.asyncio
async def test_upload_workflow(page):
    # Arrange
    await page.goto("http://localhost:3000", timeout=10000)

    # Act
    await page.set_input_files("input[type=file]", "test.pdf")
    await page.click("button:has-text('Upload')", timeout=5000)

    # Assert - wait for upload to complete
    await page.wait_for_selector("[data-upload-status='complete']", timeout=30000)
    assert await page.locator("[data-upload-status]").get_attribute("data-upload-status") == "complete"
```

**Step 2: Add retry logic for flaky operations**

```python
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def wait_for_service_ready():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        assert response.status_code == 200
```

**Step 3: Run tests**

```bash
pytest -v
```

Expected: Tests pass with proper timeouts

**Step 4: Commit timeout handling**

```bash
git add tests/
git commit -m "test(integration): add timeout handling and retry logic"
```

### Task 41: Document Test Scripts

**Files:**
- Modify: `tests/test_full_workflow.sh`, `tests/test_generation_flow.sh`, `tests/test_multi_provider.sh`

**Step 1: Add documentation headers to scripts**

```bash
#!/bin/bash
# Test: Full workflow end-to-end
# Purpose: Validates complete user journey from upload to search to generation
# Prerequisites: All services running (API, Frontend, Embedder, Generator)
# Expected: All steps pass, documents searchable, summaries generated

set -e  # Exit on error
```

**Step 2: Add comments explaining each step**

**Step 3: Commit documentation**

```bash
git add tests/*.sh
git commit -m "test(integration): document shell test scripts"
```

### Task 42: Validate - Full Integration Test Suite

**Files:**
- Read: `.test-refactor-baseline-integration.txt`

**Step 1: Run full integration suite**

```bash
cd tests
pytest -v
```

Expected: All tests pass

**Step 2: Compare with baseline**

```bash
pytest -v 2>&1 | grep -E "passed|failed"
cat ../.test-refactor-baseline-integration.txt | grep -E "passed|failed"
```

Expected: Same or better results

**Step 3: Run shell scripts**

```bash
bash test_full_workflow.sh
bash test_generation_flow.sh
bash test_multi_provider.sh
```

Expected: All scripts pass

**Step 4: Commit validation**

```bash
git commit --allow-empty -m "test(integration): validate refactor - all tests passing"
```

### Task 43: Document - Integration Testing Guidelines

**Files:**
- Create: `tests/README.md`

**Step 1: Write integration testing guide**

```markdown
# Integration Tests

Cross-service end-to-end tests for RAAS platform.

## Structure

```
tests/
├── conftest.py                 # Shared fixtures (Playwright, test data)
├── test_webapp.py              # Full web app e2e tests
├── test_upload_search.py       # Upload and search workflow
├── test_documents_page.py      # Documents page interactions
├── test_ai_summary_placement.py # AI summary feature
├── upload_test_corpus.py       # Test data management
├── test_full_workflow.sh       # Shell script - full workflow
├── test_generation_flow.sh     # Shell script - generation
└── test_multi_provider.sh      # Shell script - multi-provider
```

## Prerequisites

All services must be running:
- API: http://localhost:8000
- Frontend: http://localhost:3000
- Embedder: http://localhost:8001
- Generator: http://localhost:8002
- Qdrant: http://localhost:6333

## Running Tests

```bash
# Python e2e tests
pytest -v

# Specific test
pytest tests/test_webapp.py -v

# Shell scripts
bash test_full_workflow.sh
bash test_generation_flow.sh
```

## Best Practices

### Test Data
Use standardized fixtures from `conftest.py`:
- `test_documents` - Standard document corpus
- `uploaded_test_documents` - Pre-uploaded documents

### Timeouts
Always set appropriate timeouts:
```python
await page.goto(url, timeout=10000)
await page.click(selector, timeout=5000)
await page.wait_for_selector(selector, timeout=30000)
```

### Retry Logic
Use retries for service health checks and flaky operations.

### Cleanup
Clean up test data after tests complete.
```

**Step 2: Commit documentation**

```bash
git add tests/README.md
git commit -m "docs(integration): add integration testing guidelines"
```

---

## Final Validation

### Task 44: Run All Test Suites Across All Services

**Step 1: Run Generator tests**

```bash
cd services/generator
poetry run pytest -v
```

Expected: All pass

**Step 2: Run API tests**

```bash
cd ../api
poetry run pytest -v
```

Expected: All pass

**Step 3: Run Frontend tests**

```bash
cd ../frontend
npm test
```

Expected: All pass

**Step 4: Run Embedder tests**

```bash
cd ../embedder
poetry run pytest -v
```

Expected: All pass

**Step 5: Run Integration tests**

```bash
cd ../../tests
pytest -v
```

Expected: All pass

**Step 6: Commit final validation**

```bash
cd ..
git commit --allow-empty -m "test: final validation - all services passing"
```

### Task 45: Create Summary Report

**Files:**
- Create: `.test-refactor-summary.md`

**Step 1: Write summary report**

```markdown
# Test Refactor Summary

## Completed Phases

- ✅ Phase 1: Generator Service (10 test files, 733 lines)
- ✅ Phase 2: API Service (48+ test files, 6,939 lines)
- ✅ Phase 3: Frontend Service (8 test files, 1,999 lines)
- ✅ Phase 4: Embedder Service (1 test file, 92 lines)
- ✅ Phase 5: Root Integration Tests (11 files)

## Improvements Made

### Generator Service
- Reorganized tests into unit/ subdirectories
- Centralized fixtures in conftest.py
- Enforced AAA pattern across all tests
- Improved test naming convention
- Reduced over-mocking
- Added error handling coverage

### API Service
- Removed orphaned .pyc files
- Consolidated duplicate fixtures
- Verified integration test scope
- Enforced AAA pattern across all layers
- Improved test names

### Frontend Service
- Enforced AAA pattern in component tests
- Improved mocking strategy
- Added proper cleanup hooks
- Ensured type safety
- Standardized mock data creation

### Embedder Service
- Applied AAA pattern
- Verified endpoint alignment
- Kept minimal (as designed)

### Integration Tests
- Consolidated Playwright setup
- Removed debug utilities
- Standardized test data setup
- Updated model references
- Added timeout/retry logic
- Documented shell scripts

## Test Results

All test suites passing:
- Generator: X passed
- API: Y passed
- Frontend: Z passed
- Embedder: W passed
- Integration: V passed

## Best Practices Established

- AAA pattern enforced
- Naming convention: test_<method>_<scenario>_<expected_outcome>
- Centralized fixtures
- Minimal mocking strategy
- Test independence verified
- Documentation created for each service
```

**Step 2: Commit summary**

```bash
git add .test-refactor-summary.md
git commit -m "docs: add test refactor summary report"
```

### Task 46: Clean Up Baseline Files

**Step 1: Remove baseline text files**

```bash
git rm .test-refactor-baseline-*.txt
git rm .generator-test-audit.md .api-test-audit.md
```

**Step 2: Commit cleanup**

```bash
git commit -m "chore: remove test refactor baseline files"
```

---

## Completion

All tasks complete! The comprehensive test refactor is done:
- ✅ All services refactored
- ✅ Best practices enforced
- ✅ Documentation updated
- ✅ All tests passing
- ✅ Consistent patterns established

Ready to merge to main branch.
