import { useState, useCallback, useEffect } from 'react';

interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: any;
  execute: (apiFunc: (...args: any[]) => Promise<T>, ...args: any[]) => Promise<T | null>;
}

export const useApi = <T = any>(): UseApiReturn<T> => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<any>(null);

  const execute = useCallback(async (apiFunc: (...args: any[]) => Promise<T>, ...args: any[]): Promise<T | null> => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiFunc(...args);
      setData(result);
      return result;
    } catch (err) {
      setError(err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, execute };
};

interface UsePaginatedApiOptions {
  autoFetch?: boolean;
  showErrorToast?: boolean;
}

interface UsePaginatedApiReturn<T> {
  data: T[];
  loading: boolean;
  error: any;
  execute: (customApiCall?: () => Promise<any>) => Promise<any>;
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  goToPage: (newPage: number) => void;
  changeLimit: (newLimit: number) => void;
}

export const usePaginatedApi = <T = any>(
  apiCall?: (page: number, limit: number) => Promise<any>,
  initialPage: number = 1,
  initialLimit: number = 10,
  options: UsePaginatedApiOptions = {}
): UsePaginatedApiReturn<T> => {
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<any>(null);
  const [page, setPage] = useState<number>(initialPage);
  const [limit, setLimit] = useState<number>(initialLimit);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(0);

  const execute = useCallback(async (customApiCall?: () => Promise<any>) => {
    const callToUse = customApiCall || apiCall;
    if (!callToUse) {
      console.error('No API call provided to usePaginatedApi');
      return null;
    }
    
    setLoading(true);
    setError(null);
    try {
      const result = await callToUse();
      
      // Handle different response structures
      if (result?.data) {
        // Ensure data is always an array
        const dataArray = Array.isArray(result.data) ? result.data : [];
        setData(dataArray);
        
        // Check for pagination info
        if (result.pagination) {
          setTotal(result.pagination.total || 0);
          setTotalPages(result.pagination.pages || 0);
        } else if (result.total !== undefined) {
          setTotal(result.total);
          setTotalPages(result.total_pages || Math.ceil(result.total / limit));
        }
      } else if (Array.isArray(result)) {
        setData(result);
      } else {
        // Fallback to empty array if result is not in expected format
        setData([]);
      }
      
      return result;
    } catch (err) {
      setError(err);
      if (options.showErrorToast !== false) {
        console.error('API Error:', err);
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, [apiCall, page, limit, options.showErrorToast]);

  const goToPage = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const changeLimit = useCallback((newLimit: number) => {
    setLimit(newLimit);
    setPage(1); // Reset to first page when changing limit
  }, []);

  useEffect(() => {
    if (options.autoFetch !== false && apiCall) {
      execute();
    }
  }, [page, limit, execute, options.autoFetch, apiCall]);

  return {
    data,
    loading,
    error,
    execute,
    page,
    limit,
    total,
    totalPages,
    goToPage,
    changeLimit,
  };
};
