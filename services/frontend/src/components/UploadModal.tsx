import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, File, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '../lib/utils';
import { useUploadDocument } from '../hooks/useDocuments';
import { formatBytes } from '../utils/formatting';
import type { DocumentUploadResponse } from '../types';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess?: (document: DocumentUploadResponse) => void;
}

/**
 * Modern drag-and-drop upload modal
 * Features:
 * - React-dropzone for drag-and-drop
 * - File preview with size display
 * - Progress indicator during upload
 * - Error handling with clear messages
 * - Modern shadcn/ui inspired design
 * - Accessible with keyboard navigation
 */
export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
}) => {
  const uploadDocument = useUploadDocument();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [validationError, setValidationError] = useState('');

  // Reset form when modal closes
  const handleClose = useCallback(() => {
    setSelectedFile(null);
    setTitle('');
    setDescription('');
    setValidationError('');
    uploadDocument.reset();
    onClose();
  }, [onClose, uploadDocument]);

  // Handle file drop
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setSelectedFile(file);
      // Auto-fill title if empty
      if (!title) {
        const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '');
        setTitle(nameWithoutExt);
      }
      setValidationError('');
    }
  }, [title]);

  // Configure dropzone
  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxSize: 100 * 1024 * 1024, // 100MB
    maxFiles: 1,
    multiple: false,
  });

  // Handle file upload
  const handleUpload = async () => {
    // Validation
    if (!selectedFile) {
      setValidationError('Please select a file to upload');
      return;
    }
    if (!title.trim()) {
      setValidationError('Please enter a title');
      return;
    }

    try {
      const result = await uploadDocument.mutateAsync({
        file: selectedFile,
        title: title.trim(),
        description: description.trim() || undefined,
      });

      // Success callback
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }

      // Close modal after brief delay
      setTimeout(() => {
        handleClose();
      }, 1500);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  // Handle escape key
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !uploadDocument.isPending) {
        handleClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, handleClose, uploadDocument.isPending]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={uploadDocument.isPending ? undefined : handleClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        role="dialog"
        aria-modal="true"
        aria-labelledby="upload-modal-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 id="upload-modal-title" className="text-2xl font-semibold text-gray-900">
            Upload Document
          </h2>
          <button
            onClick={handleClose}
            disabled={uploadDocument.isPending}
            className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded-lg p-1 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Close modal"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Dropzone */}
          {!selectedFile && !uploadDocument.isSuccess && (
            <div
              {...getRootProps()}
              className={cn(
                'border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all',
                'hover:border-primary-400 hover:bg-primary-50/50',
                isDragActive
                  ? 'border-primary-500 bg-primary-50 scale-105'
                  : 'border-gray-300 bg-gray-50'
              )}
            >
              <input {...getInputProps()} aria-label="File upload" />
              <Upload
                className={cn(
                  'w-16 h-16 mx-auto mb-4 transition-colors',
                  isDragActive ? 'text-primary-600' : 'text-gray-400'
                )}
              />
              <p className="text-lg font-medium text-gray-700 mb-2">
                {isDragActive ? 'Drop your file here' : 'Drag and drop your file here'}
              </p>
              <p className="text-sm text-gray-500 mb-4">or click to browse</p>
              <p className="text-xs text-gray-400">
                Supported formats: PDF, DOCX, TXT (max 100MB)
              </p>

              {/* File rejection errors */}
              {fileRejections.length > 0 && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-600">
                    {fileRejections[0].errors[0].message}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* File Preview */}
          {selectedFile && !uploadDocument.isSuccess && (
            <div className="border-2 border-primary-200 bg-primary-50/50 rounded-xl p-6">
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                    <File className="w-6 h-6 text-primary-600" />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {selectedFile.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    {formatBytes(selectedFile.size)}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedFile(null)}
                  disabled={uploadDocument.isPending}
                  className="flex-shrink-0 text-gray-400 hover:text-gray-600 focus:outline-none disabled:opacity-50"
                  aria-label="Remove file"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}

          {/* Success Message */}
          {uploadDocument.isSuccess && (
            <div className="border-2 border-green-200 bg-green-50 rounded-xl p-6 text-center">
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <p className="text-lg font-medium text-green-900 mb-2">Upload Successful!</p>
              <p className="text-sm text-green-700">
                Your document has been uploaded and is being processed.
              </p>
            </div>
          )}

          {/* Form Fields */}
          {selectedFile && !uploadDocument.isSuccess && (
            <>
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Title <span className="text-red-500">*</span>
                </label>
                <input
                  id="title"
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  disabled={uploadDocument.isPending}
                  placeholder="Enter document title"
                  className={cn(
                    'w-full px-4 py-2 border-2 rounded-lg',
                    'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                    'disabled:bg-gray-50 disabled:text-gray-500',
                    'transition-colors'
                  )}
                />
              </div>

              <div>
                <label
                  htmlFor="description"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Description (optional)
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={uploadDocument.isPending}
                  placeholder="Enter document description"
                  rows={3}
                  className={cn(
                    'w-full px-4 py-2 border-2 rounded-lg resize-none',
                    'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                    'disabled:bg-gray-50 disabled:text-gray-500',
                    'transition-colors'
                  )}
                />
              </div>

              {/* Validation Error */}
              {validationError && (
                <div className="flex items-start space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-700">{validationError}</p>
                </div>
              )}

              {/* Upload Error */}
              {uploadDocument.error && (
                <div className="flex items-start space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-700">
                    {uploadDocument.error.message}
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {!uploadDocument.isSuccess && (
          <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
            <button
              onClick={handleClose}
              disabled={uploadDocument.isPending}
              className={cn(
                'px-6 py-2 text-sm font-medium text-gray-700 bg-white border-2 border-gray-300',
                'rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500',
                'transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              Cancel
            </button>
            <button
              onClick={handleUpload}
              disabled={!selectedFile || uploadDocument.isPending}
              className={cn(
                'px-6 py-2 text-sm font-medium text-white bg-primary-600',
                'rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500',
                'transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
                'flex items-center space-x-2'
              )}
            >
              {uploadDocument.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>Upload</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
