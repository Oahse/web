import { useState, useCallback } from 'react';
import { APIError } from '../apis/subscription';

// Generic hook for managing API call states
export function useAPICall<T = any>() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<APIError | null>(null);
  const [data, setData] = useState<T | null>(null);

  const execute = useCallback(async (apiCall: () => Promise<T>) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await apiCall();
      setData(result);
      return result;
    } catch (err) {
      const apiError = err as APIError;
      setError(apiError);
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setIsLoading(false);
    setError(null);
    setData(null);
  }, []);

  return {
    isLoading,
    error,
    data,
    execute,
    reset
  };
}

// Specific hook for subscription operations
export function useSubscriptionOperations() {
  const removeProductCall = useAPICall();
  const applyDiscountCall = useAPICall();
  const removeDiscountCall = useAPICall();
  const getDetailsCall = useAPICall();

  return {
    removeProduct: removeProductCall,
    applyDiscount: applyDiscountCall,
    removeDiscount: removeDiscountCall,
    getDetails: getDetailsCall,
  };
}

// Hook for managing multiple loading states
export function useLoadingStates() {
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, APIError | null>>({});

  const setLoading = useCallback((key: string, loading: boolean) => {
    setLoadingStates(prev => ({ ...prev, [key]: loading }));
  }, []);

  const setError = useCallback((key: string, error: APIError | null) => {
    setErrors(prev => ({ ...prev, [key]: error }));
  }, []);

  const clearError = useCallback((key: string) => {
    setErrors(prev => ({ ...prev, [key]: null }));
  }, []);

  const clearAllErrors = useCallback(() => {
    setErrors({});
  }, []);

  const isLoading = useCallback((key: string) => {
    return loadingStates[key] || false;
  }, [loadingStates]);

  const getError = useCallback((key: string) => {
    return errors[key] || null;
  }, [errors]);

  return {
    setLoading,
    setError,
    clearError,
    clearAllErrors,
    isLoading,
    getError,
    hasAnyLoading: Object.values(loadingStates).some(Boolean),
    hasAnyError: Object.values(errors).some(Boolean),
  };
}