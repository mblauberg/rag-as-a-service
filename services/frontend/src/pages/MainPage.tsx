import React, { useState, useEffect } from 'react';
import { EnhancedSearchBar } from '../components/search/EnhancedSearchBar';
import { UploadModal } from '../components/upload/UploadModal';
import { UploadFAB } from '../components/upload/UploadFAB';
import { DocumentDetailModal } from '../components/documents/DocumentDetailModal';
import { Button } from '../components/common/Button';
import { useSearchWithDebounce } from '../hooks/useSearchWithDebounce';
import { useDocuments } from '../hooks/useDocuments';
import { useModels } from '../hooks/useModels';
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
 * - Upload modal with FAB
 * - Document detail modal (overlay instead of route)
 * - Smooth animations
 */
export const MainPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  const searchResults = useSearchWithDebounce(searchQuery, selectedModel);
  const documents = useDocuments(1, 20);
  const models = useModels();

  // Auto-select GPT-5 Mini when models load
  useEffect(() => {
    if (models.data && !selectedModel) {
      const gpt5Mini = models.data.find(m => m.name.includes('gpt-5-mini'));
      setSelectedModel(gpt5Mini?.name || models.data[0]?.name || null);
    }
  }, [models.data, selectedModel]);

  const showSearch = searchQuery.length > 0;
  const dataToDisplay = showSearch ? searchResults : documents;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-border">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <svg
                className="h-8 w-8 text-primary"
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
              <span className="text-xl font-bold text-foreground">RAAS</span>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Search */}
      <main className="container mx-auto px-4">
        <div className="py-12">
          <EnhancedSearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            selectedModel={selectedModel}
            onModelChange={setSelectedModel}
            models={models.data || []}
            modelsLoading={models.isLoading}
            autoFocus
          />
        </div>

        {/* Results or Documents */}
        <div className="pb-12">
          {dataToDisplay.isLoading && (
            <div className="text-center py-12">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent" />
              <p className="mt-4 text-muted-foreground">
                {showSearch ? 'Searching...' : 'Loading documents...'}
              </p>
            </div>
          )}

          {dataToDisplay.error && (
            <div className="text-center py-12">
              <p className="text-destructive" role="alert">
                Error: {dataToDisplay.error.message}
              </p>
            </div>
          )}

          {dataToDisplay.isSuccess && (
            <div className="space-y-4">
              {showSearch ? (
                // Search Results
                <>
                  <p className="text-sm text-muted-foreground">
                    {searchResults.data?.total_results || 0} results for "{searchQuery}"
                  </p>
                  {searchResults.data?.chunks && (
                    <SearchResults
                      results={searchResults.data.chunks}
                      query={searchQuery}
                      searchResponse={searchResults.data}
                      onDocumentClick={(docId: string) => setSelectedDocId(docId)}
                    />
                  )}
                </>
              ) : (
                // Document Grid
                <>
                  <p className="text-sm text-muted-foreground">
                    {documents.data?.total || 0} documents
                  </p>
                  {documents.data?.documents.length === 0 ? (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="text-center py-12"
                    >
                      <h3 className="text-lg font-semibold text-foreground mb-2">
                        No documents yet
                      </h3>
                      <p className="text-muted-foreground mb-6">
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
                        <DocumentCard
                          key={doc.id}
                          document={doc}
                          onClick={() => setSelectedDocId(doc.id)}
                        />
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
          setUploadOpen(false);
        }}
      />

      {/* Floating Action Button */}
      {documents.data && documents.data.documents.length > 0 && (
        <UploadFAB onClick={() => setUploadOpen(true)} />
      )}

      {/* Document Detail Modal */}
      {selectedDocId && (
        <DocumentDetailModal
          documentId={selectedDocId}
          open={!!selectedDocId}
          onClose={() => setSelectedDocId(null)}
        />
      )}
    </div>
  );
};
