import React, { useEffect, createContext, useState, useCallback, useContext } from 'react';
import { TokenManager } from '../apis/client';
import { CartAPI } from '../apis/cart';
import { Cart, AddToCartRequest } from '../types';
import { toast } from 'react-hot-toast';

interface CartContextType {
  cart: Cart | null;
  loading: boolean;
  isOptimistic: boolean;
  fetchCart: () => Promise<void>;
  refreshCart: () => Promise<void>;
  addItem: (item: AddToCartRequest) => Promise<boolean>;
  removeItem: (itemId: string) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  clearCart: () => Promise<void>;
  totalItems: number;
  items: Cart['items'];
  // Enhanced functionality
  processingItems: Set<string>;
  clearingCart: boolean;
  validateForCheckout: () => boolean;
  getCartSummary: () => any;
}

export const CartContext = createContext<CartContextType | undefined>(undefined);

interface CartProviderProps {
  children: React.ReactNode;
}

export const CartProvider: React.FC<CartProviderProps> = ({ children }) => {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [isOptimistic, setIsOptimistic] = useState<boolean>(false);
  const [processingItems, setProcessingItems] = useState<Set<string>>(new Set());
  const [clearingCart, setClearingCart] = useState(false);

  // Helper function to calculate cart totals
  const calculateTotals = useCallback((cartData: Cart) => {
    const subtotal = cartData.items.reduce((sum, item) => 
      sum + (item.quantity * item.price_per_unit), 0
    );
    const taxAmount = subtotal * 0.08; // 8% tax rate - should be dynamic
    const totalAmount = subtotal + taxAmount + (cartData.shipping_amount || 0);
    
    return {
      ...cartData,
      subtotal,
      tax_amount: taxAmount,
      total_amount: totalAmount,
      item_count: cartData.items.length,
      total_items: cartData.items.reduce((sum, item) => sum + item.quantity, 0),
    };
  }, []);

  // ✅ Fetch the cart
  const fetchCart = useCallback(async () => {
    const token = TokenManager.getToken();
    if (!token) return;

    try {
      setLoading(true);
      console.log('CartContext: Fetching cart...');
      
      // Get location from localStorage (set by Header component)
      const detectedCountry = localStorage.getItem('detected_country') || 'US';
      const detectedProvince = localStorage.getItem('detected_province');
      
      // Only pass province if it's a valid value (not null, undefined, or string 'null'/'undefined')
      const validProvince = detectedProvince && detectedProvince !== 'null' && detectedProvince !== 'undefined' ? detectedProvince : undefined;
      
      const response = await CartAPI.getCart(token, detectedCountry, validProvince);
      console.log('CartContext: Fetch cart response:', response);
      
      // Backend returns { success: true, data: cart }
      // apiClient already extracts response.data, so we get { success: true, data: cart }
      // We need to access response.data to get the actual cart object
      const cartData = response?.data;
      console.log('CartContext: Setting cart data from fetch:', cartData);
      setCart(cartData);
      setIsOptimistic(false); // Clear optimistic state when real data arrives
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

  // ✅ Add item to cart with optimistic updates
  const addItem = async (item: AddToCartRequest): Promise<boolean> => {
    const token = TokenManager.getToken();
    if (!token) {
      // Throw error with specific message that executeWithAuth can catch
      throw new Error('User must be authenticated to add items to cart');
    }

    // Create optimistic item
    const optimisticItem = {
      id: `temp-${Date.now()}`,
      cart_id: cart?.id || '',
      variant_id: item.variant_id,
      quantity: item.quantity || 1,
      price_per_unit: item.price_per_unit || 0,
      total_price: (item.price_per_unit || 0) * (item.quantity || 1),
      variant: item.variant,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    // Store original cart for rollback
    const originalCart = cart;

    try {
      // Apply optimistic update
      if (cart) {
        const existingItemIndex = cart.items.findIndex(cartItem => 
          cartItem.variant_id === item.variant_id
        );

        let optimisticCart;
        if (existingItemIndex >= 0) {
          // Update existing item
          const updatedItems = [...cart.items];
          updatedItems[existingItemIndex] = {
            ...updatedItems[existingItemIndex],
            quantity: updatedItems[existingItemIndex].quantity + (item.quantity || 1),
            total_price: (updatedItems[existingItemIndex].quantity + (item.quantity || 1)) * updatedItems[existingItemIndex].price_per_unit,
          };
          optimisticCart = { ...cart, items: updatedItems };
        } else {
          // Add new item
          optimisticCart = { ...cart, items: [...cart.items, optimisticItem] };
        }

        optimisticCart = calculateTotals(optimisticCart);
        setCart(optimisticCart);
        setIsOptimistic(true);
      }

      setLoading(true);
      console.log('CartContext: Adding item to cart:', item);
      const response = await CartAPI.addToCart(item, token);
      console.log('CartContext: Add to cart response:', response);
      
      const cartData = response?.data;
      console.log('CartContext: Setting cart data:', cartData);
      setCart(cartData);
      setIsOptimistic(false);
      toast.success(`Added ${item.quantity || 1} item${(item.quantity || 1) > 1 ? 's' : ''} to cart`);
      return true;
    } catch (error: any) {
      console.error('Failed to add item to cart:', error);
      // Rollback optimistic update
      setCart(originalCart);
      setIsOptimistic(false);
      // Re-throw the error so executeWithAuth can handle 401s
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // ✅ Remove item from cart with optimistic updates
  const removeItem = async (itemId: string): Promise<void> => {
    const token = TokenManager.getToken();
    if (!token) {
      throw new Error('User must be authenticated to modify cart');
    }

    // Store original cart for rollback
    const originalCart = cart;
    const item = cart?.items?.find(item => item.id === itemId);
    const itemName = item?.variant?.product_name || item?.variant?.name || 'Item';

    // Add item to processing set
    setProcessingItems(prev => new Set(prev).add(itemId));

    try {
      // Apply optimistic update
      if (cart) {
        const updatedItems = cart.items.filter(item => item.id !== itemId);
        const optimisticCart = calculateTotals({ ...cart, items: updatedItems });
        setCart(optimisticCart);
        setIsOptimistic(true);
      }

      setLoading(true);
      const response = await CartAPI.removeFromCart(itemId, token);
      const cartData = response?.data;
      setCart(cartData);
      setIsOptimistic(false);
      toast.success(`${itemName} removed from cart`);
    } catch (error) {
      console.error('Failed to remove item from cart:', error);
      // Rollback optimistic update
      setCart(originalCart);
      setIsOptimistic(false);
      throw error;
    } finally {
      setLoading(false);
      // Remove item from processing set
      setProcessingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
    }
  };

  // ✅ Update item quantity with optimistic updates
  const updateQuantity = async (itemId: string, quantity: number): Promise<void> => {
    const token = TokenManager.getToken();
    if (!token) {
      throw new Error('User must be authenticated to update cart');
    }

    // Validate quantity
    if (quantity <= 0) {
      throw new Error('Quantity must be greater than 0');
    }

    // Find the item to check stock limits
    const item = cart?.items?.find(item => item.id === itemId);
    if (!item) {
      throw new Error('Item not found in cart');
    }

    // Check stock availability
    const maxStock = item.variant?.stock || 999;
    if (quantity > maxStock) {
      throw new Error(`Only ${maxStock} items available in stock`);
    }

    // Store original cart for rollback
    const originalCart = cart;

    // Add item to processing set
    setProcessingItems(prev => new Set(prev).add(itemId));

    try {
      // Apply optimistic update
      if (cart) {
        const updatedItems = [...cart.items];
        const itemIndex = updatedItems.findIndex(item => item.id === itemId);
        if (itemIndex >= 0) {
          updatedItems[itemIndex] = {
            ...updatedItems[itemIndex],
            quantity,
            total_price: quantity * updatedItems[itemIndex].price_per_unit,
          };
          const optimisticCart = calculateTotals({ ...cart, items: updatedItems });
          setCart(optimisticCart);
          setIsOptimistic(true);
        }
      }

      setLoading(true);
      console.log(`CartContext: Updating item ${itemId} to quantity ${quantity}`);
      
      // Validate that the item exists in current cart before making API call
      if (cart && cart.items) {
        const existingItem = cart.items.find(item => item.id === itemId);
        if (!existingItem) {
          console.warn(`CartContext: Item ${itemId} not found in current cart, refreshing cart first`);
          await fetchCart(); // Refresh cart to get latest state
          throw new Error('Cart item not found. Your cart has been refreshed with the latest items.');
        }
      }
      
      const response = await CartAPI.updateCartItem(itemId, quantity, token);
      console.log('CartContext: Update response:', response);
      const cartData = response?.data;
      console.log('CartContext: Setting updated cart data:', cartData);
      setCart(cartData);
      setIsOptimistic(false);
      toast.success('Cart updated successfully');
    } catch (error: any) {
      console.error('Failed to update cart item:', error);
      // Rollback optimistic update
      setCart(originalCart);
      setIsOptimistic(false);
      
      console.error('Error details:', {
        itemId,
        quantity,
        message: error?.message,
        response: error?.response?.data,
        status: error?.response?.status,
        currentCartItems: cart?.items?.map(item => ({ id: item.id, variant_id: item.variant_id }))
      });
      
      // If it's a 404 error, the item might have been removed or cart expired
      if (error?.response?.status === 404) {
        console.log('CartContext: 404 error, refreshing cart to get latest state');
        await fetchCart(); // Refresh cart to get latest state
        // Re-throw with more specific message
        throw new Error('Cart item not found. Your cart has been refreshed with the latest items.');
      }
      
      throw error;
    } finally {
      setLoading(false);
      // Remove item from processing set
      setProcessingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
    }
  };

  // ✅ Clear the cart with optimistic updates
  const clearCart = async () => {
    const token = TokenManager.getToken();
    if (!token) {
      throw new Error('User must be authenticated to clear cart');
    }

    if (!cart?.items?.length) {
      throw new Error('Cart is already empty');
    }

    // Store original cart for rollback
    const originalCart = cart;

    setClearingCart(true);
    
    try {
      // Apply optimistic update
      if (cart) {
        const optimisticCart = calculateTotals({ ...cart, items: [] });
        setCart(optimisticCart);
        setIsOptimistic(true);
      }

      setLoading(true);
      const response = await CartAPI.clearCart(token);
      if (response?.data) {
        setCart(response.data);
      } else {
        // Fallback if API doesn't return updated cart
        setCart(cart ? { ...cart, items: [], total_items: 0, total_amount: 0 } : null);
      }
      setIsOptimistic(false);
      toast.success('Cart cleared successfully');
    } catch (error) {
      console.error('Failed to clear cart:', error);
      // Rollback optimistic update
      setCart(originalCart);
      setIsOptimistic(false);
      throw error;
    } finally {
      setLoading(false);
      setClearingCart(false);
    }
  };

  // ✅ Derived values
  const totalItems = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0;
  const items = cart?.items || [];

  // ✅ Enhanced utility functions
  const validateForCheckout = useCallback(() => {
    if (!items.length) {
      toast.error('Your cart is empty. Add some items before checkout.');
      return false;
    }

    // Check for out of stock items
    const outOfStockItems = items.filter(item => 
      item.variant?.stock !== undefined && item.variant.stock < item.quantity
    );

    if (outOfStockItems.length > 0) {
      const itemNames = outOfStockItems.map(item => 
        item.variant?.product_name || item.variant?.name || 'Unknown item'
      ).join(', ');
      toast.error(`Some items are out of stock: ${itemNames}. Please update your cart.`);
      return false;
    }

    return true;
  }, [items]);

  const getCartSummary = useCallback(() => {
    return {
      itemCount: items.length,
      totalItems: totalItems,
      subtotal: cart?.subtotal || 0,
      tax: cart?.tax_amount || 0,
      shipping: cart?.shipping_amount || 0,
      total: cart?.total_amount || 0,
      currency: cart?.currency || 'USD'
    };
  }, [cart, items.length, totalItems]);

  // ✅ Context value
  return (
    <CartContext.Provider
      value={{
        cart,
        loading,
        isOptimistic,
        fetchCart,
        refreshCart,
        addItem,
        removeItem,
        updateQuantity,
        clearCart,
        totalItems,
        items,
        // Enhanced functionality
        processingItems,
        clearingCart,
        validateForCheckout,
        getCartSummary,
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