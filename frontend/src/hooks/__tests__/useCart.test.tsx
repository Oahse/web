import { renderHook, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useCart } from '../useCart';
import { CartProvider } from '../../store/CartContext';
import { ReactNode } from 'react';

// Mock the CartAPI and TokenManager
vi.mock('../../apis/client', () => ({
  TokenManager: {
    getToken: vi.fn(),
  },
}));

vi.mock('../../apis/cart', () => ({
  CartAPI: {
    getCart: vi.fn(),
    addToCart: vi.fn(),
    removeFromCart: vi.fn(),
    updateCartItem: vi.fn(),
    clearCart: vi.fn(),
  },
}));

import { TokenManager } from '../../api/client';
import { CartAPI } from '../../api/cart';

const mockTokenManager = TokenManager as any;
const mockCartAPI = CartAPI as any;

// Test wrapper component
const createWrapper = () => {
  return ({ children }: { children: ReactNode }) => (
    <CartProvider>{children}</CartProvider>
  );
};

// Mock cart data
const mockCart = {
  id: 'cart-1',
  items: [
    {
      id: 'item-1',
      product: {
        id: 'product-1',
        name: 'Test Product 1',
        price: 29.99,
        images: ['image1.jpg'],
      },
      variant_id: null,
      quantity: 2,
      price: 29.99,
      total: 59.98,
    },
    {
      id: 'item-2',
      product: {
        id: 'product-2',
        name: 'Test Product 2',
        price: 19.99,
        images: ['image2.jpg'],
      },
      variant_id: 'variant-1',
      quantity: 1,
      price: 19.99,
      total: 19.99,
    },
  ],
  total_items: 3,
  total_amount: 79.97,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
};

const mockAddToCartRequest = {
  product_id: 'product-3',
  variant_id: null,
  quantity: 1,
};

