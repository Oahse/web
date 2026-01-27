/**
 * Comprehensive Cart Page Integration Tests
 * Tests the entire cart functionality including:
 * - Cart page rendering and display
 * - Add to cart from product cards
 * - Real-time cart updates
 * - Cart item management (quantity, removal)
 * - Cart validation and error handling
 * - Authentication flows
 */

import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { toast } from 'react-hot-toast';

// Components
import { Cart } from '../../pages/Cart';
import { ProductCard } from '../../components/ProductCard';
import { AuthProvider } from '../../contexts/AuthContext';
import { CartProvider } from '../../contexts/CartContext';
import { WishlistProvider } from '../../contexts/WishlistContext';
import { SubscriptionProvider } from '../../contexts/SubscriptionContext';
import { LocaleProvider } from '../../contexts/LocaleContext';

// Test utilities
import { renderWithProviders, mockUsers, mockProducts } from '../utils';

// Mock APIs
vi.mock('../../apis/cart', () => ({
  CartAPI: {
    getCart: vi.fn(),
    addToCart: vi.fn(),
    updateCartItem: vi.fn(),
    removeFromCart: vi.fn(),
    clearCart: vi.fn(),
    validateCart: vi.fn(),
    applyPromocode: vi.fn(),
    removePromocode: vi.fn(),
  }
}));

