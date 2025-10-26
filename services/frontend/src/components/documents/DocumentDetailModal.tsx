import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { formatBytes, formatDate } from '@/utils/formatters';

interface DocumentDetailModalProps {
  documentId: string;
  highlightChunkId?: string;
  open: boolean;
  onClose: () => void;
}

/**
 * DocumentDetailModal - Full document view in modal overlay.
 * Replaces the DocumentDetailPage route.
 */
export const DocumentDetailModal: React.FC<DocumentDetailModalProps> = ({
  documentId,
  highlightChunkId,
  open,
  onClose,
}) => {
  const { data: document, isLoading, error } = useQuery({
    queryKey: ['document', documentId],
    queryFn: () => api.getDocument(documentId),
    enabled: open && !!documentId,
  });

  useEffect(() => {
    if (highlightChunkId && open && document) {
      // Wait for modal to render
      setTimeout(() => {
        const element = window.document.getElementById(`chunk-${highlightChunkId}`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          element.classList.add('bg-yellow-100', 'border-l-4', 'border-yellow-500', 'transition-all');

          // Remove highlight after 3 seconds
          const timer = setTimeout(() => {
            element.classList.remove('bg-yellow-100', 'border-l-4', 'border-yellow-500');
          }, 3000);

          return () => clearTimeout(timer);
        }
      }, 100);
    }
  }, [highlightChunkId, open, document]);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        {isLoading && (
          <div className="space-y-4">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-64 w-full" />
          </div>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertDescription>
              Error loading document: {(error as Error).message}
            </AlertDescription>
          </Alert>
        )}

        {document && (
          <>
            <DialogHeader>
              <DialogTitle className="text-2xl">{document.title}</DialogTitle>
              {document.description && (
                <DialogDescription>{document.description}</DialogDescription>
              )}
            </DialogHeader>

            <div className="space-y-6">
              {/* Metadata */}
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">
                  {formatBytes(document.file_size)}
                </Badge>
                <Badge variant="secondary">
                  {document.chunks?.length || 0} chunks
                </Badge>
                <Badge variant="outline">
                  Uploaded {formatDate(document.created_at)}
                </Badge>
              </div>

              {/* Chunks */}
              {document.chunks && document.chunks.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-2">Content</h3>
                  <div className="space-y-2">
                    {document.chunks.map((chunk, index) => (
                      <div
                        key={chunk.id}
                        id={`chunk-${chunk.id}`}
                        className="bg-muted/50 rounded-lg p-4"
                      >
                        <div className="flex items-start gap-2 mb-2">
                          <span className="text-xs font-medium text-muted-foreground">
                            Chunk {index + 1}
                          </span>
                          {chunk.section_title && (
                            <span className="text-xs text-muted-foreground">
                              - {chunk.section_title}
                            </span>
                          )}
                          {chunk.page_number && (
                            <span className="text-xs text-muted-foreground">
                              (Page {chunk.page_number})
                            </span>
                          )}
                        </div>
                        <pre className="whitespace-pre-wrap text-sm font-mono">
                          {chunk.chunk_text}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};
