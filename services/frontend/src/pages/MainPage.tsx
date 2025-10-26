import React, { useState, useEffect } from 'react';
import { EnhancedSearchBar } from '@/components/search/EnhancedSearchBar';
import { UploadModal } from '@/components/upload/UploadModal';
import { UploadFAB } from '@/components/upload/UploadFAB';
import { DocumentDetailModal } from '@/components/documents/DocumentDetailModal';
import { Button } from '@/components/ui/button';
import { useSearchWithDebounce } from '@/hooks/useSearchWithDebounce';
import { useDocuments } from '@/hooks/useDocuments';
import { useModels } from '@/hooks/useModels';
import { DocumentCard } from '@/components/documents/DocumentCard';
import { SearchResults } from '@/components/search/SearchResults';
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
                      transition={{ duration: 0.4 }}
                      className="text-center py-16"
                    >
                      <div className="max-w-2xl mx-auto space-y-8">
                        {/* Hero Icon */}
                        <div className="flex justify-center">
                          <div className="relative">
                            <motion.div
                              initial={{ scale: 0.8 }}
                              animate={{ scale: 1 }}
                              transition={{ duration: 0.5, type: "spring" }}
                              className="w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center"
                            >
                              <svg
                                className="w-12 h-12 text-primary"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                                />
                              </svg>
                            </motion.div>
                            <motion.div
                              initial={{ scale: 0, opacity: 0 }}
                              animate={{ scale: 1, opacity: 1 }}
                              transition={{ delay: 0.3, duration: 0.3 }}
                              className="absolute -top-2 -right-2 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center"
                            >
                              <PlusIcon className="w-5 h-5 text-white" />
                            </motion.div>
                          </div>
                        </div>

                        {/* Heading & Description */}
                        <div className="space-y-3">
                          <h2 className="text-3xl font-bold text-foreground">
                            Welcome to RAAS
                          </h2>
                          <p className="text-lg text-muted-foreground max-w-md mx-auto">
                            Upload your first document to start searching with AI-powered semantic search
                          </p>
                        </div>

                        {/* Supported File Types */}
                        <div className="flex justify-center gap-6">
                          {[
                            { icon: "📄", label: "PDF", color: "text-red-600" },
                            { icon: "📝", label: "DOCX", color: "text-blue-600" },
                            { icon: "📋", label: "TXT", color: "text-gray-600" },
                            { icon: "📊", label: "CSV", color: "text-green-600" },
                            { icon: "📑", label: "MD", color: "text-purple-600" }
                          ].map((type) => (
                            <motion.div
                              key={type.label}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: 0.4 + (["PDF", "DOCX", "TXT", "CSV", "MD"].indexOf(type.label) * 0.1) }}
                              className="flex flex-col items-center gap-2"
                            >
                              <div className="text-3xl">{type.icon}</div>
                              <span className={`text-xs font-medium ${type.color}`}>
                                {type.label}
                              </span>
                            </motion.div>
                          ))}
                        </div>

                        {/* CTA Button */}
                        <motion.div
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.6 }}
                        >
                          <Button
                            size="lg"
                            onClick={() => setUploadOpen(true)}
                            className="text-base px-8 py-6 h-auto shadow-lg hover:shadow-xl transition-shadow"
                          >
                            <PlusIcon className="mr-2 h-5 w-5" />
                            Upload Your First Document
                          </Button>
                        </motion.div>

                        {/* Benefits List */}
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.8 }}
                          className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8 text-left"
                        >
                          {[
                            {
                              title: "Semantic Search",
                              description: "Find content by meaning, not just keywords"
                            },
                            {
                              title: "AI Summaries",
                              description: "Get instant answers from your documents"
                            },
                            {
                              title: "Multiple Formats",
                              description: "Support for PDF, DOCX, TXT, CSV, and Markdown"
                            }
                          ].map((benefit, i) => (
                            <div
                              key={i}
                              className="p-4 bg-card rounded-lg border border-border"
                            >
                              <h3 className="font-semibold text-sm mb-1">{benefit.title}</h3>
                              <p className="text-xs text-muted-foreground">{benefit.description}</p>
                            </div>
                          ))}
                        </motion.div>
                      </div>
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
        onSuccess={() => {
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
