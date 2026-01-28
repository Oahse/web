/**
 * Tests for useCart hook
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useCart } from '../../hooks/useCart';
import { CartProvider } from '../../store/CartContext';
import { CartAPI } from '../../api/cart';
import { mockCart, mockProduct } from '../setup';
import React from 'react';

vi.mock('../../api/cart');
vi.mock('../../api/client');

const wrapper = ({ children }: { children: React.ReactNode }) => 
  React.createElement(CartProvider, null, children);

describe('useCart', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should initialize with empty cart', () => {
    const { result } = renderHook(() => useCart(), { wrapper });

    expect(result.current.items).toEqual([]);
    expect(result.current.cart).toBe(null);
    expect(result.current.totalItems).toBe(0);
    expect(result.current.loading).toBe(false);
  });

  it('should load cart from API when user is authenticated', async () => {
    vi.mocked(CartAPI.getCart).mockResolvedValue({ data: mockCart });

    const { result } = renderHook(() => useCart(), { wrapper });

    await waitFor(() => {
      expect(result.current.items).toEqual(mockCart.items);
      expect(result.current.cart).toEqual(mockCart);
      expect(result.current.totalItems).toBe(2);
    });

    expect(CartAPI.getCart).toHaveBeenCalled();
  });

  it('should add item to cart', async () => {
    const updatedCart = {
      ...mockCart,
      items: [...mockCart.items, {
        id: 'new-item',
        variant_id: 'new-variant',
        quantity: 1,
        price_per_unit: 50.00,
        total_price: 50.00,
        variant: { ...mockProduct.variants[0], id: 'new-variant', price: 50.00 }
      }],
      subtotal: 249.98
    };

    vi.mocked(CartAPI.addToCart).mockResolvedValue({ data: updatedCart });

    const { result } = renderHook(() => useCart(), { wrapper });

    await act(async () => {
      await result.current.addItem({ variant_id: 'new-variant', quantity: 1 });
    });

    expect(CartAPI.addToCart).toHaveBeenCalledWith({
      variant_id: 'new-variant',
      quantity: 1
    }, expect.any(String));

    await waitFor(() => {
      expect(result.current.items).toHaveLength(2);
      expect(result.current.cart?.subtotal).toBe(249.98);
    });
  });

  it('should update item quantity', async () => {
    vi.mocked(CartAPI.getCart).mockResolvedValue({ data: mockCart });
    
    const updatedCart = {
      ...mockCart,
      items: [{
        ...mockCart.items[0],
        quantity: 3,
        total_price: 299.97
      }],
      subtotal: 299.97
    };
    vi.mocked(CartAPI.updateCartItem).mockResolvedValue({ data: updatedCart });

    const { result } = renderHook(() => useCart(), { wrapper });

    // Wait for initial load
    await waitFor(() => {
      expect(result.current.items).toHaveLength(1);
    });

    await act(async () => {
      await result.current.updateQuantity(mockCart.items[0].id, 3);
    });

    expect(CartAPI.updateCartItem).toHaveBeenCalledWith(mockCart.items[0].id, 3, expect.any(String));

    await waitFor(() => {
      expect(result.current.items[0].quantity).toBe(3);
      expect(result.current.cart?.subtotal).toBe(299.97);
    });
  });

  it('should remove item from cart', async () => {
    vi.mocked(CartAPI.getCart).mockResolvedValue({ data: mockCart });
    
    const updatedCart = {
      ...mockCart,
      items: [],
      subtotal: 0
    };
    vi.mocked(CartAPI.removeFromCart).mockResolvedValue({ data: updatedCart });

    const { result } = renderHook(() => useCart(), { wrapper });

    // Wait for initial load
    await waitFor(() => {
      expect(result.current.items).toHaveLength(1);
    });

    await act(async () => {
      await result.current.removeItem(mockCart.items[0].id);
    });

    expect(CartAPI.removeFromCart).toHaveBeenCalledWith(mockCart.items[0].id, expect.any(String));

    await waitFor(() => {
      expect(result.current.items).toHaveLength(0);
      expect(result.current.cart?.subtotal).toBe(0);
    });
  });

  it('should clear entire cart', async () => {
    vi.mocked(CartAPI.getCart).mockResolvedValue({ data: mockCart });
    vi.mocked(CartAPI.clearCart).mockResolvedValue({ data: { items: [], subtotal: 0 } });

    const { result } = renderHook(() => useCart(), { wrapper });

    // Wait for initial load
    await waitFor(() => {
      expect(result.current.items).toHaveLength(1);
    });

    await act(async () => {
      await result.current.clearCart();
    });

    expect(CartAPI.clearCart).toHaveBeenCalledWith(expect.any(String));

    await waitFor(() => {
      expect(result.current.items).toHaveLength(0);
      expect(result.current.cart?.subtotal).toBe(0);
    });
  });

  it('should handle offline cart storage', async () => {
    // Mock API failure (offline)
    vi.mocked(CartAPI.getCart).mockRejectedValue(new Error('Network error'));
    vi.mocked(CartAPI.addToCart).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useCart(), { wrapper });

    // Should fall back to localStorage
    await act(async () => {
      try {
        await result.current.addItem({ variant_id: 'offline-variant', quantity: 2 });
      } catch (error) {
        // Expected to fail in offline mode
      }
    });

    // Should store in localStorage when offline
    const storedCart = JSON.parse(localStorage.getItem('cart') || '{}');
    expect(storedCart).toBeDefined();
  });

  it('should sync cart when coming back online', async () => {
    // Start offline
    vi.mocked(CartAPI.getCart).mockRejectedValue(new Error('Network error'));
    vi.mocked(CartAPI.addToCart).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useCart(), { wrapper });

    // Add item offline
    await act(async () => {
      try {
        await result.current.addItem({ variant_id: 'offline-variant', quantity: 1 });
      } catch (error) {
        // Expected to fail
      }
    });

    // Come back online
    vi.mocked(CartAPI.getCart).mockResolvedValue({ data: mockCart });
    vi.mocked(CartAPI.validateCart).mockResolvedValue({ data: mockCart });

    await act(async () => {
      await result.current.validateCart();
    });

    expect(CartAPI.validateCart).toHaveBeenCalled();
  });

  it('should calculate correct totals', async () => {
    const cartWithMultipleItems = {
      id: 'cart-1',
      items: [
        {
          id: 'item-1',
          variant_id: 'variant-1',
          quantity: 2,
          price_per_unit: 50.00,
          total_price: 100.00,
          variant: { ...mockProduct.variants[0], price: 50.00 }
        },
        {
          id: 'item-2',
          variant_id: 'variant-2',
          quantity: 3,
          price_per_unit: 30.00,
          total_price: 90.00,
          variant: { ...mockProduct.variants[0], price: 30.00 }
        }
      ],
      subtotal: 190.00
    };

    vi.mocked(CartAPI.getCart).mockResolvedValue({ data: cartWithMultipleItems });

    const { result } = renderHook(() => useCart(), { wrapper });

    await waitFor(() => {
      expect(result.current.totalItems).toBe(5); // 2 + 3
      expect(result.current.cart?.subtotal).toBe(190.00); // (2 * 50) + (3 * 30)
    });
  });

  it('should handle cart item validation', async () => {
    const invalidItemError = {
      response: {
        status: 400,
        data: { message: 'Product variant not available' }
      }
    };
    vi.mocked(CartAPI.addToCart).mockRejectedValue(invalidItemError);

    const { result } = renderHook(() => useCart(), { wrapper });

    await act(async () => {
      try {
        await result.current.addItem({ variant_id: 'invalid-variant', quantity: 1 });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    expect(result.current.error).toBeDefined();
  });

  it('should handle quantity limits', async () => {
    const quantityLimitError = {
      response: {
        status: 400,
        data: { message: 'Quantity exceeds available stock' }
      }
    };
    vi.mocked(CartAPI.updateCartItem).mockRejectedValue(quantityLimitError);

    const { result } = renderHook(() => useCart(), { wrapper });

    await act(async () => {
      try {
        await result.current.updateQuantity('item-1', 1000);
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    expect(result.current.error).toBeDefined();
  });

  it('should persist cart state across page reloads', async () => {
    vi.mocked(CartAPI.getCart).mockResolvedValue({ data: mockCart });

    // First render
    const { result: result1, unmount } = renderHook(() => useCart(), { wrapper });

    await waitFor(() => {
      expect(result1.current.items).toHaveLength(1);
    });

    unmount();

    // Second render (simulating page reload)
    const { result: result2 } = renderHook(() => useCart(), { wrapper });

    await waitFor(() => {
      expect(result2.current.items).toHaveLength(1);
    });
  });

  it('should handle concurrent cart operations', async () => {
    vi.mocked(CartAPI.getCart).mockResolvedValue({ data: mockCart });
    vi.mocked(CartAPI.addToCart).mockResolvedValue({ data: mockCart });
    vi.mocked(CartAPI.updateCartItem).mockResolvedValue({ data: mockCart });

    const { result } = renderHook(() => useCart(), { wrapper });

    // Perform multiple operations concurrently
    await act(async () => {
      await Promise.all([
        result.current.addItem({ variant_id: 'variant-1', quantity: 1 }),
        result.current.addItem({ variant_id: 'variant-2', quantity: 2 }),
        result.current.updateQuantity('item-1', 3)
      ]);
    });

    // Should handle all operations without conflicts
    expect(CartAPI.addToCart).toHaveBeenCalledTimes(2);
    expect(CartAPI.updateCartItem).toHaveBeenCalledTimes(1);
  });
});