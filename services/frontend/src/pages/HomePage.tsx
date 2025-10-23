import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Upload as UploadIcon, Search as SearchIcon, Sparkles } from 'lucide-react';
import { SearchBar } from '../components/search/SearchBar';
import { SearchResults } from '../components/search/SearchResults';
import { DocumentCard } from '../components/documents/DocumentCard';
import { UploadModal } from '../components/UploadModal';
import { useDocuments } from '../hooks/useDocuments';
import { useSearch } from '../hooks/useSearch';
import { useDebounce } from '../hooks/useDebounce';
import { cn } from '../lib/utils';
import type { DocumentUploadResponse } from '../types';

/**
 * Modern single-page HomePage with search-centric design
 *
 * Features:
 * - Prominent search bar at top center
 * - Search results displayed below search
 * - Document grid when not searching
 * - Upload button opens modal
 * - Minimal navigation, focus on search
 * - Responsive design
 * - Modern aesthetics with shadcn/ui styling
 */
export const HomePage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  // Debounce search query to avoid excessive API calls
  const debouncedQuery = useDebounce(searchQuery, 500);

  // Fetch documents for grid display
  const { data: documentsData, isLoading: isLoadingDocuments } = useDocuments(1, 12);

  // Search mutation
  const searchMutation = useSearch();

  // Trigger search when debounced query changes
  useEffect(() => {
    if (debouncedQuery.trim()) {
      searchMutation.mutate({ query: debouncedQuery, limit: 10 });
      setHasSearched(true);
    } else {
      setHasSearched(false);
    }
  }, [debouncedQuery]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handleUploadSuccess = (document: DocumentUploadResponse) => {
    console.log('Document uploaded successfully:', document);
  };

  // Determine what to show
  const showSearchResults = hasSearched && searchQuery.trim();
  const showDocuments = !showSearchResults;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-primary-50/30">
      {/* Hero Section with Search */}
      <div className="relative">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-200/30 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-200/30 rounded-full blur-3xl" />
        </div>

        {/* Content */}
        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12">
          {/* Header */}
          <div className="text-center mb-12 space-y-4">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center shadow-lg">
                <Sparkles className="w-7 h-7 text-white" />
              </div>
              <h1 className="text-5xl font-bold text-gray-900">
                RAAS
              </h1>
            </div>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Semantic document search powered by AI
            </p>
            <p className="text-sm text-gray-500 max-w-xl mx-auto">
              Upload your documents and search using natural language. Our system understands context and meaning, not just keywords.
            </p>
          </div>

          {/* Search Bar */}
          <div className="max-w-3xl mx-auto mb-8">
            <SearchBar
              onSearch={handleSearch}
              isLoading={searchMutation.isPending}
              placeholder="Search your documents..."
            />
          </div>

          {/* Quick Actions */}
          <div className="flex justify-center items-center space-x-4">
            <button
              onClick={() => setIsUploadModalOpen(true)}
              className={cn(
                'inline-flex items-center space-x-2 px-6 py-3',
                'bg-primary-600 text-white font-medium rounded-xl',
                'hover:bg-primary-700 focus:outline-none focus:ring-4 focus:ring-primary-200',
                'transition-all duration-200 shadow-lg hover:shadow-xl',
                'transform hover:-translate-y-0.5'
              )}
            >
              <UploadIcon className="w-5 h-5" />
              <span>Upload Document</span>
            </button>

            <Link
              to="/documents"
              className={cn(
                'inline-flex items-center space-x-2 px-6 py-3',
                'bg-white text-gray-700 font-medium rounded-xl border-2 border-gray-200',
                'hover:border-gray-300 hover:shadow-md focus:outline-none focus:ring-4 focus:ring-gray-200',
                'transition-all duration-200'
              )}
            >
              <FileText className="w-5 h-5" />
              <span>All Documents</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        {/* Search Results */}
        {showSearchResults && (
          <div className="mt-8">
            {searchMutation.isPending ? (
              <div className="text-center py-12">
                <div className="inline-block w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
                <p className="mt-4 text-gray-600">Searching documents...</p>
              </div>
            ) : searchMutation.error ? (
              <div className="text-center py-12">
                <div className="max-w-md mx-auto p-6 bg-red-50 border-2 border-red-200 rounded-xl">
                  <p className="text-red-800 font-medium mb-2">Search failed</p>
                  <p className="text-sm text-red-700">{searchMutation.error.message}</p>
                </div>
              </div>
            ) : searchMutation.data ? (
              <div>
                <div className="mb-6 flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">Search Results</h2>
                    <p className="text-sm text-gray-500 mt-1">
                      Found {searchMutation.data.total_results} results for "{searchQuery}"
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setSearchQuery('');
                      setHasSearched(false);
                    }}
                    className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Clear search
                  </button>
                </div>
                <SearchResults results={searchMutation.data.results} query={searchQuery} />
              </div>
            ) : null}
          </div>
        )}

        {/* Document Grid */}
        {showDocuments && (
          <div className="mt-12">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Recent Documents</h2>
              <p className="text-sm text-gray-500 mt-1">
                {documentsData?.total
                  ? `${documentsData.total} documents in your library`
                  : 'Your document library'}
              </p>
            </div>

            {isLoadingDocuments ? (
              <div className="text-center py-12">
                <div className="inline-block w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
                <p className="mt-4 text-gray-600">Loading documents...</p>
              </div>
            ) : documentsData?.documents && documentsData.documents.length > 0 ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {documentsData.documents.map((document) => (
                    <DocumentCard key={document.id} document={document} />
                  ))}
                </div>

                {documentsData.total > documentsData.documents.length && (
                  <div className="text-center mt-8">
                    <Link
                      to="/documents"
                      className={cn(
                        'inline-flex items-center space-x-2 px-6 py-3',
                        'bg-white text-gray-700 font-medium rounded-xl border-2 border-gray-200',
                        'hover:border-gray-300 hover:shadow-md focus:outline-none focus:ring-4 focus:ring-gray-200',
                        'transition-all duration-200'
                      )}
                    >
                      <span>View all {documentsData.total} documents</span>
                    </Link>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-16">
                <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <FileText className="w-10 h-10 text-gray-400" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No documents yet</h3>
                <p className="text-gray-500 mb-6">
                  Get started by uploading your first document
                </p>
                <button
                  onClick={() => setIsUploadModalOpen(true)}
                  className={cn(
                    'inline-flex items-center space-x-2 px-6 py-3',
                    'bg-primary-600 text-white font-medium rounded-xl',
                    'hover:bg-primary-700 focus:outline-none focus:ring-4 focus:ring-primary-200',
                    'transition-all duration-200 shadow-lg hover:shadow-xl'
                  )}
                >
                  <UploadIcon className="w-5 h-5" />
                  <span>Upload Your First Document</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* Feature Highlights (shown only when no search and no documents) */}
        {showDocuments && (!documentsData?.documents || documentsData.documents.length === 0) && (
          <div className="grid md:grid-cols-3 gap-8 mt-16">
            <div className="text-center p-6">
              <div className="w-14 h-14 bg-primary-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                <UploadIcon className="w-7 h-7 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Easy Upload</h3>
              <p className="text-sm text-gray-600">
                Drag and drop your PDF, DOCX, or TXT files. Documents are automatically processed and indexed.
              </p>
            </div>

            <div className="text-center p-6">
              <div className="w-14 h-14 bg-primary-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                <SearchIcon className="w-7 h-7 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Smart Search</h3>
              <p className="text-sm text-gray-600">
                Search using natural language. Our AI understands context and meaning, not just keywords.
              </p>
            </div>

            <div className="text-center p-6">
              <div className="w-14 h-14 bg-primary-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-7 h-7 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">AI-Powered</h3>
              <p className="text-sm text-gray-600">
                Powered by advanced machine learning to deliver accurate and relevant search results.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  );
};
