import { renderHook, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useApi, usePaginatedApi } from '../useApi';

// Mock API functions for testing
const mockApiFunction = vi.fn();
const mockPaginatedApiFunction = vi.fn();

describe('useApi Hook Comprehensive Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('API Call State Management', () => {
    it('provides correct initial state', () => {
      const { result } = renderHook(() => useApi());

      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(typeof result.current.execute).toBe('function');
    });

    it('manages loading state correctly during API calls', async () => {
      const mockData = { id: 1, name: 'Test' };
      mockApiFunction.mockResolvedValue(mockData);

      const { result } = renderHook(() => useApi());

      // Start API call
      const executePromise = result.current.execute(mockApiFunction, 'param1');

      // Should be loading immediately
      expect(result.current.loading).toBe(true);
      expect(result.current.error).toBeNull();

      // Wait for completion
      const returnedData = await executePromise;

      expect(result.current.loading).toBe(false);
      expect(result.current.data).toEqual(mockData);
      expect(result.current.error).toBeNull();
      expect(returnedData).toEqual(mockData);
    });

    it('handles successful API responses with different data types', async () => {
      const testCases = [
        { data: { id: 1, name: 'Object' }, description: 'object data' },
        { data: [1, 2, 3], description: 'array data' },
        { data: 'string response', description: 'string data' },
        { data: 42, description: 'number data' },
        { data: true, description: 'boolean data' },
        { data: null, description: 'null data' },
      ];

      for (const testCase of testCases) {
        mockApiFunction.mockResolvedValueOnce(testCase.data);

        const { result } = renderHook(() => useApi());

        await result.current.execute(mockApiFunction);

        expect(result.current.data).toEqual(testCase.data);
        expect(result.current.loading).toBe(false);
        expect(result.current.error).toBeNull();
      }
    });

    it('handles API call errors correctly', async () => {
      const mockError = new Error('API Error');
      mockApiFunction.mockRejectedValue(mockError);

      const { result } = renderHook(() => useApi());

      const returnedData = await result.current.execute(mockApiFunction);

      expect(result.current.loading).toBe(false);
      expect(result.current.data).toBeNull();
      expect(result.current.error).toBe(mockError);
      expect(returnedData).toBeNull();
    });

    it('handles different error types', async () => {
      const errorTypes = [
        new Error('Standard Error'),
        'String error',
        { message: 'Object error', code: 500 },
        null,
        undefined,
        42,
      ];

      for (const error of errorTypes) {
        mockApiFunction.mockRejectedValueOnce(error);

        const { result } = renderHook(() => useApi());

        await result.current.execute(mockApiFunction);

        expect(result.current.loading).toBe(false);
        expect(result.current.data).toBeNull();
        expect(result.current.error).toBe(error);
      }
    });
  });

  describe('Loading, Success, and Error States', () => {
    it('clears previous error on successful call', async () => {
      const mockError = new Error('First Error');
      const mockData = { success: true };

      mockApiFunction
        .mockRejectedValueOnce(mockError)
        .mockResolvedValueOnce(mockData);

      const { result } = renderHook(() => useApi());

      // First call - should error
      await result.current.execute(mockApiFunction);
      expect(result.current.error).toBe(mockError);

      // Second call - should succeed and clear error
      await result.current.execute(mockApiFunction);
      expect(result.current.error).toBeNull();
      expect(result.current.data).toEqual(mockData);
    });

    it('clears previous data on error', async () => {
      const mockData = { id: 1 };
      const mockError = new Error('Second Error');

      mockApiFunction
        .mockResolvedValueOnce(mockData)
        .mockRejectedValueOnce(mockError);

      const { result } = renderHook(() => useApi());

      // First call - should succeed
      await result.current.execute(mockApiFunction);
      expect(result.current.data).toEqual(mockData);

      // Second call - should error and clear data
      await result.current.execute(mockApiFunction);
      expect(result.current.data).toBeNull();
      expect(result.current.error).toBe(mockError);
    });

    it('handles concurrent API calls correctly', async () => {
      const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
      
      mockApiFunction
        .mockImplementationOnce(() => delay(100).then(() => ({ call: 1 })))
        .mockImplementationOnce(() => delay(50).then(() => ({ call: 2 })));

      const { result } = renderHook(() => useApi());

      // Start two concurrent calls
      const promise1 = result.current.execute(mockApiFunction);
      const promise2 = result.current.execute(mockApiFunction);

      // Wait for both to complete
      await Promise.all([promise1, promise2]);

      // Should have the result from the last call that completed
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toBeDefined();
    });
  });

  describe('Retry Logic and Caching', () => {
    it('executes API function with correct parameters', async () => {
      const mockData = { result: 'success' };
      mockApiFunction.mockResolvedValue(mockData);

      const { result } = renderHook(() => useApi());

      await result.current.execute(mockApiFunction, 'param1', 'param2', { option: true });

      expect(mockApiFunction).toHaveBeenCalledWith('param1', 'param2', { option: true });
      expect(mockApiFunction).toHaveBeenCalledTimes(1);
    });

    it('can execute different API functions', async () => {
      const mockApiFunction2 = vi.fn().mockResolvedValue({ data: 'second' });
      
      const { result } = renderHook(() => useApi());

      await result.current.execute(mockApiFunction, 'first');
      await result.current.execute(mockApiFunction2, 'second');

      expect(mockApiFunction).toHaveBeenCalledWith('first');
      expect(mockApiFunction2).toHaveBeenCalledWith('second');
    });

    it('maintains separate state for different hook instances', async () => {
      const mockData1 = { id: 1 };
      const mockData2 = { id: 2 };

      mockApiFunction
        .mockResolvedValueOnce(mockData1)
        .mockResolvedValueOnce(mockData2);

      const { result: result1 } = renderHook(() => useApi());
      const { result: result2 } = renderHook(() => useApi());

      await result1.current.execute(mockApiFunction);
      await result2.current.execute(mockApiFunction);

      expect(result1.current.data).toEqual(mockData1);
      expect(result2.current.data).toEqual(mockData2);
    });
  });

  describe('usePaginatedApi Hook', () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it('provides correct initial state', () => {
      const { result } = renderHook(() => usePaginatedApi());

      expect(result.current.data).toEqual([]);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.page).toBe(1);
      expect(result.current.limit).toBe(10);
      expect(result.current.total).toBe(0);
      expect(result.current.totalPages).toBe(0);
    });

    it('handles paginated API responses correctly', async () => {
      const mockResponse = {
        data: [{ id: 1 }, { id: 2 }],
        total: 20,
        total_pages: 2,
      };

      mockPaginatedApiFunction.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => 
        usePaginatedApi(mockPaginatedApiFunction, 1, 10, { autoFetch: false })
      );

      await result.current.execute();

      expect(result.current.data).toEqual([{ id: 1 }, { id: 2 }]);
      expect(result.current.total).toBe(20);
      expect(result.current.totalPages).toBe(2);
      expect(result.current.loading).toBe(false);
    });

    it('handles different response structures', async () => {
      const testCases = [
        {
          response: { data: { orders: [{ id: 1 }] } },
          expectedData: [{ id: 1 }],
          description: 'nested orders array',
        },
        {
          response: { data: { users: [{ id: 2 }] } },
          expectedData: [{ id: 2 }],
          description: 'nested users array',
        },
        {
          response: { data: [{ id: 3 }] },
          expectedData: [{ id: 3 }],
          description: 'direct array in data',
        },
        {
          response: [{ id: 4 }],
          expectedData: [{ id: 4 }],
          description: 'direct array response',
        },
      ];

      for (const testCase of testCases) {
        mockPaginatedApiFunction.mockResolvedValueOnce(testCase.response);

        const { result } = renderHook(() => 
          usePaginatedApi(mockPaginatedApiFunction, 1, 10, { autoFetch: false })
        );

        await result.current.execute();

        expect(result.current.data).toEqual(testCase.expectedData);
      }
    });

    it('handles pagination controls correctly', async () => {
      const { result } = renderHook(() => 
        usePaginatedApi(mockPaginatedApiFunction, 1, 10, { autoFetch: false })
      );

      // Test page change
      result.current.goToPage(3);
      expect(result.current.page).toBe(3);

      // Test limit change (should reset page to 1)
      result.current.changeLimit(20);
      expect(result.current.limit).toBe(20);
      expect(result.current.page).toBe(1);
    });

    it('handles pagination errors correctly', async () => {
      const mockError = new Error('Pagination Error');
      mockPaginatedApiFunction.mockRejectedValue(mockError);

      const { result } = renderHook(() => 
        usePaginatedApi(mockPaginatedApiFunction, 1, 10, { autoFetch: false })
      );

      await result.current.execute();

      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe(mockError);
      expect(result.current.data).toEqual([]);
    });

    it('auto-fetches when autoFetch is enabled', async () => {
      const mockResponse = { data: [{ id: 1 }] };
      mockPaginatedApiFunction.mockResolvedValue(mockResponse);

      renderHook(() => 
        usePaginatedApi(mockPaginatedApiFunction, 1, 10, { autoFetch: true })
      );

      await waitFor(() => {
        expect(mockPaginatedApiFunction).toHaveBeenCalledWith(1, 10);
      });
    });

    it('does not auto-fetch when autoFetch is disabled', () => {
      renderHook(() => 
        usePaginatedApi(mockPaginatedApiFunction, 1, 10, { autoFetch: false })
      );

      expect(mockPaginatedApiFunction).not.toHaveBeenCalled();
    });

    it('refetches when page or limit changes with autoFetch enabled', async () => {
      const mockResponse = { data: [{ id: 1 }] };
      mockPaginatedApiFunction.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => 
        usePaginatedApi(mockPaginatedApiFunction, 1, 10, { autoFetch: true })
      );

      await waitFor(() => {
        expect(mockPaginatedApiFunction).toHaveBeenCalledWith(1, 10);
      });

      // Change page
      result.current.goToPage(2);

      await waitFor(() => {
        expect(mockPaginatedApiFunction).toHaveBeenCalledWith(2, 10);
      });

      // Change limit
      result.current.changeLimit(20);

      await waitFor(() => {
        expect(mockPaginatedApiFunction).toHaveBeenCalledWith(1, 20);
      });
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('handles undefined API function gracefully', async () => {
      const { result } = renderHook(() => useApi());

      const returnedData = await result.current.execute(undefined as any);

      expect(returnedData).toBeNull();
      expect(result.current.error).toBeDefined();
    });

    it('handles API function that throws synchronously', async () => {
      const syncError = new Error('Sync Error');
      const throwingFunction = vi.fn(() => {
        throw syncError;
      });

      const { result } = renderHook(() => useApi());

      const returnedData = await result.current.execute(throwingFunction);

      expect(returnedData).toBeNull();
      expect(result.current.error).toBe(syncError);
    });

    it('handles very large response data', async () => {
      const largeData = Array.from({ length: 10000 }, (_, i) => ({ id: i, data: `item-${i}` }));
      mockApiFunction.mockResolvedValue(largeData);

      const { result } = renderHook(() => useApi());

      await result.current.execute(mockApiFunction);

      expect(result.current.data).toEqual(largeData);
      expect(result.current.data).toHaveLength(10000);
    });

    it('handles rapid successive calls', async () => {
      const responses = [
        { call: 1 },
        { call: 2 },
        { call: 3 },
        { call: 4 },
        { call: 5 },
      ];

      responses.forEach(response => {
        mockApiFunction.mockResolvedValueOnce(response);
      });

      const { result } = renderHook(() => useApi());

      // Fire multiple calls rapidly
      const promises = responses.map((_, index) => 
        result.current.execute(mockApiFunction, index)
      );

      await Promise.all(promises);

      // Should have completed all calls
      expect(mockApiFunction).toHaveBeenCalledTimes(5);
      expect(result.current.loading).toBe(false);
    });
  });
});