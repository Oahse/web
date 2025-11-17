import { useEffect, createContext, useState, useCallback, useContext } from 'react';
import { TokenManager } from '../apis/client';
import { CartAPI } from '../apis/cart';

export const CartContext = createContext(undefined);

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(false);

  // ✅ Fetch the cart
  const fetchCart = useCallback(async () => {
    const token = TokenManager.getToken();
    if (!token) return;

    try {
      setLoading(true);
      const response = await CartAPI.getCart(token);
      if (response?.data) {
        setCart(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch cart:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // ✅ Load cart on mount
  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  // ✅ Add item to cart
  const addItem = async (item) => {
    const token = TokenManager.getToken();
    if (!token) {
      throw new Error('User must be authenticated to add items to cart');
    }

    try {
      setLoading(true);
      const response = await CartAPI.addToCart(item, token);
      if (response?.data) {
        setCart(response.data);
      }
    } catch (error) {
      console.error('Failed to add item to cart:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // ✅ Remove item from cart
  const removeItem = async (itemId) => {
    const token = TokenManager.getToken();
    if (!token) {
      throw new Error('User must be authenticated to remove items from cart');
    }

    try {
      setLoading(true);
      const response = await CartAPI.removeFromCart(itemId, token);
      if (response?.data) {
        setCart(response.data);
      }
    } catch (error) {
      console.error('Failed to remove item from cart:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // ✅ Update item quantity
  const updateQuantity = async (itemId, quantity) => {
    const token = TokenManager.getToken();
    if (!token) {
      throw new Error('User must be authenticated to update cart items');
    }

    try {
      setLoading(true);
      const response = await CartAPI.updateCartItem(itemId, quantity, token);
      if (response?.data) {
        setCart(response.data);
      }
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
        // Fallback if API doesn’t return updated cart
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
export const useCart = () => {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart error: must be used within a CartProvider');
  }
  return context;
};