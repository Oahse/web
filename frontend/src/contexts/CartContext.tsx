import React, { createContext, useContext, useCallback, useState, useEffect } from 'react';
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

  // Fetch cart data
  const fetchCart = useCallback(async () => {
    const token = TokenManager.getToken();
    if (!token) {
      setCart(null);
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
    } catch (err) {
      setError(err);
      console.error('Failed to fetch cart:', err);
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
      throw new Error('User must be authenticated to add items to cart');
    }

    // Optimistic update using setState
    const previousCart = cart;
    if (cart) {
      const existingIndex = cart.items.findIndex(i => i.variant_id === item.variant_id);
      let newItems;
      
      if (existingIndex >= 0) {
        newItems = [...cart.items];
        newItems[existingIndex] = {
          ...newItems[existingIndex],
          quantity: newItems[existingIndex].quantity + (item.quantity || 1)
        };
      } else {
        const newItem = {
          id: `temp-${Date.now()}`,
          cart_id: cart.id || '',
          variant_id: item.variant_id,
          quantity: item.quantity || 1,
          price_per_unit: item.price_per_unit || 0,
          total_price: (item.price_per_unit || 0) * (item.quantity || 1),
          variant: item.variant,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        newItems = [...cart.items, newItem];
      }

      const optimisticCart = {
        ...cart,
        items: newItems,
        total_items: newItems.reduce((sum, i) => sum + i.quantity, 0)
      };
      setCart(optimisticCart);
    }

    try {
      const response = await CartAPI.addToCart(item, token);
      setCart(response?.data);
      toast.success(`Added ${item.quantity || 1} item${(item.quantity || 1) > 1 ? 's' : ''} to cart`);
      return true;
    } catch (error: any) {
      // Revert optimistic update
      setCart(previousCart);
      toast.error(error.message || 'Failed to add item to cart');
      throw error;
    }
  }, [cart]);

  // ✅ Optimistic remove item with useState
  const removeItem = useCallback(async (itemId: string): Promise<void> => {
    const token = TokenManager.getToken();
    if (!token) throw new Error('User must be authenticated');

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
      toast.error(error.message || 'Failed to remove item from cart');
      throw error;
    }
  }, [cart]);

  // ✅ Optimistic update quantity with useState
  const updateQuantity = useCallback(async (itemId: string, quantity: number): Promise<void> => {
    const token = TokenManager.getToken();
    if (!token) throw new Error('User must be authenticated');

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
      toast.error(error.message || 'Failed to update cart');
      throw error;
    }
  }, [cart]);

  // ✅ Optimistic clear cart with useState
  const clearCart = useCallback(async () => {
    const token = TokenManager.getToken();
    if (!token) throw new Error('User must be authenticated');

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
      toast.error(error.message || 'Failed to clear cart');
      throw error;
    }
  }, [cart]);

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