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
}

/**
 * Hook for handling async operations with loading, error states, and optimistic updates
 */
export function useAsyncOperation<T = any>(
  options: UseAsyncOperationOptions = {}
) {
  const {
    onSuccess,
    onError,
    showSuccessToast = false,
    showErrorToast = true,
    successMessage = 'Operation completed successfully',
  } = options;

  const [state, setState] = useState<AsyncOperationState<T>>({
    data: null,
    loading: false,
    error: null,
  });

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
        const err = error as Error;
        setState({ data: null, loading: false, error: err });

        if (showErrorToast) {
          // Error toast is already shown by API client interceptor
          // Only show custom error if provided
          if (onError) {
            onError(err);
          }
        }

        throw error;
      }
    },
    [onSuccess, onError, showSuccessToast, showErrorToast, successMessage]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
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
  const { loading, error, execute, reset } = useAsyncOperation<T>(options);

  const executeWithOptimisticUpdate = useCallback(
    async (
      optimisticValue: T,
      asyncFn: () => Promise<T>
    ) => {
      // Store current data for rollback
      setPreviousData(data);
      
      // Apply optimistic update
      setData(optimisticValue);

      try {
        const result = await execute(asyncFn);
        setData(result);
        return result;
      } catch (error) {
        // Rollback on error
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
          setRetryCount(0); // Reset on success
          return result;
        } catch (error) {
          lastError = error as Error;
          setRetryCount(attempt + 1);

          if (attempt < maxRetries) {
            // Wait before retrying
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
