/**
 * Tests for useCart hook - Comprehensive test suite
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useCart } from '../../hooks/useCart';
import { CartContext } from '../../store/CartContext';
import React from 'react';

describe('useCart', () => {
  const mockCartContext = {
    cart: null,
    items: [],
    itemCount: 0,
    subtotal: 0,
    total: 0,
    isLoading: false,
    error: null,
    addItem: vi.fn(),
    removeItem: vi.fn(),
    updateItemQuantity: vi.fn(),
    clearCart: vi.fn(),
    refreshCart: vi.fn(),
    applyPromocode: vi.fn(),
    removePromocode: vi.fn(),
    validateCart: vi.fn(),
    getShippingOptions: vi.fn(),
    calculateTotals: vi.fn(),
    mergeGuestCart: vi.fn()
  };

  const wrapper = ({ children }: { children: React.ReactNode }) => 
    React.createElement(CartContext.Provider, { value: mockCartContext }, children);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Context Integration', () => {
    it('should return cart context values', () => {
      const { result } = renderHook(() => useCart(), { wrapper });

      expect(result.current.cart).toBe(mockCartContext.cart);
      expect(result.current.items).toBe(mockCartContext.items);
      expect(result.current.itemCount).toBe(mockCartContext.itemCount);
      expect(result.current.subtotal).toBe(mockCartContext.subtotal);
      expect(result.current.total).toBe(mockCartContext.total);
      expect(result.current.isLoading).toBe(mockCartContext.isLoading);
      expect(result.current.error).toBe(mockCartContext.error);
    });

    it('should return cart context methods', () => {
      const { result } = renderHook(() => useCart(), { wrapper });

      expect(result.current.addItem).toBe(mockCartContext.addItem);
      expect(result.current.removeItem).toBe(mockCartContext.removeItem);
      expect(result.current.updateItemQuantity).toBe(mockCartContext.updateItemQuantity);
      expect(result.current.clearCart).toBe(mockCartContext.clearCart);
      expect(result.current.refreshCart).toBe(mockCartContext.refreshCart);
      expect(result.current.applyPromocode).toBe(mockCartContext.applyPromocode);
      expect(result.current.removePromocode).toBe(mockCartContext.removePromocode);
      expect(result.current.validateCart).toBe(mockCartContext.validateCart);
      expect(result.current.getShippingOptions).toBe(mockCartContext.getShippingOptions);
      expect(result.current.calculateTotals).toBe(mockCartContext.calculateTotals);
      expect(result.current.mergeGuestCart).toBe(mockCartContext.mergeGuestCart);
    });

    it('should throw error when used outside CartProvider', () => {
      // Mock console.error to avoid noise in test output
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        renderHook(() => useCart());
      }).toThrow('useCart must be used within a CartProvider');

      consoleSpy.mockRestore();
    });
  });

  describe('Cart State Values', () => {
    it('should handle empty cart state', () => {
      const emptyCartContext = {
        ...mockCartContext,
        cart: null,
        items: [],
        itemCount: 0,
        subtotal: 0,
        total: 0
      };

      const emptyWrapper = ({ children }: { children: React.ReactNode }) => (
        <CartContext.Provider value={emptyCartContext}>
          {children}
        </CartContext.Provider>
      );

      const { result } = renderHook(() => useCart(), { wrapper: emptyWrapper });

      expect(result.current.cart).toBeNull();
      expect(result.current.items).toHaveLength(0);
      expect(result.current.itemCount).toBe(0);
      expect(result.current.subtotal).toBe(0);
      expect(result.current.total).toBe(0);
    });

    it('should handle cart with items', () => {
      const cartWithItems = {
        ...mockCartContext,
        cart: {
          id: 'cart123',
          user_id: 'user123',
          created_at: '2024-01-01T00:00:00Z'
        },
        items: [
          {
            id: 'item123',
            variant_id: 'var123',
            quantity: 2,
            unit_price: 49.99,
            total_price: 99.98,
            variant: {
              id: 'var123',
              name: 'Red - Large',
              product: {
                id: 'prod123',
                name: 'T-Shirt',
                images: ['shirt1.jpg']
              }
            }
          },
          {
            id: 'item456',
            variant_id: 'var456',
            quantity: 1,
            unit_price: 29.99,
            total_price: 29.99,
            variant: {
              id: 'var456',
              name: 'Blue - Medium',
              product: {
                id: 'prod456',
                name: 'Jeans',
                images: ['jeans1.jpg']
              }
            }
          }
        ],
        itemCount: 3,
        subtotal: 129.97,
        total: 139.96 // Including tax/shipping
      };

      const itemsWrapper = ({ children }: { children: React.ReactNode }) => (
        <CartContext.Provider value={cartWithItems}>
          {children}
        </CartContext.Provider>
      );

      const { result } = renderHook(() => useCart(), { wrapper: itemsWrapper });

      expect(result.current.cart).toEqual(cartWithItems.cart);
      expect(result.current.items).toHaveLength(2);
      expect(result.current.itemCount).toBe(3);
      expect(result.current.subtotal).toBe(129.97);
      expect(result.current.total).toBe(139.96);
    });

    it('should handle loading state', () => {
      const loadingContext = {
        ...mockCartContext,
        isLoading: true
      };

      const loadingWrapper = ({ children }: { children: React.ReactNode }) => (
        <CartContext.Provider value={loadingContext}>
          {children}
        </CartContext.Provider>
      );

      const { result } = renderHook(() => useCart(), { wrapper: loadingWrapper });

      expect(result.current.isLoading).toBe(true);
    });

    it('should handle error state', () => {
      const errorContext = {
        ...mockCartContext,
        error: 'Failed to load cart'
      };

      const errorWrapper = ({ children }: { children: React.ReactNode }) => (
        <CartContext.Provider value={errorContext}>
          {children}
        </CartContext.Provider>
      );

      const { result } = renderHook(() => useCart(), { wrapper: errorWrapper });

      expect(result.current.error).toBe('Failed to load cart');
    });
  });

  describe('Cart Methods', () => {
    it('should provide addItem method', () => {
      const { result } = renderHook(() => useCart(), { wrapper });

      expect(typeof result.current.addItem).toBe('function');
      expect(result.current.addItem).toBe(mockCartContext.addItem);
    });

    it('should provide removeItem method', () => {
      const { result } = renderHook(() => useCart(), { wrapper });

      expect(typeof result.current.removeItem).toBe('function');
      expect(result.current.removeItem).toBe(mockCartContext.removeItem);
    });

    it('should provide updateItemQuantity method', () => {
      const { result } = renderHook(() => useCart(), { wrapper });

      expect(typeof result.current.updateItemQuantity).toBe('function');
      expect(result.current.updateItemQuantity).toBe(mockCartContext.updateItemQuantity);
    });

    it('should provide clearCart method', () => {
      const { result } = renderHook(() => useCart(), { wrapper });

      expect(typeof result.current.clearCart).toBe('function');
      expect(result.current.clearCart).toBe(mockCartContext.clearCart);
    });

    it('should provide refreshCart method', () => {
      const { result } = renderHook(() => useCart(), { wrapper });

      expect(typeof result.current.refreshCart).toBe('function');
      expect(result.current.refreshCart).toBe(mockCartContext.refreshCart);
    });
  });

  describe('Promocode Methods', () => {
    it('should provide applyPromocode method', () => {
      const { result } = renderHook(() => useCart(), { wrapper });

      expect(typeof result.current.applyPromocode).toBe('function');
      expect(result.current.applyPromocode).toBe(mockCartContext.applyPromocode);
    });

    it('should provide removePromocode method', () => {
      const { result } = renderHook(() => useCart(), { wrapper });

      expect(typeof result.current.removePromocode).toBe('function');
      expect(result.current.removePromocode).toBe(mockCartContext.removePromocode);
    });
  });

  describe('Cart Validation and Calculation Methods', () => {
    it('should provide validateCart method', () => {
      const { result } = renderHook(() => useCart(), { wrapper });

      expect(typeof result.current.validateCart).toBe('function');
      expect(result.current.validateCart).toBe(mockCartContext.validateCart);
    });

    it('should provide getShippingOptions method', () => {
      const { result } = renderHook(() => useCart(), { wrapper });

      expect(typeof result.current.getShippingOptions).toBe('function');
      expect(result.current.getShippingOptions).toBe(mockCartContext.getShippingOptions);
    });

    it('should provide calculateTotals method', () => {
      const { result } = renderHook(() => useCart(), { wrapper });

      expect(typeof result.current.calculateTotals).toBe('function');
      expect(result.current.calculateTotals).toBe(mockCartContext.calculateTotals);
    });
  });

  describe('Guest Cart Methods', () => {
    it('should provide mergeGuestCart method', () => {
      const { result } = renderHook(() => useCart(), { wrapper });

      expect(typeof result.current.mergeGuestCart).toBe('function');
      expect(result.current.mergeGuestCart).toBe(mockCartContext.mergeGuestCart);
    });
  });

  describe('Complex Cart States', () => {
    it('should handle cart with promocode applied', () => {
      const cartWithPromocode = {
        ...mockCartContext,
        cart: {
          id: 'cart123',
          promocode: {
            code: 'SAVE10',
            discount_type: 'percentage',
            discount_value: 10,
            discount_amount: 12.99
          }
        },
        items: [
          {
            id: 'item123',
            variant_id: 'var123',
            quantity: 1,
            unit_price: 129.99,
            total_price: 129.99
          }
        ],
        subtotal: 129.99,
        total: 116.99 // After 10% discount
      };

      const promocodeWrapper = ({ children }: { children: React.ReactNode }) => (
        <CartContext.Provider value={cartWithPromocode}>
          {children}
        </CartContext.Provider>
      );

      const { result } = renderHook(() => useCart(), { wrapper: promocodeWrapper });

      expect(result.current.cart?.promocode?.code).toBe('SAVE10');
      expect(result.current.subtotal).toBe(129.99);
      expect(result.current.total).toBe(116.99);
    });

    it('should handle cart with shipping information', () => {
      const cartWithShipping = {
        ...mockCartContext,
        cart: {
          id: 'cart123',
          shipping_method: {
            id: 'standard',
            name: 'Standard Shipping',
            cost: 9.99,
            estimated_days: 5
          }
        },
        items: [
          {
            id: 'item123',
            variant_id: 'var123',
            quantity: 1,
            unit_price: 99.99,
            total_price: 99.99
          }
        ],
        subtotal: 99.99,
        total: 109.98 // Including shipping
      };

      const shippingWrapper = ({ children }: { children: React.ReactNode }) => (
        <CartContext.Provider value={cartWithShipping}>
          {children}
        </CartContext.Provider>
      );

      const { result } = renderHook(() => useCart(), { wrapper: shippingWrapper });

      expect(result.current.cart?.shipping_method?.name).toBe('Standard Shipping');
      expect(result.current.cart?.shipping_method?.cost).toBe(9.99);
      expect(result.current.total).toBe(109.98);
    });

    it('should handle cart with tax information', () => {
      const cartWithTax = {
        ...mockCartContext,
        cart: {
          id: 'cart123',
          tax_amount: 8.00,
          tax_rate: 0.08,
          tax_location: 'NY, US'
        },
        items: [
          {
            id: 'item123',
            variant_id: 'var123',
            quantity: 1,
            unit_price: 100.00,
            total_price: 100.00
          }
        ],
        subtotal: 100.00,
        total: 108.00 // Including tax
      };

      const taxWrapper = ({ children }: { children: React.ReactNode }) => (
        <CartContext.Provider value={cartWithTax}>
          {children}
        </CartContext.Provider>
      );

      const { result } = renderHook(() => useCart(), { wrapper: taxWrapper });

      expect(result.current.cart?.tax_amount).toBe(8.00);
      expect(result.current.cart?.tax_rate).toBe(0.08);
      expect(result.current.cart?.tax_location).toBe('NY, US');
      expect(result.current.total).toBe(108.00);
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined context gracefully', () => {
      const undefinedWrapper = ({ children }: { children: React.ReactNode }) => (
        <CartContext.Provider value={undefined as any}>
          {children}
        </CartContext.Provider>
      );

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        renderHook(() => useCart(), { wrapper: undefinedWrapper });
      }).toThrow('useCart must be used within a CartProvider');

      consoleSpy.mockRestore();
    });

    it('should handle null context gracefully', () => {
      const nullWrapper = ({ children }: { children: React.ReactNode }) => (
        <CartContext.Provider value={null as any}>
          {children}
        </CartContext.Provider>
      );

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        renderHook(() => useCart(), { wrapper: nullWrapper });
      }).toThrow('useCart must be used within a CartProvider');

      consoleSpy.mockRestore();
    });

    it('should handle cart with mixed item types', () => {
      const mixedCartContext = {
        ...mockCartContext,
        items: [
          {
            id: 'item123',
            variant_id: 'var123',
            quantity: 1,
            unit_price: 49.99,
            total_price: 49.99,
            variant: {
              id: 'var123',
              name: 'Physical Product',
              product: { id: 'prod123', name: 'T-Shirt' }
            }
          },
          {
            id: 'item456',
            variant_id: 'var456',
            quantity: 1,
            unit_price: 19.99,
            total_price: 19.99,
            variant: {
              id: 'var456',
              name: 'Digital Product',
              product: { id: 'prod456', name: 'E-book' }
            }
          }
        ],
        itemCount: 2,
        subtotal: 69.98,
        total: 69.98
      };

      const mixedWrapper = ({ children }: { children: React.ReactNode }) => (
        <CartContext.Provider value={mixedCartContext}>
          {children}
        </CartContext.Provider>
      );

      const { result } = renderHook(() => useCart(), { wrapper: mixedWrapper });

      expect(result.current.items).toHaveLength(2);
      expect(result.current.itemCount).toBe(2);
      expect(result.current.items[0].variant?.product?.name).toBe('T-Shirt');
      expect(result.current.items[1].variant?.product?.name).toBe('E-book');
    });
  });

  describe('Real-world Usage Scenarios', () => {
    it('should handle typical e-commerce cart flow', () => {
      const ecommerceCartContext = {
        ...mockCartContext,
        cart: {
          id: 'cart123',
          user_id: 'user123',
          session_id: null,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-15T10:00:00Z'
        },
        items: [
          {
            id: 'item123',
            variant_id: 'var123',
            quantity: 2,
            unit_price: 79.99,
            total_price: 159.98,
            variant: {
              id: 'var123',
              name: 'Blue - Large',
              sku: 'SHIRT-BLUE-L',
              stock_quantity: 10,
              product: {
                id: 'prod123',
                name: 'Premium T-Shirt',
                brand: 'BrandName',
                images: ['shirt1.jpg', 'shirt2.jpg']
              }
            }
          }
        ],
        itemCount: 2,
        subtotal: 159.98,
        total: 173.58, // Including tax and shipping
        isLoading: false,
        error: null
      };

      const ecommerceWrapper = ({ children }: { children: React.ReactNode }) => (
        <CartContext.Provider value={ecommerceCartContext}>
          {children}
        </CartContext.Provider>
      );

      const { result } = renderHook(() => useCart(), { wrapper: ecommerceWrapper });

      expect(result.current.cart?.id).toBe('cart123');
      expect(result.current.items[0].variant?.sku).toBe('SHIRT-BLUE-L');
      expect(result.current.items[0].variant?.stock_quantity).toBe(10);
      expect(result.current.subtotal).toBe(159.98);
      expect(result.current.total).toBe(173.58);
    });

    it('should handle guest cart scenario', () => {
      const guestCartContext = {
        ...mockCartContext,
        cart: {
          id: 'guest_cart_456',
          user_id: null,
          session_id: 'session_789',
          created_at: '2024-01-15T10:00:00Z'
        },
        items: [
          {
            id: 'guest_item_123',
            variant_id: 'var123',
            quantity: 1,
            unit_price: 29.99,
            total_price: 29.99
          }
        ],
        itemCount: 1,
        subtotal: 29.99,
        total: 29.99
      };

      const guestWrapper = ({ children }: { children: React.ReactNode }) => (
        <CartContext.Provider value={guestCartContext}>
          {children}
        </CartContext.Provider>
      );

      const { result } = renderHook(() => useCart(), { wrapper: guestWrapper });

      expect(result.current.cart?.user_id).toBeNull();
      expect(result.current.cart?.session_id).toBe('session_789');
      expect(result.current.itemCount).toBe(1);
    });
  });
});