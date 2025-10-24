# Cleanup and SOLID Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Clean project of junk files and outdated documentation, then refactor services to follow SOLID principles with proper dependency injection and comprehensive testing.

**Architecture:** Three-track parallel approach: Track A (immediate cleanup), Track B (component refactoring with subagents), Track C (cross-cutting polish). Track A executes first and merges immediately. Track B components run in parallel. Track C applies polish after B completes.

**Tech Stack:** Python (FastAPI, SQLAlchemy, pytest), TypeScript (React, Vitest), Git worktrees, Docker Compose

**Design Reference:** `docs/plans/2025-10-24-cleanup-and-refactoring-design.md`

**Current State (2025-10-24):**
- Previous cleanup (commit f53bc98) removed worktrees and some docs
- 7 test files currently at project root need relocation
- `document_service.py` is 380 lines and needs splitting
- Frontend has minimal test coverage (1 test file)
- Parallel work in `feature/critical-rag-optimizations` is independent

---

## Track A: Immediate Safe Cleanup

### Task A1: Relocate Misplaced Test Files

**Context:** Seven test/debug files exist at project root instead of proper test directory.

**Verified Files (as of 2025-10-24):**
- Move: `test_upload_search.py` → `tests/integration/test_upload_search.py`
- Move: `test_webapp.py` → `tests/integration/test_webapp.py`
- Move: `test_documents_page.py` → `tests/integration/test_documents_page.py`
- Move: `test_raas_webapp.py` → `tests/integration/test_raas_webapp.py`
- Move: `test_ai_summary_placement.py` → `tests/integration/test_ai_summary_placement.py`
- Move: `test_summary_fix.py` → `tests/integration/test_summary_fix.py`
- Move: `test_httpx_redirects.py` → `tests/integration/test_httpx_redirects.py`
- Move: `debug_dom_structure.py` → `tests/debug/debug_dom_structure.py`
- Move: `upload_test_corpus.py` → `tests/integration/upload_test_corpus.py`

**Step 1: Verify test files exist**

Run: `ls -la test_*.py debug_*.py upload_test_corpus.py`

Expected: All 9 files present at project root

**Step 2: Move files to appropriate test directories**

```bash
mkdir -p tests/integration
mkdir -p tests/debug

# Move integration test files
mv test_upload_search.py tests/integration/
mv test_webapp.py tests/integration/
mv test_documents_page.py tests/integration/
mv test_raas_webapp.py tests/integration/
mv test_ai_summary_placement.py tests/integration/
mv test_summary_fix.py tests/integration/
mv test_httpx_redirects.py tests/integration/
mv upload_test_corpus.py tests/integration/

# Move debug file
mv debug_dom_structure.py tests/debug/
```

**Step 3: Verify tests can be discovered**

Run: `pytest tests/integration/ -v --collect-only`

