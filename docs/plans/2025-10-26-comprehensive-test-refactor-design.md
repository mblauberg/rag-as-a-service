# Comprehensive Test Refactor Design

**Date**: 2025-10-26
**Status**: Design Approved
**Approach**: Service-by-service deep clean with aggressive cleanup

---

## Overview

This design outlines a comprehensive test file clean-up and refactor across all services in the RAAS project. The goal is to remove obsolete tests, align with best practices, fix coverage gaps, and establish consistent patterns for future test development.

### Goals

1. **Remove Obsolete Tests**: Identify and remove tests for deprecated features, old code paths, and outdated APIs
2. **Align with Best Practices**: Restructure tests to follow testing best practices (AAA pattern, proper mocking, no test interdependencies)
3. **Fix Coverage Gaps**: Address under-tested services and ensure critical paths are tested
4. **Establish Patterns**: Create blueprint for future test development

### Constraints

- Keep embedder service tests minimal (service is simple)
- Keep root-level integration tests separate (cross-service e2e workflows)
- Aggressive cleanup approach (remove all technical debt)
- Apply industry best practices appropriate for this type of project

---

## Architecture

### Service-by-Service Refactor Order

Work on one service at a time, completing each before moving to the next:

1. **Generator Service** (start here - medium complexity, clean provider pattern, 733 lines)
2. **API Service** (largest and most complex, 6,939 lines)
3. **Frontend Service** (TypeScript/Vitest, different patterns, 1,999 lines)
4. **Embedder Service** (smallest, keep minimal, 92 lines)
5. **Root Integration Tests** (cross-service e2e, clean up and standardize)

### Per-Service Refactor Phases

Each service goes through the same five phases:

1. **Audit Phase**: Inventory tests, identify obsolete/redundant tests, check current vs actual code
2. **Cleanup Phase**: Remove orphaned files, outdated references, over-mocked tests
3. **Restructure Phase**: Apply best practices, enforce patterns, improve fixtures
4. **Validation Phase**: Run full suite, verify coverage, ensure no regressions
5. **Documentation Phase**: Update test docs, add testing guidelines if needed

---

## Best Practices to Enforce

### Testing Patterns (Python/pytest)

- **AAA Pattern**: Strict Arrange-Act-Assert structure in every test
- **Test Independence**: No shared state between tests, proper fixture isolation
- **Minimal Mocking**: Mock only external dependencies (APIs, databases), test real object interactions where possible
- **Fixture Organization**: Clear conftest.py hierarchy, dependency injection over global state
- **Async Best Practices**: Proper async/await usage, no blocking calls in async tests
- **Naming Convention**: `test_<method>_<scenario>_<expected_outcome>` (e.g., `test_generate_with_invalid_provider_raises_error`)

### Testing Patterns (TypeScript/Vitest)

- **AAA Pattern**: Same strict structure
- **Test Independence**: No interdependent tests
- **Component Testing**: Test components in isolation with proper mocking of child components
- **Type Safety**: Leverage TypeScript for test type checking
- **Naming Convention**: `describe/it` blocks with clear behavior descriptions

### Anti-patterns to Eliminate

- Tests testing mock behavior instead of real behavior
- Test-only code paths in production code
- Over-mocking (mocking things that should be tested)
- Tests with hidden dependencies on execution order
- Vague test names like `test_1`, `test_success`
- Commented-out tests (delete or fix them)
- Orphaned `.pyc` files and test artifacts

### Markers & Organization

- Consistent use of `@pytest.mark.asyncio`, `@pytest.mark.unit`, `@pytest.mark.integration`
- Clear separation: unit tests for logic, integration tests for cross-boundary interactions
- Test file location mirrors source file location

---

## Service-Specific Plans

### 1. Generator Service (Pilot Refactor)

**Current State:**
- 10 test files, 733 lines total
- Provider tests: Anthropic, Google, OpenAI, Ollama, base provider, registry
- Root-level tests: generation_service, ollama_client, prompt_service, schemas
- Already has good unit test organization in `unit/providers/`

