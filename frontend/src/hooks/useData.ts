import { useState, useMemo, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAsyncOperations } from './useAsync';

interface PaginationOptions {
  initialPage?: number;
  initialPageSize?: number;
  totalItems?: number;
  useUrlParams?: boolean;
  pageParam?: string;
  pageSizeParam?: string;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
}

interface UsePaginatedApiOptions {
  autoFetch?: boolean;
  showErrorToast?: boolean;
}

/**
 * Consolidated hook for pagination logic
 * Merges: usePagination, usePaginatedData
 */
export const usePagination = (options: PaginationOptions = {}) => {
  const {
    initialPage = 1,
    initialPageSize = 10,
    totalItems = 0,
    useUrlParams = false,
    pageParam = 'page',
    pageSizeParam = 'pageSize',
    onPageChange,
    onPageSizeChange,
  } = options;

  const [searchParams, setSearchParams] = useSearchParams();
  
  const getInitialPage = useCallback(() => {
    if (useUrlParams) {
      const urlPage = searchParams.get(pageParam);
      return urlPage ? Math.max(1, parseInt(urlPage, 10)) : initialPage;
    }
    return initialPage;
  }, [useUrlParams, searchParams, pageParam, initialPage]);

  const getInitialPageSize = useCallback(() => {
    if (useUrlParams) {
      const urlPageSize = searchParams.get(pageSizeParam);
      return urlPageSize ? Math.max(1, parseInt(urlPageSize, 10)) : initialPageSize;
    }
    return initialPageSize;
  }, [useUrlParams, searchParams, pageSizeParam, initialPageSize]);

  const [currentPage, setCurrentPage] = useState(getInitialPage);
  const [pageSize, setPageSizeState] = useState(getInitialPageSize);
  const [totalItemsState, setTotalItemsState] = useState(totalItems);

  const updateUrlParams = useCallback((page: number, size: number) => {
    if (useUrlParams) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set(pageParam, page.toString());
      newParams.set(pageSizeParam, size.toString());
      setSearchParams(newParams, { replace: true });
    }
  }, [useUrlParams, searchParams, pageParam, pageSizeParam, setSearchParams]);

  const totalPages = useMemo(() => {
    return Math.ceil(totalItemsState / pageSize);
  }, [totalItemsState, pageSize]);

  const canGoNext = useMemo(() => {
    return currentPage < totalPages;
  }, [currentPage, totalPages]);

  const canGoPrev = useMemo(() => {
    return currentPage > 1;
  }, [currentPage]);

  const startIndex = useMemo(() => {
    return (currentPage - 1) * pageSize;
  }, [currentPage, pageSize]);

  const endIndex = useMemo(() => {
    return Math.min(startIndex + pageSize - 1, totalItemsState - 1);
  }, [startIndex, pageSize, totalItemsState]);

  const isEmpty = useMemo(() => {
    return totalItemsState === 0;
  }, [totalItemsState]);

  const setPage = useCallback((page: number) => {
    const validPage = Math.max(1, Math.min(page, totalPages));
    setCurrentPage(validPage);
    updateUrlParams(validPage, pageSize);
    onPageChange?.(validPage);
  }, [totalPages, pageSize, updateUrlParams, onPageChange]);

  const setPageSize = useCallback((size: number) => {
    const validSize = Math.max(1, size);
    setPageSizeState(validSize);
    
    const newTotalPages = Math.ceil(totalItemsState / validSize);
    const newPage = Math.min(currentPage, newTotalPages || 1);
    
    setCurrentPage(newPage);
    updateUrlParams(newPage, validSize);
    onPageSizeChange?.(validSize);
  }, [totalItemsState, currentPage, updateUrlParams, onPageSizeChange]);

  const setTotalItems = useCallback((total: number) => {
    setTotalItemsState(Math.max(0, total));
    
    const newTotalPages = Math.ceil(total / pageSize);
    if (currentPage > newTotalPages && newTotalPages > 0) {
      setPage(newTotalPages);
    }
  }, [pageSize, currentPage, setPage]);

  const nextPage = useCallback(() => {
    if (canGoNext) {
      setPage(currentPage + 1);
    }
  }, [canGoNext, currentPage, setPage]);

  const prevPage = useCallback(() => {
    if (canGoPrev) {
      setPage(currentPage - 1);
    }
  }, [canGoPrev, currentPage, setPage]);

  const firstPage = useCallback(() => {
    setPage(1);
  }, [setPage]);

  const lastPage = useCallback(() => {
    if (totalPages > 0) {
      setPage(totalPages);
    }
  }, [totalPages, setPage]);

  const reset = useCallback(() => {
    setCurrentPage(initialPage);
    setPageSizeState(initialPageSize);
    setTotalItemsState(totalItems);
    if (useUrlParams) {
      const newParams = new URLSearchParams(searchParams);
      newParams.delete(pageParam);
      newParams.delete(pageSizeParam);
      setSearchParams(newParams, { replace: true });
    }
  }, [initialPage, initialPageSize, totalItems, useUrlParams, searchParams, pageParam, pageSizeParam, setSearchParams]);

  useEffect(() => {
    if (useUrlParams) {
      const urlPage = getInitialPage();
      const urlPageSize = getInitialPageSize();
      
      if (urlPage !== currentPage) {
        setCurrentPage(urlPage);
      }
      if (urlPageSize !== pageSize) {
        setPageSizeState(urlPageSize);
      }
    }
  }, [searchParams, useUrlParams, getInitialPage, getInitialPageSize, currentPage, pageSize]);

  useEffect(() => {
    setTotalItems(totalItems);
  }, [totalItems, setTotalItems]);

  return {
    currentPage,
    pageSize,
    totalItems: totalItemsState,
    totalPages,
    canGoNext,
    canGoPrev,
    startIndex,
    endIndex,
    isEmpty,
    setPage,
    setPageSize,
    setTotalItems,
    nextPage,
    prevPage,
    firstPage,
    lastPage,
    reset,
  };
};

