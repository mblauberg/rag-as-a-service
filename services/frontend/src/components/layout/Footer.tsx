import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="text-center text-sm text-gray-500">
          <p>&copy; {new Date().getFullYear()} RAAS - Retrieval-Augmented Generation as a Service</p>
        </div>
      </div>
    </footer>
  );
};
