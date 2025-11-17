import { useState, useMemo, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

export const usePagination = ({
  initialPage = 1,
  initialPageSize = 10,
  totalItems = 0,
  useUrlParams = false,
  pageParam = 'page',
  pageSizeParam = 'pageSize',
  onPageChange,
  onPageSizeChange,
} = {}) => {
  const [searchParams, setSearchParams] = useSearchParams();
  
  const getInitialPage = () => {
    if (useUrlParams) {
      const urlPage = searchParams.get(pageParam);
      return urlPage ? Math.max(1, parseInt(urlPage, 10)) : initialPage;
    }
    return initialPage;
  };

  const getInitialPageSize = () => {
    if (useUrlParams) {
      const urlPageSize = searchParams.get(pageSizeParam);
      return urlPageSize ? Math.max(1, parseInt(urlPageSize, 10)) : initialPageSize;
    }
    return initialPageSize;
  };

  const [currentPage, setCurrentPage] = useState(getInitialPage);
  const [pageSize, setPageSizeState] = useState(getInitialPageSize);
  const [totalItemsState, setTotalItemsState] = useState(totalItems);

  const updateUrlParams = (page, size) => {
    if (useUrlParams) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set(pageParam, page.toString());
      newParams.set(pageSizeParam, size.toString());
      setSearchParams(newParams, { replace: true });
    }
  };

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

  const setPage = (page) => {
    const validPage = Math.max(1, Math.min(page, totalPages));
    setCurrentPage(validPage);
    updateUrlParams(validPage, pageSize);
    onPageChange?.(validPage);
  };

  const setPageSize = (size) => {
    const validSize = Math.max(1, size);
    setPageSizeState(validSize);
    
    const newTotalPages = Math.ceil(totalItemsState / validSize);
    const newPage = Math.min(currentPage, newTotalPages || 1);
    
    setCurrentPage(newPage);
    updateUrlParams(newPage, validSize);
    onPageSizeChange?.(validSize);
  };

  const setTotalItems = (total) => {
    setTotalItemsState(Math.max(0, total));
    
    const newTotalPages = Math.ceil(total / pageSize);
    if (currentPage > newTotalPages && newTotalPages > 0) {
      setPage(newTotalPages);
    }
  };

  const nextPage = () => {
    if (canGoNext) {
      setPage(currentPage + 1);
    }
  };

  const prevPage = () => {
    if (canGoPrev) {
      setPage(currentPage - 1);
    }
  };

  const firstPage = () => {
    setPage(1);
  };

  const lastPage = () => {
    if (totalPages > 0) {
      setPage(totalPages);
    }
  };

  const reset = () => {
    setCurrentPage(initialPage);
    setPageSizeState(initialPageSize);
    setTotalItemsState(totalItems);
    if (useUrlParams) {
      const newParams = new URLSearchParams(searchParams);
      newParams.delete(pageParam);
      newParams.delete(pageSizeParam);
      setSearchParams(newParams, { replace: true });
    }
  };

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
  }, [totalItems]);

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

export const usePaginatedData = (
  data,
  options
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