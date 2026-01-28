/**
 * Tests for App.tsx
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { App } from '../App';

// Mock all the lazy-loaded components
vi.mock('../pages/Home', () => ({
  default: () => <div data-testid="home-page">Home Page</div>
}));

vi.mock('../pages/Products', () => ({
  default: () => <div data-testid="products-page">Products Page</div>
}));

vi.mock('../pages/Login', () => ({
  default: () => <div data-testid="login-page">Login Page</div>
}));

vi.mock('../pages/Register', () => ({
  default: () => <div data-testid="register-page">Register Page</div>
}));

vi.mock('../components/layout/Layout', () => ({
  Layout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="layout">{children}</div>
  ),
  AuthLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="auth-layout">{children}</div>
  )
}));

// Mock all context providers
vi.mock('../store/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="auth-provider">{children}</div>
  )
}));

vi.mock('../store/CartContext', () => ({
  CartProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="cart-provider">{children}</div>
  )
}));

vi.mock('../store/WishlistContext', () => ({
  WishlistProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="wishlist-provider">{children}</div>
  )
}));

vi.mock('../store/SubscriptionContext', () => ({
  SubscriptionProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="subscription-provider">{children}</div>
  )
}));

vi.mock('../store/ThemeContext', () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="theme-provider">{children}</div>
  )
}));

vi.mock('../components/ui/FontLoader', () => ({
  FontLoader: () => <div data-testid="font-loader" />
}));

vi.mock('../components/ErrorBoundary', () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="error-boundary">{children}</div>
  )
}));

vi.mock('../components/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="protected-route">{children}</div>
  )
}));

// Mock Stripe
vi.mock('@stripe/stripe-js', () => ({
  loadStripe: vi.fn(() => Promise.resolve({}))
}));

vi.mock('@stripe/react-stripe-js', () => ({
  Elements: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="stripe-elements">{children}</div>
  )
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  Toaster: () => <div data-testid="toaster" />
}));

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render without crashing', () => {
    render(<App />);
    
    expect(screen.getByTestId('error-boundary')).toBeInTheDocument();
    expect(screen.getByTestId('auth-provider')).toBeInTheDocument();
    expect(screen.getByTestId('cart-provider')).toBeInTheDocument();
    expect(screen.getByTestId('wishlist-provider')).toBeInTheDocument();
    expect(screen.getByTestId('subscription-provider')).toBeInTheDocument();
    expect(screen.getByTestId('theme-provider')).toBeInTheDocument();
  });

  it('should render Stripe Elements provider', () => {
    render(<App />);
    
    expect(screen.getByTestId('stripe-elements')).toBeInTheDocument();
  });

  it('should render Toaster for notifications', () => {
    render(<App />);
    
    expect(screen.getByTestId('toaster')).toBeInTheDocument();
  });

  it('should render FontLoader', () => {
    render(<App />);
    
    expect(screen.getByTestId('font-loader')).toBeInTheDocument();
  });

  it('should wrap everything in ErrorBoundary', () => {
    render(<App />);
    
    const errorBoundary = screen.getByTestId('error-boundary');
    expect(errorBoundary).toBeInTheDocument();
    
    // Check that providers are inside error boundary
    expect(errorBoundary).toContainElement(screen.getByTestId('auth-provider'));
  });

  it('should provide all necessary contexts', () => {
    render(<App />);
    
    // Check that all context providers are rendered
    expect(screen.getByTestId('auth-provider')).toBeInTheDocument();
    expect(screen.getByTestId('cart-provider')).toBeInTheDocument();
    expect(screen.getByTestId('wishlist-provider')).toBeInTheDocument();
    expect(screen.getByTestId('subscription-provider')).toBeInTheDocument();
    expect(screen.getByTestId('theme-provider')).toBeInTheDocument();
  });

  it('should handle Stripe initialization', async () => {
    const { loadStripe } = await import('@stripe/stripe-js');
    
    render(<App />);
    
    expect(loadStripe).toHaveBeenCalledWith(
      expect.stringContaining('pk_test_') || ''
    );
  });
});