# Complete Phase 4 Frontend Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the Phase 4 UX redesign by implementing shadcn/ui, creating modern components, and consolidating to a single-page search-centric application.

**Architecture:** Bottom-up implementation: install dependencies → create utilities/hooks → build components → create MainPage → update routing → cleanup old files. All new components use shadcn/ui and modern patterns (custom hooks, debouncing, keyboard shortcuts).

**Tech Stack:** React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, Radix UI, framer-motion, React Query

---

## Phase 1: Foundation Layer (Dependencies & Setup)

### Task 1.1: Install shadcn/ui

**Context:** shadcn/ui provides modern, accessible components built on Radix UI. We'll use it to replace custom common components.

**Files:**
- Create: `services/frontend/components.json`
- Modify: `services/frontend/tailwind.config.js`
- Modify: `services/frontend/tsconfig.json`
- Create: `services/frontend/src/lib/utils.ts`

**Step 1: Initialize shadcn/ui**

Run from frontend directory:
```bash
cd services/frontend
npx shadcn-ui@latest init
```

When prompted, choose:
- **Style:** Default
- **Base color:** Slate
- **CSS variables:** Yes

Expected: Creates `components.json`, updates `tailwind.config.js` and `tsconfig.json`, creates `src/lib/utils.ts`

**Step 2: Verify configuration files**

Check that `components.json` exists:
```bash
cat components.json
```

Expected output should include:
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "src/index.css",
    "baseColor": "slate"
  }
}
```

**Step 3: Verify lib/utils.ts created**

Run: `cat src/lib/utils.ts`

Expected: File contains `cn()` function for class name merging

**Step 4: Commit initialization**

```bash
git add components.json tailwind.config.js tsconfig.json src/lib/
git commit -m "feat: initialize shadcn/ui component library"
```

---

### Task 1.2: Install shadcn/ui Components

**Context:** Install the specific components we need for the refactor.

**Files:**
- Create: `services/frontend/src/components/ui/button.tsx`
- Create: `services/frontend/src/components/ui/card.tsx`
- Create: `services/frontend/src/components/ui/input.tsx`
- Create: `services/frontend/src/components/ui/dialog.tsx`
- Create: `services/frontend/src/components/ui/badge.tsx`
- Create: `services/frontend/src/components/ui/textarea.tsx`

**Step 1: Install button component**

Run:
```bash
cd services/frontend
npx shadcn-ui@latest add button
```

Expected: Creates `src/components/ui/button.tsx`

**Step 2: Install remaining components**

Run:
```bash
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add textarea
```

Expected: Creates 5 new files in `src/components/ui/`

**Step 3: Verify all components installed**

Run: `ls src/components/ui/`

Expected output:
```
badge.tsx
button.tsx
card.tsx
dialog.tsx
input.tsx
textarea.tsx
```

**Step 4: Commit components**

```bash
git add src/components/ui/
git commit -m "feat: install shadcn/ui components (button, card, input, dialog, badge, textarea)"
```

---

### Task 1.3: Verify Dependencies

**Context:** Ensure framer-motion and Radix icons are installed.

**Files:**
- Modify: `services/frontend/package.json` (if needed)

**Step 1: Check for framer-motion**

Run:
```bash
cd services/frontend
npm list framer-motion
```

Expected: Shows installed version or "not found"

**Step 2: Check for Radix icons**

Run:
```bash
npm list @radix-ui/react-icons
```

Expected: Shows installed version or "not found"

**Step 3: Install missing dependencies (if needed)**

If either is missing, run:
```bash
npm install framer-motion @radix-ui/react-icons
```

**Step 4: Commit if packages were installed**

```bash
git add package.json package-lock.json
git commit -m "feat: install framer-motion and @radix-ui/react-icons"
```

---

## Phase 2: Utilities & Hooks Layer

### Task 2.1: Create Formatters Utility

**Context:** Shared formatting functions to prevent duplication across components.

**Files:**
- Create: `services/frontend/src/utils/formatters.ts`

**Step 1: Create formatters.ts**

Create file `services/frontend/src/utils/formatters.ts`:

```typescript
/**
 * Shared formatting utilities for dates, file sizes, and status badges.
 */

/**
 * Format a date string with optional time.
 */
