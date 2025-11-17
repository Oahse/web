import React, { useEffect, useState, createContext, useCallback, useContext } from 'react';
import { useAuth } from './AuthContext';
import { toast } from 'react-hot-toast';
import WishlistAPI from '../apis/wishlists';

export const WishlistContext = createContext(undefined);

export const WishlistProvider = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  const [wishlists, setWishlists] = useState([]);
  const [defaultWishlist, setDefaultWishlist] = useState(undefined);

  // ✅ Wrap fetchWishlists in useCallback to prevent infinite useEffect loops
  const fetchWishlists = useCallback(async () => {
    if (!isAuthenticated || !user?.id) {
      setWishlists([]);
      setDefaultWishlist(undefined);
      return;
    }

    try {
      console.log('WishlistContext: Fetching wishlists with WishlistAPI.getWishlists');
      const response = await WishlistAPI.getWishlists(user.id);
      if (response.success) {
        setWishlists(response.data);
        setDefaultWishlist(response.data.find(wl => wl.is_default) || response.data[0]);
      } else {
        console.error('Failed to fetch wishlists:', response.message);
        toast.error(response.message || 'Failed to load wishlists.');
      }
    } catch (error) {
      console.error('Failed to fetch wishlists:', error);
      toast.error('Failed to load wishlists.');
    }
  }, [isAuthenticated, user]);

  // ✅ Run fetch on mount or when auth changes
  useEffect(() => {
    fetchWishlists();
  }, [fetchWishlists]);

  const addItem = async (productId, variantId, quantity = 1) => {
    if (!isAuthenticated || !user?.id) {
      toast.error('Please log in to add items to wishlist.');
      return false;
    }

    let currentDefaultWishlist = defaultWishlist;

    // If no wishlist exists, create one
    if (!currentDefaultWishlist) {
      try {
        const response = await WishlistAPI.createWishlist(user.id, {
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

    try {
      const response = await WishlistAPI.addItemToWishlist(user.id, currentDefaultWishlist.id, {
        product_id: productId,
        variant_id: variantId,
        quantity,
      });

      if (response.success) {
        toast.success('Item added to wishlist!');
        fetchWishlists();
        return true;
      } else {
        console.error('Failed to add item to wishlist:', response.message);
        toast.error(response.message || 'Failed to add item to wishlist.');
        return false;
      }
    } catch (error) {
      console.error('Failed to add item to wishlist:', error);
      toast.error('Failed to add item to wishlist.');
      return false;
    }
  };

  const removeItem = async (wishlistId, itemId) => {
    if (!isAuthenticated || !user?.id) {
      toast.error('Please log in to remove items from wishlist.');
      return false;
    }

    try {
      const response = await WishlistAPI.removeItemFromWishlist(user.id, wishlistId, itemId);
      if (response.success) {
        toast.success('Item removed from wishlist!');
        fetchWishlists();
        return true;
      } else {
        console.error('Failed to remove item from wishlist:', response.message);
        toast.error(response.message || 'Failed to remove item from wishlist.');
        return false;
      }
    } catch (error) {
      console.error('Failed to remove item from wishlist:', error);
      toast.error('Failed to remove item from wishlist.');
      return false;
    }
  };

  const isInWishlist = (productId, variantId) => {
    if (!defaultWishlist || !defaultWishlist.items) return false;
    return defaultWishlist.items.some(
      item => item.product_id === productId && (!variantId || item.variant_id === variantId)
    );
  };

  const clearWishlist = async () => {
    if (!isAuthenticated || !user?.id || !defaultWishlist) {
      toast.error('Please log in to clear wishlist.');
      return false;
    }

    try {
      const itemIds = defaultWishlist.items.map(item => item.id);
      const response = await WishlistAPI.clearWishlist(user.id, defaultWishlist.id, itemIds);
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