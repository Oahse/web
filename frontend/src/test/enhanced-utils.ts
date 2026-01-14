/**
 * Enhanced Test Utilities for Frontend Test Coverage
 * Provides comprehensive testing utilities without JSX dependencies
 */

import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { ReactElement, ReactNode, createElement } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { TEST_CONFIG, PROPERTY_TEST_CONFIG } from './test-config';
import * as fc from 'fast-check';

// Test configuration interfaces
export interface TestRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialState?: any;
  queryClient?: QueryClient;
  routerProps?: {
    initialEntries?: string[];
    initialIndex?: number;
  };
}

export interface MockAPIResponse {
  data?: any;
  error?: any;
  status?: number;
  headers?: Record<string, string>;
}

export interface PropertyTestConfig {
  iterations?: number;
  timeout?: number;
  seed?: number;
  verbose?: boolean;
}

// Create a test query client
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

// Simple wrapper for basic testing
function SimpleWrapper({ children, queryClient }: { children: ReactNode; queryClient?: QueryClient }) {
  const testQueryClient = queryClient || createTestQueryClient();

  return createElement(
    BrowserRouter,
    null,
    createElement(
      QueryClientProvider,
      { client: testQueryClient },
      children
    )
  );
}

// Enhanced render function with minimal providers
export function renderWithProviders(
  ui: ReactElement,
  options: TestRenderOptions = {}
): RenderResult {
  const {
    queryClient,
    routerProps,
    ...renderOptions
  } = options;

  const Wrapper = ({ children }: { children: ReactNode }) => 
    createElement(SimpleWrapper, { queryClient, children });

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

// Render with specific router configuration
export function renderWithRouter(
  ui: ReactElement,
  options: TestRenderOptions = {}
): RenderResult {
  const { routerProps, ...otherOptions } = options;

  const Wrapper = ({ children }: { children: ReactNode }) => 
    createElement(BrowserRouter, { ...routerProps, children });

  return render(ui, { wrapper: Wrapper, ...otherOptions });
}

// Mock data generators for testing
export const mockUsers = {
  customer: {
    id: '1',
    email: 'customer@test.com',
    firstname: 'John',
    lastname: 'Doe',
    role: 'Customer' as const,
    verified: true,
    phone: '+1234567890',
    created_at: '2023-01-01T00:00:00Z',
  },
  admin: {
    id: '2',
    email: 'admin@test.com',
    firstname: 'Admin',
    lastname: 'User',
    role: 'Admin' as const,
    verified: true,
    phone: '+1234567891',
    created_at: '2023-01-01T00:00:00Z',
  },
  supplier: {
    id: '3',
    email: 'supplier@test.com',
    firstname: 'Supplier',
    lastname: 'User',
    role: 'Supplier' as const,
    verified: true,
    phone: '+1234567892',
    created_at: '2023-01-01T00:00:00Z',
  },
};

export const mockProducts = {
  simple: {
    id: '1',
    name: 'Test Product',
    description: 'A test product for testing',
    price: 29.99,
    category: 'Electronics',
    brand: 'TestBrand',
    sku: 'TEST-001',
    stock_quantity: 100,
    is_active: true,
    images: ['https://example.com/image1.jpg'],
    variants: [],
    created_at: '2023-01-01T00:00:00Z',
  },
  withVariants: {
    id: '2',
    name: 'Variable Product',
    description: 'A product with variants',
    price: 49.99,
    category: 'Clothing',
    brand: 'TestBrand',
    sku: 'VAR-001',
    stock_quantity: 50,
    is_active: true,
    images: ['https://example.com/image2.jpg'],
    variants: [
      {
        id: '1',
        name: 'Small Red',
        price: 49.99,
        sku: 'VAR-001-SM-RED',
        stock_quantity: 10,
        attributes: { size: 'Small', color: 'Red' },
      },
    ],
    created_at: '2023-01-01T00:00:00Z',
  },
};

// Property-based testing utilities
export function runPropertyTest<T>(
  name: string,
  arbitrary: fc.Arbitrary<T>,
  predicate: (value: T) => boolean | void,
  config: Partial<PropertyTestConfig> = {}
): void {
  const testConfig = { ...PROPERTY_TEST_CONFIG, ...config };
  
  fc.assert(
    fc.property(arbitrary, predicate),
    {
      numRuns: testConfig.numRuns,
      timeout: testConfig.timeout,
      seed: testConfig.seed,
      verbose: testConfig.verbose,
    }
  );
}

export function runAsyncPropertyTest<T>(
  name: string,
  arbitrary: fc.Arbitrary<T>,
  predicate: (value: T) => Promise<boolean | void>,
  config: Partial<PropertyTestConfig> = {}
): Promise<void> {
  const testConfig = { ...PROPERTY_TEST_CONFIG, ...config };
  
  return fc.assert(
    fc.asyncProperty(arbitrary, predicate),
    {
      numRuns: testConfig.numRuns,
      timeout: testConfig.timeout,
      seed: testConfig.seed,
      verbose: testConfig.verbose,
    }
  );
}

// Data generators for property-based testing
export const userArbitrary = fc.record({
  id: fc.string({ minLength: 1, maxLength: 50 }),
  email: fc.emailAddress(),
  firstname: fc.string({ minLength: 1, maxLength: 50 }),
  lastname: fc.string({ minLength: 1, maxLength: 50 }),
  role: fc.constantFrom('Admin', 'Customer', 'Supplier'),
  verified: fc.boolean(),
  phone: fc.option(fc.string({ minLength: 10, maxLength: 15 })),
  created_at: fc.date({ min: new Date('2020-01-01'), max: new Date() }).map(d => d.toISOString()),
});

export const productArbitrary = fc.record({
  id: fc.string({ minLength: 1, maxLength: 50 }),
  name: fc.string({ minLength: 1, maxLength: 200 }),
  description: fc.string({ minLength: 10, maxLength: 1000 }),
  price: fc.float({ min: Math.fround(0.01), max: Math.fround(10000), noNaN: true }),
  category: fc.constantFrom('Electronics', 'Clothing', 'Books', 'Home', 'Sports'),
  brand: fc.string({ minLength: 1, maxLength: 50 }),
  sku: fc.string({ minLength: 1, maxLength: 50 }),
  stock_quantity: fc.integer({ min: 0, max: 1000 }),
  is_active: fc.boolean(),
  images: fc.array(fc.webUrl(), { minLength: 0, maxLength: 5 }),
  created_at: fc.date({ min: new Date('2020-01-01'), max: new Date() }).map(d => d.toISOString()),
});

// Mock API utilities
export function createMockResponse(data: any, status: number = 200): MockAPIResponse {
  return {
    data,
    status,
    headers: {
      'content-type': 'application/json',
    },
  };
}

export function createMockError(
  message: string,
  status: number = 500,
  code?: string
): MockAPIResponse {
  return {
    error: {
      message,
      code: code || status.toString(),
      statusCode: status,
    },
    status,
  };
}

// Test performance utilities
export function measureRenderTime(renderFn: () => void): number {
  const start = performance.now();
  renderFn();
  const end = performance.now();
  return end - start;
}

// Form testing utilities
export function fillForm(container: HTMLElement, values: Record<string, string>): void {
  Object.entries(values).forEach(([name, value]) => {
    const input = container.querySelector(`[name="${name}"]`) as HTMLInputElement;
    if (input) {
      input.value = value;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
}

// Wait utilities
export function waitForAsync(ms: number = 0): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Random data generators
export function generateRandomString(length: number = 10): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

export function generateRandomEmail(): string {
  return `${generateRandomString(8)}@${generateRandomString(5)}.com`;
}

export function generateRandomNumber(min: number = 0, max: number = 100): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

// Re-export commonly used testing utilities
export * from '@testing-library/react';
export * from '@testing-library/user-event';
export { vi, expect, describe, it, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';
export * as fc from 'fast-check';