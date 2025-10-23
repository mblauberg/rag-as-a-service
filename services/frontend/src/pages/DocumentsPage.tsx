import React from 'react';
import { Link } from 'react-router-dom';
import { DocumentList } from '../components/documents/DocumentList';
import { Button } from '../components/common/Button';

export const DocumentsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Documents</h1>
        <Link to="/">
          <Button>
            <div className="flex items-center">
              <svg
                className="w-5 h-5 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              Upload New
            </div>
          </Button>
        </Link>
      </div>
      <DocumentList />
    </div>
  );
};