export function formatDate(dateString: string, includeTime = false): string {
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...(includeTime && { hour: '2-digit', minute: '2-digit' })
  };
  return new Date(dateString).toLocaleString('en-US', options);
}

/**
 * Format file size in bytes to human-readable format.
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

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

**Step 2: Verify file created**

Run: `cat src/utils/formatters.ts | head -20`

Expected: Shows the formatters code

**Step 3: Commit**

```bash
git add src/utils/formatters.ts
git commit -m "feat: add shared formatting utilities"
```

---

### Task 2.2: Create useDebounce Hook

**Context:** Generic debounce hook to delay value updates and reduce API calls.

**Files:**
- Create: `services/frontend/src/hooks/useDebounce.ts`

**Step 1: Create useDebounce.ts**

Create file `services/frontend/src/hooks/useDebounce.ts`:

```typescript
import { useEffect, useState } from 'react';

/**
 * Debounce a value - only updates after specified delay.
 *
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds (default 300ms)
 * @returns Debounced value
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

**Step 2: Verify file created**

Run: `cat src/hooks/useDebounce.ts`

Expected: Shows the hook code

**Step 3: Commit**

```bash
git add src/hooks/useDebounce.ts
git commit -m "feat: add useDebounce hook for value debouncing"
```

---

### Task 2.3: Create useSearchWithDebounce Hook

**Context:** Combines debouncing with React Query for seamless search.

**Files:**
- Create: `services/frontend/src/hooks/useSearchWithDebounce.ts`

**Step 1: Create useSearchWithDebounce.ts**

Create file `services/frontend/src/hooks/useSearchWithDebounce.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { useDebounce } from './useDebounce';
import { api } from '../services/api';

/**
 * Search with automatic debouncing (300ms).
 * Only triggers search when query length > 0.
 *
 * @param query - Search query string
 * @param limit - Maximum number of results (default 20)
 * @returns React Query result with search data
 */
export function useSearchWithDebounce(query: string, limit: number = 20) {
  const debouncedQuery = useDebounce(query, 300);

  return useQuery({
    queryKey: ['search', debouncedQuery, limit],
    queryFn: () => api.search({ query: debouncedQuery, limit }),
    enabled: debouncedQuery.length > 0,
    staleTime: 10000, // Results fresh for 10 seconds
  });
}
```

**Step 2: Verify file created**

Run: `cat src/hooks/useSearchWithDebounce.ts`

Expected: Shows the hook code

**Step 3: Commit**

```bash
git add src/hooks/useSearchWithDebounce.ts
git commit -m "feat: add useSearchWithDebounce hook for optimized queries"
```

---

## Phase 3: Component Layer

### Task 3.1: Create EnhancedSearchBar Component

**Context:** Modern search bar with keyboard shortcuts and glassmorphism.

**Files:**
- Create: `services/frontend/src/components/search/EnhancedSearchBar.tsx`

**Step 1: Create EnhancedSearchBar.tsx**

Create file `services/frontend/src/components/search/EnhancedSearchBar.tsx`:

```typescript
import React, { useEffect, useRef } from 'react';
import { MagnifyingGlassIcon } from '@radix-ui/react-icons';

interface EnhancedSearchBarProps {
  value: string;
  onChange: (value: string) => void;
  autoFocus?: boolean;
  placeholder?: string;
}

/**
 * Enhanced SearchBar component with keyboard shortcuts and modern design.
 *
 * Features:
 * - Press "/" to focus from anywhere
 * - Press "Escape" to clear and blur
 * - Glassmorphism styling with backdrop-blur
 * - Keyboard hint badge
 */
