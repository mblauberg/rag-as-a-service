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
 * Format bytes to human-readable file size.
 */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

/**
 * Capitalize first letter of status string.
 */
export function formatStatus(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
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
