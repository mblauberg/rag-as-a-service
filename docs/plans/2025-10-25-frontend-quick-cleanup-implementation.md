# Frontend Quick Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove dead code, eliminate duplication, and improve code organization in the React frontend

**Architecture:** Refactoring existing code without changing functionality - pure cleanup focused on DRY principles, SOLID principles, and removing maintenance burden

**Tech Stack:** React, TypeScript, Vitest, Vite

---

## Task 1: Remove Dead Code - Unused Files

**Files:**
- Delete: `services/frontend/src/components/common/Card.tsx`
- Delete: `services/frontend/src/hooks/useSearch.ts`

**Step 1: Verify Card.tsx is unused**

Run: `grep -r "from.*common/Card" services/frontend/src --include="*.tsx" --include="*.ts"`
Expected: No results (file is not imported anywhere)

**Step 2: Verify useSearch.ts is unused**

Run: `grep -r "useSearch['\"]" services/frontend/src --include="*.tsx" --include="*.ts" | grep -v useSearchWithDebounce`
Expected: Only shows definition, no imports (useSearchWithDebounce is used instead)

**Step 3: Delete unused files**

```bash
rm services/frontend/src/components/common/Card.tsx
rm services/frontend/src/hooks/useSearch.ts
```

**Step 4: Run tests to verify no breakage**

Run: `cd services/frontend && npm test`
Expected: All tests pass

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor(frontend): remove unused Card.tsx and useSearch.ts"
```

---

## Task 2: Remove Dead Code - Unused Functions

**Files:**
- Modify: `services/frontend/src/utils/formatters.ts:30-50`
- Modify: `services/frontend/src/utils/__tests__/formatters.test.ts`

**Step 1: Verify formatStatus and getStatusColor are unused in production code**

Run: `grep -r "formatStatus\|getStatusColor" services/frontend/src --include="*.tsx" --include="*.ts" | grep -v "test\|\.test\."`
Expected: Only shows definitions, no actual usage

**Step 2: Remove formatStatus function**

In `services/frontend/src/utils/formatters.ts`, delete lines 27-32:

```typescript
/**
 * Capitalize first letter of status string.
 */
export function formatStatus(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}
```

**Step 3: Remove getStatusColor function and StatusType**

In `services/frontend/src/utils/formatters.ts`, delete lines 34-50:

```typescript
/**
 * Status type for documents.
 */
export type StatusType = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * Get Tailwind CSS classes for status badge.
 */
