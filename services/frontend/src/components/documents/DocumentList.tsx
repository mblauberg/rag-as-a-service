import React, { useState } from 'react';
import { useDocuments } from '../../hooks/useDocuments';
import { DocumentCard } from './DocumentCard';
import { Spinner } from '../common/Spinner';
import { Button } from '../common/Button';

export const DocumentList: React.FC = () => {
  const [page, setPage] = useState(1);
  const limit = 10;

  const { data, isLoading, error } = useDocuments(page, limit);

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
        <p className="text-red-600">Error loading documents: {error.message}</p>
      </div>
    );
  }

  if (!data || data.documents.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
        <p className="mt-1 text-sm text-gray-500">Get started by uploading a document.</p>
      </div>
    );
  }

  const totalPages = Math.ceil(data.total / limit);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">
          All Documents
          <span className="ml-2 text-sm font-normal text-gray-500">({data.total} total)</span>
        </h2>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-1">
        {data.documents.map((document) => (
          <DocumentCard key={document.id} document={document} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-4">
          <Button
            variant="secondary"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            Previous
          </Button>
          <span className="text-sm text-gray-700">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="secondary"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
};
