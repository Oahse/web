import React, { useEffect, createContext, useState, useCallback, useContext } from 'react';
import { TokenManager } from '../apis/client';
import { CartAPI } from '../apis/cart';
import { Cart, AddToCartRequest } from '../types';

interface CartContextType {
  cart: Cart | null;
  loading: boolean;
  fetchCart: () => Promise<void>;
  refreshCart: () => Promise<void>;
  addItem: (item: AddToCartRequest) => Promise<boolean>;
  removeItem: (itemId: string) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  clearCart: () => Promise<void>;
  totalItems: number;
  items: Cart['items'];
}

export const CartContext = createContext<CartContextType | undefined>(undefined);

interface CartProviderProps {
  children: React.ReactNode;
}

export const CartProvider: React.FC<CartProviderProps> = ({ children }) => {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // ✅ Fetch the cart
  const fetchCart = useCallback(async () => {
    const token = TokenManager.getToken();
    if (!token) return;

    try {
      setLoading(true);
      const response = await CartAPI.getCart(token);
      // Backend returns { success: true, data: cart }
      // apiClient returns response.data, so we get { success: true, data: cart }
      // We need to access response.data to get the actual cart
      const cartData = response?.data || response;
      setCart(cartData);
    } catch (error) {
      console.error('Failed to fetch cart:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // ✅ Refresh cart (alias for fetchCart for price updates)
  const refreshCart = useCallback(async () => {
    await fetchCart();
  }, [fetchCart]);

  // ✅ Load cart on mount
  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  // ✅ Add item to cart
  const addItem = async (item: AddToCartRequest): Promise<boolean> => {
    const token = TokenManager.getToken();
    if (!token) {
      throw new Error('User must be authenticated to add items to cart');
    }

    try {
      setLoading(true);
      const response = await CartAPI.addToCart(item, token);
      const cartData = response?.data || response;
      setCart(cartData);
      return true;
    } catch (error) {
      console.error('Failed to add item to cart:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // ✅ Remove item from cart
  const removeItem = async (itemId: string): Promise<void> => {
    const token = TokenManager.getToken();
    if (!token) {
      throw new Error('User must be authenticated to remove items from cart');
    }

    try {
      setLoading(true);
      const response = await CartAPI.removeFromCart(itemId, token);
      const cartData = response?.data || response;
      setCart(cartData);
    } catch (error) {
      console.error('Failed to remove item from cart:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // ✅ Update item quantity
  const updateQuantity = async (itemId: string, quantity: number): Promise<void> => {
    const token = TokenManager.getToken();
    if (!token) {
      throw new Error('User must be authenticated to update cart items');
    }

    try {
      setLoading(true);
      const response = await CartAPI.updateCartItem(itemId, quantity, token);
      const cartData = response?.data || response;
      setCart(cartData);
    } catch (error) {
      console.error('Failed to update cart item:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // ✅ Clear the cart
  const clearCart = async () => {
    const token = TokenManager.getToken();
    if (!token) {
      throw new Error('User must be authenticated to clear cart');
    }

    try {
      setLoading(true);
      const response = await CartAPI.clearCart(token);
      if (response?.data) {
        setCart(response.data);
      } else {
        // Fallback if API doesn't return updated cart
        setCart(cart ? { ...cart, items: [], total_items: 0, total_amount: 0 } : null);
      }
    } catch (error) {
      console.error('Failed to clear cart:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // ✅ Derived values
  const totalItems = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0;
  const items = cart?.items || [];

  // ✅ Context value
  return (
    <CartContext.Provider
      value={{
        cart,
        loading,
        fetchCart,
        refreshCart,
        addItem,
        removeItem,
        updateQuantity,
        clearCart,
        totalItems,
        items,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = (): CartContextType => {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart error: must be used within a CartProvider');
  }
  return context;
};