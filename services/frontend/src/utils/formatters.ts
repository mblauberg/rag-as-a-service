/**
 * Shared formatting utilities for dates, file sizes, and status badges.
 */

import type { FileIconType } from '@/components/ui/file-icon';

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
 * Format bytes to human-readable file size.
 */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

/**
 * Get file type icon based on file extension.
 */
export const getFileTypeIcon = (filename: string): FileIconType => {
  const ext = filename.split('.').pop()?.toLowerCase();

  const iconMap: Record<string, FileIconType> = {
    pdf: 'pdf',
    docx: 'docx',
    doc: 'doc',
    txt: 'txt',
    csv: 'csv',
    md: 'md',
    markdown: 'markdown'
  };

  return iconMap[ext || ''] || 'default';
};

/**
 * Get file type color classes based on file extension.
 */
export const getFileTypeColor = (filename: string): string => {
  const ext = filename.split('.').pop()?.toLowerCase();

  const colorMap: Record<string, string> = {
    pdf: 'text-red-600 bg-red-50',
    docx: 'text-blue-600 bg-blue-50',
    doc: 'text-blue-600 bg-blue-50',
    txt: 'text-gray-600 bg-gray-50',
    csv: 'text-green-600 bg-green-50',
    md: 'text-purple-600 bg-purple-50',
    markdown: 'text-purple-600 bg-purple-50'
  };

  return colorMap[ext || ''] || 'text-gray-600 bg-gray-50';
};
