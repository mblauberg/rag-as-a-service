import React from 'react';
import { Link } from 'react-router-dom';
import { UploadForm } from '../components/documents/UploadForm';
import { Button } from '../components/common/Button';

export const HomePage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to RAAS
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Retrieval-Augmented Generation as a Service
        </p>
        <p className="text-gray-600 max-w-2xl mx-auto mb-8">
          Upload your documents and perform semantic search to find relevant information quickly and efficiently.
          Our system uses advanced AI to understand the meaning of your queries and find the most relevant content.
        </p>
        <div className="flex justify-center space-x-4">
          <Link to="/documents">
            <Button>View All Documents</Button>
          </Link>
          <Link to="/search">
            <Button variant="secondary">Search Documents</Button>
          </Link>
        </div>
      </div>

      <div className="max-w-2xl mx-auto">
        <UploadForm />
      </div>

      <div className="grid md:grid-cols-3 gap-6 mt-12">
        <div className="text-center p-6">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-6 h-6 text-primary-600"
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
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Documents</h3>
          <p className="text-gray-600">
            Upload PDF, DOCX, or TXT files up to 100MB. Your documents are automatically processed and indexed.
          </p>
        </div>

        <div className="text-center p-6">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-6 h-6 text-primary-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Semantic Search</h3>
          <p className="text-gray-600">
            Search using natural language. Our AI understands context and meaning, not just keywords.
          </p>
        </div>

        <div className="text-center p-6">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-6 h-6 text-primary-600"
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
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Manage Content</h3>
          <p className="text-gray-600">
            View, organize, and delete your documents. Track processing status and see document details.
          </p>
        </div>
      </div>
    </div>
  );
};
