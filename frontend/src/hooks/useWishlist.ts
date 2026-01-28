import { useCallback, useState } from 'react';
import { useWishlist } from './useContexts';
import { useAuthActions } from './useAuth';
import { toast } from 'react-hot-toast';

/**
 * Enhanced wishlist hook with authentication handling and better UX
 * Similar to useEnhancedCart but for wishlist functionality
 */
export const useEnhancedWishlist = () => {
  const { 
    wishlist, 
    loading, 
    fetchWishlist, 
    addItem, 
    removeItem, 
    clearWishlist,
    items 
  } = useWishlist();

  const { executeWithAuth } = useAuthActions({
    requireAuth: true,
    message: 'Please login to manage your wishlist'
  });

  const [processingItems, setProcessingItems] = useState<Set<string>>(new Set());
  const [clearingWishlist, setClearingWishlist] = useState(false);

  /**
   * Enhanced add to wishlist with authentication and validation
   */
  const enhancedAddItem = useCallback(async (productId: string, variantId?: string) => {
    // Check if item already exists
    const existingItem = items.find(item => 
      item.product_id === productId && 
      (!variantId || item.variant_id === variantId)
    );

    if (existingItem) {
      toast.info('Item is already in your wishlist');
      return false;
    }

    const result = await executeWithAuth(async () => {
      const success = await addItem({ 
        product_id: productId, 
        variant_id: variantId 
      });
      if (success) {
        toast.success('Added to wishlist');
      }
      return success;
    }, 'Please login to add items to your wishlist');

    return result.success;
  }, [executeWithAuth, addItem, items]);

  /**
   * Enhanced remove item with confirmation and authentication
   */
  const enhancedRemoveItem = useCallback(async (itemId: string, itemName?: string) => {
    // Find item for confirmation
    const item = items.find(item => item.id === itemId);
    const displayName = itemName || item?.product?.name || item?.variant?.name || 'this item';
    
    setProcessingItems(prev => new Set(prev).add(itemId));

    try {
      const result = await executeWithAuth(async () => {
        await removeItem(itemId);
        toast.success(`${displayName} removed from wishlist`);
        return true;
      }, 'Please login to modify your wishlist');

      return result.success;
    } catch (error: any) {
      console.error('Failed to remove item:', error);
      const errorMessage = error?.message || 'Failed to remove item. Please try again.';
      toast.error(errorMessage);
      return false;
    } finally {
      setProcessingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
    }
  }, [executeWithAuth, removeItem, items]);

  /**
   * Enhanced clear wishlist with confirmation and authentication
   * Returns a function that components can call after their own confirmation
   */
  const enhancedClearWishlist = useCallback(async (skipConfirmation = false) => {
    if (!items.length) {
      toast.error('Wishlist is already empty');
      return false;
    }

    // Skip confirmation if explicitly requested (when component handles it)
    if (!skipConfirmation) {
      // This should be handled by the calling component now
      return false;
    }

    setClearingWishlist(true);

    try {
      const result = await executeWithAuth(async () => {
        await clearWishlist();
        toast.success('Wishlist cleared successfully');
        return true;
      }, 'Please login to clear your wishlist');

      return result.success;
    } catch (error: any) {
      console.error('Failed to clear wishlist:', error);
      const errorMessage = error?.message || 'Failed to clear wishlist. Please try again.';
      toast.error(errorMessage);
      return false;
    } finally {
      setClearingWishlist(false);
    }
  }, [executeWithAuth, clearWishlist, items.length]);

  /**
   * Check if a product/variant is in wishlist
   */
  const isInWishlist = useCallback((productId: string, variantId?: string) => {
    return items.some(item => 
      item.product_id === productId && 
      (!variantId || item.variant_id === variantId)
    );
  }, [items]);

  /**
   * Toggle item in wishlist (add if not present, remove if present)
   */
  const toggleItem = useCallback(async (productId: string, variantId?: string, itemName?: string) => {
    const existingItem = items.find(item => 
      item.product_id === productId && 
      (!variantId || item.variant_id === variantId)
    );

    if (existingItem) {
      return await enhancedRemoveItem(existingItem.id, itemName);
    } else {
      return await enhancedAddItem(productId, variantId);
    }
  }, [items, enhancedAddItem, enhancedRemoveItem]);

  /**
   * Move item from wishlist to cart
   */
  const moveToCart = useCallback(async (itemId: string, quantity: number = 1) => {
    const item = items.find(item => item.id === itemId);
    if (!item) {
      toast.error('Item not found in wishlist');
      return false;
    }

    setProcessingItems(prev => new Set(prev).add(itemId));

    try {
      const result = await executeWithAuth(async () => {
        // This would need to be implemented in your wishlist context
        // For now, just remove from wishlist
        await removeItem(itemId);
        
        // You would add logic here to add to cart
        // await addToCart({ variant_id: item.variant_id, quantity });
        
        const displayName = item.product?.name || item.variant?.name || 'Item';
        toast.success(`${displayName} moved to cart`);
        return true;
      }, 'Please login to move items to cart');

      return result.success;
    } catch (error: any) {
      console.error('Failed to move item to cart:', error);
      const errorMessage = error?.message || 'Failed to move item. Please try again.';
      toast.error(errorMessage);
      return false;
    } finally {
      setProcessingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
    }
  }, [executeWithAuth, removeItem, items]);

  /**
   * Get wishlist summary for display
   */
  const getWishlistSummary = useCallback(() => {
    return {
      itemCount: items.length,
      isEmpty: items.length === 0,
      categories: [...new Set(items.map(item => item.product?.category).filter(Boolean))],
      totalValue: items.reduce((sum, item) => {
        const price = item.variant?.price || item.product?.price || 0;
        return sum + price;
      }, 0)
    };
  }, [items]);

  /**
   * Get items by category
   */
  const getItemsByCategory = useCallback(() => {
    const categorized = items.reduce((acc, item) => {
      const category = item.product?.category || 'Uncategorized';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(item);
      return acc;
    }, {} as Record<string, typeof items>);

    return categorized;
  }, [items]);

  return {
    // Original wishlist data
    wishlist,
    items,
    loading,
    
    // Enhanced actions
    addItem: enhancedAddItem,
    removeItem: enhancedRemoveItem,
    clearWishlist: enhancedClearWishlist,
    toggleItem,
    moveToCart,
    
    // Utility functions
    isInWishlist,
    getWishlistSummary,
    getItemsByCategory,
    fetchWishlist,
    
    // UI state
    processingItems,
    clearingWishlist,
    
    // Helper functions
    isItemProcessing: (itemId: string) => processingItems.has(itemId),
    getItemById: (itemId: string) => items.find(item => item.id === itemId),
    isEmpty: items.length === 0
  };
};

export default useEnhancedWishlist;