export const EnhancedSearchBar: React.FC<EnhancedSearchBarProps> = ({
  value,
  onChange,
  autoFocus = false,
  placeholder = 'Search documents...'
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Focus search on "/" key
      if (e.key === '/' && document.activeElement !== inputRef.current) {
        e.preventDefault();
        inputRef.current?.focus();
      }

      // Clear on Escape
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        onChange('');
        inputRef.current?.blur();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onChange]);

  return (
    <div className="relative w-full max-w-3xl mx-auto">
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-6 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className="
            w-full pl-14 pr-20 py-4 text-lg
            bg-white/70 backdrop-blur-md
            border border-gray-200/50
            rounded-full shadow-lg
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
            transition-all duration-200
            placeholder:text-gray-400
          "
        />
        <kbd className="
          absolute right-6 top-1/2 -translate-y-1/2
          px-2 py-1 text-xs font-medium
          bg-gray-100 text-gray-600
          border border-gray-200
          rounded
          pointer-events-none
        ">
          /
        </kbd>
      </div>
    </div>
  );
};
```

**Step 2: Verify file created**

Run: `cat src/components/search/EnhancedSearchBar.tsx | head -30`

Expected: Shows component code

**Step 3: Commit**

```bash
git add src/components/search/EnhancedSearchBar.tsx
git commit -m "feat: create EnhancedSearchBar with keyboard shortcuts"
```

---

### Task 3.2: Create UploadModal Component (Part 1 - Structure)

**Context:** Modern upload modal with drag-and-drop using shadcn/ui Dialog.

**Files:**
- Create: `services/frontend/src/components/upload/UploadModal.tsx`

**Step 1: Create upload directory**

Run:
```bash
mkdir -p services/frontend/src/components/upload
```

**Step 2: Create UploadModal.tsx with basic structure**

Create file `services/frontend/src/components/upload/UploadModal.tsx`:

```typescript
import React, { useState } from 'react';
import { useUploadDocument } from '../../hooks/useDocuments';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { cn } from '../../lib/utils';

interface UploadModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: (documentId: string) => void;
}

/**
 * UploadModal component with drag-and-drop file upload.
 *
 * Features:
 * - Drag and drop file upload
 * - File validation (.pdf, .docx, .txt)
 * - Auto-fill title from filename
 * - shadcn/ui Dialog component
 */
