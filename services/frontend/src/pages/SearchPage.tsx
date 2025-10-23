import React from 'react';
import { useSearch } from '../hooks/useSearch';
import { SearchBar } from '../components/search/SearchBar';
import { SearchResults } from '../components/search/SearchResults';
import { Spinner } from '../components/common/Spinner';

export const SearchPage: React.FC = () => {
  const search = useSearch();

  const handleSearch = (query: string) => {
    search.mutate({ query, limit: 10 });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Semantic Search</h1>
        <p className="text-gray-600">
          Search across all your documents using natural language. We'll find the most relevant content based on meaning, not just keywords.
        </p>
      </div>

      <SearchBar onSearch={handleSearch} isLoading={search.isPending} />

      {search.isPending && (
        <div className="flex justify-center items-center py-12">
          <Spinner size="lg" />
        </div>
      )}

      {search.error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">
            Search failed: {search.error.message}
          </p>
        </div>
      )}

      {search.data && (
        <SearchResults results={search.data.results} query={search.data.query} />
      )}

      {!search.data && !search.isPending && !search.error && (
        <div className="text-center py-12">
          <svg
            className="mx-auto h-16 w-16 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">Start searching</h3>
          <p className="mt-2 text-gray-600">
            Enter a query above to search through your documents
          </p>
        </div>
      )}
    </div>
  );
};
