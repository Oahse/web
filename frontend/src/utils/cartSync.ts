/**
 * Cart synchronization utilities
 * Helps detect and handle cart state inconsistencies
 */

import { toast } from 'react-hot-toast';

export interface CartSyncError {
  type: 'item_not_found' | 'cart_expired' | 'sync_error';
  message: string;
  itemId?: string;
  shouldRefresh: boolean;
}

/**
 * Analyzes cart-related errors and determines the appropriate response
 */
export const analyzeCartError = (error: any): CartSyncError => {
  const status = error?.status || error?.statusCode || error?.response?.status;
  const message = error?.message || error?.response?.data?.message || 'Unknown error';

  // 404 errors typically mean the cart item no longer exists
  if (status === 404) {
    if (message.includes('Cart item not found')) {
      return {
        type: 'item_not_found',
        message: 'This item is no longer in your cart. Your cart has been updated.',
        shouldRefresh: true
      };
    }
    
    if (message.includes('Cart not found') || message.includes('expired')) {
      return {
        type: 'cart_expired',
        message: 'Your cart has expired. Please add items again.',
        shouldRefresh: true
      };
    }
  }

  // Generic sync error
  return {
    type: 'sync_error',
    message: 'Cart synchronization issue. Refreshing cart...',
    shouldRefresh: true
  };
};

/**
 * Handles cart synchronization errors with appropriate user feedback
 */
export const handleCartSyncError = (error: any, refreshCart: () => Promise<void>) => {
  const syncError = analyzeCartError(error);
  
  // Show user-friendly message
  toast.error(syncError.message);
  
  // Refresh cart if needed
  if (syncError.shouldRefresh) {
    refreshCart().catch(refreshError => {
      console.error('Failed to refresh cart after sync error:', refreshError);
      toast.error('Unable to refresh cart. Please reload the page.');
    });
  }
  
  return syncError;
};

/**
 * Validates that a cart item exists before performing operations
 */
export const validateCartItem = (cart: any, itemId: string): boolean => {
  if (!cart?.items || !Array.isArray(cart.items)) {
    return false;
  }
  
  return cart.items.some((item: any) => item.id === itemId);
};

/**
 * Detects potential cart synchronization issues
 */
export const detectSyncIssues = (cart: any): string[] => {
  const issues: string[] = [];
  
  if (!cart) {
    issues.push('Cart data is missing');
    return issues;
  }
  
  if (!cart.items || !Array.isArray(cart.items)) {
    issues.push('Cart items array is invalid');
  }
  
  if (cart.items) {
    // Check for items with missing required fields
    cart.items.forEach((item: any, index: number) => {
      if (!item.id) {
        issues.push(`Item ${index + 1} is missing ID`);
      }
      
      if (!item.variant_id) {
        issues.push(`Item ${index + 1} is missing variant ID`);
      }
      
      if (typeof item.quantity !== 'number' || item.quantity <= 0) {
        issues.push(`Item ${index + 1} has invalid quantity`);
      }
      
      if (typeof item.price_per_unit !== 'number' || item.price_per_unit < 0) {
        issues.push(`Item ${index + 1} has invalid price`);
      }
    });
  }
  
  return issues;
};