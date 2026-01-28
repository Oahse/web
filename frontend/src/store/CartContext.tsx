import React, { createContext, useContext, useCallback, useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { TokenManager } from '../api/client';
import { CartAPI } from '../api/cart';
import { Cart, AddToCartRequest } from '../types';
import { toast } from 'react-hot-toast';
import { handleCartSyncError, validateCartItem } from '../utils/cartSync';

interface CartContextType {
  cart: Cart | null;
  loading: boolean;
  error: any;
  addItem: (item: AddToCartRequest) => Promise<boolean>;
  removeItem: (itemId: string) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  clearCart: () => Promise<void>;
  refreshCart: () => Promise<void>;
  totalItems: number;
  items: Cart['items'];
  validateCart: () => Promise<void>;
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
  
  // Safely get navigation hooks
  let navigate: any = null;
  let location: any = null;
  
  try {
    navigate = useNavigate();
    location = useLocation();
  } catch (error) {
    // Navigation hooks not available (e.g., during testing or outside Router)
    console.warn('Navigation hooks not available in CartProvider:', error);
  }


  // Helper function to handle authentication errors
  const handleAuthError = useCallback((error: any) => {
    if (error.message === 'User must be authenticated to add items to cart' || 
        error.message === 'User must be authenticated') {
      if (navigate && location) {
        navigate("/login", {
          replace: true,
          state: { from: location },
        });
      } else {
        // Fallback if navigation is not available
        window.location.href = '/login';
      }
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
      // Ensure new object reference for React to detect changes
      setCart(cartData ? { ...cartData } : null);
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

  // Validate cart function
  const validateCart = useCallback(async () => {
    const token = TokenManager.getToken();
    if (!token) return;

    try {
      const response = await CartAPI.validateCart(token);
      if (response?.data) {
        setCart(response.data);
        toast.success('Cart synchronized');
      }
    } catch (error: any) {
      console.error('Failed to validate cart:', error);
      // If validation fails, just refresh the cart
      await fetchCart();
    }
  }, [fetchCart]);


  // Initial cart fetch and periodic updates
  useEffect(() => {
    // Fetch immediately on mount
    fetchCart();


    // Validate cart every 5 minutes to catch sync issues
    const validationInterval = setInterval(() => {
      if (TokenManager.getToken() && cart?.items && cart.items.length > 0) {
        validateCart();
      }
    }, 300000); // 5 minutes


    return () => {
      clearInterval(validationInterval);
    };
  }, [validateCart]);
  

  // ✅ Optimistic add item with useState first
  const addItem = async (item: AddToCartRequest): Promise<boolean> => {
    const token = TokenManager.getToken();
    if (!token) {
      const error = new Error('User must be authenticated to add items to cart');
      handleAuthError(error);
      throw error;
    }


    try {
      // Always call backend first to get complete cart data
      const response = await CartAPI.addToCart({
        variant_id: item.variant_id,
        quantity: item.quantity || 1
      }, token);
      
      // Update state with complete backend response - ensure new object reference
      const newCart = { ...response?.data };
      setCart(newCart);
      toast.success(`Added ${item.quantity || 1} item${(item.quantity || 1) > 1 ? 's' : ''} to cart`);
      return true;
    } catch (error: any) {
      handleAuthError(error);
      throw error;
    }
  };

  // ✅ Optimistic remove item with useState first
  const removeItem = async (itemId: string): Promise<void> => {
    const token = TokenManager.getToken();
    if (!token) {
      const error = new Error('User must be authenticated');
      handleAuthError(error);
      throw error;
    }

    const item = cart?.items?.find(i => i.id === itemId);
    if (!item) {
      toast.error('Item not found in cart. Refreshing cart...');
      await fetchCart();
      throw new Error('Item not found in cart');
    }

    const itemName = item?.variant?.product_name || item?.variant?.name || 'Item';

    // Store previous cart for rollback
    const previousCart = cart;

    // Optimistic update: Remove item immediately from UI
    if (cart) {
      const newItems = cart.items.filter(i => i.id !== itemId);
      const newSubtotal = newItems.reduce((sum, i) => sum + i.total_price, 0);
      
      setCart({
        ...cart,
        items: newItems,
        total_items: newItems.reduce((sum, i) => sum + i.quantity, 0),
        subtotal: newSubtotal,
        item_count: newItems.length
      });
    }

    try {
      const response = await CartAPI.removeFromCart(itemId, token);
      // Update with backend response to ensure consistency - ensure new object reference
      const newCart = { ...response?.data };
      setCart(newCart);
      toast.success(`${itemName} removed from cart`);
    } catch (error: any) {
      // Revert optimistic update on error
      setCart(previousCart);
      handleCartSyncError(error, fetchCart);
      throw error;
    }
  };

  // ✅ Optimistic update quantity with useState first
  const updateQuantity = async (itemId: string, quantity: number): Promise<void> => {
    const token = TokenManager.getToken();
    if (!token) {
      const error = new Error('User must be authenticated');
      handleAuthError(error);
      throw error;
    }

    if (quantity <= 0) throw new Error('Quantity must be greater than 0');

    // Check if item exists in current cart
    const itemExists = validateCartItem(cart, itemId);
    if (!itemExists) {
      toast.error('Item not found in cart. Refreshing cart...');
      await fetchCart();
      throw new Error('Item not found in cart');
    }


    // Optimistic update: Update quantity immediately in UI
    if (cart) {
      const newItems = cart.items.map(item => 
        item.id === itemId 
          ? { ...item, quantity, total_price: quantity * item.price_per_unit }
          : item
      );
      const newSubtotal = newItems.reduce((sum, i) => sum + i.total_price, 0);
      
      setCart({
        ...cart,
        items: newItems,
        total_items: newItems.reduce((sum, i) => sum + i.quantity, 0),
        subtotal: newSubtotal
      });
    }

    try {
      const response = await CartAPI.updateCartItem(itemId, quantity, token);
      // Update with backend response to ensure consistency - ensure new object reference
      const newCart = { ...response?.data };
      console.log(newCart,'=======dsdsdsinc')
      setCart(newCart);
      toast.success('Cart updated');
    } catch (error: any) {
      handleCartSyncError(error, fetchCart);
      throw error;
    }
  };

  // ✅ Optimistic clear cart with useState first
  const clearCart = async () => {
    const token = TokenManager.getToken();
    if (!token) {
      const error = new Error('User must be authenticated');
      handleAuthError(error);
      throw error;
    }

    if (!cart?.items?.length) throw new Error('Cart is already empty');

    // Optimistic update: Clear cart immediately in UI
    const optimisticCart = { 
      ...cart, 
      items: [], 
      total_items: 0,
      subtotal: 0,
      tax_amount: 0,
      tax_rate: 0,
      shipping_cost: 0, // Updated field name
      shipping_amount: 0, // Keep for backward compatibility
      total_amount: 0,
      item_count: 0
    };
    setCart(optimisticCart);

    try {
      const response = await CartAPI.clearCart(token);
      // Update with backend response to ensure consistency - ensure new object reference
      const newCart = { ...(response?.data || optimisticCart) };
      setCart(newCart);
      toast.success('Cart cleared');
    } catch (error: any) {
      handleAuthError(error);
      throw error;
    }
  };

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
        refreshCart: fetchCart,
        totalItems,
        items,
        validateCart,
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