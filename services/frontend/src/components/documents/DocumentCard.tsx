import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { TrashIcon } from '@radix-ui/react-icons';
import { api } from '@/services/api';
import type { Document } from '@/types';
import { formatBytes, formatDate } from '@/utils/formatters';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/common/Button';
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

/**
 * DocumentCard - Displays document metadata in a card.
 * Click to open document detail modal.
 */
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
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ y: -4 }}
        transition={{ duration: 0.2 }}
      >
        <Card
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={handleCardClick}
        >
          <CardHeader>
            <CardTitle className="text-lg">{document.title}</CardTitle>
            {document.description && (
              <CardDescription className="line-clamp-2">
                {document.description}
              </CardDescription>
            )}
          </CardHeader>

          <CardContent>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary">{formatBytes(document.file_size)}</Badge>
              <Badge variant="secondary">{document.file_name}</Badge>
            </div>
          </CardContent>

          <CardFooter className="flex justify-between items-center">
            <span className="text-xs text-muted-foreground">
              {formatDate(document.created_at)}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDeleteClick}
              disabled={deleteMutation.isPending}
              aria-label="Delete document"
            >
              <TrashIcon className="h-4 w-4 text-destructive" />
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
