import React, { createContext, useContext, useCallback, useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { TokenManager } from '../apis/client';
import { CartAPI } from '../apis/cart';
import { Cart, AddToCartRequest } from '../types';
import { toast } from 'react-hot-toast';

interface CartContextType {
  cart: Cart | null;
  loading: boolean;
  error: any;
  addItem: (item: AddToCartRequest) => Promise<boolean>;
  removeItem: (itemId: string) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  clearCart: () => Promise<void>;
  totalItems: number;
  items: Cart['items'];
  refreshCart: () => Promise<void>;
}

export const CartContext = createContext<CartContextType | undefined>(undefined);

interface CartProviderProps {
  children: React.ReactNode;
}

export const CartProvider: React.FC<CartProviderProps> = ({ children }) => {
  // ✅ Using useState for all local state management
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<any>(null);
  
  const navigate = useNavigate();
  const location = useLocation();

  // Helper function to handle authentication errors
  const handleAuthError = useCallback((error: any) => {
    if (error.message === 'User must be authenticated to add items to cart' || 
        error.message === 'User must be authenticated') {
      navigate("/login", {
        replace: true,
        state: { from: location },
      });
    } else {
      console.error(error);
      toast.error(error.message || 'Failed to perform cart operation');
    }
  }, [navigate, location]);

  // Fetch cart data
  const fetchCart = useCallback(async () => {
    const token = TokenManager.getToken();
    if (!token) {
      setCart(null);
      setError(null); // Clear any previous errors when not authenticated
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const country = localStorage.getItem('detected_country') || 'US';
      const province = localStorage.getItem('detected_province');
      const validProvince = province && province !== 'null' && province !== 'undefined' ? province : undefined;
      
      const response = await CartAPI.getCart(token, country, validProvince);
      const cartData = response?.data;
      setCart(cartData);
      return cartData;
    } catch (err: any) {
      // Handle authentication errors gracefully
      if (err?.status === 401 || err?.response?.status === 401) {
        setCart(null);
        setError(null); // Don't show error for auth issues
        TokenManager.clearTokens(); // Clear invalid token
      } else {
        setError(err);
        console.error('Failed to fetch cart:', err);
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Refresh cart function
  const refreshCart = useCallback(async () => {
    await fetchCart();
  }, [fetchCart]);

  // Initial cart fetch and periodic updates
  useEffect(() => {
    fetchCart();
    
    // Poll cart every 30 seconds if user is authenticated
    const interval = setInterval(() => {
      if (TokenManager.getToken()) {
        fetchCart();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchCart]);

  // ✅ Optimistic add item with useState
  const addItem = useCallback(async (item: AddToCartRequest): Promise<boolean> => {
    const token = TokenManager.getToken();
    if (!token) {
      const error = new Error('User must be authenticated to add items to cart');
      handleAuthError(error);
      throw error;
    }

    // Only send the required fields to the backend
    const requestData = {
      variant_id: item.variant_id,
      quantity: item.quantity || 1
    };

    try {
      const response = await CartAPI.addToCart(requestData, token);
      setCart(response?.data);
      toast.success(`Added ${item.quantity || 1} item${(item.quantity || 1) > 1 ? 's' : ''} to cart`);
      return true;
    } catch (error: any) {
      handleAuthError(error);
      throw error;
    }
  }, [handleAuthError]);

  // ✅ Optimistic remove item with useState
  const removeItem = useCallback(async (itemId: string): Promise<void> => {
    const token = TokenManager.getToken();
    if (!token) {
      const error = new Error('User must be authenticated');
      handleAuthError(error);
      throw error;
    }

    const item = cart?.items?.find(i => i.id === itemId);
    const itemName = item?.variant?.product_name || item?.variant?.name || 'Item';

    // Optimistic update using setState
    const previousCart = cart;
    if (cart) {
      const newItems = cart.items.filter(i => i.id !== itemId);
      const optimisticCart = {
        ...cart,
        items: newItems,
        total_items: newItems.reduce((sum, i) => sum + i.quantity, 0)
      };
      setCart(optimisticCart);
    }

    try {
      const response = await CartAPI.removeFromCart(itemId, token);
      setCart(response?.data);
      toast.success(`${itemName} removed from cart`);
    } catch (error: any) {
      // Revert optimistic update
      setCart(previousCart);
      handleAuthError(error);
      throw error;
    }
  }, [cart, handleAuthError]);

  // ✅ Optimistic update quantity with useState
  const updateQuantity = useCallback(async (itemId: string, quantity: number): Promise<void> => {
    const token = TokenManager.getToken();
    if (!token) {
      const error = new Error('User must be authenticated');
      handleAuthError(error);
      throw error;
    }

    if (quantity <= 0) throw new Error('Quantity must be greater than 0');

    // Optimistic update using setState
    const previousCart = cart;
    if (cart) {
      const newItems = cart.items.map(item => 
        item.id === itemId 
          ? { ...item, quantity, total_price: quantity * item.price_per_unit }
          : item
      );
      const optimisticCart = {
        ...cart,
        items: newItems,
        total_items: newItems.reduce((sum, i) => sum + i.quantity, 0)
      };
      setCart(optimisticCart);
    }

    try {
      const response = await CartAPI.updateCartItem(itemId, quantity, token);
      setCart(response?.data);
      toast.success('Cart updated');
    } catch (error: any) {
      // Revert optimistic update
      setCart(previousCart);
      handleAuthError(error);
      throw error;
    }
  }, [cart, handleAuthError]);

  // ✅ Optimistic clear cart with useState
  const clearCart = useCallback(async () => {
    const token = TokenManager.getToken();
    if (!token) {
      const error = new Error('User must be authenticated');
      handleAuthError(error);
      throw error;
    }

    if (!cart?.items?.length) throw new Error('Cart is already empty');

    // Optimistic update using setState
    const previousCart = cart;
    const optimisticCart = { ...cart, items: [], total_items: 0 };
    setCart(optimisticCart);

    try {
      const response = await CartAPI.clearCart(token);
      setCart(response?.data || optimisticCart);
      toast.success('Cart cleared');
    } catch (error: any) {
      // Revert optimistic update
      setCart(previousCart);
      handleAuthError(error);
      throw error;
    }
  }, [cart, handleAuthError]);

  const totalItems = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0;
  const items = cart?.items || [];

  return (
    <CartContext.Provider
      value={{
        cart,
        loading,
        error,
        addItem,
        removeItem,
        updateQuantity,
        clearCart,
        totalItems,
        items,
        refreshCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = (): CartContextType => {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};