/**
 * Hook for client-side paginated data
 */
export const usePaginatedData = <T>(
  data: T[],
  options: PaginationOptions = {}
) => {
  const pagination = usePagination({
    ...options,
    totalItems: data.length,
  });

  const paginatedData = useMemo(() => {
    const start = pagination.startIndex;
    const end = start + pagination.pageSize;
    return data.slice(start, end);
  }, [data, pagination.startIndex, pagination.pageSize]);

  return {
    ...pagination,
    data: paginatedData,
    originalData: data,
  };
};

/**
 * Hook for server-side paginated API calls
 * Merges: usePaginatedApi from useApi
 */
export const usePaginatedApi = <T = any>(
  apiCall?: (page: number, limit: number) => Promise<any>,
  initialPage: number = 1,
  initialLimit: number = 10,
  options: UsePaginatedApiOptions = {}
) => {
  const [data, setData] = useState<T[]>([]);
  const [page, setPage] = useState<number>(initialPage);
  const [limit, setLimit] = useState<number>(initialLimit);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(0);

  const { loading, error, execute } = useAsyncOperations({
    showErrorToast: options.showErrorToast
  });

  const executeApi = useCallback(async (customApiCall?: () => Promise<any>) => {
    const callToUse = customApiCall || apiCall;
    if (!callToUse) {
      console.error('No API call provided to usePaginatedApi');
      return null;
    }
    
    const result = await execute(async () => {
      return customApiCall ? await callToUse() : await callToUse(page, limit);
    });

    if (result?.data) {
      let dataArray: T[] = [];
      let totalCount = 0;
      let totalPagesCount = 0;
      
      // Handle different response structures
      if (Array.isArray(result.data)) {
        dataArray = result.data;
        totalCount = result.total || result.data.length;
        totalPagesCount = result.total_pages || result.pages || Math.ceil(totalCount / limit);
      } else if (typeof result.data === 'object') {
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
      setData([]);
      setTotal(0);
      setTotalPages(0);
    }
    
    return result;
  }, [apiCall, page, limit, execute]);

  const goToPage = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const changeLimit = useCallback((newLimit: number) => {
    setLimit(newLimit);
    setPage(1);
  }, []);

  useEffect(() => {
    if (options.autoFetch !== false && apiCall) {
      const timeoutId = setTimeout(() => {
        executeApi();
      }, 100);
      
      return () => clearTimeout(timeoutId);
    }
  }, [page, limit, executeApi, options.autoFetch, apiCall]);

  return {
    data,
    loading,
    error,
    execute: executeApi,
    page,
    limit,
    total,
    totalPages,
    goToPage,
    changeLimit,
  };
};