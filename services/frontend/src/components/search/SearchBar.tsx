import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
}

/**
 * Enhanced SearchBar component with modern design
 * Features:
 * - Modern shadcn/ui inspired styling
 * - Lucide-react icons
 * - Loading state with spinner
 * - Accessible with ARIA labels
 * - Responsive design
 */
export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  isLoading = false,
  placeholder = 'Search documents...',
  className,
}) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  };

  return (
    <form onSubmit={handleSubmit} className={cn('w-full', className)}>
      <div className="relative group">
        {/* Search Icon */}
        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary-600 transition-colors">
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
          ) : (
            <Search className="w-5 h-5" aria-hidden="true" />
          )}
        </div>

        {/* Input Field */}
        <input
          type="text"
          value={query}
          onChange={handleChange}
          placeholder={placeholder}
          disabled={isLoading}
          aria-label="Search query"
          aria-describedby={isLoading ? 'search-loading' : undefined}
          className={cn(
            'w-full h-12 pl-12 pr-4 text-base',
            'bg-white border-2 border-gray-200',
            'rounded-xl shadow-sm',
            'transition-all duration-200',
            'placeholder:text-gray-400',
            'hover:border-gray-300 hover:shadow-md',
            'focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-100 focus:shadow-lg',
            'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
            'text-gray-900'
          )}
        />

        {/* Screen reader loading announcement */}
        {isLoading && (
          <span id="search-loading" className="sr-only">
            Searching...
          </span>
        )}
      </div>

      {/* Search hint text */}
      <p className="mt-2 text-sm text-gray-500 text-center">
        Press Enter to search or type to begin
      </p>
    </form>
  );
};
