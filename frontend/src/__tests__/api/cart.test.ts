/**
 * Tests for Cart API - Aligned with backend reality
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CartAPI } from '../../api/cart';
import { apiClient } from '../../api/client';
import { mockApiResponses, mockCart } from '../setup';

vi.mock('../../api/client');

describe('CartAPI', () => {
  const mockAccessToken = 'mock_access_token';

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn((key) => {
          if (key === 'detected_country') return 'US';
          if (key === 'detected_province') return 'CA';
          return null;
        }),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    });
  });

  describe('getCart', () => {
    it('should fetch user cart with location parameters', async () => {
      const mockResponse = mockApiResponses.cart.get;
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await CartAPI.getCart(mockAccessToken, 'US', 'CA');

      expect(apiClient.get).toHaveBeenCalledWith('/v1/cart?country=US&province=CA', {
        headers: { 'Authorization': `Bearer ${mockAccessToken}` },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should handle empty cart', async () => {
      const emptyCartResponse = {
        success: true,
        data: {
          id: 'cart-123',
          items: [],
          subtotal: 0,
          total: 0,
          currency: 'USD'
        }
      };
      vi.mocked(apiClient.get).mockResolvedValue(emptyCartResponse);

      const result = await CartAPI.getCart(mockAccessToken);

      expect(result.data.items).toEqual([]);
      expect(result.data.total).toBe(0);
    });
  });

  describe('addToCart', () => {
    it('should add item to cart with backend format', async () => {
      const mockResponse = mockApiResponses.cart.add;
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const itemData = {
        variant_id: 'variant-123',
        quantity: 2
      };

      const result = await CartAPI.addToCart(itemData, mockAccessToken);

      expect(apiClient.post).toHaveBeenCalledWith('/v1/cart/add?country=US&province=CA', itemData, {
        headers: { 'Authorization': `Bearer ${mockAccessToken}` },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should handle insufficient stock error', async () => {
      const errorResponse = {
        response: {
          status: 400,
          data: { message: 'Insufficient stock available' }
        }
      };
      vi.mocked(apiClient.post).mockRejectedValue(errorResponse);

      const itemData = {
        variant_id: 'variant-123',
        quantity: 999
      };

      await expect(CartAPI.addToCart(itemData, mockAccessToken)).rejects.toThrow();
    });
  });

  describe('updateCartItem', () => {
    it('should update cart item quantity with backend format', async () => {
      const updatedCart = {
        ...mockCart,
        items: [{
          ...mockCart.items[0],
          quantity: 3,
          total_price: 239.97
        }]
      };
      const mockResponse = { success: true, data: updatedCart };
      vi.mocked(apiClient.put).mockResolvedValue(mockResponse);

      const result = await CartAPI.updateCartItem('cart-item-123', 3, mockAccessToken);

      expect(apiClient.put).toHaveBeenCalledWith('/v1/cart/items/cart-item-123?country=US&province=CA', {
        quantity: 3
      }, {
        headers: { 'Authorization': `Bearer ${mockAccessToken}` },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should handle item not found error', async () => {
      const errorResponse = {
        response: {
          status: 404,
          data: { message: 'Cart item not found' }
        }
      };
      vi.mocked(apiClient.put).mockRejectedValue(errorResponse);

      await expect(CartAPI.updateCartItem('nonexistent', 2, mockAccessToken)).rejects.toThrow();
    });
  });

  describe('removeFromCart', () => {
    it('should remove item from cart', async () => {
      const updatedCart = {
        ...mockCart,
        items: [],
        subtotal: 0,
        total: 0
      };
      const mockResponse = { success: true, data: updatedCart };
      vi.mocked(apiClient.delete).mockResolvedValue(mockResponse);

      const result = await CartAPI.removeFromCart('cart-item-123', mockAccessToken);

      expect(apiClient.delete).toHaveBeenCalledWith('/v1/cart/items/cart-item-123', {
        headers: { 'Authorization': `Bearer ${mockAccessToken}` },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should handle removing non-existent item', async () => {
      const errorResponse = {
        response: {
          status: 404,
          data: { message: 'Cart item not found' }
        }
      };
      vi.mocked(apiClient.delete).mockRejectedValue(errorResponse);

      await expect(CartAPI.removeFromCart('nonexistent', mockAccessToken)).rejects.toThrow();
    });
  });

  describe('clearCart', () => {
    it('should clear entire cart', async () => {
      const emptyCart = {
        id: 'cart-123',
        items: [],
        subtotal: 0,
        total: 0,
        currency: 'USD'
      };
      const mockResponse = { success: true, data: emptyCart };
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await CartAPI.clearCart(mockAccessToken);

      expect(apiClient.post).toHaveBeenCalledWith('/v1/cart/clear', {}, {
        headers: { 'Authorization': `Bearer ${mockAccessToken}` },
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('applyPromocode', () => {
    it('should apply valid promo code', async () => {
      const discountedCart = {
        ...mockCart,
        discount_code: 'SAVE10',
        discount_amount: 18.40,
        total: 165.57
      };
      const mockResponse = { success: true, data: discountedCart };
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await CartAPI.applyPromocode('SAVE10', mockAccessToken);

      expect(apiClient.post).toHaveBeenCalledWith('/v1/cart/promocode', {
        code: 'SAVE10'
      }, {
        headers: { 'Authorization': `Bearer ${mockAccessToken}` },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should handle invalid promo code', async () => {
      const errorResponse = {
        response: {
          status: 400,
          data: { message: 'Invalid or expired promo code' }
        }
      };
      vi.mocked(apiClient.post).mockRejectedValue(errorResponse);

      await expect(CartAPI.applyPromocode('INVALID', mockAccessToken)).rejects.toThrow();
    });
  });

  describe('removePromocode', () => {
    it('should remove applied promo code', async () => {
      const cartWithoutDiscount = {
        ...mockCart,
        discount_code: null,
        discount_amount: 0,
        total: 183.97
      };
      const mockResponse = { success: true, data: cartWithoutDiscount };
      vi.mocked(apiClient.delete).mockResolvedValue(mockResponse);

      const result = await CartAPI.removePromocode(mockAccessToken);

      expect(apiClient.delete).toHaveBeenCalledWith('/v1/cart/promocode', {
        headers: { 'Authorization': `Bearer ${mockAccessToken}` },
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('checkStock', () => {
    it('should check stock availability for a variant', async () => {
      const stockResponse = {
        success: true,
        data: {
          variant_id: 'variant-123',
          available: true,
          stock_quantity: 10
        }
      };
      vi.mocked(apiClient.get).mockResolvedValue(stockResponse);

      const result = await CartAPI.checkStock('variant-123', 2);

      expect(apiClient.get).toHaveBeenCalledWith('/v1/inventory/check-stock/variant-123?quantity=2');
      expect(result).toEqual(stockResponse);
    });

    it('should handle invalid variant ID', async () => {
      await expect(CartAPI.checkStock(null, 2)).rejects.toThrow('Invalid variant ID provided');
      await expect(CartAPI.checkStock('undefined', 2)).rejects.toThrow('Invalid variant ID provided');
    });
  });

  describe('validateCart', () => {
    it('should validate cart items', async () => {
      const validationResult = {
        valid: true,
        issues: [],
        updated_cart: mockCart
      };
      const mockResponse = { success: true, data: validationResult };
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await CartAPI.validateCart(mockAccessToken);

      expect(apiClient.post).toHaveBeenCalledWith('/v1/cart/validate?country=US&province=CA', {}, {
        headers: { 'Authorization': `Bearer ${mockAccessToken}` },
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getCartItemCount', () => {
    it('should get cart item count', async () => {
      const countResponse = { success: true, data: 3 };
      vi.mocked(apiClient.get).mockResolvedValue(countResponse);

      const result = await CartAPI.getCartItemCount(mockAccessToken);

      expect(apiClient.get).toHaveBeenCalledWith('/v1/cart/count', {
        headers: { 'Authorization': `Bearer ${mockAccessToken}` },
      });
      expect(result).toEqual(countResponse);
    });
  });

  describe('checkBulkStock', () => {
    it('should check stock for multiple items', async () => {
      const items = [
        { variant_id: 'variant-123', quantity: 2 },
        { variant_id: 'variant-456', quantity: 1 }
      ];
      const stockResponse = {
        success: true,
        data: {
          results: [
            { variant_id: 'variant-123', available: true, stock_quantity: 10 },
            { variant_id: 'variant-456', available: true, stock_quantity: 5 }
          ]
        }
      };
      vi.mocked(apiClient.post).mockResolvedValue(stockResponse);

      const result = await CartAPI.checkBulkStock(items);

      expect(apiClient.post).toHaveBeenCalledWith('/v1/inventory/check-stock/bulk', items);
      expect(result).toEqual(stockResponse);
    });

    it('should handle invalid items array', async () => {
      await expect(CartAPI.checkBulkStock([])).rejects.toThrow('Invalid items array provided');
      await expect(CartAPI.checkBulkStock(null)).rejects.toThrow('Invalid items array provided');
    });
  });

  describe('error handling', () => {
    it('should handle network errors', async () => {
      const networkError = new Error('Network Error');
      vi.mocked(apiClient.get).mockRejectedValue(networkError);

      await expect(CartAPI.getCart(mockAccessToken)).rejects.toThrow('Network Error');
    });

    it('should handle server errors', async () => {
      const serverError = {
        response: {
          status: 500,
          data: { message: 'Internal Server Error' }
        }
      };
      vi.mocked(apiClient.get).mockRejectedValue(serverError);

      await expect(CartAPI.getCart(mockAccessToken)).rejects.toThrow();
    });

    it('should handle timeout errors', async () => {
      const timeoutError = {
        code: 'ECONNABORTED',
        message: 'timeout of 5000ms exceeded'
      };
      vi.mocked(apiClient.get).mockRejectedValue(timeoutError);

      await expect(CartAPI.getCart(mockAccessToken)).rejects.toThrow();
    });
  });
});