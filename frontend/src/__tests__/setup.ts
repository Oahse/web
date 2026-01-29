/**
 * Test setup and utilities
 */
import { vi } from 'vitest';
import '@testing-library/jest-dom';

// Mock user data
export const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  username: 'testuser',
  phone: '+1234567890',
  country: 'US',
  is_verified: true,
  role: 'customer',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
};

// Mock admin user
export const mockAdminUser = {
  ...mockUser,
  id: 'admin-123',
  email: 'admin@example.com',
  first_name: 'Admin',
  last_name: 'User',
  role: 'admin'
};

// Mock product data
export const mockProduct = {
  id: 'product-123',
  name: 'Test Product',
  description: 'A test product for testing',
  brand: 'Test Brand',
  category: {
    id: 'category-123',
    name: 'Test Category',
    description: 'Test category'
  },
  variants: [
    {
      id: 'variant-123',
      name: 'Test Variant',
      sku: 'TEST-001',
      price: 99.99,
      sale_price: 79.99,
      weight: 1.0,
      is_active: true,
      inventory: {
        quantity_available: 50,
        quantity_reserved: 0
      }
    }
  ],
  images: [
    {
      id: 'image-123',
      url: 'https://example.com/image.jpg',
      alt_text: 'Test product image',
      is_primary: true
    }
  ],
  is_active: true,
  is_featured: false,
  rating: 4.5,
  review_count: 10,
  created_at: '2024-01-01T00:00:00Z'
};

// Mock cart data
export const mockCart = {
  id: 'cart-123',
  items: [
    {
      id: 'cart-item-123',
      variant_id: 'variant-123',
      quantity: 2,
      price_per_unit: 79.99,
      total_price: 159.98,
      variant: {
        id: 'variant-123',
        name: 'Test Variant',
        sku: 'TEST-001',
        price: 79.99,
        product: {
          id: 'product-123',
          name: 'Test Product',
          images: [
            {
              url: 'https://example.com/image.jpg',
              alt_text: 'Test product image'
            }
          ]
        }
      }
    }
  ],
  subtotal: 159.98,
  tax_amount: 14.00,
  shipping_cost: 9.99,
  discount_amount: 0,
  total: 183.97,
  currency: 'USD',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
};

// Mock order data
export const mockOrder = {
  id: 'order-123',
  order_number: 'ORD-2024-001',
  status: 'pending',
  payment_status: 'paid',
  items: [
    {
      id: 'order-item-123',
      variant_id: 'variant-123',
      quantity: 2,
      price_per_unit: 79.99,
      total_price: 159.98,
      variant: {
        id: 'variant-123',
        name: 'Test Variant',
        sku: 'TEST-001',
        product: {
          id: 'product-123',
          name: 'Test Product'
        }
      }
    }
  ],
  subtotal: 159.98,
  tax_amount: 14.00,
  shipping_cost: 9.99,
  discount_amount: 0,
  total_amount: 183.97,
  currency: 'USD',
  shipping_address: {
    street: '123 Test St',
    city: 'Test City',
    state: 'CA',
    country: 'US',
    postal_code: '12345'
  },
  billing_address: {
    street: '123 Test St',
    city: 'Test City',
    state: 'CA',
    country: 'US',
    postal_code: '12345'
  },
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
};

// Mock API responses
export const mockApiResponses = {
  auth: {
    login: {
      success: true,
      data: {
        user: mockUser,
        access_token: 'mock_access_token',
        refresh_token: 'mock_refresh_token',
        token_type: 'bearer',
        expires_in: 3600
      }
    },
    register: {
      success: true,
      data: {
        user: mockUser,
        message: 'Registration successful'
      }
    },
    profile: {
      success: true,
      data: mockUser
    }
  },
  products: {
    list: {
      success: true,
      data: [mockProduct],
      pagination: {
        page: 1,
        limit: 20,
        total: 1,
        pages: 1
      }
    },
    detail: {
      success: true,
      data: mockProduct
    }
  },
  cart: {
    get: {
      success: true,
      data: mockCart
    },
    add: {
      success: true,
      data: mockCart
    }
  },
  orders: {
    list: {
      success: true,
      data: [mockOrder],
      pagination: {
        page: 1,
        limit: 20,
        total: 1,
        pages: 1
      }
    },
    detail: {
      success: true,
      data: mockOrder
    },
    create: {
      success: true,
      data: mockOrder
    }
  }
};

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock fetch
global.fetch = vi.fn();

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: vi.fn(),
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
};

// Mock environment variables
vi.mock('../config/environment', () => ({
  API_BASE_URL: 'http://localhost:8000',
  STRIPE_PUBLISHABLE_KEY: 'pk_test_mock',
  ENVIRONMENT: 'test'
}));

// Test utilities
export const createMockEvent = (overrides = {}) => ({
  preventDefault: vi.fn(),
  stopPropagation: vi.fn(),
  target: { value: '' },
  ...overrides
});

export const createMockFile = (name = 'test.jpg', type = 'image/jpeg', size = 1024) => {
  const file = new File(['test'], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
};

export const waitForLoadingToFinish = () => {
  return new Promise(resolve => setTimeout(resolve, 0));
};

// Custom render function with providers
import React from 'react';
import { render, RenderOptions } from '@testing-library/react';

// Mock providers for testing
const MockProvider = ({ children }: { children: React.ReactNode }) => {
  return React.createElement('div', { 'data-testid': 'mock-provider' }, children);
};

export const renderWithProviders = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: MockProvider, ...options });

// Re-export everything from testing-library
export * from '@testing-library/react';
export { renderWithProviders as render };