export const UploadModal: React.FC<UploadModalProps> = ({
  open,
  onClose,
  onSuccess
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const uploadDocument = useUploadDocument();

  // Drag handlers will be added in next step
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragIn = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragOut = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const validFile = files.find(f =>
      ['.pdf', '.docx', '.txt'].some(ext => f.name.toLowerCase().endsWith(ext))
    );

    if (validFile) {
      setFile(validFile);
      if (!title) {
        setTitle(validFile.name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      if (!title) {
        setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file || !title) {
      return;
    }

    try {
      const result = await uploadDocument.mutateAsync({
        file,
        title,
        description: description || undefined
      });

      onSuccess?.(result.id);
      onClose();

      // Reset form
      setFile(null);
      setTitle('');
      setDescription('');
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Dropzone will be added in next step */}
          <div>Dropzone placeholder</div>

          <div className="flex justify-end space-x-3">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={uploadDocument.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!file || !title || uploadDocument.isPending}
            >
              {uploadDocument.isPending ? 'Uploading...' : 'Upload'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
```

**Step 3: Verify file created**

Run: `cat src/components/upload/UploadModal.tsx | head -40`

Expected: Shows component structure

**Step 4: Commit**

```bash
git add src/components/upload/
git commit -m "feat: create UploadModal structure with shadcn/ui Dialog"
```

---

### Task 3.3: Complete UploadModal Component (Part 2 - Dropzone)

**Context:** Add the drag-and-drop dropzone UI.

**Files:**
- Modify: `services/frontend/src/components/upload/UploadModal.tsx:116-117`

**Step 1: Replace dropzone placeholder**

Edit `services/frontend/src/components/upload/UploadModal.tsx`:

Find line ~116:
```typescript
          {/* Dropzone will be added in next step */}
          <div>Dropzone placeholder</div>
```

Replace with:
```typescript
          <div
            onDragEnter={handleDragIn}
            onDragLeave={handleDragOut}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={cn(
              "border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
              isDragging
                ? "border-primary-500 bg-primary-50"
                : "border-gray-300 hover:border-gray-400"
            )}
          >
            <input
              type="file"
              id="file-upload"
              className="sr-only"
              accept=".pdf,.docx,.txt"
              onChange={handleFileInput}
            />

            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="space-y-2">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <div className="text-sm text-gray-600">
                  <span className="font-medium text-primary-600">Click to upload</span>
                  {' or drag and drop'}
                </div>
                <p className="text-xs text-gray-500">
                  PDF, DOCX, or TXT (up to 100MB)
                </p>
                {file && (
                  <p className="text-sm font-medium text-gray-900 mt-2">
                    Selected: {file.name}
                  </p>
                )}
              </div>
            </label>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Title *</label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter document title"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Description (optional)</label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter document description"
              rows={3}
            />
          </div>
```

**Step 2: Verify modification**

Run: `grep -A 10 "onDragEnter" src/components/upload/UploadModal.tsx`

Expected: Shows the dropzone code

**Step 3: Commit**

```bash
git add src/components/upload/UploadModal.tsx
git commit -m "feat: add drag-and-drop dropzone to UploadModal"
```

---

## Phase 4: Update Existing Components

### Task 4.1: Update DocumentCard to Use Formatters

**Context:** Remove inline formatting functions and use shared utilities.

**Files:**
- Modify: `services/frontend/src/components/documents/DocumentCard.tsx:1-10`
- Modify: `services/frontend/src/components/documents/DocumentCard.tsx:26-90`

**Step 1: Add formatters import**

Edit `services/frontend/src/components/documents/DocumentCard.tsx`:

At the top, add import:
```typescript
import { formatDate, formatFileSize, getStatusColor } from '../../utils/formatters';
```

**Step 2: Remove inline formatting functions**

Find and remove these functions (around lines 26-57):
- `formatDate` function
- `formatFileSize` function
- `getStatusBadge` function (keep only the JSX part)

**Step 3: Update getStatusBadge to use utility**

Replace the `getStatusBadge` function with:
```typescript
const getStatusBadge = (status: string) => {
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(status as any)}`}>
      {status}
    </span>
  );
};
```

**Step 4: Verify changes**

Run: `grep -n "formatDate\|formatFileSize" src/components/documents/DocumentCard.tsx`

Expected: Should only show import line, not function definitions

**Step 5: Commit**

```bash
git add src/components/documents/DocumentCard.tsx
git commit -m "refactor: use shared formatters in DocumentCard"
```

---

### Task 4.2: Update DocumentDetailPage to Use Formatters

**Context:** Same refactor as DocumentCard - use shared utilities.

**Files:**
- Modify: `services/frontend/src/pages/DocumentDetailPage.tsx:1-15`
- Modify: `services/frontend/src/pages/DocumentDetailPage.tsx:57-90`

**Step 1: Add formatters import**

Edit `services/frontend/src/pages/DocumentDetailPage.tsx`:

Add import:
```typescript
import { formatDate, formatFileSize, getStatusColor } from '../utils/formatters';
```

**Step 2: Remove inline formatting functions**

Find and remove these functions (around lines 57-90):
- `formatDate` function
- `formatFileSize` function
- `getStatusBadge` function

**Step 3: Update getStatusBadge to use utility**

Replace `getStatusBadge` with:
```typescript
const getStatusBadge = (status: string) => {
  return (
    <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(status as any)}`}>
      {status}
    </span>
  );
};
```

**Step 4: Verify changes**

Run: `grep -c "function format" src/pages/DocumentDetailPage.tsx`

Expected: 0 (no function definitions, only imports)

**Step 5: Commit**

```bash
git add src/pages/DocumentDetailPage.tsx
git commit -m "refactor: use shared formatters in DocumentDetailPage"
```

---

## Phase 5: Main Page Layer

### Task 5.1: Create MainPage Component

**Context:** Single-page app with search-centric design, replacing HomePage/SearchPage/DocumentsPage.

**Files:**
- Create: `services/frontend/src/pages/MainPage.tsx`

**Step 1: Create MainPage.tsx**

Create file `services/frontend/src/pages/MainPage.tsx`:

```typescript
import React, { useState } from 'react';
import { EnhancedSearchBar } from '../components/search/EnhancedSearchBar';
import { UploadModal } from '../components/upload/UploadModal';
import { Button } from '../components/ui/button';
import { useSearchWithDebounce } from '../hooks/useSearchWithDebounce';
import { useDocuments } from '../hooks/useDocuments';
import { DocumentCard } from '../components/documents/DocumentCard';
import { SearchResults } from '../components/search/SearchResults';
import { motion, AnimatePresence } from 'framer-motion';
import { PlusIcon } from '@radix-ui/react-icons';

/**
 * MainPage - Single-page search-centric application.
 *
 * Features:
 * - Prominent search bar at center
 * - Debounced search with automatic results
 * - Document grid when not searching
 * - Upload modal
 * - Smooth animations
 */
export const MainPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [uploadOpen, setUploadOpen] = useState(false);

  const searchResults = useSearchWithDebounce(searchQuery);
  const documents = useDocuments(1, 20);

  const showSearch = searchQuery.length > 0;
  const dataToDisplay = showSearch ? searchResults : documents;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <svg
                className="h-8 w-8 text-primary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <span className="text-xl font-bold text-gray-900">RAAS</span>
            </div>

            <Button onClick={() => setUploadOpen(true)} size="sm">
              <PlusIcon className="mr-2 h-4 w-4" />
              Upload
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Search */}
      <main className="container mx-auto px-4">
        <div className="py-12">
          <EnhancedSearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            autoFocus
          />
        </div>

        {/* Results or Documents */}
        <div className="pb-12">
          {dataToDisplay.isLoading && (
            <div className="text-center py-12">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent" />
              <p className="mt-4 text-gray-600">
                {showSearch ? 'Searching...' : 'Loading documents...'}
              </p>
            </div>
          )}

          {dataToDisplay.error && (
            <div className="text-center py-12">
              <p className="text-red-600">
                Error: {dataToDisplay.error.message}
              </p>
            </div>
          )}

          {dataToDisplay.isSuccess && (
            <div className="space-y-4">
              {showSearch ? (
                // Search Results
                <>
                  <p className="text-sm text-gray-600">
                    {searchResults.data.total_results} results for "{searchQuery}"
                  </p>
                  <SearchResults results={searchResults.data.results} query={searchQuery} />
                </>
              ) : (
                // Document Grid
                <>
                  <p className="text-sm text-gray-600">
                    {documents.data.total} documents
                  </p>
                  {documents.data.documents.length === 0 ? (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="text-center py-12"
                    >
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        No documents yet
                      </h3>
                      <p className="text-gray-600 mb-6">
                        Upload your first document to get started
                      </p>
                      <Button onClick={() => setUploadOpen(true)}>
                        <PlusIcon className="mr-2 h-4 w-4" />
                        Upload Document
                      </Button>
                    </motion.div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {documents.data.documents.map((doc) => (
                        <DocumentCard key={doc.id} document={doc} />
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Upload Modal */}
      <UploadModal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onSuccess={(id) => {
          console.log('Upload successful:', id);
        }}
      />
    </div>
  );
};
```

**Step 2: Verify file created**

Run: `cat src/pages/MainPage.tsx | head -50`

Expected: Shows MainPage component

**Step 3: Commit**

```bash
git add src/pages/MainPage.tsx
git commit -m "feat: create search-centric MainPage component"
```

---

## Phase 6: Routing Layer

### Task 6.1: Update App.tsx Routing

**Context:** Remove Layout wrapper and old routes, use only MainPage and DocumentDetailPage.

**Files:**
- Modify: `services/frontend/src/App.tsx`

**Step 1: Update imports in App.tsx**

Edit `services/frontend/src/App.tsx`:

Replace imports:
```typescript
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MainPage } from './pages/MainPage';
import { DocumentDetailPage } from './pages/DocumentDetailPage';
```

**Step 2: Remove Layout wrapper and old routes**

Replace the entire App component with:
```typescript
// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5000,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<MainPage />} />
          <Route path="/documents/:id" element={<DocumentDetailPage />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
```

**Step 3: Verify routes**

Run: `grep -A 5 "<Routes>" src/App.tsx`

Expected: Shows only 2 routes (MainPage and DocumentDetailPage)

**Step 4: Test TypeScript compilation**

Run:
```bash
npx tsc --noEmit
```

Expected: May have pre-existing errors but no NEW errors about missing components

**Step 5: Commit**

```bash
git add src/App.tsx
git commit -m "refactor: update routing to use MainPage, remove Layout wrapper"
```

---

## Phase 7: Cleanup Layer

### Task 7.1: Delete Old Pages

**Context:** Remove obsolete page components replaced by MainPage.

**Files:**
- Delete: `services/frontend/src/pages/HomePage.tsx`
- Delete: `services/frontend/src/pages/SearchPage.tsx`
- Delete: `services/frontend/src/pages/DocumentsPage.tsx`

**Step 1: Delete old page files**

Run:
```bash
cd services/frontend
rm src/pages/HomePage.tsx
rm src/pages/SearchPage.tsx
rm src/pages/DocumentsPage.tsx
```

**Step 2: Verify files deleted**

Run: `ls src/pages/`

Expected output:
```
DocumentDetailPage.tsx
MainPage.tsx
```

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: remove obsolete pages (HomePage, SearchPage, DocumentsPage)"
```

---

### Task 7.2: Delete Old Layout Components

**Context:** Remove Layout, Header, Footer replaced by MainPage's self-contained header.

**Files:**
- Delete: `services/frontend/src/components/layout/Layout.tsx`
- Delete: `services/frontend/src/components/layout/Header.tsx`
- Delete: `services/frontend/src/components/layout/Footer.tsx`

**Step 1: Delete layout files**

Run:
```bash
cd services/frontend
rm src/components/layout/Layout.tsx
rm src/components/layout/Header.tsx
rm src/components/layout/Footer.tsx
rmdir src/components/layout
```

**Step 2: Verify directory removed**

Run: `ls src/components/ | grep layout`

Expected: No output (directory deleted)

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: remove old Layout components"
```

---

### Task 7.3: Delete Old Common Components

**Context:** Remove custom components replaced by shadcn/ui.

**Files:**
- Delete: `services/frontend/src/components/common/Button.tsx`
- Delete: `services/frontend/src/components/common/Card.tsx`
- Delete: `services/frontend/src/components/common/Input.tsx`
- Delete: `services/frontend/src/components/common/Modal.tsx`
- Delete: `services/frontend/src/components/common/Spinner.tsx`

**Step 1: Delete common components**

Run:
```bash
cd services/frontend
rm src/components/common/Button.tsx
rm src/components/common/Card.tsx
rm src/components/common/Input.tsx
rm src/components/common/Modal.tsx
rm src/components/common/Spinner.tsx
rmdir src/components/common
```

**Step 2: Verify directory removed**

Run: `ls src/components/ | grep common`

Expected: No output

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: remove old common components (replaced by shadcn/ui)"
```

---

### Task 7.4: Delete Old SearchBar Component

**Context:** Remove old SearchBar replaced by EnhancedSearchBar.

**Files:**
- Delete: `services/frontend/src/components/search/SearchBar.tsx`

**Step 1: Delete old SearchBar**

Run:
```bash
cd services/frontend
rm src/components/search/SearchBar.tsx
```

**Step 2: Verify SearchBar tests still exist**

Run: `ls src/components/__tests__/ | grep SearchBar`

Expected: `SearchBar.test.tsx` still exists (will need updating)

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: remove old SearchBar component"
```

---

### Task 7.5: Delete Old UploadModal Component

**Context:** Remove old UploadModal at root level, replaced by upload/UploadModal.tsx.

**Files:**
- Delete: `services/frontend/src/components/UploadModal.tsx`

**Step 1: Delete old UploadModal**

Run:
```bash
cd services/frontend
rm src/components/UploadModal.tsx
```

**Step 2: Verify new UploadModal exists**

Run: `ls src/components/upload/`

Expected: `UploadModal.tsx`

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: remove old UploadModal component"
```

---

### Task 7.6: Delete Old Formatting Utility

**Context:** Remove formatting.ts replaced by formatters.ts.

**Files:**
- Delete: `services/frontend/src/utils/formatting.ts`

**Step 1: Verify no imports of formatting.ts**

Run:
```bash
cd services/frontend
grep -r "from.*formatting" src/ --include="*.ts" --include="*.tsx" || echo "No imports found"
```

Expected: "No imports found"

**Step 2: Delete formatting.ts**

Run:
```bash
rm src/utils/formatting.ts
```

**Step 3: Verify formatters.ts exists**

Run: `ls src/utils/`

Expected: `formatters.ts` present

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: remove old formatting.ts utility"
```

---

### Task 7.7: Check for Unused DocumentList Component

**Context:** Verify if DocumentList is still used or can be deleted.

**Files:**
- Possibly delete: `services/frontend/src/components/documents/DocumentList.tsx`

**Step 1: Search for DocumentList imports**

Run:
```bash
cd services/frontend
grep -r "DocumentList" src/ --include="*.ts" --include="*.tsx"
```

**Step 2: If no imports found, delete DocumentList**

If output shows only the component file itself:
```bash
rm src/components/documents/DocumentList.tsx
```

**Step 3: If deleted, commit**

```bash
git add -A
git commit -m "refactor: remove unused DocumentList component"
```

If still in use, skip this task.

---

## Phase 8: Verification Layer

### Task 8.1: Run TypeScript Type Check

**Context:** Ensure no type errors from refactoring.

**Step 1: Run type check**

Run:
```bash
cd services/frontend
npx tsc --noEmit
```

Expected: Only pre-existing errors (test setup, logger), no new errors

**Step 2: If new errors appear, fix them**

Review errors and fix any issues with:
- Missing imports
- Type mismatches
- Undefined components

**Step 3: Document result**

Note: TypeScript compilation passes with only pre-existing errors

---

### Task 8.2: Run Tests

**Context:** Verify all tests still pass after refactoring.

**Step 1: Run test suite**

Run:
```bash
cd services/frontend
npm test -- --run
```

Expected: All tests pass (or same baseline failures as before)

**Step 2: If tests fail, investigate**

Common issues:
- Missing component imports in tests
- Changed component APIs
- Updated props

Fix failing tests before proceeding.

**Step 3: Document test results**

Note: Tests passing (X/X tests)

---

### Task 8.3: Run Development Server

**Context:** Verify app runs and basic functionality works.

**Step 1: Start dev server**

Run:
```bash
cd services/frontend
npm run dev
```

**Step 2: Manual testing checklist**

Open http://localhost:3000 and verify:
- [ ] MainPage loads without errors
- [ ] Search bar has focus on load
- [ ] Pressing "/" focuses search
- [ ] Pressing Escape clears search
- [ ] Document grid displays (if documents exist)
- [ ] Upload button opens modal
- [ ] Upload modal has drag-drop zone
- [ ] Clicking document card navigates to detail page
- [ ] Browser back button returns to MainPage

**Step 3: Check browser console**

Expected: No errors in console

**Step 4: Stop dev server**

Press Ctrl+C

---

### Task 8.4: Build for Production

**Context:** Ensure production build succeeds.

**Step 1: Run build**

Run:
```bash
cd services/frontend
npm run build
```

Expected: Build completes successfully

**Step 2: Check build output**

Run: `ls dist/`

Expected: Shows built files (index.html, assets/, etc.)

**Step 3: Test production build**

Run:
```bash
npm run preview
```

Open http://localhost:4173 and verify app works

**Step 4: Document build success**

Note: Production build successful, app functional

---

## Summary

**Total Tasks:** 33
**Estimated Time:** 4-6 hours

**What Was Built:**
- ✅ shadcn/ui component library installed
- ✅ Shared utilities (formatters, useDebounce, useSearchWithDebounce)
- ✅ EnhancedSearchBar with keyboard shortcuts
- ✅ Modern UploadModal with drag-and-drop
- ✅ Single-page MainPage component
- ✅ Removed 15+ obsolete files
- ✅ Only 2 routes: / and /documents/:id

**Success Criteria:**
- ✅ TypeScript compilation passes
- ✅ All tests pass
- ✅ Build succeeds
- ✅ Manual testing checklist complete
- ✅ No console errors
- ✅ Modern search-centric UX

**Files Created:** 8
**Files Modified:** 3
**Files Deleted:** 15+

**Final Structure:**
```
src/
├── components/
│   ├── documents/
│   │   ├── DocumentCard.tsx (updated)
│   │   └── SearchResults.tsx
│   ├── search/
│   │   └── EnhancedSearchBar.tsx (new)
│   ├── upload/
│   │   └── UploadModal.tsx (new)
│   ├── ui/ (shadcn - new)
│   └── ErrorBoundary.tsx
├── hooks/
│   ├── useDebounce.ts (new)
│   ├── useSearchWithDebounce.ts (new)
│   └── ...
├── lib/
│   └── utils.ts (new)
├── pages/
│   ├── MainPage.tsx (new)
│   └── DocumentDetailPage.tsx (updated)
├── utils/
│   └── formatters.ts (new)
└── App.tsx (updated)
```
