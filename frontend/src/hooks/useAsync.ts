import { useState, useCallback } from 'react';
import { toast } from 'react-hot-toast';

interface AsyncOperationState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

interface UseAsyncOperationOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
  showSuccessToast?: boolean;
  showErrorToast?: boolean;
  successMessage?: string;
  logError?: boolean;
  fallbackMessage?: string;
}

/**
 * Consolidated hook for async operations, API calls, and error handling
 * Merges: useAsyncOperation, useApi, useErrorHandler
 */
export function useAsyncOperations<T = any>(
  options: UseAsyncOperationOptions = {}
) {
  const {
    onSuccess,
    onError,
    showSuccessToast = false,
    showErrorToast = true,
    successMessage = 'Operation completed successfully',
    logError = true,
    fallbackMessage = 'An unexpected error occurred'
  } = options;

  const [state, setState] = useState<AsyncOperationState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  // Error handling logic
  const handleError = useCallback((error: any) => {
    let apiError;

    if (error?.error && error?.message) {
      apiError = error;
    } else if (error?.response?.data) {
      apiError = {
        error: true,
        message: error.response.data.message || error.response.data.detail || fallbackMessage,
        details: error.response.data.details,
        status: error.response.status,
        timestamp: error.response.data.timestamp,
        path: error.response.data.path,
      };
    } else if (error?.message) {
      apiError = {
        error: true,
        message: error.message,
        status: 500,
      };
    } else {
      apiError = {
        error: true,
        message: fallbackMessage,
        status: 500,
      };
    }

    if (logError) {
      console.error('Error handled:', {
        message: apiError.message,
        status: apiError.status,
        details: apiError.details,
        timestamp: apiError.timestamp,
        path: apiError.path,
        originalError: error,
      });
    }

    if (showErrorToast) {
      const message = getErrorMessage(apiError);
      toast.error(message);
    }

    if (onError) {
      onError(apiError);
    }

    return apiError;
  }, [logError, showErrorToast, fallbackMessage, onError]);

  // Main execution function
  const execute = useCallback(
    async (asyncFn: () => Promise<T>) => {
      setState({ data: null, loading: true, error: null });

      try {
        const result = await asyncFn();
        setState({ data: result, loading: false, error: null });

        if (showSuccessToast) {
          toast.success(successMessage);
        }

        if (onSuccess) {
          onSuccess(result);
        }

        return result;
      } catch (error) {
        const handledError = handleError(error);
        setState({ data: null, loading: false, error: handledError });
        throw error;
      }
    },
    [onSuccess, showSuccessToast, successMessage, handleError]
  );

  // API-style execution (for backward compatibility)
  const executeApi = useCallback(async (apiFunc: (...args: any[]) => Promise<T>, ...args: any[]): Promise<T | null> => {
    try {
      return await execute(() => apiFunc(...args));
    } catch (error) {
      return null;
    }
  }, [execute]);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    executeApi,
    handleError,
    reset,
  };
}

/**
 * Hook for optimistic updates with rollback on error
 */
export function useOptimisticUpdate<T>(
  initialData: T,
  options: UseAsyncOperationOptions = {}
) {
  const [data, setData] = useState<T>(initialData);
  const [previousData, setPreviousData] = useState<T>(initialData);
  const { loading, error, execute, reset } = useAsyncOperations<T>(options);

  const executeWithOptimisticUpdate = useCallback(
    async (
      optimisticValue: T,
      asyncFn: () => Promise<T>
    ) => {
      setPreviousData(data);
      setData(optimisticValue);

      try {
        const result = await execute(asyncFn);
        setData(result);
        return result;
      } catch (error) {
        setData(previousData);
        throw error;
      }
    },
    [data, previousData, execute]
  );

  return {
    data,
    loading,
    error,
    execute: executeWithOptimisticUpdate,
    reset: () => {
      setData(initialData);
      reset();
    },
  };
}

/**
 * Hook for retry logic
 */
export function useRetry(maxRetries = 3, retryDelay = 1000) {
  const [retryCount, setRetryCount] = useState(0);

  const executeWithRetry = useCallback(
    async <T,>(asyncFn: () => Promise<T>): Promise<T> => {
      let lastError: Error | null = null;

      for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
          const result = await asyncFn();
          setRetryCount(0);
          return result;
        } catch (error) {
          lastError = error as Error;
          setRetryCount(attempt + 1);

          if (attempt < maxRetries) {
            await new Promise((resolve) => setTimeout(resolve, retryDelay * (attempt + 1)));
          }
        }
      }

      throw lastError;
    },
    [maxRetries, retryDelay]
  );

  return {
    retryCount,
    executeWithRetry,
    resetRetryCount: () => setRetryCount(0),
  };
}

// Helper function for error messages
const getErrorMessage = (error: any) => {
  const status = error.status;
  const message = error.message;

  switch (status) {
    case 400:
      if (error.details && Array.isArray(error.details)) {
        const validationErrors = error.details;
        if (validationErrors.length === 1) {
          return validationErrors[0].message;
        } else if (validationErrors.length > 1) {
          return `Please check: ${validationErrors.map((e: any) => e.field).join(', ')}`;
        }
      }
      return message || 'Invalid request. Please check your input.';
    
    case 401:
      return 'Please log in to continue.';
    
    case 403:
      return 'You don\'t have permission to perform this action.';
    
    case 404:
      return 'The requested resource was not found.';
    
    case 409:
      return message || 'This action conflicts with existing data.';
    
    case 422:
      if (error.details && Array.isArray(error.details)) {
        const validationErrors = error.details;
        if (validationErrors.length === 1) {
          return validationErrors[0].message;
        }
      }
      return message || 'Please check your input and try again.';
    
    case 429:
      return 'Too many requests. Please wait a moment and try again.';
    
    case 500:
      return 'Server error. Please try again later.';
    
    case 502:
    case 503:
    case 504:
      return 'Service temporarily unavailable. Please try again later.';
    
    default:
      if (status && status >= 500) {
        return 'Server error. Please try again later.';
      }
      return message || 'An unexpected error occurred.';
  }
};

// Backward compatibility exports
export const useApi = useAsyncOperations;
export const useAsyncOperation = useAsyncOperations;
export const useErrorHandler = (options = {}) => {
  const { handleError } = useAsyncOperations(options);
  return { handleError };
};