**Cleanup Actions:**
1. Remove outdated model references (if found)
2. Consolidate test structure: Move all tests under `unit/` directory following pattern: `unit/providers/`, `unit/services/`, `unit/clients/`, `unit/`
3. Fixture refactor: Centralize common fixtures in `conftest.py` (mock LLM responses, test configs, provider instances)
4. Apply AAA pattern: Audit each test for clear Arrange-Act-Assert sections
5. Remove over-mocking: Ensure we're testing real provider logic, not just mock behavior
6. Improve test names: Ensure all tests follow naming convention
7. Add missing coverage: Error handling, edge cases, provider fallbacks

**Expected Outcome:**
- Cleaner directory structure mirroring source code
- All tests follow consistent patterns
- Better fixture reuse
- Improved readability and maintainability
- Blueprint for API service refactor

### 2. API Service (Apply Lessons from Generator)

**Current State:**
- 48+ test files, 6,939 lines total
- Well-organized hexagonal architecture: api/, application/, domain/, infrastructure/, ports/
- Already has good separation of concerns
- Orphaned `.pyc` files identified: `test_generator_client`, `test_reranker`, `test_upload_integration`

**Cleanup Actions:**
1. Remove orphaned artifacts: Delete `.pyc` files for non-existent tests, clean up `__pycache__` directories
2. Audit test-to-code alignment: Verify each test file tests current code, not deprecated features
3. Fixture consolidation: Review conftest.py hierarchy, eliminate duplicate fixtures, improve dependency injection
4. Integration test review: Ensure integration tests in `integration/` truly test cross-boundary interactions, not unit behavior
5. Port/interface tests: Verify contract tests align with current port definitions
6. Mock reduction: Identify over-mocked tests where real implementations could be tested
7. Apply AAA pattern: Enforce across all 6,939 lines
8. Test data management: Centralize test data creation (documents, chunks, search queries) in fixtures
9. Async pattern consistency: Ensure all async tests follow same patterns

**Specific Focus Areas:**
- Document processing tests: Verify support for current file types (PDF, CSV, DOCX, text)
- Search tests: Ensure semantic, keyword, hybrid, BM25 all tested correctly
- Reranking: Remove any outdated reranker implementations
- Infrastructure: Database, Qdrant, external service tests

**Expected Outcome:**
- No orphaned test artifacts
- All tests aligned with current codebase
- Consistent patterns across all layers
- Reduced duplication in fixtures and test data
- Clear separation between unit and integration tests

### 3. Frontend Service (TypeScript/Vitest)

**Current State:**
- 8 test files, 1,999 lines total
- Well-organized component tests in `__tests__` directories
- Components: DocumentCard, DocumentDetailModal, EnhancedSearchBar, UploadModal, UploadFAB
- Utils: modelUtils, formatters, fileValidation

**Cleanup Actions:**
1. Enforce AAA pattern in all component tests
2. Review mocking strategy for child components
3. Ensure proper cleanup in afterEach hooks
4. Verify type safety in test assertions
5. Test accessibility where applicable
6. Standardize mock data creation

**Expected Outcome:**
- Consistent testing patterns adapted for React/TypeScript
- Proper component isolation
- Type-safe test assertions

### 4. Embedder Service (Keep Minimal)

**Current State:**
- 1 test file, 92 lines total
- Basic smoke tests for endpoints: root, health, ready, embed

**Cleanup Actions:**
1. Verify current endpoint tests match actual API
2. Ensure health/readiness checks are tested
3. Keep simple - no over-engineering
4. Apply AAA pattern to existing tests
5. Clean up any orphaned artifacts

**Expected Outcome:**
- Minimal but correct tests
- No over-engineering for simple service

### 5. Root Integration Tests (Keep Separate)

**Current State:**
- 11 files: Playwright e2e tests + utility scripts
- Tests: webapp, upload_search, documents_page, ai_summary_placement, summary_fix, httpx_redirects
- Scripts: test_full_workflow.sh, test_generation_flow.sh, test_multi_provider.sh
- Utilities: upload_test_corpus.py, debug_dom_structure.py

**Cleanup Actions:**
1. Consolidate duplicate Playwright setup code
2. Remove debug utilities (`debug_dom_structure.py`) or move to dev tools
3. Standardize test data setup (`upload_test_corpus.py`)
4. Update any outdated model references (e.g., `gpt-5-mini` → valid model)
5. Ensure e2e tests cover critical user journeys only
6. Document what each test script validates
7. Add timeout handling and retry logic where appropriate

