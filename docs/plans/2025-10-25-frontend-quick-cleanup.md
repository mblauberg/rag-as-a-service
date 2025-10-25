# Frontend Quick Cleanup - Design Document

**Date:** 2025-10-25
**Type:** Code Quality Improvement
**Scope:** Quick cleanup (1-2 hours)
**Risk:** Low

## Objective

Improve frontend code quality through targeted cleanup: remove dead code, eliminate duplication, and improve organization without major structural changes.

## Background

Current state analysis revealed:
- **Dead code:** Unused files and functions (common/Card.tsx, useSearch.ts, unused formatters)
- **Duplication:** File validation logic repeated in UploadModal
- **Organizational issues:** Confusing common/ vs ui/ component split
- **Import inconsistency:** Mix of relative and alias imports

User goals:
- General cleanup and modernization
- Apply SOLID principles without overengineering
- Remove technical debt and unused code

**Test Status:** All 161 tests passing, build succeeds

## Design

### 1. Dead Code Removal

Remove files and functions that provide zero value:

**Files to Delete:**
- `src/components/common/Card.tsx` - Unused re-export
- `src/hooks/useSearch.ts` - Defined but never imported
- Delete related test coverage for removed functions

**Functions to Remove:**
- `src/utils/formatters.ts::formatStatus()` - Only used in tests
- `src/utils/formatters.ts::getStatusColor()` - Only used in tests
- Remove corresponding tests in `src/utils/__tests__/formatters.test.ts`

**Props to Remove:**
- `src/components/search/SummaryDisplay.tsx::onCitationClick` - Unused optional prop
- Update prop interface and remove related rendering logic

**Rationale:** These artifacts create maintenance burden and confusion without providing value. Removing them reduces cognitive load.

### 2. Duplication Removal

**Problem:** UploadModal duplicates file validation logic across two handlers:
- `handleDrop` (lines 76-93)
- `handleFileInput` (lines 96-112)

Both validate:
- Allowed extensions (.pdf, .docx, .txt)
- File size limit (100MB)
- Extract title from filename

**Solution:** Create `src/utils/fileValidation.ts`:

```typescript
export const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt'] as const;
export const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

export interface FileValidationResult {
  valid: boolean;
  error?: string;
}

export function validateUploadFile(file: File): FileValidationResult {
  // Check extension
  const hasValidExtension = ALLOWED_EXTENSIONS.some(ext =>
    file.name.toLowerCase().endsWith(ext)
  );

  if (!hasValidExtension) {
    return {
      valid: false,
      error: 'Please upload a PDF, DOCX, or TXT file'
    };
  }

  // Check size
  if (file.size > MAX_FILE_SIZE) {
    return {
      valid: false,
      error: 'File size must be less than 100MB'
    };
  }

  return { valid: true };
}

export function extractTitleFromFilename(filename: string): string {
  return filename.replace(/\.[^/.]+$/, '');
}
```

**Update UploadModal:**
- Import validation functions
- Replace duplicated logic in both handlers
- Use shared constants for file input accept attribute
- Estimated reduction: ~20 lines

**SOLID Principles Applied:**
- **Single Responsibility:** Validation logic separate from UI logic
- **Open/Closed:** Easy to add new file types by modifying constants
- **DRY:** Single source of truth for validation rules

### 3. Component Organization

**Problem:** Confusing dual structure:
- `src/components/common/` - Contains Button (custom)
- `src/components/ui/` - Contains shadcn/ui components

**Solution:** Consolidate to single `ui/` folder:
1. Move `src/components/common/Button.tsx` → `src/components/ui/button.tsx`
2. Delete `src/components/common/` folder
3. Update all imports (4 files):
   - `src/components/documents/DocumentCard.tsx`
   - `src/components/upload/UploadFAB.tsx`
   - `src/components/upload/UploadModal.tsx`
   - `src/pages/MainPage.tsx`

Change from:
```typescript
import { Button } from '../common/Button';
```

To:
```typescript
import { Button } from '@/components/ui/button';
```

**Rationale:** Single component folder eliminates decision paralysis ("where does this go?") and matches shadcn/ui conventions.

### 4. Import Consistency

**Problem:** Mixed import styles:
- Relative: `import { Button } from '../common/Button'`
- Alias: `import { formatBytes } from '@/utils/formatters'`

**Solution:** Standardize all imports to use `@/` path alias:
- Review all component files
- Convert relative imports to alias imports where applicable
- Improves refactoring safety (moving files doesn't break imports)

### 5. Minor Cleanups

- Remove any unused imports found during refactoring
- Ensure consistent code formatting
- Update tests to reflect removed functions

## Out of Scope

Deliberately excluded to maintain quick cleanup scope:

- Splitting MainPage into smaller components
- Extracting custom hooks from MainPage
- Feature-based folder restructuring
- API client architecture changes
- Fixing test warnings (act() warnings, accessibility)
- Performance optimizations
- Bundle size analysis

These would require larger architectural decisions and are candidates for future refactoring.

## Testing Strategy

### Automated Tests
1. Run test suite: `npm test`
   - All 161 tests must pass
   - 15 skipped tests remain skipped
2. Type checking: `npm run build`
   - Must succeed with no TypeScript errors

### Manual Smoke Tests
1. Upload a document (.pdf, .docx, .txt)
2. Verify file validation works (invalid extension, oversized file)
3. Search for content
4. View document details modal
5. Delete a document

### Verification Criteria
- ✅ All tests pass
- ✅ Build succeeds
- ✅ No runtime errors in browser console
- ✅ All features work identically to before
- ✅ Code is demonstrably cleaner

## Implementation Plan

1. **Dead Code Removal**
   - Delete unused files
   - Remove unused functions from formatters.ts
   - Remove unused prop from SummaryDisplay
   - Update tests

2. **Extract File Validation**
   - Create fileValidation.ts utility
   - Add tests for validation functions
   - Update UploadModal to use new utility

3. **Component Organization**
   - Move Button to ui/ folder
   - Delete common/ folder
   - Update all imports

4. **Import Cleanup**
   - Standardize to @/ aliases
   - Remove unused imports

5. **Verification**
   - Run full test suite
   - Build production bundle
   - Manual smoke testing

## Risk Assessment

**Overall Risk: LOW**

- Mostly deletions and extractions
- No logic changes to core functionality
- Comprehensive test coverage validates changes
- Easy to rollback if issues arise

**Potential Issues:**
- Import path errors (mitigated by TypeScript compiler)
- Test failures (mitigated by running tests after each change)
- Missed references to deleted code (mitigated by grep searches)

## Success Metrics

- Fewer files in codebase (4+ files deleted)
- Reduced line count in UploadModal (~20 lines)
- More consistent import style (100% use @/ aliases)
- All tests passing
- No regression in functionality

## Future Work

After this quick cleanup, consider:
- **Medium refactor:** Extract MainPage into smaller components
- **Accessibility:** Fix Dialog accessibility warnings
- **Test quality:** Address act() warnings in tests
- **Architecture:** Feature-based folder structure
