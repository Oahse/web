/**
 * Test setup and configuration
 */
import React from 'react';
import { beforeAll, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock environment variables
vi.mock('../config/environment', () => ({
  API_BASE_URL: 'http://localhost:8000/api',
  STRIPE_PUBLIC_KEY: 'pk_test_mock_key',
  ENVIRONMENT: 'test'
}));

// Mock API client
vi.mock('../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn()
  },
  TokenManager: {
    getToken: vi.fn(),
    setToken: vi.fn(),
    removeToken: vi.fn(),
    isTokenExpired: vi.fn(() => false)
  }
}));

// Mock React Router
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({ pathname: '/', search: '', hash: '', state: null }),
    useParams: () => ({}),
    BrowserRouter: ({ children }: { children: React.ReactNode }) => children,
    Routes: ({ children }: { children: React.ReactNode }) => children,
    Route: ({ element }: { element: React.ReactNode }) => element
  };
});

// Mock Stripe
vi.mock('@stripe/stripe-js', () => ({
  loadStripe: vi.fn(() => Promise.resolve({
    elements: vi.fn(() => ({
      create: vi.fn(() => ({
        mount: vi.fn(),
        unmount: vi.fn(),
        on: vi.fn(),
        off: vi.fn()
      })),
      getElement: vi.fn()
    })),
    confirmCardPayment: vi.fn(),
    confirmPayment: vi.fn()
  }))
}));

vi.mock('@stripe/react-stripe-js', () => ({
  Elements: ({ children }: { children: React.ReactNode }) => children,
  useStripe: () => ({
    confirmCardPayment: vi.fn(),
    confirmPayment: vi.fn()
  }),
  useElements: () => ({
    getElement: vi.fn()
  }),
  CardElement: () => React.createElement('div', { 'data-testid': 'card-element' })
}));

// Mock toast notifications
vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(),
    dismiss: vi.fn()
  },
  Toaster: () => null
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn()
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
  length: 0,
  key: vi.fn()
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
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}));

// Cleanup after each test
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  localStorageMock.clear();
  sessionStorageMock.clear();
});

// Global test utilities
export const mockUser = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  email: 'test@example.com',
  username: 'testuser',
  first_name: 'Test',
  last_name: 'User',
  is_verified: true,
  is_active: true
};

export const mockProduct = {
  id: '123e4567-e89b-12d3-a456-426614174001',
  name: 'Test Product',
  description: 'A test product',
  category: 'electronics',
  brand: 'TestBrand',
  variants: [{
    id: '123e4567-e89b-12d3-a456-426614174002',
    name: 'Default Variant',
    price: 99.99,
    sku: 'TEST-001',
    is_active: true
  }]
};

export const mockCart = {
  id: '123e4567-e89b-12d3-a456-426614174003',
  items: [{
    id: '123e4567-e89b-12d3-a456-426614174004',
    variant_id: mockProduct.variants[0].id,
    quantity: 2,
    price_per_unit: mockProduct.variants[0].price,
    total_price: mockProduct.variants[0].price * 2,
    variant: mockProduct.variants[0]
  }],
  subtotal: 199.98,
  total_items: 2
};

export const mockSubscription = {
  id: '123e4567-e89b-12d3-a456-426614174005',
  status: 'active',
  frequency: 'monthly',
  next_billing_date: '2024-02-01T00:00:00Z',
  items: [{
    id: '123e4567-e89b-12d3-a456-426614174006',
    variant_id: mockProduct.variants[0].id,
    quantity: 1,
    price: mockProduct.variants[0].price,
    variant: mockProduct.variants[0]
  }]
};

// Test wrapper components
export const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  return React.createElement('div', { 'data-testid': 'test-wrapper' }, children);
};

// Mock API responses
export const mockApiResponses = {
  auth: {
    login: {
      access_token: 'mock_access_token',
      refresh_token: 'mock_refresh_token',
      token_type: 'bearer',
      user: mockUser
    },
    register: mockUser,
    profile: mockUser
  },
  products: {
    list: [mockProduct],
    detail: mockProduct
  },
  cart: {
    get: mockCart,
    add: mockCart,
    update: mockCart,
    remove: mockCart
  },
  subscriptions: {
    list: [mockSubscription],
    detail: mockSubscription,
    create: mockSubscription
  }
};