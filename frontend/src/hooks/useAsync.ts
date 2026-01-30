import { useState, useCallback } from 'react';
import { toast } from 'react-hot-toast';

interface UseAsyncOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: any) => void;
  showSuccessToast?: boolean;
  showErrorToast?: boolean;
  successMessage?: string;
}

export function useAsync(options: UseAsyncOptions = {}) {
  const {
    onSuccess,
    onError,
    showSuccessToast = false,
    showErrorToast = true,
    successMessage = 'Success',
  } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<any>(null);

  const execute = useCallback(async (asyncFn: (...args: any[]) => Promise<any>, ...args: any[]) => {
    if (!asyncFn) return null;

    setLoading(true);
    setError(null);

    try {
      const result = await asyncFn(...args);
      setData(result);
      
      if (showSuccessToast) {
        toast.success(successMessage);
      }
      
      if (onSuccess) {
        onSuccess(result);
      }
      
      return result;
    } catch (err: any) {
      // Enhance error with more context for common backend issues
      const enhancedError = {
        ...err,
        message: err?.data?.message || err?.message || 'An error occurred',
        statusCode: err?.statusCode || err?.response?.status || err?.status,
        correlationId: err?.data?.correlation_id,
        timestamp: err?.data?.timestamp
      };

      setError(enhancedError);
      
      if (showErrorToast) {
        // Provide user-friendly toast messages for common errors
        let toastMessage = enhancedError.message;
        
        if (enhancedError.statusCode === 500) {
          if (enhancedError.message?.includes('shipping_amount')) {
            toastMessage = "Order data format issue. Please try again later.";
          } else {
            toastMessage = "Server temporarily unavailable. Please try again.";
          }
        } else if (enhancedError.statusCode === 401) {
          toastMessage = "Please log in to continue.";
        } else if (enhancedError.statusCode === 403) {
          toastMessage = "Permission denied.";
        }
        
        toast.error(toastMessage);
      }
      
      if (onError) {
        onError(enhancedError);
      }
      
      throw enhancedError;
    } finally {
      setLoading(false);
    }
  }, [onSuccess, onError, showSuccessToast, showErrorToast, successMessage]);

  return { data, loading, error, execute };
}

// Alias for API calls - same functionality
export const useApi = useAsync;

// Paginated version for admin pages
export function usePaginatedApi(options: UseAsyncOptions = {}) {
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  
  const { data, loading, error, execute: baseExecute } = useAsync(options);

  const execute = useCallback(async (apiFunction: (...args: any[]) => Promise<any>, ...args: any[]) => {
    try {
      const result = await baseExecute(apiFunction, ...args);
      
      if (result && typeof result === 'object') {
        // Handle paginated response structure
        if (result.data && Array.isArray(result.data)) {
          setTotalPages(result.total_pages || 1);
          setTotalItems(result.total || result.data.length);
        }
      }
      
      return result;
    } catch (err) {
      // Error is already handled in the baseExecute function
      console.warn('Paginated API operation failed:', err);
      throw err;
    }
  }, [baseExecute]);

  return {
    data,
    loading,
    error,
    execute,
    currentPage,
    setCurrentPage,
    totalPages,
    totalItems
  };
}