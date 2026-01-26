import React from 'react';
import { AlertCircle } from 'lucide-react';

export const Error = ({ message = 'Something went wrong', onRetry }: { message?: string, onRetry?: () => void }) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
      <h3 className="heading text-lg mb-2">Error</h3>
      <p className="body-text text-gray-600 mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="button-text bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Try Again
        </button>
      )}
    </div>
  );
};

export default Error;