export function getStatusColor(status: StatusType): string {
  const colors: Record<StatusType, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
}
```

**Step 4: Remove tests for deleted functions**

In `services/frontend/src/utils/__tests__/formatters.test.ts`, remove all tests for `formatStatus` and `getStatusColor`:
- Remove `describe('formatStatus', ...)` block
- Remove `describe('getStatusColor', ...)` block
- Keep tests for `formatDate` and `formatBytes`

**Step 5: Run tests to verify**

Run: `cd services/frontend && npm test`
Expected: All remaining tests pass

**Step 6: Commit**

```bash
git add services/frontend/src/utils/formatters.ts services/frontend/src/utils/__tests__/formatters.test.ts
git commit -m "refactor(frontend): remove unused formatStatus and getStatusColor functions"
```

---

## Task 3: Remove Dead Code - Unused Prop

**Files:**
- Modify: `services/frontend/src/components/search/SummaryDisplay.tsx:4,7-8,44-48`

**Step 1: Verify onCitationClick is never passed**

Run: `grep -r "SummaryDisplay" services/frontend/src --include="*.tsx" -A 5 | grep onCitationClick`
Expected: Only shows interface definition and destructuring, never passed as prop

**Step 2: Remove onCitationClick from interface**

In `services/frontend/src/components/search/SummaryDisplay.tsx`, update interface (around line 4):

```typescript
interface SummaryDisplayProps {
  summary: string;
  modelUsed: string;
}
```

**Step 3: Remove from component destructuring**

In same file, update component declaration (around line 7):

```typescript
export const SummaryDisplay: React.FC<SummaryDisplayProps> = ({
  summary,
  modelUsed
}) => {
```

**Step 4: Remove onClick handler from citation rendering**

In same file, update citation rendering (around line 44-48) from:

```typescript
onClick={() => onCitationClick?.(citationNum)}
```

To remove the onClick entirely, making citations non-clickable. Find the citation rendering code and remove the click handler.

**Step 5: Run tests**

Run: `cd services/frontend && npm test`
Expected: All tests pass

**Step 6: Commit**

```bash
git add services/frontend/src/components/search/SummaryDisplay.tsx
git commit -m "refactor(frontend): remove unused onCitationClick prop from SummaryDisplay"
```

---

## Task 4: Create File Validation Utility - Write Test First

**Files:**
- Create: `services/frontend/src/utils/__tests__/fileValidation.test.ts`

**Step 1: Write comprehensive tests for file validation**

Create `services/frontend/src/utils/__tests__/fileValidation.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import {
  validateUploadFile,
  extractTitleFromFilename,
  ALLOWED_EXTENSIONS,
  MAX_FILE_SIZE
} from '../fileValidation';

describe('fileValidation', () => {
  describe('validateUploadFile', () => {
    it('should accept valid PDF file', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const result = validateUploadFile(file);
      expect(result.valid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('should accept valid DOCX file', () => {
      const file = new File(['content'], 'document.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });
      const result = validateUploadFile(file);
      expect(result.valid).toBe(true);
    });

    it('should accept valid TXT file', () => {
      const file = new File(['content'], 'notes.txt', { type: 'text/plain' });
      const result = validateUploadFile(file);
      expect(result.valid).toBe(true);
    });

    it('should accept uppercase extensions', () => {
      const file = new File(['content'], 'TEST.PDF', { type: 'application/pdf' });
      const result = validateUploadFile(file);
      expect(result.valid).toBe(true);
    });

    it('should reject invalid file extension', () => {
      const file = new File(['content'], 'image.jpg', { type: 'image/jpeg' });
      const result = validateUploadFile(file);
      expect(result.valid).toBe(false);
      expect(result.error).toBe('Please upload a PDF, DOCX, or TXT file');
    });

    it('should reject file exceeding size limit', () => {
      const largeContent = new Array(101 * 1024 * 1024).fill('a').join('');
      const file = new File([largeContent], 'large.pdf', { type: 'application/pdf' });
      const result = validateUploadFile(file);
      expect(result.valid).toBe(false);
      expect(result.error).toBe('File size must be less than 100MB');
    });

    it('should accept file at size limit', () => {
      // Create file just under 100MB
      const content = new Array(50 * 1024 * 1024).fill('a').join('');
      const file = new File([content], 'medium.pdf', { type: 'application/pdf' });
      const result = validateUploadFile(file);
      expect(result.valid).toBe(true);
    });
  });

  describe('extractTitleFromFilename', () => {
    it('should extract title from PDF filename', () => {
      expect(extractTitleFromFilename('my-document.pdf')).toBe('my-document');
    });

    it('should extract title from DOCX filename', () => {
      expect(extractTitleFromFilename('report.docx')).toBe('report');
    });

    it('should extract title from TXT filename', () => {
      expect(extractTitleFromFilename('notes.txt')).toBe('notes');
    });

    it('should handle filenames with multiple dots', () => {
      expect(extractTitleFromFilename('my.file.name.pdf')).toBe('my.file.name');
    });

    it('should handle filename without extension', () => {
      expect(extractTitleFromFilename('noextension')).toBe('noextension');
    });
  });

  describe('constants', () => {
    it('should export correct allowed extensions', () => {
      expect(ALLOWED_EXTENSIONS).toEqual(['.pdf', '.docx', '.txt']);
    });

    it('should export correct max file size', () => {
      expect(MAX_FILE_SIZE).toBe(100 * 1024 * 1024);
    });
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `cd services/frontend && npm test fileValidation`
Expected: FAIL - module not found

**Step 3: Commit test**

```bash
git add services/frontend/src/utils/__tests__/fileValidation.test.ts
git commit -m "test(frontend): add tests for file validation utility"
```

---

## Task 5: Create File Validation Utility - Implement

**Files:**
- Create: `services/frontend/src/utils/fileValidation.ts`

**Step 1: Implement file validation utility**

Create `services/frontend/src/utils/fileValidation.ts`:

```typescript
/**
 * File validation utilities for document uploads.
 * Centralizes validation logic to avoid duplication.
 */

export const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt'] as const;
export const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

export interface FileValidationResult {
  valid: boolean;
  error?: string;
}

/**
 * Validate file for upload based on extension and size.
 */
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

/**
 * Extract document title from filename by removing extension.
 */
export function extractTitleFromFilename(filename: string): string {
  return filename.replace(/\.[^/.]+$/, '');
}
```

**Step 2: Run tests to verify they pass**

Run: `cd services/frontend && npm test fileValidation`
Expected: All tests pass

**Step 3: Commit implementation**

```bash
git add services/frontend/src/utils/fileValidation.ts
git commit -m "feat(frontend): add file validation utility"
```

---

## Task 6: Refactor UploadModal to Use File Validation Utility

**Files:**
- Modify: `services/frontend/src/components/upload/UploadModal.tsx:2,69-94,96-112`

**Step 1: Add import for validation utilities**

In `services/frontend/src/components/upload/UploadModal.tsx`, add to imports (around line 2):

```typescript
import { validateUploadFile, extractTitleFromFilename, ALLOWED_EXTENSIONS } from '@/utils/fileValidation';
```

**Step 2: Refactor handleDrop to use validation utility**

Replace lines 69-94 with:

```typescript
const handleDrop = (e: React.DragEvent) => {
  e.preventDefault();
  e.stopPropagation();
  setIsDragging(false);
  setError(null);

  const files = Array.from(e.dataTransfer.files);
  const droppedFile = files[0];

  if (!droppedFile) {
    return;
  }

  const validation = validateUploadFile(droppedFile);

  if (!validation.valid) {
    setError(validation.error!);
    return;
  }

  setFile(droppedFile);
  if (!title) {
    setTitle(extractTitleFromFilename(droppedFile.name));
  }
};
```

**Step 3: Refactor handleFileInput to use validation utility**

Replace lines 96-112 with:

```typescript
const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
  const selectedFile = e.target.files?.[0];

  if (!selectedFile) {
    return;
  }

  setError(null);

  const validation = validateUploadFile(selectedFile);

  if (!validation.valid) {
    setError(validation.error!);
    return;
  }

  setFile(selectedFile);
  if (!title) {
    setTitle(extractTitleFromFilename(selectedFile.name));
  }
};
```

**Step 4: Update file input accept attribute to use constant**

Find the file input element and update accept attribute to use the constant:

```typescript
accept={ALLOWED_EXTENSIONS.join(',')}
```

**Step 5: Run tests**

Run: `cd services/frontend && npm test`
Expected: All tests pass

**Step 6: Verify line count reduction**

Run: `wc -l services/frontend/src/components/upload/UploadModal.tsx`
Expected: File should be ~20 lines shorter than before

**Step 7: Commit**

```bash
git add services/frontend/src/components/upload/UploadModal.tsx
git commit -m "refactor(frontend): use file validation utility in UploadModal"
```

---

## Task 7: Move Button Component to ui Folder

**Files:**
- Move: `services/frontend/src/components/common/Button.tsx` → `services/frontend/src/components/ui/button.tsx`

**Step 1: Move Button.tsx to ui folder**

```bash
git mv services/frontend/src/components/common/Button.tsx services/frontend/src/components/ui/button.tsx
```

**Step 2: Run tests to verify**

Run: `cd services/frontend && npm test`
Expected: Tests fail due to import errors

**Step 3: Commit move**

```bash
git commit -m "refactor(frontend): move Button component to ui folder"
```

---

## Task 8: Update Button Imports - Part 1

**Files:**
- Modify: `services/frontend/src/components/documents/DocumentCard.tsx`
- Modify: `services/frontend/src/components/upload/UploadFAB.tsx`

**Step 1: Update DocumentCard.tsx import**

Find the Button import and change from:

```typescript
import { Button } from '../common/Button';
```

To:

```typescript
import { Button } from '@/components/ui/button';
```

**Step 2: Update UploadFAB.tsx import**

Find the Button import and change from:

```typescript
import { Button } from '../common/Button';
```

To:

```typescript
import { Button } from '@/components/ui/button';
```

**Step 3: Run tests**

Run: `cd services/frontend && npm test`
Expected: Some tests still fail (2 more files to update)

**Step 4: Commit**

```bash
git add services/frontend/src/components/documents/DocumentCard.tsx services/frontend/src/components/upload/UploadFAB.tsx
git commit -m "refactor(frontend): update Button imports in DocumentCard and UploadFAB"
```

---

## Task 9: Update Button Imports - Part 2

**Files:**
- Modify: `services/frontend/src/components/upload/UploadModal.tsx`
- Modify: `services/frontend/src/pages/MainPage.tsx`

**Step 1: Update UploadModal.tsx import**

Find the Button import (around line 10) and change from:

```typescript
import { Button } from '../common/Button';
```

To:

```typescript
import { Button } from '@/components/ui/button';
```

**Step 2: Update MainPage.tsx import**

Find the Button import and change from:

```typescript
import { Button } from '../components/common/Button';
```

To:

```typescript
import { Button } from '@/components/ui/button';
```

**Step 3: Run tests**

Run: `cd services/frontend && npm test`
Expected: All tests pass

**Step 4: Commit**

```bash
git add services/frontend/src/components/upload/UploadModal.tsx services/frontend/src/pages/MainPage.tsx
git commit -m "refactor(frontend): update Button imports in UploadModal and MainPage"
```

---

## Task 10: Delete Empty common Folder

**Files:**
- Delete: `services/frontend/src/components/common/` (directory)

**Step 1: Verify common folder is empty**

Run: `ls -la services/frontend/src/components/common/`
Expected: Only shows . and .. (directory is empty)

**Step 2: Delete common folder**

```bash
rmdir services/frontend/src/components/common/
```

**Step 3: Run tests**

Run: `cd services/frontend && npm test`
Expected: All tests pass

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor(frontend): remove empty common components folder"
```

---

## Task 11: Standardize Imports - Component Files

**Files:**
- Modify: Multiple component files with relative imports

**Step 1: Find all files with relative imports**

Run: `grep -r "from '\.\." services/frontend/src/components --include="*.tsx" --include="*.ts" -l`
Expected: List of files with relative imports

**Step 2: Convert relative imports to alias imports**

For each file found, convert patterns like:
- `from '../../utils/formatters'` → `from '@/utils/formatters'`
- `from '../hooks/useDocuments'` → `from '@/hooks/useDocuments'`
- `from '../../lib/utils'` → `from '@/lib/utils'`

Use search and replace carefully, ensuring not to break imports.

**Step 3: Run tests**

Run: `cd services/frontend && npm test`
Expected: All tests pass

**Step 4: Run type checking**

Run: `cd services/frontend && npm run build`
Expected: Build succeeds with no TypeScript errors

**Step 5: Commit**

```bash
git add services/frontend/src/components/
git commit -m "refactor(frontend): standardize component imports to use @ alias"
```

---

## Task 12: Standardize Imports - Page Files

**Files:**
- Modify: `services/frontend/src/pages/MainPage.tsx`

**Step 1: Review MainPage.tsx imports**

Check if MainPage uses any relative imports that should be converted to alias imports.

**Step 2: Convert relative imports to alias imports**

Change patterns like:
- `from '../components/...'` → `from '@/components/...'`
- `from '../hooks/...'` → `from '@/hooks/...'`

**Step 3: Run tests**

Run: `cd services/frontend && npm test`
Expected: All tests pass

**Step 4: Commit**

```bash
git add services/frontend/src/pages/MainPage.tsx
git commit -m "refactor(frontend): standardize page imports to use @ alias"
```

---

## Task 13: Remove Unused Imports

**Files:**
- Multiple files may have unused imports after refactoring

**Step 1: Run build to check for unused imports**

Run: `cd services/frontend && npm run build`
Expected: TypeScript may report unused imports (or build succeeds cleanly)

**Step 2: Remove any unused imports identified**

If the build identifies unused imports, remove them from the relevant files.

**Step 3: Run tests**

Run: `cd services/frontend && npm test`
Expected: All tests pass

**Step 4: Commit if changes made**

```bash
git add -A
git commit -m "refactor(frontend): remove unused imports"
```

---

## Task 14: Final Verification - Test Suite

**Files:**
- N/A (verification only)

**Step 1: Run complete test suite**

Run: `cd services/frontend && npm test`
Expected: All 161 tests pass (or adjusted count after removing test-only code)

**Step 2: Verify test coverage hasn't decreased**

Run: `cd services/frontend && npm run test:coverage`
Expected: Coverage remains similar or improves

**Step 3: Document test results**

Output test results showing:
- Total tests: X passing
- Removed tests for dead code: Y tests
- All features still covered

---

## Task 15: Final Verification - Build

**Files:**
- N/A (verification only)

**Step 1: Clean build**

```bash
cd services/frontend
rm -rf dist
npm run build
```

Expected: Build succeeds with no errors or warnings

**Step 2: Check bundle size**

Run: `ls -lh services/frontend/dist/assets/`
Expected: Bundle created successfully

**Step 3: Document build success**

Confirm:
- TypeScript compilation successful
- No type errors
- Vite build completed

---

## Task 16: Final Verification - Manual Smoke Test

**Files:**
- N/A (manual testing)

**Step 1: Start development server**

Run: `cd services/frontend && npm run dev`
Expected: Dev server starts on localhost:5173

**Step 2: Test document upload**

Manual steps:
1. Click upload FAB
2. Drag and drop a PDF file
3. Verify file validation works
4. Submit upload
5. Verify document appears in list

**Step 3: Test invalid file upload**

Manual steps:
1. Try uploading .jpg file
2. Verify error: "Please upload a PDF, DOCX, or TXT file"
3. Try uploading 101MB file (if available)
4. Verify error: "File size must be less than 100MB"

**Step 4: Test search functionality**

Manual steps:
1. Search for content
2. Verify results display
3. Verify summary renders
4. Verify citations display (non-clickable now)

**Step 5: Test document details**

Manual steps:
1. Click on a document
2. Verify modal opens
3. Verify all details shown
4. Close modal

**Step 6: Document smoke test results**

Confirm all manual tests passed.

---

## Task 17: Create Cleanup Summary

**Files:**
- Create: `docs/plans/2025-10-25-frontend-quick-cleanup-summary.md`

**Step 1: Document changes made**

Create summary file:

```markdown
# Frontend Quick Cleanup - Summary

**Date:** 2025-10-25
**Branch:** feature/frontend-quick-cleanup

## Changes Made

### Dead Code Removed
- ✅ Deleted `src/components/common/Card.tsx` (unused re-export)
- ✅ Deleted `src/hooks/useSearch.ts` (unused hook)
- ✅ Removed `formatStatus()` function from formatters.ts
- ✅ Removed `getStatusColor()` function from formatters.ts
- ✅ Removed `StatusType` type from formatters.ts
- ✅ Removed `onCitationClick` prop from SummaryDisplay component
- ✅ Removed corresponding tests for deleted functions

### Duplication Eliminated
- ✅ Created `src/utils/fileValidation.ts` utility
- ✅ Extracted file validation logic from UploadModal
- ✅ Centralized validation constants (ALLOWED_EXTENSIONS, MAX_FILE_SIZE)
- ✅ ~20 lines removed from UploadModal

### Organization Improved
- ✅ Moved Button component from `common/` to `ui/` folder
- ✅ Deleted empty `components/common/` directory
- ✅ Updated 4 import statements for Button component

### Import Consistency
- ✅ Standardized all imports to use `@/` path alias
- ✅ Removed relative imports (`../` patterns)
- ✅ Improved refactoring safety

## Test Results
- Tests passing: [INSERT FINAL COUNT]
- Tests removed: [INSERT COUNT] (for deleted functions)
- Build status: ✅ Success
- Manual smoke tests: ✅ All passed

## Metrics
- Files deleted: 2
- Functions removed: 2
- Lines reduced: ~40-50 total
- Import statements updated: [INSERT COUNT]

## Next Steps
Consider for future refactoring:
- Split MainPage into smaller components
- Extract custom hooks from MainPage
- Feature-based folder structure
- Fix test warnings (act(), accessibility)
```

**Step 2: Fill in actual counts**

Update [INSERT] placeholders with actual numbers from the refactoring.

**Step 3: Commit summary**

```bash
git add docs/plans/2025-10-25-frontend-quick-cleanup-summary.md
git commit -m "docs: add frontend quick cleanup summary"
```

---

## Completion Checklist

- [ ] All dead code removed (files and functions)
- [ ] File validation utility created and tested
- [ ] UploadModal refactored to use utility
- [ ] Button moved to ui/ folder
- [ ] All Button imports updated
- [ ] common/ folder deleted
- [ ] All imports standardized to @ alias
- [ ] Unused imports removed
- [ ] All tests passing
- [ ] Build succeeds
- [ ] Manual smoke tests pass
- [ ] Summary document created

## Post-Implementation

After completing all tasks:

1. **Review changes:** `git log --oneline feature/frontend-quick-cleanup`
2. **Final verification:** Run full test suite and build
3. **Merge to master** (or create PR if preferred)
4. **Deploy** (if applicable)

## Notes for Engineer

- **DRY:** The file validation utility eliminates duplication
- **YAGNI:** Removed code that provided zero value
- **SOLID:** Single Responsibility - validation separated from UI
- **TDD:** Tests written before implementation (Task 4 before Task 5)
- **Frequent commits:** Each task is a separate commit for easy rollback

**Total estimated time:** 1-2 hours
**Complexity:** Low - mostly deletions and simple refactoring
**Risk:** Low - comprehensive test coverage validates all changes
