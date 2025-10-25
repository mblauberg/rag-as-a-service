import { describe, it, expect } from 'vitest';
import { formatDate, formatBytes } from '../formatters';

describe('formatDate', () => {
  describe('Basic Formatting', () => {
    it('should format date without time by default', () => {
      const date = '2024-01-15T10:30:45Z';
      const result = formatDate(date);
      expect(result).toMatch(/Jan 15, 2024/);
      expect(result).not.toMatch(/10:30/);
    });

    it('should format date with time when includeTime is true', () => {
      const date = '2024-01-15T10:30:45Z';
      const result = formatDate(date, true);
      expect(result).toMatch(/Jan 15, 2024/);
      expect(result).toMatch(/\d{1,2}:\d{2}/); // Should include time
    });

    it('should format different months correctly', () => {
      const dates = [
        { input: '2024-01-01T00:00:00Z', expected: 'Jan' },
        { input: '2024-02-01T00:00:00Z', expected: 'Feb' },
        { input: '2024-03-01T00:00:00Z', expected: 'Mar' },
        { input: '2024-04-01T00:00:00Z', expected: 'Apr' },
        { input: '2024-05-01T00:00:00Z', expected: 'May' },
        { input: '2024-06-01T00:00:00Z', expected: 'Jun' },
        { input: '2024-07-01T00:00:00Z', expected: 'Jul' },
        { input: '2024-08-01T00:00:00Z', expected: 'Aug' },
        { input: '2024-09-01T00:00:00Z', expected: 'Sep' },
        { input: '2024-10-01T00:00:00Z', expected: 'Oct' },
        { input: '2024-11-01T00:00:00Z', expected: 'Nov' },
        { input: '2024-12-01T00:00:00Z', expected: 'Dec' },
      ];

      dates.forEach(({ input, expected }) => {
        expect(formatDate(input)).toContain(expected);
      });
    });

    it('should format different years correctly', () => {
      expect(formatDate('2020-01-01T00:00:00Z')).toContain('2020');
      expect(formatDate('2021-01-01T00:00:00Z')).toContain('2021');
      expect(formatDate('2025-01-01T00:00:00Z')).toContain('2025');
    });

    it('should format different days correctly', () => {
      expect(formatDate('2024-01-01T00:00:00Z')).toMatch(/Jan 1, 2024/);
      expect(formatDate('2024-01-15T00:00:00Z')).toMatch(/Jan 15, 2024/);
      expect(formatDate('2024-01-31T00:00:00Z')).toMatch(/Jan 31, 2024/);
    });
  });

  describe('Edge Cases', () => {
    it('should handle ISO 8601 format', () => {
      const result = formatDate('2024-01-15T10:30:45.123Z');
      expect(result).toMatch(/Jan 15, 2024/);
    });

    it('should handle date strings without milliseconds', () => {
      const result = formatDate('2024-01-15T10:30:45Z');
      expect(result).toMatch(/Jan 15, 2024/);
    });

    it('should handle midnight times', () => {
      const result = formatDate('2024-01-15T00:00:00Z');
      expect(result).toMatch(/Jan 15, 2024/);
    });

    it('should handle end-of-day times', () => {
      const result = formatDate('2024-01-15T12:00:00Z');
      expect(result).toMatch(/Jan 15, 2024/);
    });

    it('should handle leap year dates', () => {
      const result = formatDate('2024-02-29T12:00:00Z');
      expect(result).toMatch(/Feb 29, 2024/);
    });
  });
});

describe('formatBytes', () => {
  describe('Bytes Range', () => {
    it('should format 0 bytes', () => {
      expect(formatBytes(0)).toBe('0 B');
    });

    it('should format single byte', () => {
      expect(formatBytes(1)).toBe('1 B');
    });

    it('should format bytes under 1 KB', () => {
      expect(formatBytes(500)).toBe('500 B');
      expect(formatBytes(1023)).toBe('1023 B');
    });
  });

  describe('Kilobytes Range', () => {
    it('should format exactly 1 KB', () => {
      expect(formatBytes(1024)).toBe('1.00 KB');
    });

    it('should format kilobytes with decimals', () => {
      expect(formatBytes(1536)).toBe('1.50 KB');
      expect(formatBytes(2048)).toBe('2.00 KB');
    });

    it('should format kilobytes rounding to 2 decimals', () => {
      expect(formatBytes(1234)).toBe('1.21 KB');
      expect(formatBytes(5678)).toBe('5.54 KB');
    });

    it('should format bytes just under 1 MB', () => {
      expect(formatBytes(1024 * 1024 - 1)).toMatch(/KB$/);
    });
  });

  describe('Megabytes Range', () => {
    it('should format exactly 1 MB', () => {
      expect(formatBytes(1024 * 1024)).toBe('1.00 MB');
    });

    it('should format megabytes with decimals', () => {
      expect(formatBytes(1.5 * 1024 * 1024)).toBe('1.50 MB');
      expect(formatBytes(2 * 1024 * 1024)).toBe('2.00 MB');
    });

    it('should format large megabytes', () => {
      expect(formatBytes(50 * 1024 * 1024)).toBe('50.00 MB');
      expect(formatBytes(100 * 1024 * 1024)).toBe('100.00 MB');
    });

    it('should format megabytes rounding to 2 decimals', () => {
      expect(formatBytes(1234567)).toBe('1.18 MB');
      expect(formatBytes(10485760)).toBe('10.00 MB');
    });
  });

  describe('Boundary Cases', () => {
    it('should handle boundary at 1 KB', () => {
      expect(formatBytes(1023)).toBe('1023 B');
      expect(formatBytes(1024)).toBe('1.00 KB');
      expect(formatBytes(1025)).toMatch(/KB$/);
    });

    it('should handle boundary at 1 MB', () => {
      expect(formatBytes(1024 * 1024 - 1)).toMatch(/KB$/);
      expect(formatBytes(1024 * 1024)).toBe('1.00 MB');
      expect(formatBytes(1024 * 1024 + 1)).toMatch(/MB$/);
    });
  });
});

describe('Integration Tests', () => {
  it('should work together for document metadata display', () => {
    const fileSize = 1024 * 1024;
    const createdAt = '2024-01-15T10:30:00Z';

    const formattedSize = formatBytes(fileSize);
    const formattedDate = formatDate(createdAt);

    expect(formattedSize).toBe('1.00 MB');
    expect(formattedDate).toMatch(/Jan 15, 2024/);
  });
});
