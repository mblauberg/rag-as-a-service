import React, { useState, useEffect } from 'react';
import { useUploadDocument } from '@/hooks/useDocuments';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import { validateUploadFile, extractTitleFromFilename, ALLOWED_EXTENSIONS } from '@/utils/fileValidation';

interface UploadModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: (documentId: string) => void;
}

/**
 * UploadModal component with drag-and-drop file upload.
 *
 * Features:
 * - Drag and drop file upload
 * - File validation (.pdf, .docx, .txt)
 * - Auto-fill title from filename
 * - shadcn/ui Dialog component
 */
export const UploadModal: React.FC<UploadModalProps> = ({
  open,
  onClose,
  onSuccess
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);

  const uploadDocument = useUploadDocument();

  // Clear error when modal opens
  useEffect(() => {
    if (open) {
      setError(null);
    }
  }, [open]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragIn = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragOut = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    setError(null);

    const files = Array.from(e.dataTransfer.files);
    const droppedFile = files[0];

    if (!droppedFile) {
      return;
    }

    const validation = validateUploadFile(droppedFile);

    if (!validation.valid) {
      setError(validation.error!);
      return;
    }

    setFile(droppedFile);
    if (!title) {
      setTitle(extractTitleFromFilename(droppedFile.name));
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];

    if (!selectedFile) {
      return;
    }

    setError(null);

    const validation = validateUploadFile(selectedFile);

    if (!validation.valid) {
      setError(validation.error!);
      return;
    }

    setFile(selectedFile);
    if (!title) {
      setTitle(extractTitleFromFilename(selectedFile.name));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file || !title) {
      return;
    }

    setError(null);

    try {
      const result = await uploadDocument.mutateAsync({
        file,
        title,
        description: description || undefined
      });

      onSuccess?.(result.id);
      onClose();

      // Reset form
      setFile(null);
      setTitle('');
      setDescription('');
    } catch (error) {
      console.error('Upload failed:', error);
      setError(error instanceof Error ? error.message : 'Failed to upload document');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
          <DialogDescription>
            Upload PDF, DOCX, or TXT files up to 100MB. Add a title and optional description.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div
            onDragEnter={handleDragIn}
            onDragLeave={handleDragOut}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={cn(
              "border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
              isDragging
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50"
            )}
          >
            <input
              type="file"
              id="file-upload"
              className="sr-only"
              accept={ALLOWED_EXTENSIONS.join(',')}
              onChange={handleFileInput}
            />

            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="space-y-2">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <div className="text-sm text-muted-foreground">
                  <span className="font-medium text-primary">Click to upload</span>
                  {' or drag and drop'}
                </div>
                <p className="text-xs text-muted-foreground">
                  PDF, DOCX, or TXT (up to 100MB)
                </p>
                {file && (
                  <p className="text-sm font-medium text-foreground mt-2">
                    Selected: {file.name}
                  </p>
                )}
              </div>
            </label>
          </div>

          {error && (
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium">Title *</label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter document title"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Description (optional)</label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter document description"
              rows={3}
            />
          </div>

          <div className="flex justify-end space-x-3">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={uploadDocument.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!file || !title || uploadDocument.isPending}
            >
              {uploadDocument.isPending ? 'Uploading...' : 'Upload'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
