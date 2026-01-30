import React, { useEffect, useState, createContext, useCallback, useContext, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { toast } from 'react-hot-toast';
import WishlistAPI from '../api/wishlists';
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
        setWishlists(response.data);
        setDefaultWishlist(response.data.find((wl: Wishlist) => wl.is_default) || response.data[0]);
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

    // Optimistic update: add item to UI immediately
    const optimisticItem: any = {
      id: `temp-${Date.now()}`,
      product_id: productId,
      variant_id: variantId,
      quantity,
      wishlist_id: currentDefaultWishlist.id,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

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
        // Fetch fresh data to get the real item with all details
        await fetchWishlists();
        return true;
      } else {
        // Revert optimistic update on error
        setDefaultWishlist(previousWishlist);
        console.error('Failed to add item to wishlist:', response.message);
        toast.error(response.message || 'Failed to add item to wishlist.');
        return false;
      }
    } catch (error) {
      // Revert optimistic update on error
      setDefaultWishlist(previousWishlist);
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
      console.warn('Cannot remove temporary item, waiting for real data...');
      // Refresh data to get real item IDs
      await fetchWishlists();
      return false;
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
        // Fetch fresh data to ensure consistency
        fetchWishlists();
        return true;
      } else {
        // Revert optimistic update on error
        setDefaultWishlist(previousWishlist);
        console.error('Failed to remove item from wishlist:', response.message);
        toast.error(response.message || 'Failed to remove item from wishlist.');
        return false;
      }
    } catch (error) {
      // Revert optimistic update on error
      setDefaultWishlist(previousWishlist);
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

    try {
      const itemIds = defaultWishlist.items.map(item => item.id);
      const response = await WishlistAPI.clearWishlist(userId, defaultWishlist.id, itemIds);
      if (response.success) {
        toast.success('Wishlist cleared!');
        fetchWishlists();
        return true;
      } else {
        console.error('Failed to clear wishlist:', response.message);
        toast.error(response.message || 'Failed to clear wishlist.');
        return false;
      }
    } catch (error) {
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