describe('useCart Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTokenManager.getToken.mockReturnValue('mock-token');
  });

  describe('Cart State Management', () => {
    it('provides initial cart state', () => {
      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      expect(result.current.cart).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.totalItems).toBe(0);
      expect(result.current.items).toEqual([]);
      expect(typeof result.current.fetchCart).toBe('function');
      expect(typeof result.current.addItem).toBe('function');
      expect(typeof result.current.removeItem).toBe('function');
      expect(typeof result.current.updateQuantity).toBe('function');
      expect(typeof result.current.clearCart).toBe('function');
    });

    it('fetches cart on mount when token exists', async () => {
      mockCartAPI.getCart.mockResolvedValue({ data: mockCart });

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.cart).toEqual(mockCart);
        expect(result.current.totalItems).toBe(3);
        expect(result.current.items).toEqual(mockCart.items);
        expect(result.current.loading).toBe(false);
      });

      expect(mockCartAPI.getCart).toHaveBeenCalledWith('mock-token');
    });

    it('does not fetch cart when no token exists', async () => {
      mockTokenManager.getToken.mockReturnValue(null);

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      // Wait a bit to ensure no API call is made
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockCartAPI.getCart).not.toHaveBeenCalled();
      expect(result.current.cart).toBeNull();
    });

    it('handles cart fetch error gracefully', async () => {
      mockCartAPI.getCart.mockRejectedValue(new Error('Fetch failed'));

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.cart).toBeNull();
      expect(result.current.totalItems).toBe(0);
    });
  });

  describe('Add, Remove, and Update Operations', () => {
    it('adds item to cart successfully', async () => {
      const updatedCart = {
        ...mockCart,
        items: [...mockCart.items, {
          id: 'item-3',
          product: { id: 'product-3', name: 'New Product', price: 39.99 },
          variant_id: null,
          quantity: 1,
          price: 39.99,
          total: 39.99,
        }],
        total_items: 4,
        total_amount: 119.96,
      };

      mockCartAPI.getCart.mockResolvedValue({ data: mockCart });
      mockCartAPI.addToCart.mockResolvedValue({ data: updatedCart });

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      // Wait for initial cart load
      await waitFor(() => {
        expect(result.current.cart).toEqual(mockCart);
      });

      // Add item
      const success = await result.current.addItem(mockAddToCartRequest);

      expect(success).toBe(true);
      expect(result.current.cart).toEqual(updatedCart);
      expect(result.current.totalItems).toBe(4);
      expect(mockCartAPI.addToCart).toHaveBeenCalledWith(mockAddToCartRequest, 'mock-token');
    });

    it('handles add item failure', async () => {
      mockCartAPI.getCart.mockResolvedValue({ data: mockCart });
      mockCartAPI.addToCart.mockRejectedValue(new Error('Add failed'));

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.cart).toEqual(mockCart);
      });

      await expect(result.current.addItem(mockAddToCartRequest))
        .rejects.toThrow('Add failed');

      // Cart should remain unchanged
      expect(result.current.cart).toEqual(mockCart);
    });

    it('throws error when adding item without authentication', async () => {
      mockTokenManager.getToken.mockReturnValue(null);

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await expect(result.current.addItem(mockAddToCartRequest))
        .rejects.toThrow('User must be authenticated to add items to cart');
    });

    it('removes item from cart successfully', async () => {
      const updatedCart = {
        ...mockCart,
        items: [mockCart.items[1]], // Remove first item
        total_items: 1,
        total_amount: 19.99,
      };

      mockCartAPI.getCart.mockResolvedValue({ data: mockCart });
      mockCartAPI.removeFromCart.mockResolvedValue({ data: updatedCart });

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.cart).toEqual(mockCart);
      });

      // Remove item
      await result.current.removeItem('item-1');

      expect(result.current.cart).toEqual(updatedCart);
      expect(result.current.totalItems).toBe(1);
      expect(mockCartAPI.removeFromCart).toHaveBeenCalledWith('item-1', 'mock-token');
    });

    it('handles remove item failure', async () => {
      mockCartAPI.getCart.mockResolvedValue({ data: mockCart });
      mockCartAPI.removeFromCart.mockRejectedValue(new Error('Remove failed'));

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.cart).toEqual(mockCart);
      });

      await expect(result.current.removeItem('item-1'))
        .rejects.toThrow('Remove failed');

      // Cart should remain unchanged
      expect(result.current.cart).toEqual(mockCart);
    });

    it('throws error when removing item without authentication', async () => {
      mockTokenManager.getToken.mockReturnValue(null);

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await expect(result.current.removeItem('item-1'))
        .rejects.toThrow('User must be authenticated to remove items from cart');
    });

    it('updates item quantity successfully', async () => {
      const updatedCart = {
        ...mockCart,
        items: [
          { ...mockCart.items[0], quantity: 5, total: 149.95 },
          mockCart.items[1],
        ],
        total_items: 6,
        total_amount: 169.94,
      };

      mockCartAPI.getCart.mockResolvedValue({ data: mockCart });
      mockCartAPI.updateCartItem.mockResolvedValue({ data: updatedCart });

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.cart).toEqual(mockCart);
      });

      // Update quantity
      await result.current.updateQuantity('item-1', 5);

      expect(result.current.cart).toEqual(updatedCart);
      expect(result.current.totalItems).toBe(6);
      expect(mockCartAPI.updateCartItem).toHaveBeenCalledWith('item-1', 5, 'mock-token');
    });

    it('handles update quantity failure', async () => {
      mockCartAPI.getCart.mockResolvedValue({ data: mockCart });
      mockCartAPI.updateCartItem.mockRejectedValue(new Error('Update failed'));

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.cart).toEqual(mockCart);
      });

      await expect(result.current.updateQuantity('item-1', 5))
        .rejects.toThrow('Update failed');

      // Cart should remain unchanged
      expect(result.current.cart).toEqual(mockCart);
    });

    it('throws error when updating quantity without authentication', async () => {
      mockTokenManager.getToken.mockReturnValue(null);

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await expect(result.current.updateQuantity('item-1', 5))
        .rejects.toThrow('User must be authenticated to update cart items');
    });
  });

  describe('Persistence and Synchronization', () => {
    it('clears cart successfully', async () => {
      const emptyCart = {
        ...mockCart,
        items: [],
        total_items: 0,
        total_amount: 0,
      };

      mockCartAPI.getCart.mockResolvedValue({ data: mockCart });
      mockCartAPI.clearCart.mockResolvedValue({ data: emptyCart });

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.cart).toEqual(mockCart);
      });

      // Clear cart
      await result.current.clearCart();

      expect(result.current.cart).toEqual(emptyCart);
      expect(result.current.totalItems).toBe(0);
      expect(result.current.items).toEqual([]);
      expect(mockCartAPI.clearCart).toHaveBeenCalledWith('mock-token');
    });

    it('handles clear cart with fallback when API does not return updated cart', async () => {
      mockCartAPI.getCart.mockResolvedValue({ data: mockCart });
      mockCartAPI.clearCart.mockResolvedValue({}); // No data returned

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.cart).toEqual(mockCart);
      });

      // Clear cart
      await result.current.clearCart();

      // Should fallback to empty cart state
      expect(result.current.cart).toEqual({
        ...mockCart,
        items: [],
        total_items: 0,
        total_amount: 0,
      });
      expect(result.current.totalItems).toBe(0);
    });

    it('handles clear cart failure', async () => {
      mockCartAPI.getCart.mockResolvedValue({ data: mockCart });
      mockCartAPI.clearCart.mockRejectedValue(new Error('Clear failed'));

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.cart).toEqual(mockCart);
      });

      await expect(result.current.clearCart())
        .rejects.toThrow('Clear failed');

      // Cart should remain unchanged
      expect(result.current.cart).toEqual(mockCart);
    });

    it('throws error when clearing cart without authentication', async () => {
      mockTokenManager.getToken.mockReturnValue(null);

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await expect(result.current.clearCart())
        .rejects.toThrow('User must be authenticated to clear cart');
    });

    it('manually fetches cart when requested', async () => {
      const updatedCart = { ...mockCart, total_items: 5 };

      mockCartAPI.getCart
        .mockResolvedValueOnce({ data: mockCart })
        .mockResolvedValueOnce({ data: updatedCart });

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      // Wait for initial load
      await waitFor(() => {
        expect(result.current.cart).toEqual(mockCart);
      });

      // Manually fetch cart
      await result.current.fetchCart();

      expect(result.current.cart).toEqual(updatedCart);
      expect(mockCartAPI.getCart).toHaveBeenCalledTimes(2);
    });
  });

  describe('Derived Values and Edge Cases', () => {
    it('calculates total items correctly', async () => {
      const cartWithVariousQuantities = {
        ...mockCart,
        items: [
          { ...mockCart.items[0], quantity: 3 },
          { ...mockCart.items[1], quantity: 7 },
          { ...mockCart.items[0], id: 'item-3', quantity: 2 },
        ],
      };

      mockCartAPI.getCart.mockResolvedValue({ data: cartWithVariousQuantities });

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.totalItems).toBe(12); // 3 + 7 + 2
      });
    });

    it('handles empty cart correctly', async () => {
      const emptyCart = {
        ...mockCart,
        items: [],
        total_items: 0,
        total_amount: 0,
      };

      mockCartAPI.getCart.mockResolvedValue({ data: emptyCart });

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.cart).toEqual(emptyCart);
        expect(result.current.totalItems).toBe(0);
        expect(result.current.items).toEqual([]);
      });
    });

    it('handles cart with null/undefined items', async () => {
      const cartWithNullItems = {
        ...mockCart,
        items: null,
      };

      mockCartAPI.getCart.mockResolvedValue({ data: cartWithNullItems });

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.totalItems).toBe(0);
        expect(result.current.items).toEqual([]);
      });
    });

    it('handles API responses with different data structures', async () => {
      const nestedResponse = {
        success: true,
        data: mockCart,
      };

      mockCartAPI.getCart.mockResolvedValue(nestedResponse);

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.cart).toEqual(mockCart);
      });
    });

    it('throws error when used outside CartProvider', () => {
      expect(() => {
        renderHook(() => useCart());
      }).toThrow('useCart error: must be used within a CartProvider');
    });
  });

  describe('Loading States', () => {
    it('manages loading state during fetch operations', async () => {
      let resolvePromise: (value: any) => void;
      const fetchPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });

      mockCartAPI.getCart.mockReturnValue(fetchPromise);

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      // Should be loading initially
      expect(result.current.loading).toBe(true);

      // Resolve the promise
      resolvePromise!({ data: mockCart });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.cart).toEqual(mockCart);
      });
    });

    it('manages loading state during add operations', async () => {
      mockCartAPI.getCart.mockResolvedValue({ data: mockCart });
      
      let resolveAddPromise: (value: any) => void;
      const addPromise = new Promise(resolve => {
        resolveAddPromise = resolve;
      });
      mockCartAPI.addToCart.mockReturnValue(addPromise);

      const { result } = renderHook(() => useCart(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.cart).toEqual(mockCart);
      });

      // Start add operation
      const addPromiseResult = result.current.addItem(mockAddToCartRequest);

      // Should be loading
      expect(result.current.loading).toBe(true);

      // Resolve the add promise
      resolveAddPromise!({ data: mockCart });

      await addPromiseResult;

      expect(result.current.loading).toBe(false);
    });
  });
});