import React from 'react';
import { motion } from 'framer-motion';
import type { SearchResult, SearchResponse } from '@/types';
import { SummaryDisplay } from './SummaryDisplay';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
  searchResponse?: SearchResponse;
  onDocumentClick?: (documentId: string) => void;
}

/**
 * SearchResults - Displays search results with optional summary.
 * Click result to open document detail modal.
 */
export const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  query,
  searchResponse,
  onDocumentClick,
}) => {
  const handleResultClick = (documentId: string) => {
    if (onDocumentClick) {
      onDocumentClick(documentId);
    }
  };

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
        <h3 className="mt-2 text-sm font-medium text-foreground">No results found</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Try adjusting your search query or search for different terms.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary if present */}
      {searchResponse?.summary && searchResponse?.model_used && (
        <SummaryDisplay
          summary={searchResponse.summary}
          modelUsed={searchResponse.model_used}
        />
      )}

      {/* Results */}
      <div className="space-y-3">
        {results.map((result, index) => (
          <motion.div
            key={`${result.document_id}-${result.chunk_index}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleResultClick(result.document_id)}
            >
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base">{result.document_title}</CardTitle>
                  <Badge variant="secondary">
                    {(result.score * 100).toFixed(0)}% match
                  </Badge>
                </div>
              </CardHeader>

              <CardContent>
                <p className="text-sm text-muted-foreground line-clamp-3">
                  {highlightText(result.chunk_text, query)}
                </p>
                <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                  <span>Chunk {result.chunk_index + 1}</span>
                  {result.section_title && (
                    <>
                      <span>•</span>
                      <span>{result.section_title}</span>
                    </>
                  )}
                  {result.page_number && (
                    <>
                      <span>•</span>
                      <span>Page {result.page_number}</span>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
