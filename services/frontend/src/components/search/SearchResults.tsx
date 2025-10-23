import React from 'react';
import { Link } from 'react-router-dom';
import type { SearchResult } from '../../types';
import { Card } from '../common/Card';

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
}

export const SearchResults: React.FC<SearchResultsProps> = ({ results, query }) => {
  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text;

    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return (
      <>
        {parts.map((part, index) =>
          part.toLowerCase() === query.toLowerCase() ? (
            <mark key={index} className="bg-yellow-200 font-semibold">
              {part}
            </mark>
          ) : (
            <span key={index}>{part}</span>
          )
        )}
      </>
    );
  };

  if (results.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
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
        <h3 className="mt-2 text-sm font-medium text-gray-900">No results found</h3>
        <p className="mt-1 text-sm text-gray-500">
          Try adjusting your search query or search for different terms.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">
        Found {results.length} {results.length === 1 ? 'result' : 'results'}
      </h3>
      {results.map((result) => (
        <Card key={`${result.document_id}-${result.chunk_index}`}>
          <div className="space-y-3">
            <div className="flex items-start justify-between">
              <Link
                to={`/documents/${result.document_id}`}
                className="text-lg font-semibold text-primary-600 hover:text-primary-800"
              >
                {result.document_title}
              </Link>
              <span className="ml-2 px-2 py-1 text-xs font-medium bg-primary-100 text-primary-800 rounded-full">
                {(result.score * 100).toFixed(1)}% match
              </span>
            </div>
            {result.section_title && (
              <div className="text-sm text-blue-600 mb-2">
                📍 {result.section_title}
              </div>
            )}
            {result.page_number && (
              <div className="text-sm text-gray-500 mb-2">
                Page {result.page_number}
              </div>
            )}
            <p className="text-gray-700 leading-relaxed">
              {highlightText(result.chunk_text, query)}
            </p>
            <div className="flex items-center text-sm text-gray-500">
              <svg
                className="w-4 h-4 mr-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"
                />
              </svg>
              Chunk {result.chunk_index + 1}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};
