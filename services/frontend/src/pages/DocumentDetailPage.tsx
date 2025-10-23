import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useDocument, useDeleteDocument } from '../hooks/useDocuments';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Spinner } from '../components/common/Spinner';
import { formatBytes, formatDate, formatStatus, getStatusColor } from '../utils/formatting';

export const DocumentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: document, isLoading, error } = useDocument(id!);
  const deleteDocument = useDeleteDocument();

  const handleDelete = async () => {
    if (!id) return;

    if (window.confirm(`Are you sure you want to delete "${document?.title}"? This action cannot be undone.`)) {
      try {
        await deleteDocument.mutateAsync(id);
        navigate('/documents');
      } catch (error) {
        console.error('Failed to delete document:', error);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error loading document: {error.message}</p>
        <Link to="/documents" className="mt-4 inline-block">
          <Button variant="secondary">Back to Documents</Button>
        </Link>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Document not found</p>
        <Link to="/documents" className="mt-4 inline-block">
          <Button variant="secondary">Back to Documents</Button>
        </Link>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    return (
      <span
        className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(status)}`}
      >
        {formatStatus(status)}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <Link to="/documents" className="text-primary-600 hover:text-primary-800 text-sm mb-2 inline-block">
            ← Back to Documents
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">{document.title}</h1>
        </div>
        <Button variant="danger" onClick={handleDelete} isLoading={deleteDocument.isPending}>
          Delete Document
        </Button>
      </div>

      <Card>
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Document Information</h2>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-gray-500">File Name</dt>
                <dd className="mt-1 text-sm text-gray-900">{document.file_name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">File Type</dt>
                <dd className="mt-1 text-sm text-gray-900">{document.file_type}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">File Size</dt>
                <dd className="mt-1 text-sm text-gray-900">{formatBytes(document.file_size)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Chunks</dt>
                <dd className="mt-1 text-sm text-gray-900">{document.chunks?.length || 0}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Upload Status</dt>
                <dd className="mt-1">{getStatusBadge(document.upload_status)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Embedding Status</dt>
                <dd className="mt-1">{getStatusBadge(document.embedding_status)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Created</dt>
                <dd className="mt-1 text-sm text-gray-900">{formatDate(document.created_at, true)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Updated</dt>
                <dd className="mt-1 text-sm text-gray-900">{formatDate(document.updated_at, true)}</dd>
              </div>
            </dl>
          </div>

          {document.description && (
            <div>
              <dt className="text-sm font-medium text-gray-500 mb-1">Description</dt>
              <dd className="text-sm text-gray-900">{document.description}</dd>
            </div>
          )}
        </div>
      </Card>

      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Document Chunks ({document.chunks?.length || 0})
        </h2>
        {document.chunks && document.chunks.length > 0 ? (
          <div className="space-y-4">
            {document.chunks.map((chunk) => (
              <Card key={chunk.id}>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-500">
                      Chunk {chunk.chunk_index + 1}
                    </span>
                    {chunk.token_count && (
                      <span className="text-xs text-gray-500">
                        {chunk.token_count} tokens
                      </span>
                    )}
                  </div>
                  <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {chunk.chunk_text}
                  </p>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <p className="text-gray-500 text-center">No chunks available</p>
          </Card>
        )}
      </div>
    </div>
  );
};
