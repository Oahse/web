import { useState, useCallback, useEffect } from 'react';

export const useApi = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (apiFunc, ...args) => {
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

export const usePaginatedApi = (apiCall, initialPage = 1, initialLimit = 10, options = {}) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(initialPage);
  const [limit, setLimit] = useState(initialLimit);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiCall(page, limit);
      
      // Handle different response structures
      if (result?.data) {
        setData(result.data);
        
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

  const goToPage = useCallback((newPage) => {
    setPage(newPage);
  }, []);

  const changeLimit = useCallback((newLimit) => {
    setLimit(newLimit);
    setPage(1); // Reset to first page when changing limit
  }, []);

  useEffect(() => {
    if (options.autoFetch !== false) {
      execute();
    }
  }, [page, limit, execute, options.autoFetch]);

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
