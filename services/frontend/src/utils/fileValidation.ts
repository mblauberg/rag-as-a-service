/**
 * File validation utilities for document uploads.
 * Centralizes validation logic to avoid duplication.
 */

export const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md', '.markdown', '.csv'] as const;
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
      error: 'Please upload a PDF, DOCX, TXT, Markdown (.md), or CSV file'
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
