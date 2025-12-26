/**
 * Property-Based Tests for useApi Hook
 * Feature: frontend-test-coverage, Property 7: Hook Return Value Stability
 * Validates: Requirements 2.3
 */

import { renderHook, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import * as fc from 'fast-check';
import { useApi, usePaginatedApi } from '../useApi';
import { runPropertyTest, apiResponseArbitrary } from '../../test/property-utils';

// Mock API functions for testing
const mockApiFunction = vi.fn();
const mockPaginatedApiFunction = vi.fn();

describe('useApi Hook Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Property 7: Hook Return Value Stability', () => {
    it('maintains consistent return value structure across different data types', () => {
      // Feature: frontend-test-coverage, Property 7: Hook Return Value Stability
      // Validates: Requirements 2.3
      
      runPropertyTest(
        'useApi return value structure consistency',
        fc.oneof(
          fc.record({ id: fc.integer(), name: fc.string() }), // object
          fc.array(fc.integer()), // array
          fc.string(), // string
          fc.integer(), // number
          fc.boolean(), // boolean
          fc.constant(null), // null
          fc.constant(undefined), // undefined
        ),
        async (mockData) => {
          mockApiFunction.mockResolvedValue(mockData);

          const { result } = renderHook(() => useApi());

          // Initial state should have consistent structure
          expect(result.current).toHaveProperty('data');
          expect(result.current).toHaveProperty('loading');
          expect(result.current).toHaveProperty('error');
          expect(result.current).toHaveProperty('execute');
          expect(typeof result.current.execute).toBe('function');

          // Execute API call
          await result.current.execute(mockApiFunction);

          // Return value structure should remain consistent
          expect(result.current).toHaveProperty('data');
          expect(result.current).toHaveProperty('loading');
          expect(result.current).toHaveProperty('error');
          expect(result.current).toHaveProperty('execute');
          expect(typeof result.current.execute).toBe('function');

          // Data should match what was returned
          expect(result.current.data).toEqual(mockData);
          expect(result.current.loading).toBe(false);
          expect(result.current.error).toBeNull();
        },
        { iterations: 50 }
      );
    });

    it('maintains consistent return values for error scenarios', () => {
      // Feature: frontend-test-coverage, Property 7: Hook Return Value Stability
      // Validates: Requirements 2.3
      
      runPropertyTest(
        'useApi error handling return value consistency',
        fc.oneof(
          fc.record({ message: fc.string(), code: fc.integer() }), // error object
          fc.string(), // string error
          fc.constant(null), // null error
          fc.constant(undefined), // undefined error
          fc.integer(), // number error
        ),
        async (mockError) => {
          mockApiFunction.mockRejectedValue(mockError);

          const { result } = renderHook(() => useApi());

          // Execute API call that will fail
          await result.current.execute(mockApiFunction);

          // Return value structure should remain consistent even on error
          expect(result.current).toHaveProperty('data');
          expect(result.current).toHaveProperty('loading');
          expect(result.current).toHaveProperty('error');
          expect(result.current).toHaveProperty('execute');
          expect(typeof result.current.execute).toBe('function');

          // Error state should be consistent
          expect(result.current.data).toBeNull();
          expect(result.current.loading).toBe(false);
          expect(result.current.error).toBe(mockError);
        },
        { iterations: 50 }
      );
    });

    it('maintains consistent execute function behavior with different parameters', () => {
      // Feature: frontend-test-coverage, Property 7: Hook Return Value Stability
      // Validates: Requirements 2.3
      
      runPropertyTest(
        'useApi execute function parameter consistency',
        fc.record({
          params: fc.array(fc.oneof(
            fc.string(),
            fc.integer(),
            fc.boolean(),
            fc.record({ key: fc.string() }),
            fc.constant(null),
            fc.constant(undefined),
          ), { minLength: 0, maxLength: 5 }),
          responseData: fc.oneof(
            fc.record({ result: fc.string() }),
            fc.array(fc.integer()),
            fc.string(),
          ),
        }),
        async ({ params, responseData }) => {
          mockApiFunction.mockResolvedValue(responseData);

          const { result } = renderHook(() => useApi());

          // Execute with different parameter combinations
          const returnedData = await result.current.execute(mockApiFunction, ...params);

          // Execute function should always return the same data that's stored in state
          expect(returnedData).toEqual(result.current.data);
          expect(returnedData).toEqual(responseData);

          // API function should be called with correct parameters
          expect(mockApiFunction).toHaveBeenCalledWith(...params);
        },
        { iterations: 50 }
      );
    });

    it('maintains consistent state transitions during loading', () => {
      // Feature: frontend-test-coverage, Property 7: Hook Return Value Stability
      // Validates: Requirements 2.3
      
      runPropertyTest(
        'useApi loading state transition consistency',
        fc.record({
          delay: fc.integer({ min: 0, max: 100 }),
          responseData: fc.oneof(
            fc.record({ id: fc.integer() }),
            fc.array(fc.string()),
            fc.string(),
          ),
        }),
        async ({ delay, responseData }) => {
          // Mock API with delay
          mockApiFunction.mockImplementation(() => 
            new Promise(resolve => 
              setTimeout(() => resolve(responseData), delay)
            )
          );

          const { result } = renderHook(() => useApi());

          // Initial state should be consistent
          expect(result.current.loading).toBe(false);
          expect(result.current.data).toBeNull();
          expect(result.current.error).toBeNull();

          // Start API call
          const executePromise = result.current.execute(mockApiFunction);

          // Should be loading
          expect(result.current.loading).toBe(true);
          expect(result.current.data).toBeNull();
          expect(result.current.error).toBeNull();

          // Wait for completion
          await executePromise;

          // Final state should be consistent
          expect(result.current.loading).toBe(false);
          expect(result.current.data).toEqual(responseData);
          expect(result.current.error).toBeNull();
        },
        { iterations: 30 }
      );
    });

    it('maintains consistent return values across multiple hook instances', () => {
      // Feature: frontend-test-coverage, Property 7: Hook Return Value Stability
      // Validates: Requirements 2.3
      
      runPropertyTest(
        'useApi multiple instance consistency',
        fc.record({
          data1: fc.record({ id: fc.integer(), value: fc.string() }),
          data2: fc.record({ id: fc.integer(), value: fc.string() }),
        }),
        async ({ data1, data2 }) => {
          mockApiFunction
            .mockResolvedValueOnce(data1)
            .mockResolvedValueOnce(data2);

          const { result: result1 } = renderHook(() => useApi());
          const { result: result2 } = renderHook(() => useApi());

          // Both instances should have consistent initial structure
          expect(result1.current).toMatchObject({
            data: null,
            loading: false,
            error: null,
          });
          expect(result2.current).toMatchObject({
            data: null,
            loading: false,
            error: null,
          });

          // Execute different calls on each instance
          await result1.current.execute(mockApiFunction);
          await result2.current.execute(mockApiFunction);

          // Each instance should maintain its own consistent state
          expect(result1.current.data).toEqual(data1);
          expect(result2.current.data).toEqual(data2);

          // Both should have consistent structure
          expect(result1.current).toMatchObject({
            loading: false,
            error: null,
          });
          expect(result2.current).toMatchObject({
            loading: false,
            error: null,
          });
        },
        { iterations: 50 }
      );
    });

    it('maintains consistent paginated API return values', () => {
      // Feature: frontend-test-coverage, Property 7: Hook Return Value Stability
      // Validates: Requirements 2.3
      
      runPropertyTest(
        'usePaginatedApi return value consistency',
        fc.record({
          data: fc.array(fc.record({ id: fc.integer(), name: fc.string() }), { minLength: 0, maxLength: 20 }),
          total: fc.integer({ min: 0, max: 1000 }),
          page: fc.integer({ min: 1, max: 10 }),
          limit: fc.integer({ min: 1, max: 100 }),
        }),
        async ({ data, total, page, limit }) => {
          const mockResponse = {
            data,
            total,
            total_pages: Math.ceil(total / limit),
          };

          mockPaginatedApiFunction.mockResolvedValue(mockResponse);

          const { result } = renderHook(() => 
            usePaginatedApi(mockPaginatedApiFunction, page, limit, { autoFetch: false })
          );

          // Initial state should have consistent structure
          expect(result.current).toHaveProperty('data');
          expect(result.current).toHaveProperty('loading');
          expect(result.current).toHaveProperty('error');
          expect(result.current).toHaveProperty('execute');
          expect(result.current).toHaveProperty('page');
          expect(result.current).toHaveProperty('limit');
          expect(result.current).toHaveProperty('total');
          expect(result.current).toHaveProperty('totalPages');
          expect(result.current).toHaveProperty('goToPage');
          expect(result.current).toHaveProperty('changeLimit');

          // Execute API call
          await result.current.execute();

          // Return value structure should remain consistent
          expect(result.current.data).toEqual(data);
          expect(result.current.total).toBe(total);
          expect(result.current.page).toBe(page);
          expect(result.current.limit).toBe(limit);
          expect(result.current.loading).toBe(false);
          expect(result.current.error).toBeNull();

          // Function properties should remain functions
          expect(typeof result.current.execute).toBe('function');
          expect(typeof result.current.goToPage).toBe('function');
          expect(typeof result.current.changeLimit).toBe('function');
        },
        { iterations: 50 }
      );
    });

    it('maintains consistent return values during pagination operations', () => {
      // Feature: frontend-test-coverage, Property 7: Hook Return Value Stability
      // Validates: Requirements 2.3
      
      runPropertyTest(
        'usePaginatedApi pagination operation consistency',
        fc.record({
          initialPage: fc.integer({ min: 1, max: 5 }),
          newPage: fc.integer({ min: 1, max: 10 }),
          initialLimit: fc.integer({ min: 5, max: 20 }),
          newLimit: fc.integer({ min: 10, max: 50 }),
        }),
        async ({ initialPage, newPage, initialLimit, newLimit }) => {
          const { result } = renderHook(() => 
            usePaginatedApi(mockPaginatedApiFunction, initialPage, initialLimit, { autoFetch: false })
          );

          // Initial values should match parameters
          expect(result.current.page).toBe(initialPage);
          expect(result.current.limit).toBe(initialLimit);

          // Change page
          result.current.goToPage(newPage);
          expect(result.current.page).toBe(newPage);
          expect(result.current.limit).toBe(initialLimit); // limit should remain unchanged

          // Change limit (should reset page to 1)
          result.current.changeLimit(newLimit);
          expect(result.current.page).toBe(1);
          expect(result.current.limit).toBe(newLimit);

          // All other properties should remain consistent
          expect(result.current).toHaveProperty('data');
          expect(result.current).toHaveProperty('loading');
          expect(result.current).toHaveProperty('error');
          expect(result.current).toHaveProperty('total');
          expect(result.current).toHaveProperty('totalPages');
        },
        { iterations: 50 }
      );
    });
  });
});