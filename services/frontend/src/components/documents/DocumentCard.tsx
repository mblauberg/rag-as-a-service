import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import type { Document } from '../../types';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Modal } from '../common/Modal';
import { useDeleteDocument } from '../../hooks/useDocuments';
import { formatBytes, formatDate, formatStatus, getStatusColor } from '../../utils/formatters';

interface DocumentCardProps {
  document: Document;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({ document }) => {
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const deleteDocument = useDeleteDocument();

  const handleDelete = async () => {
    try {
      await deleteDocument.mutateAsync(document.id);
      setShowDeleteModal(false);
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    return (
      <span
        className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(status)}`}
      >
        {formatStatus(status)}
      </span>
    );
  };

  return (
    <>
      <Card className="hover:shadow-lg transition-shadow duration-200">
        <div className="flex flex-col space-y-3">
          <div className="flex justify-between items-start">
            <Link to={`/documents/${document.id}`} className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 hover:text-primary-600">
                {document.title}
              </h3>
            </Link>
            <Button
              variant="danger"
              size="sm"
              onClick={() => setShowDeleteModal(true)}
              className="ml-2"
            >
              Delete
            </Button>
          </div>

          {document.description && (
            <p className="text-sm text-gray-600 line-clamp-2">{document.description}</p>
          )}

          <div className="flex flex-wrap gap-2">
            {getStatusBadge(document.embedding_status)}
          </div>

          <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-gray-500">
            <div className="flex items-center">
              <svg
                className="w-4 h-4 mr-1"
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
              {document.file_name}
            </div>
            <div className="flex items-center">
              <svg
                className="w-4 h-4 mr-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
                />
              </svg>
              {formatBytes(document.file_size)}
            </div>
            <div className="flex items-center">
              <svg
                className="w-4 h-4 mr-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              {formatDate(document.created_at)}
            </div>
          </div>
        </div>
      </Card>

      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Confirm Delete"
      >
        <div className="space-y-4">
          <p className="text-gray-700">
            Are you sure you want to delete "{document.title}"? This action cannot be undone.
          </p>
          <div className="flex justify-end space-x-3">
            <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDelete}
              isLoading={deleteDocument.isPending}
            >
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};