**Expected Outcome:**
- Clean, focused e2e tests for cross-service workflows
- Standardized setup and test data management
- Clear documentation of test coverage

---

## Validation & Quality Gates

### Per-Service Validation Checklist

After each service refactor, verify:
- ✅ All tests pass (no regressions introduced)
- ✅ No orphaned `.pyc` or cache files remain
- ✅ All tests follow AAA pattern
- ✅ Test names follow naming convention
- ✅ Fixtures properly organized in conftest.py
- ✅ No commented-out tests (deleted or fixed)
- ✅ Proper use of pytest markers (@pytest.mark.unit, @pytest.mark.integration, @pytest.mark.asyncio)
- ✅ No over-mocking (tests verify real behavior)
- ✅ Test independence verified (can run in any order)
- ✅ Coverage maintained or improved

### Automated Checks

- Run full test suite: `poetry run pytest` (API, Generator, Embedder)
- Run type checking: `npm run type-check` (Frontend)
- Run linting: `poetry run ruff check` / `npm run lint`
- Verify no test interdependencies: `poetry run pytest --random-order`

### Documentation Updates

- Update testing guidelines in relevant README files
- Document new fixture patterns for future contributors
- Add examples of good test structure
- Document test data management approach

---

## Implementation Strategy

### Execution Approach

- Work in feature branch: `feature/test-refactor-comprehensive`
- One service per commit for easy review and rollback
- Run full test suite before and after each service refactor
- Use git worktree for isolation from ongoing work

### Risk Mitigation

- **Baseline First**: Capture current test results before any changes
- **Incremental Validation**: Run tests after each cleanup action, not just at the end
- **Rollback Strategy**: Each service is a separate commit, easy to revert if needed
- **Preserve Behavior**: Tests should pass before and after refactor (we're improving structure, not changing what's tested)
- **Coverage Tracking**: Ensure coverage doesn't decrease during refactor

### Time Estimates (per service)

- Generator: 2-3 hours (pilot, establish patterns)
- API: 6-8 hours (largest, most complex)
- Frontend: 2-3 hours (different patterns, TypeScript)
- Embedder: 30 minutes (minimal work)
- Integration: 1-2 hours (cleanup and standardization)
- **Total**: ~12-17 hours of focused work

### Success Criteria

- All tests passing with same or better coverage
- No orphaned files or outdated references
- Consistent patterns across all services
- Clear, maintainable test structure
- Documentation updated with testing guidelines
- Blueprint established for future test development

---

## Current Test Inventory

### API Service
- **Location**: `services/api/tests/`
- **Lines of Code**: 6,939 lines
- **Organization**: Hexagonal architecture (api/, application/, domain/, infrastructure/, ports/, services/, unit/, utils/)
- **Test Files**: 48+ files

### Generator Service
- **Location**: `services/generator/tests/`
- **Lines of Code**: 733 lines
- **Test Files**: 10 files
- **Organization**: Root level + unit/providers/

### Embedder Service
- **Location**: `services/embedder/tests/`
- **Lines of Code**: 92 lines
- **Test Files**: 1 file (test_embeddings.py)

### Frontend Service
- **Location**: `services/frontend/src/`
- **Lines of Code**: 1,999 lines
- **Test Files**: 8 files in `__tests__/` directories

### Root Integration Tests
- **Location**: `tests/`
- **Test Files**: 11 files (mix of Python and shell scripts)
- **Framework**: Playwright for e2e tests

---

## Known Issues to Address

1. **Orphaned `.pyc` files** in API service: `test_generator_client`, `test_reranker`, `test_upload_integration`
2. **Outdated model references**: `gpt-5-mini` in `test_summary_fix.py`
3. **Minimal embedder coverage**: Only 92 lines (acceptable for simple service)
4. **Debug utilities**: `debug_dom_structure.py` should be removed or moved
5. **Test data management**: Inconsistent approaches across services

---

## Next Steps

After design approval:
1. Set up git worktree for isolated development
2. Create detailed implementation plan with bite-sized tasks
3. Execute service-by-service refactor following this design
4. Validate and commit each service individually
5. Merge to main branch after all services complete
