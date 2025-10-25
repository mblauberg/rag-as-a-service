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
      // Create a mock file with size > 100MB
      const file = new File(['content'], 'large.pdf', { type: 'application/pdf' });
      Object.defineProperty(file, 'size', { value: 101 * 1024 * 1024 });
      const result = validateUploadFile(file);
      expect(result.valid).toBe(false);
      expect(result.error).toBe('File size must be less than 100MB');
    });

    it('should accept file at size limit', () => {
      // Create a mock file with size just under 100MB
      const file = new File(['content'], 'medium.pdf', { type: 'application/pdf' });
      Object.defineProperty(file, 'size', { value: 50 * 1024 * 1024 });
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