vi.mock('../../apis/auth', () => ({
  AuthAPI: {
    login: vi.fn(),
    logout: vi.fn(),
    getProfile: vi.fn(),
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

// Mock navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

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

describe('Cart Page Comprehensive Tests', () => {
  const { CartAPI } = require('../../apis/cart');
  const { AuthAPI } = require('../../apis/auth');

  // Mock data
  const mockUser = {
    ...mockUsers.customer,
    id: 'user-123',
    email: 'test@example.com',
    firstname: 'John',
    lastname: 'Doe',
    role: 'customer' as const,
    verified: true,
    is_active: true,
    created_at: '2023-01-01T00:00:00Z',
  };

  const mockProduct = {
    id: 'product-1',
    name: 'Test Product',
    description: 'A test product for cart testing',
    slug: 'test-product',
    category_id: 'cat-1',
    rating_average: 4.5,
    review_count: 10,
    variants: [{
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
    }],
    created_at: '2023-01-01T00:00:00Z',
  };

  const mockCartItem = {
    id: 'item-1',
    cart_id: 'cart-123',
    variant_id: 'variant-1',
    variant: mockProduct.variants[0],
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

  // Test wrapper component
  const TestWrapper = ({ children, authenticated = true }: { children: React.ReactNode; authenticated?: boolean }) => {
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
          <LocaleProvider>
            <WishlistProvider>
              <SubscriptionProvider>
                <CartProvider>
                  <Routes>
                    <Route path="/" element={<div>Home</div>} />
                    <Route path="/products" element={<div>Products</div>} />
                    <Route path="/products/:id" element={<div>Product Details</div>} />
                    <Route path="/cart" element={<Cart />} />
                    <Route path="/checkout" element={<div>Checkout</div>} />
                    <Route path="/login" element={<div>Login Page</div>} />
                    {children}
                  </Routes>
                </CartProvider>
              </SubscriptionProvider>
            </WishlistProvider>
          </LocaleProvider>
        </AuthProvider>
      </BrowserRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    mockLocalStorage.getItem.mockImplementation((key) => {
      if (key === 'detected_country') return 'US';
      if (key === 'detected_province') return 'CA';
      return null;
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Cart Page Rendering', () => {
    it('should render empty cart state when cart is empty', async () => {
      CartAPI.getCart.mockResolvedValue({ data: mockEmptyCart });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      // Navigate to cart
      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Your cart is empty')).toBeInTheDocument();
        expect(screen.getByText('Continue Shopping')).toBeInTheDocument();
      });

      expect(screen.getByRole('link', { name: /continue shopping/i })).toHaveAttribute('href', '/products');
    });

    it('should render cart with items correctly', async () => {
      CartAPI.getCart.mockResolvedValue({ data: mockCart });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Your Shopping Cart')).toBeInTheDocument();
        expect(screen.getByText('Test Product')).toBeInTheDocument();
        expect(screen.getByText('Default Variant')).toBeInTheDocument();
        expect(screen.getByDisplayValue('2')).toBeInTheDocument(); // quantity input
        expect(screen.getByText('$29.99')).toBeInTheDocument(); // price per unit
        expect(screen.getByText('$59.98')).toBeInTheDocument(); // item total
        expect(screen.getByText('$75.96')).toBeInTheDocument(); // cart total
      });
    });

    it('should display cart summary correctly', async () => {
      CartAPI.getCart.mockResolvedValue({ data: mockCart });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Order Summary')).toBeInTheDocument();
        expect(screen.getByText('$59.98')).toBeInTheDocument(); // subtotal
        expect(screen.getByText('$5.99')).toBeInTheDocument(); // tax
        expect(screen.getByText('$9.99')).toBeInTheDocument(); // shipping
        expect(screen.getByText('$75.96')).toBeInTheDocument(); // total
      });
    });

    it('should show free shipping progress when applicable', async () => {
      const cartWithLowSubtotal = {
        ...mockCart,
        subtotal: 50.00,
        total_amount: 65.99,
        shipping_amount: 10.00,
      };
      CartAPI.getCart.mockResolvedValue({ data: cartWithLowSubtotal });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText(/Add.*more to get.*FREE Standard Shipping/)).toBeInTheDocument();
        expect(screen.getByText('$50.00')).toBeInTheDocument(); // amount needed
      });
    });

    it('should show free shipping achieved message', async () => {
      const cartWithFreeShipping = {
        ...mockCart,
        subtotal: 150.00,
        shipping_amount: 0,
        total_amount: 155.99,
      };
      CartAPI.getCart.mockResolvedValue({ data: cartWithFreeShipping });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText(/You've qualified for FREE Standard Shipping/)).toBeInTheDocument();
        expect(screen.getByText('Free')).toBeInTheDocument();
      });
    });
  });

  describe('Add to Cart Functionality', () => {
    it('should add item to cart from product card', async () => {
      const user = userEvent.setup();
      
      // Mock empty cart initially, then cart with item after adding
      CartAPI.getCart
        .mockResolvedValueOnce({ data: mockEmptyCart })
        .mockResolvedValueOnce({ data: mockCart });
      
      CartAPI.addToCart.mockResolvedValue({ data: mockCart });

      render(
        <TestWrapper>
          <Route path="/test" element={
            <div>
              <ProductCard product={mockProduct} />
              <Cart />
            </div>
          } />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      // Wait for initial render
      await waitFor(() => {
        expect(screen.getByText('Your cart is empty')).toBeInTheDocument();
      });

      // Click add to cart button
      const addToCartButton = screen.getByRole('button', { name: /add to cart/i });
      await user.click(addToCartButton);

      // Verify API call
      await waitFor(() => {
        expect(CartAPI.addToCart).toHaveBeenCalledWith({
          variant_id: 'variant-1',
          quantity: 1,
        }, expect.any(String));
      });

      // Verify success toast
      expect(toast.success).toHaveBeenCalledWith('Added 1 item to cart');

      // Verify cart updates
      await waitFor(() => {
        expect(screen.getByText('Test Product')).toBeInTheDocument();
        expect(screen.queryByText('Your cart is empty')).not.toBeInTheDocument();
      });
    });

    it('should handle add to cart errors gracefully', async () => {
      const user = userEvent.setup();
      
      CartAPI.getCart.mockResolvedValue({ data: mockEmptyCart });
      CartAPI.addToCart.mockRejectedValue(new Error('Product out of stock'));

      render(
        <TestWrapper>
          <Route path="/test" element={<ProductCard product={mockProduct} />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      const addToCartButton = screen.getByRole('button', { name: /add to cart/i });
      await user.click(addToCartButton);

      await waitFor(() => {
        expect(CartAPI.addToCart).toHaveBeenCalled();
      });

      // Should not show success toast
      expect(toast.success).not.toHaveBeenCalled();
    });

    it('should redirect unauthenticated users to login', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper authenticated={false}>
          <Route path="/test" element={<ProductCard product={mockProduct} />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      const addToCartButton = screen.getByRole('button', { name: /add to cart/i });
      await user.click(addToCartButton);

      // Should redirect to login
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/login', expect.any(Object));
      });
    });
  });

  describe('Cart Item Management', () => {
    beforeEach(() => {
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
    });

    it('should update item quantity', async () => {
      const user = userEvent.setup();
      
      const updatedCart = {
        ...mockCart,
        items: [{
          ...mockCartItem,
          quantity: 3,
          total_price: 89.97,
        }],
        subtotal: 89.97,
        total_amount: 105.95,
      };
      
      CartAPI.updateCartItem.mockResolvedValue({ data: updatedCart });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByDisplayValue('2')).toBeInTheDocument();
      });

      // Click plus button to increase quantity
      const plusButton = screen.getByRole('button', { name: /increase quantity/i });
      await user.click(plusButton);

      await waitFor(() => {
        expect(CartAPI.updateCartItem).toHaveBeenCalledWith('item-1', 3, expect.any(String));
      });

      expect(toast.success).toHaveBeenCalledWith('Cart updated');
    });

    it('should handle quantity input changes', async () => {
      const user = userEvent.setup();
      
      const updatedCart = {
        ...mockCart,
        items: [{
          ...mockCartItem,
          quantity: 5,
          total_price: 149.95,
        }],
        subtotal: 149.95,
        total_amount: 165.93,
      };
      
      CartAPI.updateCartItem.mockResolvedValue({ data: updatedCart });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByDisplayValue('2')).toBeInTheDocument();
      });

      // Change quantity input directly
      const quantityInput = screen.getByDisplayValue('2');
      await user.clear(quantityInput);
      await user.type(quantityInput, '5');

      await waitFor(() => {
        expect(CartAPI.updateCartItem).toHaveBeenCalledWith('item-1', 5, expect.any(String));
      });
    });

    it('should remove item when quantity becomes 0', async () => {
      const user = userEvent.setup();
      
      CartAPI.removeFromCart.mockResolvedValue({ data: mockEmptyCart });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByDisplayValue('2')).toBeInTheDocument();
      });

      // Click minus button twice to reach 0
      const minusButton = screen.getByRole('button', { name: /decrease quantity/i });
      await user.click(minusButton);
      await user.click(minusButton);

      await waitFor(() => {
        expect(CartAPI.removeFromCart).toHaveBeenCalledWith('item-1', expect.any(String));
      });
    });

    it('should remove item when remove button is clicked', async () => {
      const user = userEvent.setup();
      
      CartAPI.removeFromCart.mockResolvedValue({ data: mockEmptyCart });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Test Product')).toBeInTheDocument();
      });

      // Click remove button
      const removeButton = screen.getByRole('button', { name: /remove/i });
      await user.click(removeButton);

      await waitFor(() => {
        expect(CartAPI.removeFromCart).toHaveBeenCalledWith('item-1', expect.any(String));
      });

      expect(toast.success).toHaveBeenCalledWith('Default Variant removed from cart');
    });

    it('should clear entire cart', async () => {
      const user = userEvent.setup();
      
      CartAPI.clearCart.mockResolvedValue({ data: mockEmptyCart });
      
      // Mock window.confirm
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Test Product')).toBeInTheDocument();
      });

      // Click clear cart button
      const clearButton = screen.getByRole('button', { name: /clear cart/i });
      await user.click(clearButton);

      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to remove all 1 items from your cart?');

      await waitFor(() => {
        expect(CartAPI.clearCart).toHaveBeenCalled();
      });

      expect(toast.success).toHaveBeenCalledWith('Cart cleared');

      confirmSpy.mockRestore();
    });

    it('should handle item removal errors', async () => {
      const user = userEvent.setup();
      
      CartAPI.removeFromCart.mockRejectedValue(new Error('Failed to remove item'));

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Test Product')).toBeInTheDocument();
      });

      const removeButton = screen.getByRole('button', { name: /remove/i });
      await user.click(removeButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Failed to remove item. Please try again.');
      });
    });
  });

  describe('Real-time Cart Updates', () => {
    it('should refresh cart data periodically', async () => {
      vi.useFakeTimers();
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(CartAPI.getCart).toHaveBeenCalledTimes(1);
      });

      // Fast-forward 30 seconds
      act(() => {
        vi.advanceTimersByTime(30000);
      });

      await waitFor(() => {
        expect(CartAPI.getCart).toHaveBeenCalledTimes(2);
      });

      vi.useRealTimers();
    });

    it('should refresh cart when window regains focus', async () => {
      CartAPI.getCart.mockResolvedValue({ data: mockCart });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

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

    it('should validate cart periodically', async () => {
      vi.useFakeTimers();
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
      CartAPI.validateCart.mockResolvedValue({ data: mockCart });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Test Product')).toBeInTheDocument();
      });

      // Fast-forward 5 minutes
      act(() => {
        vi.advanceTimersByTime(300000);
      });

      await waitFor(() => {
        expect(CartAPI.validateCart).toHaveBeenCalled();
      });

      vi.useRealTimers();
    });

    it('should handle cart validation with sync issues', async () => {
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
      CartAPI.validateCart.mockResolvedValue({ 
        data: {
          ...mockCart,
          items: [], // Cart was cleared elsewhere
        }
      });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Test Product')).toBeInTheDocument();
      });

      // Manually trigger validation
      act(() => {
        // This would be triggered by the validation interval
        CartAPI.validateCart();
      });

      expect(toast.success).toHaveBeenCalledWith('Cart synchronized');
    });
  });

  describe('Coupon Code Functionality', () => {
    beforeEach(() => {
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
    });

    it('should apply valid coupon code', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Coupon code')).toBeInTheDocument();
      });

      // Enter coupon code
      const couponInput = screen.getByPlaceholderText('Coupon code');
      await user.type(couponInput, 'SAVE10');

      // Click apply button
      const applyButton = screen.getByRole('button', { name: /apply/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('Coupon SAVE10 applied successfully!');
      });

      // Input should be cleared
      expect(couponInput).toHaveValue('');
    });

    it('should handle invalid coupon code', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Coupon code')).toBeInTheDocument();
      });

      const couponInput = screen.getByPlaceholderText('Coupon code');
      await user.type(couponInput, 'INVALID');

      const applyButton = screen.getByRole('button', { name: /apply/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Invalid coupon code. Please check and try again.');
      });
    });

    it('should validate coupon code format', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Coupon code')).toBeInTheDocument();
      });

      const couponInput = screen.getByPlaceholderText('Coupon code');
      await user.type(couponInput, '   '); // Only spaces

      const applyButton = screen.getByRole('button', { name: /apply/i });
      await user.click(applyButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled();
      });
    });
  });

  describe('Checkout Flow', () => {
    beforeEach(() => {
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
    });

    it('should navigate to checkout when authenticated', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Proceed to Checkout')).toBeInTheDocument();
      });

      const checkoutButton = screen.getByRole('button', { name: /proceed to checkout/i });
      await user.click(checkoutButton);

      expect(mockNavigate).toHaveBeenCalledWith('/checkout');
    });

    it('should redirect to login when not authenticated', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper authenticated={false}>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Login to Checkout')).toBeInTheDocument();
      });

      const checkoutButton = screen.getByRole('button', { name: /login to checkout/i });
      await user.click(checkoutButton);

      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    it('should validate cart before checkout', async () => {
      const user = userEvent.setup();
      
      // Mock empty cart
      CartAPI.getCart.mockResolvedValue({ data: mockEmptyCart });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Your cart is empty')).toBeInTheDocument();
      });

      // Should not have checkout button for empty cart
      expect(screen.queryByRole('button', { name: /checkout/i })).not.toBeInTheDocument();
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle cart loading errors', async () => {
      CartAPI.getCart.mockRejectedValue(new Error('Failed to load cart'));

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      // Should still render the page but show empty state
      await waitFor(() => {
        expect(screen.getByText('Your cart is empty')).toBeInTheDocument();
      });
    });

    it('should handle network connectivity issues', async () => {
      const user = userEvent.setup();
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
      CartAPI.updateCartItem.mockRejectedValue(new Error('Network error'));

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByDisplayValue('2')).toBeInTheDocument();
      });

      const plusButton = screen.getByRole('button', { name: /\+/ });
      await user.click(plusButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Failed to update cart. Please try again.');
      });
    });

    it('should handle out of stock items', async () => {
      const outOfStockCart = {
        ...mockCart,
        items: [{
          ...mockCartItem,
          variant: {
            ...mockCartItem.variant,
            stock: 0,
          }
        }]
      };
      
      CartAPI.getCart.mockResolvedValue({ data: outOfStockCart });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Out of Stock')).toBeInTheDocument();
      });
    });

    it('should handle item not found errors during updates', async () => {
      const user = userEvent.setup();
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
      CartAPI.updateCartItem.mockRejectedValue({
        message: 'Item not found in cart',
        status: 404
      });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByDisplayValue('2')).toBeInTheDocument();
      });

      const plusButton = screen.getByRole('button', { name: /\+/ });
      await user.click(plusButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Failed to update cart. Please try again.');
        // Should refresh cart after 404 error
        expect(CartAPI.getCart).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Loading States and UI Feedback', () => {
    it('should show loading state during cart operations', async () => {
      const user = userEvent.setup();
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
      
      // Mock slow API response
      CartAPI.updateCartItem.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: mockCart }), 1000))
      );

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByDisplayValue('2')).toBeInTheDocument();
      });

      const plusButton = screen.getByRole('button', { name: /\+/ });
      await user.click(plusButton);

      // Should show loading state
      expect(plusButton).toBeDisabled();
    });

    it('should show processing state for individual items', async () => {
      const user = userEvent.setup();
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });
      CartAPI.removeFromCart.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: mockEmptyCart }), 500))
      );

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Test Product')).toBeInTheDocument();
      });

      const removeButton = screen.getByRole('button', { name: /remove/i });
      await user.click(removeButton);

      // Should show loading spinner in remove button
      expect(removeButton).toBeDisabled();
    });

    it('should refresh cart manually', async () => {
      const user = userEvent.setup();
      
      CartAPI.getCart.mockResolvedValue({ data: mockCart });

      render(
        <TestWrapper>
          <Route path="/test" element={<Cart />} />
        </TestWrapper>
      );

      window.history.pushState({}, '', '/test');

      await waitFor(() => {
        expect(screen.getByText('Test Product')).toBeInTheDocument();
        expect(CartAPI.getCart).toHaveBeenCalledTimes(1);
      });

      // Click refresh button
      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      await waitFor(() => {
        expect(CartAPI.getCart).toHaveBeenCalledTimes(2);
      });
    });
  });
});