Expected: Test files discovered (may have import errors, that's ok for now)

**Step 4: Commit**

```bash
git add tests/integration/ tests/debug/
git add test_*.py debug_*.py upload_test_corpus.py  # Register deletions
git commit -m "chore: move test and debug files to proper directories

Move 8 test files and 1 debug file from project root to organized directories:
- tests/integration/ - Integration and end-to-end tests
- tests/debug/ - Debug utilities

Improves project organization and test discoverability."
```

---

### Task A2: Remove Generated Files from Git Tracking

**Context:** Generated files (coverage, pytest cache, Python bytecode) are tracked in git.

**Files:**
- Untrack: `services/api/htmlcov/` (entire directory)
- Untrack: `services/api/.pytest_cache/`
- Untrack: `services/generator/.pytest_cache/`
- Untrack: All `__pycache__/` directories

**Step 1: List generated files tracked by git**

Run: `git ls-files | grep -E "(htmlcov|\.pytest_cache|__pycache__|\.pyc$)"`

Expected: List of generated files currently tracked

**Step 2: Remove from git tracking (keep local files)**

```bash
# Remove coverage reports
git rm -r --cached services/api/htmlcov/ 2>/dev/null || true

# Remove pytest cache
git rm -r --cached services/api/.pytest_cache/ 2>/dev/null || true
git rm -r --cached services/generator/.pytest_cache/ 2>/dev/null || true

# Remove all __pycache__ directories
find . -type d -name "__pycache__" -not -path "*/node_modules/*" -not -path "*/.venv/*" | while read dir; do
    git rm -r --cached "$dir" 2>/dev/null || true
done
```

**Step 3: Verify files untracked but still exist locally**

Run: `git status --short | grep "D "`

Expected: Multiple deletion entries (files removed from git)

Run: `test -d services/api/htmlcov && echo "htmlcov still exists locally" || echo "htmlcov missing"`

Expected: "htmlcov still exists locally"

**Step 4: Commit**

```bash
git commit -m "chore: remove generated files from git tracking

Remove coverage reports (htmlcov/), pytest cache, and Python bytecode (__pycache__/)
from version control. These are generated at runtime and should not be tracked."
```

---

### Task A3: Delete Duplicate Settings File

**Context:** Duplicate Claude settings file with malformed name.

**Files:**
- Delete: `.claude/settings.local 2.json`

**Step 1: Verify file exists**

Run: `ls -la ".claude/settings.local"*`

Expected: Shows both `settings.local.json` and `settings.local 2.json`

**Step 2: Delete duplicate**

```bash
rm ".claude/settings.local 2.json"
```

**Step 3: Verify deletion**

Run: `ls -la ".claude/settings.local"*`

Expected: Only `settings.local.json` remains

**Step 4: Commit**

```bash
git add ".claude/settings.local 2.json"
git commit -m "chore: remove duplicate Claude settings file

Delete malformed '.claude/settings.local 2.json' file (contains space in name).
Keep only the proper 'settings.local.json' file."
```

---

### Task A4: Delete Outdated Plan Documents

**Context:** 8 plan documents for completed/merged features should be removed.

**Verified State:** 11 plan files currently exist in master (as of 2025-10-24). The previous cleanup (f53bc98) did not remove these plan files.

**Files to Delete:**
- Delete: `docs/plans/2025-10-23-comprehensive-quality-improvements-design.md` (merged)
- Delete: `docs/plans/2025-10-23-comprehensive-quality-improvements.md` (merged)
- Delete: `docs/plans/2025-10-24-complete-phase4-frontend-refactor.md` (completed)
- Delete: `docs/plans/2025-10-24-kubernetes-scaffolding-design.md` (merged)
- Delete: `docs/plans/2025-10-24-kubernetes-scaffolding-implementation.md` (merged)
- Delete: `docs/plans/2025-10-24-kubernetes-scalability-resilience-design.md` (completed)
- Delete: `docs/plans/2025-10-24-project-cleanup-design.md` (completed, superseded by this plan)
- Delete: `docs/plans/2025-10-24-semantic-chunking-remaining-tasks.md` (completed)

**Step 1: List current plan files**

Run: `ls -1 docs/plans/*.md`

Expected: Shows 11 plan files

**Step 2: Delete outdated plans**

```bash
cd docs/plans
rm 2025-10-23-comprehensive-quality-improvements-design.md
rm 2025-10-23-comprehensive-quality-improvements.md
rm 2025-10-24-complete-phase4-frontend-refactor.md
rm 2025-10-24-kubernetes-scaffolding-design.md
rm 2025-10-24-kubernetes-scaffolding-implementation.md
rm 2025-10-24-kubernetes-scalability-resilience-design.md
rm 2025-10-24-project-cleanup-design.md
rm 2025-10-24-semantic-chunking-remaining-tasks.md
cd ../..
```

**Step 3: Verify only active plans remain**

Run: `ls -1 docs/plans/*.md`

Expected: Shows only 3 files:
- `2025-01-24-critical-rag-optimizations.md` (active work)
- `2025-10-24-cleanup-and-refactoring-design.md` (this plan's design)
- `2025-10-24-rag-optimization-implementation.md` (future work)

**Step 4: Commit**

```bash
git add docs/plans/
git commit -m "chore: remove outdated plan documents

Delete 8 plan documents for completed/merged features:
- 2025-10-23 comprehensive quality improvements (merged to master)
- 2025-10-24 complete phase 4 frontend refactor (completed)
- 2025-10-24 kubernetes scaffolding design + implementation (merged)
- 2025-10-24 kubernetes scalability/resilience (completed)
- 2025-10-24 project cleanup design (completed in f53bc98)
- 2025-10-24 semantic chunking tasks (completed)

Preserve active plans:
- 2025-01-24 critical RAG optimizations (in progress)
- 2025-10-24 cleanup and refactoring design (this work)
- 2025-10-24 RAG optimization implementation (future work)"
```

---

### Task A5: Review and Archive Large Documentation Files

**Context:** Two large documentation files may be outdated.

**Files:**
- Review: `docs/ENHANCEMENT_PRIORITIZATION_PLAN.md` (743 lines)
- Review: `docs/RAG_OPTIMIZATION_ANALYSIS.md` (804 lines)

**Step 1: Read ENHANCEMENT_PRIORITIZATION_PLAN.md**

Run: `head -50 docs/ENHANCEMENT_PRIORITIZATION_PLAN.md`

Expected: Shows document header and initial content

**Step 2: Determine if document is still relevant**

Decision criteria:
- Does it contain future work not captured elsewhere? → **Keep**
- Is all information now in code or other docs? → **Archive or Delete**
- Is it referenced by other documentation? → **Keep**

**Step 3: Read RAG_OPTIMIZATION_ANALYSIS.md**

Run: `head -50 docs/RAG_OPTIMIZATION_ANALYSIS.md`

Expected: Shows analysis content

**Step 4: Decision on each file**

If keeping: No action needed, move to next task

If archiving:
```bash
mkdir -p docs/archive
mv docs/ENHANCEMENT_PRIORITIZATION_PLAN.md docs/archive/ 2>/dev/null || true
mv docs/RAG_OPTIMIZATION_ANALYSIS.md docs/archive/ 2>/dev/null || true
```

If deleting:
```bash
rm docs/ENHANCEMENT_PRIORITIZATION_PLAN.md 2>/dev/null || true
rm docs/RAG_OPTIMIZATION_ANALYSIS.md 2>/dev/null || true
```

**Step 5: Commit if changes made**

```bash
git add docs/
git commit -m "chore: archive/remove large documentation files

[Describe decision made: archived to docs/archive/ or deleted entirely]
[Explain reasoning: outdated, superseded by X, etc.]"
```

---

### Task A6: Enhance .gitignore

**Context:** Add comprehensive exclusions to prevent future tracking of generated files.

**Files:**
- Modify: `.gitignore`

**Step 1: Read current .gitignore**

Run: `cat .gitignore`

Expected: Shows existing gitignore entries

**Step 2: Add comprehensive exclusions**

Edit `.gitignore` and add the following sections:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing
.pytest_cache/
htmlcov/
.coverage
.coverage.*
.tox/
.nox/
coverage.xml
*.cover
.hypothesis/

# Type checking
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/

# Virtual environments
.env.local
.venv/
.venv*/
venv/
venv*/
ENV/
env/
env.bak/
venv.bak/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~
.project
.pydevproject
.settings/

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Claude Code
.claude/settings.local*.json

# Logs
*.log
logs/
```

**Step 3: Verify no currently tracked files match new patterns**

Run: `git ls-files | grep -E "(\.pyc$|__pycache__|htmlcov|\.pytest_cache|\.coverage)" | head -5`

Expected: No output (we already removed these in A2)

**Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: enhance .gitignore with comprehensive exclusions

Add exhaustive patterns for:
- Python bytecode and build artifacts
- Testing and coverage reports
- Type checking cache
- Virtual environments
- IDE and OS files
- Logs and temporary files

Prevents future accidental tracking of generated files."
```

---

### Task A7: Verify Track A Completion

**Context:** Ensure all Track A cleanup completed successfully.

**Step 1: Verify test files relocated**

Run: `ls tests/integration/test_*.py tests/debug/debug_*.py`

Expected: 8 test files in integration/ and 1 debug file in debug/

**Step 2: Verify no generated files tracked**

Run: `git ls-files | grep -E "(htmlcov|\.pytest_cache|__pycache__|\.pyc$)" | wc -l`

Expected: `0` (or minimal)

**Step 3: Verify plan documents cleaned**

Run: `ls -1 docs/plans/*.md | wc -l`

Expected: `3` (critical-rag-optimizations + cleanup design + rag-optimization-implementation)

**Step 4: Verify .gitignore updated**

Run: `grep "\.pytest_cache" .gitignore`

Expected: Shows `.pytest_cache/` entry

**Step 5: Review all Track A commits**

Run: `git log --oneline --decorate -n 6`

Expected: Shows 6 commits from Track A tasks

**Step 6: Run quick sanity tests**

Run: `python3 -m py_compile services/api/app/main.py`

Expected: No syntax errors

Run: `cd services/frontend && npx tsc --noEmit || echo "TypeScript check may fail if deps not installed"`

Expected: Either success or expected failure

---

### Task A8: Merge Track A to Master

**Context:** Track A is complete and ready to merge (zero risk, no code changes).

**Step 1: Switch to master branch**

```bash
cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas
git checkout master
```

**Step 2: Merge feature branch**

```bash
git merge feature/cleanup-and-refactoring --no-ff -m "Merge Track A: Project cleanup

Completed immediate safe cleanup operations:
- Relocated integration tests to proper directory
- Removed generated files from git tracking
- Deleted outdated plan documents
- Enhanced .gitignore with comprehensive exclusions
- Deleted duplicate settings file

No code changes, zero risk."
```

**Step 3: Verify merge success**

Run: `git log --oneline --decorate -n 1`

Expected: Shows merge commit on master

**Step 4: Switch back to feature branch for Track B**

```bash
cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/.worktrees/cleanup-and-refactoring
git checkout feature/cleanup-and-refactoring
git merge master  # Bring in merge commit
```

**Step 5: Confirm Track A complete**

Run: `echo "✓ Track A merged to master. Ready for Track B (component refactoring)."`

---

## Track B: Component Refactoring (Subagent-Driven Development)

**Note:** Track B uses `superpowers:subagent-driven-development` to dispatch independent subagents for each component. Each subagent follows TDD, implements the refactor, and commits independently.

### Task B1: Split document_service.py (API Service)

**Context:** 380-line file violates Single Responsibility Principle. Extract into focused service classes.

**Subagent Task Specification:**

```
Component: Split document_service.py into focused services
Goal: Refactor 380-line service into 4 focused classes following Single Responsibility Principle

Instructions:
1. Read services/api/app/services/document_service.py
2. Write failing tests for each new service class
3. Extract DocumentUploadService (file I/O, validation)
4. Extract DocumentMetadataService (database CRUD)
5. Extract ChunkingOrchestrator (chunking coordination)
6. Update DocumentService to facade pattern
7. Add dependency injection factories
8. Run all tests to verify behavior preserved
9. Commit with message: "refactor(api): split document_service into focused services"

Design reference: docs/plans/2025-10-24-cleanup-and-refactoring-design.md (Section: Track B1)

Files to create:
- services/api/app/services/document_upload_service.py
- services/api/app/services/document_metadata_service.py
- services/api/app/services/chunking_orchestrator.py
- services/api/tests/unit/test_document_upload_service.py
- services/api/tests/unit/test_document_metadata_service.py
- services/api/tests/unit/test_chunking_orchestrator.py

Files to modify:
- services/api/app/services/document_service.py (refactor to facade)
- services/api/app/core/dependencies.py (add factories)

Success criteria:
- All existing integration tests pass
- New unit tests for each service (>80% coverage)
- document_service.py under 150 lines
- Zero code duplication between services
```

**Execution:**

Use `superpowers:subagent-driven-development` skill to dispatch subagent with above specification.

**Verification after subagent completes:**

Run: `pytest services/api/tests/ -v`

Expected: All tests pass

Run: `wc -l services/api/app/services/document_service.py`

Expected: Under 150 lines

---

### Task B2: Fix Dependency Injection Violations (API Service)

**Context:** Services create dependencies internally instead of accepting via constructor.

**Subagent Task Specification:**

```
Component: Fix dependency injection violations
Goal: Proper dependency injection throughout API service (zero global singletons)

Instructions:
1. Identify all global service instances at module level
2. Update service constructors to accept dependencies
3. Add factory functions to core/dependencies.py
4. Remove all global instances
5. Update route handlers to use Depends()
6. Update tests to mock dependencies via overrides
7. Run all tests to verify
8. Commit with message: "refactor(api): fix dependency injection violations"

Design reference: docs/plans/2025-10-24-cleanup-and-refactoring-design.md (Section: Track B2)

Files to modify:
- services/api/app/core/dependencies.py (add factories)
- services/api/app/services/*.py (remove globals, update constructors)
- services/api/app/api/routes/*.py (add Depends() injection)
- services/api/tests/conftest.py (add override fixtures)

Success criteria:
- Zero global service instances
- All dependencies via constructors or Depends()
- Tests easily mock dependencies
- All integration tests still pass
```

**Execution:**

Use `superpowers:subagent-driven-development` skill to dispatch subagent with above specification.

**Verification after subagent completes:**

Run: `grep -r "^[a-z_]*_service = " services/api/app/services/ | wc -l`

Expected: `0` (no global instances)

Run: `pytest services/api/tests/ -v`

Expected: All tests pass

---

### Task B3: Add Frontend Component Tests

**Context:** Only 1 test file exists. Need comprehensive component testing.

**Subagent Task Specification:**

```
Component: Add comprehensive frontend component tests
Goal: Achieve >80% test coverage for key React components

Instructions:
1. Create test utilities in test/test-utils.tsx (custom render with providers)
2. Write EnhancedSearchBar tests (keyboard shortcuts, debouncing)
3. Write UploadModal tests (drag-drop, validation, file handling)
4. Write DocumentCard tests (rendering, status badges, formatting)
5. Write formatters utility tests (date, file size, status colors)
6. Run coverage report: npm test -- --coverage
7. Verify >80% coverage for tested components
8. Commit with message: "test(frontend): add comprehensive component tests"

Design reference: docs/plans/2025-10-24-cleanup-and-refactoring-design.md (Section: Track B3)

Files to create:
- services/frontend/src/test/test-utils.tsx
- services/frontend/src/components/search/__tests__/EnhancedSearchBar.test.tsx
- services/frontend/src/components/upload/__tests__/UploadModal.test.tsx
- services/frontend/src/components/documents/__tests__/DocumentCard.test.tsx
- services/frontend/src/utils/__tests__/formatters.test.ts

Testing approach:
- Use @testing-library/react for rendering
- Use @testing-library/user-event for interactions
- Mock API calls with vi.mock()
- Test user behavior, not implementation details

Success criteria:
- All 5 test files created
- Tests pass consistently
- Coverage >80% for tested components
- No flaky tests
```

**Execution:**

Use `superpowers:subagent-driven-development` skill to dispatch subagent with above specification.

**Verification after subagent completes:**

Run: `cd services/frontend && npm test -- --coverage`

Expected: Coverage >80% for components, all tests pass

---

### Task B4: Wait for All Track B Subagents

**Context:** Three subagents running in parallel. Wait for all to complete before proceeding to Track C.

**Step 1: Check B1 status**

If B1 complete, verify:
- `document_service.py` refactored to facade
- New service classes created
- Tests pass

**Step 2: Check B2 status**

If B2 complete, verify:
- No global service instances
- Dependency injection via Depends()
- Tests pass

**Step 3: Check B3 status**

If B3 complete, verify:
- New test files created
- Coverage >80%
- Tests pass

**Step 4: Review all Track B commits**

Run: `git log --oneline --decorate -n 10 | grep -E "(refactor|test)"`

Expected: Shows commits from all three Track B components

**Step 5: Run full test suite**

Run: `cd services/api && poetry run pytest`

Expected: All backend tests pass

Run: `cd services/frontend && npm test`

Expected: All frontend tests pass

**Step 6: Confirm Track B complete**

Run: `echo "✓ Track B complete. All components refactored and tested. Ready for Track C."`

---

## Track C: Cross-Cutting Polish

**Context:** Apply consistent improvements across all services after Track B refactors complete.

### Task C1: Standardize Backend Error Handling

**Context:** Ensure all services use custom exceptions consistently.

**Files:**
- Modify: All `services/api/app/services/*.py` files
- Review: `services/api/app/core/exceptions.py`

**Step 1: Audit services for generic exceptions**

Run: `grep -n "except Exception as e" services/api/app/services/*.py`

Expected: List of files with generic exception handling

**Step 2: Create new custom exceptions if needed**

Edit `services/api/app/core/exceptions.py` if new exception types identified:

```python
class ChunkingError(RAASException):
    """Raised when text chunking fails."""
    def __init__(self, reason: str):
        super().__init__(
            f"Failed to chunk document: {reason}",
            status_code=500
        )

class ValidationError(RAASException):
    """Raised when input validation fails."""
    def __init__(self, field: str, reason: str):
        super().__init__(
            f"Validation failed for {field}: {reason}",
            status_code=400,
            details={"field": field, "reason": reason}
        )
```

**Step 3: Replace generic exceptions in document_upload_service.py**

Find and replace patterns like:
```python
# Before
except Exception as e:
    logger.error(f"Upload failed: {e}")
    raise

# After
except IOError as e:
    logger.error(f"Failed to save file {filename}: {e}")
    raise FileProcessingError(filename=filename, reason=str(e))
```

**Step 4: Add request ID to error logs**

Update logging calls to include request context:

```python
logger.error(
    f"Failed to process document {document_id}",
    exc_info=True,
    extra={"document_id": str(document_id), "filename": filename}
)
```

**Step 5: Run tests to verify**

Run: `poetry run pytest services/api/tests/ -v`

Expected: All tests pass, error handling improved

**Step 6: Commit**

```bash
git add services/api/app/
git commit -m "refactor(api): standardize error handling with custom exceptions

- Replace generic Exception catches with specific exception types
- Add request context to error logs
- Ensure consistent error handling across all services
- Improve error messages with actionable information"
```

---

### Task C2: Standardize Frontend Error Handling

**Context:** Use shadcn/ui Toast for all errors with user-friendly messages.

**Files:**
- Modify: `services/frontend/src/services/api.ts`
- Create: `services/frontend/src/utils/errorMessages.ts`

**Step 1: Create error message mapping**

Create `services/frontend/src/utils/errorMessages.ts`:

```typescript
/**
 * User-friendly error messages mapped from API error types.
 */

export const ERROR_MESSAGES: Record<string, string> = {
  'DocumentNotFoundError': 'The document you requested could not be found.',
  'EmbeddingFailedError': 'Unable to process document. Please try again later.',
  'InvalidFileTypeError': 'This file type is not supported. Please upload PDF, DOCX, or TXT files.',
  'FileProcessingError': 'Unable to extract text from this file. It may be password-protected or corrupted.',
  'QdrantConnectionError': 'Search service temporarily unavailable. Your documents are safe and will be searchable again shortly.',
  'ValidationError': 'The information provided is invalid. Please check your input and try again.',
};

export function getUserFriendlyError(error: any): string {
  // Check if error has a type field (from backend)
  if (error?.response?.data?.type) {
    const errorType = error.response.data.type;
    if (ERROR_MESSAGES[errorType]) {
      return ERROR_MESSAGES[errorType];
    }
  }

  // Check for network errors
  if (error?.message === 'Network Error') {
    return 'Unable to connect to the server. Please check your internet connection.';
  }

  // Generic fallback
  return error?.response?.data?.detail || error?.message || 'An unexpected error occurred. Please try again.';
}
```

**Step 2: Update API client to use Toast**

Modify `services/frontend/src/services/api.ts` to centralize error handling:

```typescript
import { toast } from '@/components/ui/use-toast';
import { getUserFriendlyError } from '@/utils/errorMessages';

// Add interceptor for error responses
this.client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = getUserFriendlyError(error);
    toast({
      title: 'Error',
      description: message,
      variant: 'destructive',
    });
    return Promise.reject(error);
  }
);
```

**Step 3: Replace alert() calls with Toast**

Search for any remaining `alert()` or `window.alert()`:

Run: `grep -r "alert(" services/frontend/src/ | grep -v node_modules`

Replace with Toast notifications.

**Step 4: Test error handling**

Run: `npm test`

Expected: Tests pass

Manually test in browser:
- Upload invalid file type → see friendly error
- Try to access non-existent document → see friendly error

**Step 5: Commit**

```bash
git add services/frontend/src/
git commit -m "refactor(frontend): standardize error handling with user-friendly messages

- Create error message mapping for API error types
- Centralize error handling in API client with Toast notifications
- Replace generic error messages with actionable user-friendly ones
- Remove alert() calls in favor of Toast component"
```

---

### Task C3: Apply Code Formatting (Backend)

**Context:** Ensure consistent code style across Python files.

**Files:**
- Modify: All `services/api/app/**/*.py` files

**Step 1: Run Black formatter**

```bash
cd services/api
poetry run black app/ tests/ --check
```

Expected: Shows files that need formatting

**Step 2: Apply Black formatting**

```bash
poetry run black app/ tests/
```

Expected: Files reformatted

**Step 3: Run isort for import ordering**

```bash
poetry run isort app/ tests/ --check
```

Expected: Shows files that need import reordering

**Step 4: Apply isort**

```bash
poetry run isort app/ tests/
```

Expected: Imports reordered

**Step 5: Run mypy for type checking**

```bash
poetry run mypy app/ --ignore-missing-imports
```

Expected: No type errors (or document known issues)

**Step 6: Verify tests still pass**

Run: `poetry run pytest`

Expected: All tests pass (formatting shouldn't change behavior)

**Step 7: Commit**

```bash
git add services/api/
git commit -m "style(api): apply Black and isort formatting

- Run Black formatter on all Python files
- Sort imports with isort
- Fix any mypy type hint issues
- No functional changes, only style improvements"
```

---

### Task C4: Apply Code Formatting (Frontend)

**Context:** Ensure consistent code style across TypeScript files.

**Files:**
- Modify: All `services/frontend/src/**/*.{ts,tsx}` files

**Step 1: Run Prettier check**

```bash
cd services/frontend
npx prettier --check "src/**/*.{ts,tsx}"
```

Expected: Shows files that need formatting

**Step 2: Apply Prettier formatting**

```bash
npx prettier --write "src/**/*.{ts,tsx}"
```

Expected: Files reformatted

**Step 3: Run ESLint**

```bash
npx eslint "src/**/*.{ts,tsx}" --fix
```

Expected: Auto-fixable issues corrected

**Step 4: Check TypeScript compilation**

```bash
npx tsc --noEmit
```

Expected: No TypeScript errors

**Step 5: Verify tests still pass**

Run: `npm test`

Expected: All tests pass

**Step 6: Commit**

```bash
git add services/frontend/src/
git commit -m "style(frontend): apply Prettier and ESLint formatting

- Run Prettier on all TypeScript files
- Apply ESLint auto-fixes
- Verify TypeScript strict mode compliance
- No functional changes, only style improvements"
```

---

### Task C5: Verify Track C Completion

**Context:** Ensure all Track C polish completed successfully.

**Step 1: Verify error handling standardized**

Backend:
Run: `grep -r "except Exception as e" services/api/app/services/ | wc -l`

Expected: `0` or very few (specific exceptions used)

Frontend:
Run: `grep -r "alert(" services/frontend/src/ | grep -v node_modules | wc -l`

Expected: `0` (all replaced with Toast)

**Step 2: Verify code formatting applied**

Backend:
Run: `cd services/api && poetry run black app/ tests/ --check`

Expected: "All done! ✨"

Frontend:
Run: `cd services/frontend && npx prettier --check "src/**/*.{ts,tsx}"`

Expected: "All matched files use Prettier code style!"

**Step 3: Run full test suite**

Backend:
Run: `cd services/api && poetry run pytest --cov`

Expected: All tests pass, coverage report generated

Frontend:
Run: `cd services/frontend && npm test -- --coverage`

Expected: All tests pass, coverage >80%

**Step 4: Review all Track C commits**

Run: `git log --oneline --decorate -n 5 | grep -E "(refactor|style)"`

Expected: Shows commits from Track C tasks

**Step 5: Confirm Track C complete**

Run: `echo "✓ Track C complete. All polish and consistency improvements applied."`

---

## Final Verification & Merge

### Task F1: Run Integration Tests

**Context:** Verify entire application works end-to-end after all refactoring.

**Step 1: Start Docker Compose stack**

```bash
cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas
docker-compose -f infrastructure/docker-compose/docker-compose.yml up --build -d
```

**Step 2: Wait for services to be healthy**

```bash
sleep 30
docker-compose -f infrastructure/docker-compose/docker-compose.yml ps
```

Expected: All services showing "healthy" status

**Step 3: Run integration test script**

```bash
./infrastructure/scripts/integration-test.sh
```

Expected: All tests pass (health, upload, search, delete)

**Step 4: Stop services**

```bash
docker-compose -f infrastructure/docker-compose/docker-compose.yml down
```

**Step 5: Document results**

If tests pass: Move to next task

If tests fail: Investigate failures, fix issues, re-run tests

---

### Task F2: Merge to Master

**Context:** All tracks complete, tests pass. Ready to merge.

**Step 1: Review all commits since Track A merge**

Run: `git log --oneline --decorate master..feature/cleanup-and-refactoring`

Expected: Shows all Track B and Track C commits

**Step 2: Switch to master and merge**

```bash
cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas
git checkout master
git merge feature/cleanup-and-refactoring --no-ff -m "Merge cleanup and SOLID refactoring work

Completed comprehensive cleanup and refactoring:

Track A (Cleanup):
- Relocated integration tests to proper directory
- Removed generated files from git tracking
- Deleted outdated plan documents
- Enhanced .gitignore

Track B (Component Refactoring):
- Split document_service.py into focused services (SRP)
- Fixed dependency injection violations (DIP)
- Added comprehensive frontend component tests (>80% coverage)

Track C (Polish):
- Standardized error handling with custom exceptions
- Applied code formatting (Black, Prettier)
- User-friendly error messages throughout

All tests pass. Application behavior preserved."
```

**Step 3: Verify merge**

Run: `git log --oneline --decorate -n 1`

Expected: Shows merge commit on master

**Step 4: Push to remote (if applicable)**

```bash
git push origin master
```

**Step 5: Clean up feature branch**

```bash
git branch -d feature/cleanup-and-refactoring
```

**Step 6: Remove worktree**

```bash
git worktree remove .worktrees/cleanup-and-refactoring
```

---

## Success Criteria Checklist

**Repository Cleanliness:**
- [ ] No test files at project root
- [ ] No generated files tracked in git
- [ ] Only 2 RAG plan docs remain in docs/plans/
- [ ] Comprehensive .gitignore in place

**SOLID Compliance:**
- [ ] No file >200 lines (excluding tests)
- [ ] Each service has single, clear responsibility
- [ ] Zero global service singletons
- [ ] All dependencies injected

**Test Coverage:**
- [ ] Backend tests >80% coverage
- [ ] Frontend component tests exist and pass
- [ ] All integration tests pass
- [ ] No flaky tests

**Code Quality:**
- [ ] Zero TypeScript errors
- [ ] All formatters pass (Black, Prettier)
- [ ] Consistent error handling across services
- [ ] User-friendly error messages

**Build & Deploy:**
- [ ] All Docker Compose services start successfully
- [ ] Integration tests pass end-to-end
- [ ] No console errors in browser
- [ ] Application works as before (behavior preserved)

---

## Execution Summary

**Total Tasks:** ~35 bite-sized tasks across 3 tracks
**Estimated Time:** 12-18 hours total
- Track A: 1-2 hours (sequential)
- Track B: 6-8 hours (parallel subagents)
- Track C: 3-4 hours (sequential)
- Final Verification: 1-2 hours

**Key Milestones:**
1. Track A merged to master (immediate cleanup complete)
2. All Track B subagents complete (components refactored)
3. Track C applied (polish complete)
4. Integration tests pass (ready to merge)
5. Final merge to master (work complete)

---

## Notes for Executor

**Track A:** Can be executed immediately. Low risk, no code changes. Merge to master as soon as complete.

**Track B:** Use `superpowers:subagent-driven-development` to dispatch three independent subagents. They can run in parallel since they touch different codebases.

**Track C:** Sequential execution after Track B completes. Review all refactored code before applying polish.

**Testing:** Run tests after each task. Don't proceed if tests fail without investigating.

**Commits:** Frequent, descriptive commits. Follow conventional commit format (feat:, refactor:, test:, chore:, style:).

**Questions:** Reference design doc at `docs/plans/2025-10-24-cleanup-and-refactoring-design.md` for context and rationale.
