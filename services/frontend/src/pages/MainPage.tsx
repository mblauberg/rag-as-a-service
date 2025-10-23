import React, { useState } from 'react';
import { EnhancedSearchBar } from '../components/search/EnhancedSearchBar';
import { UploadModal } from '../components/upload/UploadModal';
import { Button } from '../components/ui/button';
import { useSearchWithDebounce } from '../hooks/useSearchWithDebounce';
import { useDocuments } from '../hooks/useDocuments';
import { DocumentCard } from '../components/documents/DocumentCard';
import { SearchResults } from '../components/search/SearchResults';
import { motion } from 'framer-motion';
import { PlusIcon } from '@radix-ui/react-icons';

/**
 * MainPage - Single-page search-centric application.
 *
 * Features:
 * - Prominent search bar at center
 * - Debounced search with automatic results
 * - Document grid when not searching
 * - Upload modal
 * - Smooth animations
 */
export const MainPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [uploadOpen, setUploadOpen] = useState(false);

  const searchResults = useSearchWithDebounce(searchQuery);
  const documents = useDocuments(1, 20);

  const showSearch = searchQuery.length > 0;
  const dataToDisplay = showSearch ? searchResults : documents;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <svg
                className="h-8 w-8 text-primary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <span className="text-xl font-bold text-gray-900">RAAS</span>
            </div>

            <Button onClick={() => setUploadOpen(true)} size="sm">
              <PlusIcon className="mr-2 h-4 w-4" />
              Upload
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Search */}
      <main className="container mx-auto px-4">
        <div className="py-12">
          <EnhancedSearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            autoFocus
          />
        </div>

        {/* Results or Documents */}
        <div className="pb-12">
          {dataToDisplay.isLoading && (
            <div className="text-center py-12">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent" />
              <p className="mt-4 text-gray-600">
                {showSearch ? 'Searching...' : 'Loading documents...'}
              </p>
            </div>
          )}

          {dataToDisplay.error && (
            <div className="text-center py-12">
              <p className="text-red-600">
                Error: {dataToDisplay.error.message}
              </p>
            </div>
          )}

          {dataToDisplay.isSuccess && (
            <div className="space-y-4">
              {showSearch ? (
                // Search Results
                <>
                  <p className="text-sm text-gray-600">
                    {searchResults.data?.total_results || 0} results for "{searchQuery}"
                  </p>
                  {searchResults.data?.results && (
                    <SearchResults results={searchResults.data.results} query={searchQuery} />
                  )}
                </>
              ) : (
                // Document Grid
                <>
                  <p className="text-sm text-gray-600">
                    {documents.data?.total || 0} documents
                  </p>
                  {documents.data?.documents.length === 0 ? (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="text-center py-12"
                    >
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        No documents yet
                      </h3>
                      <p className="text-gray-600 mb-6">
                        Upload your first document to get started
                      </p>
                      <Button onClick={() => setUploadOpen(true)}>
                        <PlusIcon className="mr-2 h-4 w-4" />
                        Upload Document
                      </Button>
                    </motion.div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {documents.data?.documents.map((doc) => (
                        <DocumentCard key={doc.id} document={doc} />
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Upload Modal */}
      <UploadModal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onSuccess={(id) => {
          console.log('Upload successful:', id);
        }}
      />
    </div>
  );
};
