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
      throw err; // Re-throw the error to be caught by the API client interceptor
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
      // If using the default apiCall, pass page and limit
      const result = customApiCall ? await callToUse() : await callToUse(page, limit);
      
      // Handle different response structures
      if (result?.data) {
        let dataArray: T[] = [];
        let totalCount = 0;
        let totalPagesCount = 0;
        
        // Check if result.data is directly an array
        if (Array.isArray(result.data)) {
          dataArray = result.data;
          totalCount = result.total || result.data.length;
          totalPagesCount = result.total_pages || result.pages || Math.ceil(totalCount / limit);
        } 
        // Check if result.data is an object with nested arrays (common backend pattern)
        else if (typeof result.data === 'object') {
          // First check if result.data.data exists (nested data structure)
          if (Array.isArray(result.data.data)) {
            dataArray = result.data.data;
            totalCount = result.data.total || result.total || result.data.data.length;
            totalPagesCount = result.data.pages || result.data.total_pages || result.pages || result.total_pages || Math.ceil(totalCount / limit);
          } else {
            // Look for common array property names
            const possibleArrayKeys = ['orders', 'users', 'products', 'variants', 'items', 'results', 'addresses', 'inventory_items', 'locations'];
            for (const key of possibleArrayKeys) {
              if (Array.isArray(result.data[key])) {
                dataArray = result.data[key];
                totalCount = result.data.total || result.total || dataArray.length;
                totalPagesCount = result.data.pages || result.data.total_pages || result.pages || result.total_pages || Math.ceil(totalCount / limit);
                break;
              }
            }
            
            // If no array found in nested properties, check if data itself should be treated as single item
            if (dataArray.length === 0 && Object.keys(result.data).length > 0) {
              totalCount = result.data.total || result.total || 0;
              totalPagesCount = result.data.total_pages || result.data.pages || result.pages || result.total_pages || Math.ceil(totalCount / limit);
            }
          }
        }
        
        setData(dataArray);
        setTotal(totalCount);
        setTotalPages(totalPagesCount);
        
        // Override with root level pagination info if available
        if (result.pagination) {
          setTotal(result.pagination.total || totalCount);
          setTotalPages(result.pagination.pages || result.pagination.total_pages || totalPagesCount);
        } else if (result.total !== undefined) {
          setTotal(result.total);
          setTotalPages(result.total_pages || result.pages || Math.ceil(result.total / limit));
        }
      } else if (Array.isArray(result)) {
        setData(result);
        setTotal(result.length);
        setTotalPages(Math.ceil(result.length / limit));
      } else {
        // Fallback to empty array if result is not in expected format
        setData([]);
        setTotal(0);
        setTotalPages(0);
      }
      
      return result;
    } catch (err) {
      setError(err);
      if (options.showErrorToast !== false) {
        console.error('API Error:', err);
      }
      throw err; // Re-throw the error
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
      // Add a small delay to prevent rapid successive API calls
      const timeoutId = setTimeout(() => {
        execute();
      }, 100);
      
      return () => clearTimeout(timeoutId);
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
