import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { TrashIcon } from '@radix-ui/react-icons';
import { api } from '@/services/api';
import type { Document } from '@/types';
import { formatBytes, formatDate, getFileTypeIcon, getFileTypeColor } from '@/utils/formatters';
import { FileIcon } from '@/components/ui/file-icon';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';

interface DocumentCardProps {
  document: Document;
  onClick?: () => void;
}

/** DocumentCard - Displays document metadata. Click to open detail modal. */
export const DocumentCard: React.FC<DocumentCardProps> = ({ document, onClick }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setDeleteConfirmOpen(false);
    },
  });

  const handleCardClick = () => {
    if (onClick) {
      onClick();
    } else {
      // Fallback to navigation if no onClick provided (backward compatibility)
      navigate(`/documents/${document.id}`);
    }
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = () => {
    deleteMutation.mutate(document.id);
  };

  return (
    <>
      <motion.div
        variants={{
          hidden: { opacity: 0, y: 20 },
          show: { opacity: 1, y: 0 }
        }}
        whileHover={{ y: -6, transition: { duration: 0.2 } }}
        transition={{ duration: 0.2 }}
      >
        <Card
          className="cursor-pointer hover:shadow-lg hover:shadow-primary/5 transition-all duration-200 border-2 hover:border-primary/20 group"
          onClick={handleCardClick}
        >
          <CardHeader className="pb-3">
            <div className="flex items-start gap-3">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${getFileTypeColor(document.file_name)}`}>
                <FileIcon type={getFileTypeIcon(document.file_name)} className="w-6 h-6" />
              </div>

              <div className="flex-1 min-w-0">
                <CardTitle className="text-lg line-clamp-1 group-hover:text-primary transition-colors">
                  {document.title}
                </CardTitle>
                {document.description && (
                  <CardDescription className="line-clamp-2 mt-1">
                    {document.description}
                  </CardDescription>
                )}
              </div>
            </div>
          </CardHeader>

          <CardContent className="pb-3">
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary" className="font-mono text-xs">
                {formatBytes(document.file_size)}
              </Badge>
              <Badge variant="outline" className="text-xs">
                {document.file_name}
              </Badge>
            </div>
          </CardContent>

          <CardFooter className="flex justify-between items-center pt-3 border-t">
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {formatDate(document.created_at)}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDeleteClick}
              disabled={deleteMutation.isPending}
              aria-label="Delete document"
              className="opacity-0 group-hover:opacity-100 transition-opacity hover:bg-destructive/10 hover:text-destructive"
            >
              <TrashIcon className="h-4 w-4" />
            </Button>
          </CardFooter>
        </Card>
      </motion.div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Document</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{document.title}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteConfirmOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
