/**
 * Utility functions for formatting data in the frontend.
 * Provides consistent formatting for bytes, dates, and status values.
 */

/**
 * Formats a number of bytes into a human-readable string.
 *
 * @param bytes - The number of bytes to format
 * @returns A formatted string with appropriate unit (B, KB, or MB)
 *
 * @example
 * formatBytes(500) // "500 B"
 * formatBytes(2048) // "2.00 KB"
 * formatBytes(5242880) // "5.00 MB"
 */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(2)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

/**
 * Formats an ISO date string into a localized human-readable format.
 *
 * @param date - ISO date string to format
 * @param includeTime - Whether to include time in the output (default: false)
 * @returns A formatted date string
 *
 * @example
 * formatDate("2025-10-24T10:30:00Z") // "Oct 24, 2025"
 * formatDate("2025-10-24T10:30:00Z", true) // "Oct 24, 2025, 10:30 AM"
 */
export function formatDate(date: string, includeTime: boolean = false): string {
  const dateObj = new Date(date);

  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  };

  if (includeTime) {
    options.hour = '2-digit';
    options.minute = '2-digit';
  }

  return dateObj.toLocaleString('en-US', options);
}

/**
 * Formats a status string into a user-friendly capitalized format.
 *
 * @param status - The status string to format
 * @returns A capitalized status string
 *
 * @example
 * formatStatus("pending") // "Pending"
 * formatStatus("processing") // "Processing"
 * formatStatus("completed") // "Completed"
 */
export function formatStatus(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

/**
 * Type definition for status colors mapping.
 */
type StatusColor = 'bg-yellow-100 text-yellow-800' | 'bg-blue-100 text-blue-800' | 'bg-green-100 text-green-800' | 'bg-red-100 text-red-800' | 'bg-gray-100 text-gray-800';

/**
 * Gets the Tailwind CSS classes for a status badge based on the status value.
 *
 * @param status - The status to get colors for
 * @returns Tailwind CSS class string for the status badge
 *
 * @example
 * getStatusColor("pending") // "bg-yellow-100 text-yellow-800"
 * getStatusColor("completed") // "bg-green-100 text-green-800"
 */
export function getStatusColor(status: string): StatusColor {
  const statusColors: Record<string, StatusColor> = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  return statusColors[status] || 'bg-gray-100 text-gray-800';
}
