import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility function to merge Tailwind CSS classes with proper conflict resolution.
 * Combines clsx for conditional classes and tailwind-merge for Tailwind-specific merging.
 *
 * @param inputs - Class values to merge (strings, objects, arrays)
 * @returns Merged class string with resolved Tailwind conflicts
 *
 * @example
 * cn('px-2 py-1', 'px-4') // Returns 'py-1 px-4' (px-4 overrides px-2)
 * cn('text-red-500', condition && 'text-blue-500') // Conditional classes
 * cn({ 'bg-blue-500': isActive, 'bg-gray-500': !isActive }) // Object syntax
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
