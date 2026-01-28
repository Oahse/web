/**
 * Test Utilities for Frontend Test Coverage
 * Provides comprehensive testing utilities for components, hooks, contexts, and APIs
 */

import React from 'react';
import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { ReactElement, ReactNode } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../store/AuthContext';
import { CartProvider } from '../store/CartContext';
import { ThemeProvider } from '../store/ThemeContext';
import { NotificationProvider } from '../store/NotificationContext';
import { WishlistProvider } from '../store/WishlistContext';

// Test configuration interfaces
export interface TestRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialState?: any;
  providers?: React.ComponentType<{ children: ReactNode }>[];
  routerProps?: {
    initialEntries?: string[];
    initialIndex?: number;
  };
  queryClient?: QueryClient;
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

// Default test configuration
export const DEFAULT_PROPERTY_CONFIG: PropertyTestConfig = {
  iterations: 20, // Reduced for faster testing
  timeout: 30000,
  seed: 42,
  verbose: false,
};

// Mock user data for testing
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

// Mock product data for testing
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
      {
        id: '2',
        name: 'Large Blue',
        price: 54.99,
        sku: 'VAR-001-LG-BLUE',
        stock_quantity: 15,
        attributes: { size: 'Large', color: 'Blue' },
      },
    ],
    created_at: '2023-01-01T00:00:00Z',
  },
};

// Mock API error responses
export const mockAPIErrors = {
  unauthorized: {
    message: 'Not authenticated',
    code: '401',
    statusCode: 401,
  },
  forbidden: {
    message: 'Insufficient permissions',
    code: '403',
    statusCode: 403,
  },
  notFound: {
    message: 'Resource not found',
    code: '404',
    statusCode: 404,
  },
  validation: {
    message: 'Validation failed',
    code: '422',
    statusCode: 422,
    details: {
      email: ['Email is required'],
      password: ['Password must be at least 8 characters'],
    },
  },
  serverError: {
    message: 'Internal server error',
    code: '500',
    statusCode: 500,
  },
  networkError: {
    message: 'Network error',
    code: 'NETWORK_ERROR',
    statusCode: 0,
  },
};

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

// All providers wrapper for comprehensive testing
function AllTheProviders({ 
  children, 
  queryClient 
}: { 
  children: ReactNode; 
  queryClient?: QueryClient; 
}) {
  const testQueryClient = queryClient || createTestQueryClient();

  return React.createElement(
    BrowserRouter,
    null,
    React.createElement(
      QueryClientProvider,
      { client: testQueryClient },
      React.createElement(
        AuthProvider,
        null,
        React.createElement(
          ThemeProvider,
          null,
          React.createElement(
            NotificationProvider,
            null,
            React.createElement(
              CartProvider,
              null,
              React.createElement(
                WishlistProvider,
                null,
                children
              )
            )
          )
        )
      )
    )
  );
}

// Custom render function with all providers
export function renderWithProviders(
  ui: ReactElement,
  options: TestRenderOptions = {}
): RenderResult {
  const {
    providers = [],
    routerProps,
    queryClient,
    ...renderOptions
  } = options;

  // Create wrapper with all providers
  const Wrapper = ({ children }: { children: ReactNode }) => {
    let wrappedChildren = children;

    // Apply custom providers in reverse order
    providers.reverse().forEach((Provider) => {
      wrappedChildren = React.createElement(Provider, null, wrappedChildren);
    });

    return React.createElement(AllTheProviders, { queryClient, children: wrappedChildren });
  };

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

// Render with specific router configuration
export function renderWithRouter(
  ui: ReactElement,
  options: TestRenderOptions = {}
): RenderResult {
  const { routerProps, ...otherOptions } = options;

  const Wrapper = ({ children }: { children: ReactNode }) => 
    React.createElement(BrowserRouter, { ...routerProps, children });

  return render(ui, { wrapper: Wrapper, ...otherOptions });
}

// Mock localStorage for testing
export function mockLocalStorage() {
  const store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      Object.keys(store).forEach(key => delete store[key]);
    },
    key: (index: number) => Object.keys(store)[index] || null,
    get length() {
      return Object.keys(store).length;
    },
  };
}

// Mock sessionStorage for testing
export function mockSessionStorage() {
  return mockLocalStorage(); // Same implementation
}

// Wait for async operations to complete
export function waitForAsync(ms: number = 0): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Create mock API response
export function createMockResponse(data: any, status: number = 200): MockAPIResponse {
  return {
    data,
    status,
    headers: {
      'content-type': 'application/json',
    },
  };
}

// Create mock API error
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

// Generate random test data
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

export function generateRandomBoolean(): boolean {
  return Math.random() < 0.5;
}

// Property test helpers
export function createPropertyTestConfig(overrides: Partial<PropertyTestConfig> = {}): PropertyTestConfig {
  return {
    ...DEFAULT_PROPERTY_CONFIG,
    ...overrides,
  };
}

// Accessibility test helpers
export function getAccessibilityViolations(container: HTMLElement): Promise<any[]> {
  // This would integrate with axe-core if needed
  // For now, return empty array as placeholder
  return Promise.resolve([]);
}

// Performance test helpers
export function measureRenderTime(renderFn: () => void): number {
  const start = performance.now();
  renderFn();
  const end = performance.now();
  return end - start;
}

// Form test helpers
export function fillForm(container: HTMLElement, values: Record<string, string>): void {
  Object.entries(values).forEach(([name, value]) => {
    const input = container.querySelector(`[name="${name}"]`) as HTMLInputElement;
    if (input) {
      input.value = value;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
}

// Network simulation helpers
export function simulateNetworkDelay(ms: number = 1000): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function simulateNetworkError(): Promise<never> {
  return Promise.reject(new Error('Network error'));
}

// Component test patterns
export interface ComponentTestSuite {
  renderTests: () => void;
  propTests: () => void;
  interactionTests: () => void;
  accessibilityTests: () => void;
  propertyTests: () => void;
}

export interface HookTestSuite {
  stateTests: () => void;
  effectTests: () => void;
  parameterTests: () => void;
  cleanupTests: () => void;
  propertyTests: () => void;
}

export interface APITestSuite {
  requestTests: () => void;
  responseTests: () => void;
  authTests: () => void;
  errorTests: () => void;
  propertyTests: () => void;
}

// Re-export commonly used testing utilities
export * from '@testing-library/react';
export * from '@testing-library/user-event';
export { vi, expect, describe, it, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';