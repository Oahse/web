import React, { useEffect, useState, createContext, useCallback, useContext, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { ProductsAPI } from '../api/products';
import { WishlistAPI } from '../api/wishlists';
import { toast } from 'react-hot-toast';
import { Wishlist } from '../types';

interface WishlistContextType {
  wishlists: Wishlist[];
  defaultWishlist: Wishlist | undefined;
  loading: boolean;
  error: string | null;
  fetchWishlists: (retryCount?: number) => Promise<void>;
  addItem: (productId: string, variantId?: string, quantity?: number) => Promise<boolean>;
  removeItem: (wishlistId: string, itemId: string) => Promise<boolean>;
  isInWishlist: (productId: string, variantId?: string) => boolean;
  clearWishlist: () => Promise<boolean>;
}

export const WishlistContext = createContext<WishlistContextType | undefined>(undefined);

export const WishlistProvider = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated, user } = useAuth();
  const [wishlists, setWishlists] = useState<Wishlist[]>([]);
  const [defaultWishlist, setDefaultWishlist] = useState<Wishlist | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // ✅ Wrap fetchWishlists in useCallback to prevent infinite useEffect loops
  const fetchWishlists = useCallback(async (retryCount = 0) => {
    if (!isAuthenticated || !user || !(user as any).id) {
      setWishlists([]);
      setDefaultWishlist(undefined);
      setLoading(false);
      setError(null);
      return;
    }

    const userId = (user as any).id;

    setLoading(true);
    setError(null);

    try {
      const response = await WishlistAPI.getWishlists(userId);
      // The API client returns the response data directly, which includes success, data, message
      if (response.success) {
        // Fetch complete product data for each wishlist item
        const enhancedWishlists = await Promise.all(
          response.data.map(async (wishlist: Wishlist) => {
            const enhancedItems = await Promise.all(
              wishlist.items.map(async (item: any) => {
                try {
                  // Fetch complete product data
                  const productResponse = await ProductsAPI.getProduct(item.product_id);
                  if (productResponse.success && productResponse.data) {
                    const productData = productResponse.data;
                    return {
                      ...item,
                      product: productData,
                      variant: productData.variants?.find((v: any) => v.id === item.variant_id) || 
                              productData.variants?.[0] || item.variant
                    };
                  }
                  return item;
                } catch (error) {
                  console.error(`Failed to fetch product ${item.product_id}:`, error);
                  return item;
                }
              })
            );
            return {
              ...wishlist,
              items: enhancedItems
            };
          })
        );
        
        setWishlists(enhancedWishlists);
        setDefaultWishlist(enhancedWishlists.find((wl: Wishlist) => wl.is_default) || enhancedWishlists[0]);
        setError(null);
      } else {
        const errorMsg = response.message || 'Failed to load wishlists.';
        console.error('Failed to fetch wishlists:', errorMsg);
        setError(errorMsg);
        
        // Retry mechanism: retry up to 2 times with exponential backoff
        if (retryCount < 2) {
          const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s
          setTimeout(() => fetchWishlists(retryCount + 1), delay);
        } else {
          toast.error(errorMsg);
        }
      }
    } catch (error: any) {
      const errorMsg = 'Failed to load wishlists.';
      console.error('Failed to fetch wishlists:', error);
      setError(errorMsg);
      
      // Don't retry on 404 (endpoint doesn't exist) - just set empty wishlists
      if (error?.response?.status === 404) {
        setWishlists([]);
        setDefaultWishlist(undefined);
        setError(null); // Clear error for 404 since it's expected if feature doesn't exist
      } else if (retryCount < 2) {
        // Retry mechanism: retry up to 2 times with exponential backoff (for network errors)
        const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s
        setTimeout(() => fetchWishlists(retryCount + 1), delay);
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, user]);

  // ✅ Run fetch on mount or when auth changes
  useEffect(() => {
    fetchWishlists();
  }, [fetchWishlists]);

  const addItem = async (productId: string, variantId?: string, quantity = 1): Promise<boolean> => {
    if (!isAuthenticated || !user || !(user as any).id) {
      toast.error('Please log in to add items to wishlist.');
      return false;
    }

    const userId = (user as any).id;

    let currentDefaultWishlist = defaultWishlist;

    // If no wishlist exists, create one
    if (!currentDefaultWishlist) {
      try {
        const response = await WishlistAPI.createWishlist(userId, {
          name: 'My Wishlist',
          is_default: true,
        });
        if (response.success) {
          currentDefaultWishlist = response.data;
          setDefaultWishlist(response.data);
          setWishlists(prev => [...prev, response.data]);
          toast.success('Default wishlist created!');
        } else {
          console.error('Failed to create default wishlist:', response.message);
          toast.error(response.message || 'Failed to create default wishlist.');
          return false;
        }
      } catch (error) {
        console.error('Failed to create default wishlist:', error);
        toast.error('Failed to create default wishlist.');
        return false;
      }
    }

    if (!currentDefaultWishlist) {
      return false;
    }

    // Optimistic update: add item to UI immediately with product data
    const optimisticItem: any = {
      id: `temp-${Date.now()}`,
      product_id: productId,
      variant_id: variantId,
      quantity,
      wishlist_id: currentDefaultWishlist.id,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    // Try to get product data for optimistic update
    try {
      const productResponse = await ProductsAPI.getProduct(productId);
      if (productResponse.success && productResponse.data) {
        const productData = productResponse.data;
        optimisticItem.product = productData;
        optimisticItem.variant = productData.variants?.find((v: any) => v.id === variantId) || 
                               productData.variants?.[0] || null;
      }
    } catch (error) {
      console.warn('Failed to fetch product data for optimistic update:', error);
      // Continue without product data - fallback will show placeholder
    }

    const previousWishlist = currentDefaultWishlist;
    setDefaultWishlist(prev => prev ? {
      ...prev,
      items: [...prev.items, optimisticItem],
    } : undefined);

    try {
      const response = await WishlistAPI.addItemToWishlist(userId, currentDefaultWishlist.id, {
        product_id: productId,
        variant_id: variantId,
        quantity,
      });

      if (response.success) {
        toast.success('Item added to wishlist!');
        // Don't fetch immediately - let optimistic update handle UI
        // Background refresh will happen naturally on next page load or user action
        return true;
      } else {
        // Revert optimistic update on error and fetch fresh data
        setDefaultWishlist(previousWishlist);
        fetchWishlists();
        console.error('Failed to add item to wishlist:', response.message);
        toast.error(response.message || 'Failed to add item to wishlist.');
        return false;
      }
    } catch (error) {
      // Revert optimistic update on error and fetch fresh data
      setDefaultWishlist(previousWishlist);
      fetchWishlists();
      console.error('Failed to add item to wishlist:', error);
      toast.error('Failed to add item to wishlist.');
      return false;
    }
  };

  const removeItem = async (wishlistId: string, itemId: string): Promise<boolean> => {
    if (!isAuthenticated || !user || !(user as any).id) {
      toast.error('Please log in to remove items from wishlist.');
      return false;
    }

    // Check if this is a temporary item (from optimistic update)
    if (itemId.startsWith('temp-')) {
      console.log('Removing temporary item from optimistic update');
      // For temporary items, just remove them from the optimistic state
      // No need to call the API since they don't exist on the backend yet
      setDefaultWishlist(prev => prev ? {
        ...prev,
        items: prev.items.filter(item => item.id !== itemId),
      } : undefined);
      toast.success('Item removed from wishlist!');
      return true;
    }

    const userId = (user as any).id;

    // Optimistic update: remove item from UI immediately
    const previousWishlist = defaultWishlist;
    setDefaultWishlist(prev => prev ? {
      ...prev,
      items: prev.items.filter(item => item.id !== itemId),
    } : undefined);

    try {
      const response = await WishlistAPI.removeItemFromWishlist(userId, wishlistId, itemId);
      if (response.success) {
        toast.success('Item removed from wishlist!');
        // Don't fetch immediately - let optimistic update handle UI
        // Background refresh will happen naturally on next page load or user action
        return true;
      } else {
        // Revert optimistic update on error and fetch fresh data
        setDefaultWishlist(previousWishlist);
        fetchWishlists();
        console.error('Failed to remove item from wishlist:', response.message);
        toast.error(response.message || 'Failed to remove item from wishlist.');
        return false;
      }
    } catch (error) {
      // Revert optimistic update on error and fetch fresh data
      setDefaultWishlist(previousWishlist);
      fetchWishlists();
      console.error('Failed to remove item from wishlist:', error);
      toast.error('Failed to remove item from wishlist.');
      return false;
    }
  };

  const isInWishlist = (productId: string, variantId?: string): boolean => {
    if (!defaultWishlist || !defaultWishlist.items) return false;
    return defaultWishlist.items.some(
      item => item.product_id === productId && (!variantId || item.variant_id === variantId)
    );
  };

  const clearWishlist = async (): Promise<boolean> => {
    if (!isAuthenticated || !user || !(user as any).id || !defaultWishlist) {
      toast.error('Please log in to clear wishlist.');
      return false;
    }

    const userId = (user as any).id;

    // Optimistic update: clear items immediately
    const previousWishlist = defaultWishlist;
    setDefaultWishlist(prev => prev ? { ...prev, items: [] } : undefined);

    try {
      // Filter out temporary items (optimistic updates) before sending to API
      const realItemIds = defaultWishlist.items
        .filter(item => !item.id.startsWith('temp-'))
        .map(item => item.id);
      
      if (realItemIds.length === 0) {
        // Only temporary items exist, just clear optimistically
        toast.success('Wishlist cleared!');
        return true;
      }
      
      const response = await WishlistAPI.clearWishlist(userId, defaultWishlist.id, realItemIds);
      if (response.success) {
        toast.success('Wishlist cleared!');
        // Don't fetch immediately - let optimistic update handle UI
        return true;
      } else {
        // Revert optimistic update on error and fetch fresh data
        setDefaultWishlist(previousWishlist);
        fetchWishlists();
        console.error('Failed to clear wishlist:', response.message);
        toast.error(response.message || 'Failed to clear wishlist.');
        return false;
      }
    } catch (error) {
      // Revert optimistic update on error and fetch fresh data
      setDefaultWishlist(previousWishlist);
      fetchWishlists();
      console.error('Failed to clear wishlist:', error);
      toast.error('Failed to clear wishlist.');
      return false;
    }
  };

  return (
    <WishlistContext.Provider
      value={{
        wishlists,
        defaultWishlist,
        loading,
        error,
        fetchWishlists,
        addItem,
        removeItem,
        isInWishlist,
        clearWishlist,
      }}
    >
      {children}
    </WishlistContext.Provider>
  );
};
export const useWishlist = () => {
  const context = useContext(WishlistContext);
  if (context === undefined) {
    throw new Error('useWishlist error: must be used within a WishlistProvider');
  }
  return context;
};