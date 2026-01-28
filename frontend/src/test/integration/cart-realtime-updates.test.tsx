/**
 * Cart Real-time Updates Integration Tests
 * Tests real-time cart synchronization, updates, and state management
 */

import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { toast } from 'react-hot-toast';

// Components
import { Cart } from '../../pages/Cart';
import { ProductCard } from '../../components/ProductCard';
import { AuthProvider } from '../../store/AuthContext';
import { CartProvider, useCart } from '../../store/CartContext';

// Mock APIs
vi.mock('../../apis/cart', () => ({
  CartAPI: {
    getCart: vi.fn(),
    addToCart: vi.fn(),
    updateCartItem: vi.fn(),
    removeFromCart: vi.fn(),
    clearCart: vi.fn(),
    validateCart: vi.fn(),
  }
}));

// Mock toast notifications
vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(),
  }
}));

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

describe('Cart Real-time Updates', () => {
  const { CartAPI } = require('../../apis/cart');

  // Mock data
  const mockUser = {
    id: 'user-123',
    email: 'test@example.com',
    firstname: 'John',
    lastname: 'Doe',
    role: 'customer' as const,
    verified: true,
    is_active: true,
    created_at: '2023-01-01T00:00:00Z',
  };

  const mockVariant = {
    id: 'variant-1',
    product_id: 'product-1',
    sku: 'TEST-001',
    name: 'Default Variant',
    base_price: 29.99,
    sale_price: null,
    current_price: 29.99,
    stock: 10,
    is_active: true,
    attributes: { color: 'Red', size: 'M' },
    images: [{
      id: 'img-1',
      variant_id: 'variant-1',
      url: 'https://example.com/image.jpg',
      alt_text: 'Test Product Image',
      is_primary: true,
      sort_order: 1,
    }],
    created_at: '2023-01-01T00:00:00Z',
    product_name: 'Test Product',
  };

  const mockCartItem = {
    id: 'item-1',
    cart_id: 'cart-123',
    variant_id: 'variant-1',
    variant: mockVariant,
    quantity: 2,
    price_per_unit: 29.99,
    total_price: 59.98,
    created_at: '2023-01-01T00:00:00Z',
  };

  const mockCart = {
    id: 'cart-123',
    user_id: 'user-123',
    items: [mockCartItem],
    subtotal: 59.98,
    tax_amount: 5.99,
    shipping_amount: 9.99,
    total_amount: 75.96,
    total_items: 2,
    item_count: 1,
    currency: 'USD',
    created_at: '2023-01-01T00:00:00Z',
  };

  const mockEmptyCart = {
    id: 'cart-123',
    user_id: 'user-123',
    items: [],
    subtotal: 0,
    tax_amount: 0,
    shipping_amount: 0,
    total_amount: 0,
    total_items: 0,
    item_count: 0,
    currency: 'USD',
    created_at: '2023-01-01T00:00:00Z',
  };

  // Test component that displays cart state
  const CartStateDisplay = () => {
    const { cart, totalItems, loading, updateTrigger } = useCart();
    
    return (
      <div>
        <div data-testid="cart-loading">{loading ? 'Loading' : 'Not Loading'}</div>
        <div data-testid="cart-items-count">{cart?.items?.length || 0}</div>
        <div data-testid="cart-total-items">{totalItems}</div>
        <div data-testid="cart-total-amount">${cart?.total_amount || 0}</div>
        <div data-testid="update-trigger">{updateTrigger || 0}</div>
        <div data-testid="cart-id">{cart?.id || 'no-cart'}</div>
      </div>
    );
  };

  // Test wrapper component
  const TestWrapper = ({ 
    children, 
    authenticated = true 
  }: { 
    children: React.ReactNode; 
    authenticated?: boolean;
  }) => {
    const authContextValue = {
      user: authenticated ? mockUser : null,
      isAuthenticated: authenticated,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateUser: vi.fn(),
      setIntendedDestination: vi.fn(),
    };

    return (
      <BrowserRouter>
        <AuthProvider value={authContextValue}>
          <CartProvider>
            {children}
          </CartProvider>
        </AuthProvider>
      </BrowserRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockImplementation((key) => {
      if (key === 'detected_country') return 'US';
      if (key === 'detected_province') return 'CA';
      return null;
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial Cart Loading', () => {
    it('should load cart data on mount', async () => {
      CartAPI.getCart.mockResolvedValue({ data: mockCart });

      render(
        <TestWrapper>
          <CartStateDisplay />
        </TestWrapper>
      );

      // Should start loading
      expect(screen.getByTestId('cart-loading')).toHaveTextContent('Loading');

      await waitFor(() => {
        expect(screen.getByTestId('cart-loading')).toHaveTextContent('Not Loading');
        expect(screen.getByTestId('cart-items-count')).toHaveTextContent('1');
        expect(screen.getByTestId('cart-total-items')).toHaveTextContent('2');
        expect(screen.getByTestId('cart-total-amount')).toHaveTextContent('$75.96');
      });

      expect(CartAPI.getCart).toHaveBeenCalledWith(
        expect.any(String), // token
        'US', // country
        'CA'  // province
      );
    });

    it('should handle cart loading errors gracefully', async () => {
      CartAPI.getCart.mockRejectedValue(new Error('Failed to load cart'));

      render(
        <TestWrapper>
          <CartStateDisplay />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId('cart-loading')).toHaveTextContent('Not Loading');
        expect(screen.getByTestId('cart-items-count')).toHaveTextContent('0');
        expect(screen.getByTestId('cart-id')).toHaveTextContent('no-cart');
      });
    });

    it('should not load cart when user is not authenticated', async () => {
      render(
        <TestWrapper authenticated={false}>
          <CartStateDisplay />
        </TestWrapper>
      );

      // Should not be loading and should have no cart
      expect(screen.getByTestId('cart-loading')).toHaveTextContent('Not Loading');
      expect(screen.getByTestId('cart-items-count')).toHaveTextContent('0');
      expect(screen.getByTestId('cart-id')).toHaveTextContent('no-cart');

      // Should not call API
      expect(CartAPI.getCart).not.toHaveBeenCalled();
    });
  });

  describe('Periodic Cart Updates', () => {
    it('should refresh cart data periodically', async () => {
      vi.useFakeTimers();
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });

      render(
        <TestWrapper>
          <CartStateDisplay />
        </TestWrapper>
      );

      // Initial load
      await waitFor(() => {
        expect(CartAPI.getCart).toHaveBeenCalledTimes(1);
      });

      // Fast-forward 30 seconds (polling interval)
      act(() => {
        vi.advanceTimersByTime(30000);
      });

      await waitFor(() => {
        expect(CartAPI.getCart).toHaveBeenCalledTimes(2);
      });

      // Fast-forward another 30 seconds
      act(() => {
        vi.advanceTimersByTime(30000);
      });

      await waitFor(() => {
        expect(CartAPI.getCart).toHaveBeenCalledTimes(3);
      });

      vi.useRealTimers();
    });

    it('should validate cart periodically when cart has items', async () => {
      vi.useFakeTimers();
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
      CartAPI.validateCart.mockResolvedValue({ data: mockCart });

      render(
        <TestWrapper>
          <CartStateDisplay />
        </TestWrapper>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('cart-items-count')).toHaveTextContent('1');
      });

      // Fast-forward 5 minutes (validation interval)
      act(() => {
        vi.advanceTimersByTime(300000);
      });

      await waitFor(() => {
        expect(CartAPI.validateCart).toHaveBeenCalled();
      });

      vi.useRealTimers();
    });

    it('should not validate empty cart', async () => {
      vi.useFakeTimers();
      
      CartAPI.getCart.mockResolvedValue({ data: mockEmptyCart });
      CartAPI.validateCart.mockResolvedValue({ data: mockEmptyCart });

      render(
        <TestWrapper>
          <CartStateDisplay />
        </TestWrapper>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('cart-items-count')).toHaveTextContent('0');
      });

      // Fast-forward 5 minutes
      act(() => {
        vi.advanceTimersByTime(300000);
      });

      // Should not validate empty cart
      expect(CartAPI.validateCart).not.toHaveBeenCalled();

      vi.useRealTimers();
    });

    it('should stop polling when user logs out', async () => {
      vi.useFakeTimers();
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });

      const { rerender } = render(
        <TestWrapper authenticated={true}>
          <CartStateDisplay />
        </TestWrapper>
      );

      // Initial load
      await waitFor(() => {
        expect(CartAPI.getCart).toHaveBeenCalledTimes(1);
      });

      // User logs out
      rerender(
        <TestWrapper authenticated={false}>
          <CartStateDisplay />
        </TestWrapper>
      );

      // Fast-forward 30 seconds
      act(() => {
        vi.advanceTimersByTime(30000);
      });

      // Should not poll when not authenticated
      expect(CartAPI.getCart).toHaveBeenCalledTimes(1);

      vi.useRealTimers();
    });
  });

  describe('Window Focus Updates', () => {
    it('should refresh cart when window regains focus', async () => {
      CartAPI.getCart.mockResolvedValue({ data: mockCart });

      render(
        <TestWrapper>
          <CartStateDisplay />
        </TestWrapper>
      );

      // Initial load
      await waitFor(() => {
        expect(CartAPI.getCart).toHaveBeenCalledTimes(1);
      });

      // Simulate window focus event
      act(() => {
        window.dispatchEvent(new Event('focus'));
      });

      await waitFor(() => {
        expect(CartAPI.getCart).toHaveBeenCalledTimes(2);
      });
    });

    it('should not refresh on focus when not authenticated', async () => {
      render(
        <TestWrapper authenticated={false}>
          <CartStateDisplay />
        </TestWrapper>
      );

      // Simulate window focus event
      act(() => {
        window.dispatchEvent(new Event('focus'));
      });

      // Should not call API
      expect(CartAPI.getCart).not.toHaveBeenCalled();
    });
  });

  describe('Optimistic Updates', () => {
    it('should update UI immediately when adding items', async () => {
      const user = userEvent.setup();
      
      // Start with empty cart
      CartAPI.getCart.mockResolvedValue({ data: mockEmptyCart });
      
      // Mock slow add to cart response
      CartAPI.addToCart.mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({ data: mockCart }), 500)
        )
      );

      const mockProduct = {
        id: 'product-1',
        name: 'Test Product',
        variants: [mockVariant],
      };

      render(
        <TestWrapper>
          <div>
            <ProductCard product={mockProduct} />
            <CartStateDisplay />
          </div>
        </TestWrapper>
      );

      // Wait for initial empty cart
      await waitFor(() => {
        expect(screen.getByTestId('cart-items-count')).toHaveTextContent('0');
      });

      // Click add to cart
      const addToCartButton = screen.getByRole('button', { name: /add to cart/i });
      await user.click(addToCartButton);

      // UI should update immediately (optimistic update)
      await waitFor(() => {
        expect(screen.getByTestId('cart-items-count')).toHaveTextContent('1');
      });

      // Wait for API response to complete
      await waitFor(() => {
        expect(CartAPI.addToCart).toHaveBeenCalled();
      }, { timeout: 1000 });
    });

    it('should revert optimistic updates on error', async () => {
      const user = userEvent.setup();
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
      CartAPI.removeFromCart.mockRejectedValue(new Error('Failed to remove item'));

      render(
        <TestWrapper>
          <Cart />
        </TestWrapper>
      );

      // Wait for cart to load
      await waitFor(() => {
        expect(screen.getByText('Test Product')).toBeInTheDocument();
        expect(screen.getByDisplayValue('2')).toBeInTheDocument();
      });

      // Click remove button
      const removeButton = screen.getByRole('button', { name: /remove/i });
      await user.click(removeButton);

      // Item should be removed optimistically
      await waitFor(() => {
        expect(screen.queryByText('Test Product')).not.toBeInTheDocument();
      });

      // Wait for error and revert
      await waitFor(() => {
        expect(screen.getByText('Test Product')).toBeInTheDocument();
        expect(toast.error).toHaveBeenCalled();
      });
    });

    it('should handle quantity updates optimistically', async () => {
      const user = userEvent.setup();
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
      
      // Mock slow update response
      const updatedCart = {
        ...mockCart,
        items: [{
          ...mockCartItem,
          quantity: 3,
          total_price: 89.97,
        }],
        total_items: 3,
        subtotal: 89.97,
        total_amount: 105.95,
      };
      
      CartAPI.updateCartItem.mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({ data: updatedCart }), 300)
        )
      );

      render(
        <TestWrapper>
          <div>
            <Cart />
            <CartStateDisplay />
          </div>
        </TestWrapper>
      );

      // Wait for cart to load
      await waitFor(() => {
        expect(screen.getByDisplayValue('2')).toBeInTheDocument();
        expect(screen.getByTestId('cart-total-items')).toHaveTextContent('2');
      });

      // Click plus button
      const plusButton = screen.getByRole('button', { name: /increase quantity/i });
      await user.click(plusButton);

      // Should update optimistically
      await waitFor(() => {
        expect(screen.getByDisplayValue('3')).toBeInTheDocument();
        expect(screen.getByTestId('cart-total-items')).toHaveTextContent('3');
      });

      // Wait for API response
      await waitFor(() => {
        expect(CartAPI.updateCartItem).toHaveBeenCalledWith('item-1', 3, expect.any(String));
      }, { timeout: 500 });
    });
  });

  describe('Cart Validation and Sync', () => {
    it('should sync cart when validation detects changes', async () => {
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
      
      // Mock validation returning different cart state
      const syncedCart = {
        ...mockCart,
        items: [], // Cart was cleared elsewhere
        subtotal: 0,
        total_amount: 0,
        total_items: 0,
      };
      CartAPI.validateCart.mockResolvedValue({ data: syncedCart });

      render(
        <TestWrapper>
          <CartStateDisplay />
        </TestWrapper>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('cart-items-count')).toHaveTextContent('1');
      });

      // Manually trigger validation (simulating periodic validation)
      act(() => {
        // This would be called by the validation interval
        CartAPI.validateCart().then(response => {
          // The context should update with the validated cart
        });
      });

      await waitFor(() => {
        expect(CartAPI.validateCart).toHaveBeenCalled();
        expect(toast.success).toHaveBeenCalledWith('Cart synchronized');
      });
    });

    it('should handle validation errors by refreshing cart', async () => {
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
      CartAPI.validateCart.mockRejectedValue(new Error('Validation failed'));

      render(
        <TestWrapper>
          <CartStateDisplay />
        </TestWrapper>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('cart-items-count')).toHaveTextContent('1');
        expect(CartAPI.getCart).toHaveBeenCalledTimes(1);
      });

      // Manually trigger validation
      act(() => {
        CartAPI.validateCart().catch(() => {
          // Should trigger cart refresh on validation error
        });
      });

      await waitFor(() => {
        expect(CartAPI.validateCart).toHaveBeenCalled();
        // Should refresh cart after validation error
        expect(CartAPI.getCart).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Update Triggers and Re-renders', () => {
    it('should trigger re-renders when cart updates', async () => {
      const user = userEvent.setup();
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
      CartAPI.updateCartItem.mockResolvedValue({ 
        data: {
          ...mockCart,
          items: [{
            ...mockCartItem,
            quantity: 3,
          }],
        }
      });

      render(
        <TestWrapper>
          <div>
            <Cart />
            <CartStateDisplay />
          </div>
        </TestWrapper>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('update-trigger')).toHaveTextContent('0');
      });

      // Update quantity
      const plusButton = screen.getByRole('button', { name: /\+/ });
      await user.click(plusButton);

      // Update trigger should increment
      await waitFor(() => {
        expect(screen.getByTestId('update-trigger')).toHaveTextContent('1');
      });
    });

    it('should force re-renders with new object references', async () => {
      const renderSpy = vi.fn();
      
      const TestComponent = () => {
        const { cart } = useCart();
        renderSpy(cart?.id);
        return <div data-testid="cart-id">{cart?.id || 'no-cart'}</div>;
      };

      CartAPI.getCart
        .mockResolvedValueOnce({ data: mockCart })
        .mockResolvedValueOnce({ data: { ...mockCart } }); // Same data, new object

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      // Wait for initial render
      await waitFor(() => {
        expect(screen.getByTestId('cart-id')).toHaveTextContent('cart-123');
        expect(renderSpy).toHaveBeenCalledWith('cart-123');
      });

      // Trigger refresh
      act(() => {
        window.dispatchEvent(new Event('focus'));
      });

      // Should re-render with new object reference
      await waitFor(() => {
        expect(renderSpy).toHaveBeenCalledTimes(3); // Initial + loading + new data
      });
    });
  });

  describe('Memory Leaks and Cleanup', () => {
    it('should cleanup intervals on unmount', async () => {
      const clearIntervalSpy = vi.spyOn(global, 'clearInterval');
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });

      const { unmount } = render(
        <TestWrapper>
          <CartStateDisplay />
        </TestWrapper>
      );

      // Wait for component to mount and set up intervals
      await waitFor(() => {
        expect(screen.getByTestId('cart-items-count')).toHaveTextContent('1');
      });

      // Unmount component
      unmount();

      // Should cleanup intervals
      expect(clearIntervalSpy).toHaveBeenCalledTimes(2); // Polling + validation intervals

      clearIntervalSpy.mockRestore();
    });

    it('should cleanup event listeners on unmount', async () => {
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });

      const { unmount } = render(
        <TestWrapper>
          <CartStateDisplay />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId('cart-items-count')).toHaveTextContent('1');
      });

      unmount();

      // Should cleanup focus event listener
      expect(removeEventListenerSpy).toHaveBeenCalledWith('focus', expect.any(Function));

      removeEventListenerSpy.mockRestore();
    });
  });
});