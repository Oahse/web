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
      console.log('CartContext: Fetching cart...');
      
      // Get location from localStorage (set by Header component)
      const detectedCountry = localStorage.getItem('detected_country') || 'US';
      const detectedProvince = localStorage.getItem('detected_province') || null;
      
      const response = await CartAPI.getCart(token, detectedCountry, detectedProvince);
      console.log('CartContext: Fetch cart response:', response);
      
      // Backend returns { success: true, data: cart }
      // apiClient already extracts response.data, so we get { success: true, data: cart }
      // We need to access response.data to get the actual cart object
      const cartData = response?.data;
      console.log('CartContext: Setting cart data from fetch:', cartData);
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

  // ✅ Load cart on mount and when location changes (only if authenticated)
  useEffect(() => {
    const token = TokenManager.getToken();
    if (token) {
      fetchCart();
    }
    
    // Listen for location changes
    const handleLocationChange = () => {
      const token = TokenManager.getToken();
      if (token) {
        console.log('Location changed, refreshing cart for tax recalculation');
        fetchCart();
      }
    };
    
    window.addEventListener('locationDetected', handleLocationChange);
    
    return () => {
      window.removeEventListener('locationDetected', handleLocationChange);
    };
  }, [fetchCart]);

  // ✅ Add item to cart
  const addItem = async (item: AddToCartRequest): Promise<boolean> => {
    const token = TokenManager.getToken();
    if (!token) {
      // Return false instead of throwing error - let useAuthenticatedAction handle the redirect
      return false;
    }

    try {
      setLoading(true);
      console.log('CartContext: Adding item to cart:', item);
      const response = await CartAPI.addToCart(item, token);
      console.log('CartContext: Add to cart response:', response);
      
      // Backend returns { success: true, data: cart }
      // apiClient already extracts response.data, so we get { success: true, data: cart }
      // We need to access response.data to get the actual cart object
      const cartData = response?.data;
      console.log('CartContext: Setting cart data:', cartData);
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
      // Return early instead of throwing error - let useAuthenticatedAction handle the redirect
      return;
    }

    try {
      setLoading(true);
      const response = await CartAPI.removeFromCart(itemId, token);
      const cartData = response?.data;
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
      // Return early instead of throwing error - let useAuthenticatedAction handle the redirect
      return;
    }

    try {
      setLoading(true);
      const response = await CartAPI.updateCartItem(itemId, quantity, token);
      const cartData = response?.data;
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
      // Return early instead of throwing error - let useAuthenticatedAction handle the redirect
      return;
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