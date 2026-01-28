import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';
import * as SubscriptionAPI from '../apis/subscription';
import { toast } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

// Enhanced subscription interface with product management support
interface Subscription {
  id: string;
  plan_id: string;
  status: string;
  price: number;
  currency: string;
  billing_cycle: string;
  auto_renew: boolean;
  current_period_start: string;
  current_period_end: string;
  next_billing_date: string;
  products: SubscriptionProduct[];
  discounts?: AppliedDiscount[];
  subtotal?: number;
  total?: number;
  tax_amount?: number;
  shipping_cost?: number;
  created_at: string;
  updated_at: string;
}

// Subscription product interface
interface SubscriptionProduct {
  id: string;
  subscription_id: string;
  product_id: string;
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  image?: string;
  added_at: string;
}

// Applied discount interface
interface AppliedDiscount {
  id: string;
  subscription_id: string;
  discount_id: string;
  discount_code: string;
  discount_type: 'PERCENTAGE' | 'FIXED_AMOUNT' | 'FREE_SHIPPING';
  discount_amount: number;
  applied_at: string;
}

// Optimistic update state for tracking pending operations
interface OptimisticState {
  removingProducts: Set<string>; // Product IDs being removed
  applyingDiscounts: Set<string>; // Discount codes being applied
  removingDiscounts: Set<string>; // Discount IDs being removed
}

// Transaction state for rollback capability
interface TransactionState {
  subscriptionSnapshots: Map<string, Subscription>; // Subscription ID -> snapshot
  operationId: string | null;
}

interface SubscriptionContextType {
  subscriptions: Subscription[];
  activeSubscription: Subscription | null;
  loading: boolean;
  error: string | null;
  optimisticState: OptimisticState;
  refreshSubscriptions: () => Promise<void>;
  createSubscription: (data: any) => Promise<Subscription | null>;
  updateSubscription: (subscriptionId: string, data: any) => Promise<Subscription | null>;
  cancelSubscription: (subscriptionId: string, reason?: string) => Promise<boolean>;
  activateSubscription: (subscriptionId: string) => Promise<boolean>;
  pauseSubscription: (subscriptionId: string, reason?: string) => Promise<boolean>;
  resumeSubscription: (subscriptionId: string) => Promise<boolean>;
  addProductsToSubscription: (subscriptionId: string, variantIds: string[]) => Promise<boolean>;
  removeProductsFromSubscription: (subscriptionId: string, variantIds: string[]) => Promise<boolean>;
  // Enhanced product management methods
  removeProduct: (subscriptionId: string, productId: string) => Promise<boolean>;
  getSubscriptionDetails: (subscriptionId: string) => Promise<SubscriptionAPI.SubscriptionDetailsResponse | null>;
  // Discount management methods
  applyDiscount: (subscriptionId: string, discountCode: string) => Promise<boolean>;
  removeDiscount: (subscriptionId: string, discountId: string) => Promise<boolean>;
  // Transaction management
  startTransaction: (subscriptionId: string) => string;
  commitTransaction: (operationId: string) => void;
  rollbackTransaction: (operationId: string) => void;
}

const SubscriptionContext = createContext<SubscriptionContextType | undefined>(undefined);

export const useSubscription = () => {
  const context = useContext(SubscriptionContext);
  if (context === undefined) {
    throw new Error('useSubscription must be used within a SubscriptionProvider');
  }
  return context;
};

interface SubscriptionProviderProps {
  children: React.ReactNode;
}

export const SubscriptionProvider: React.FC<SubscriptionProviderProps> = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  // Optimistic update state
  const [optimisticState, setOptimisticState] = useState<OptimisticState>({
    removingProducts: new Set(),
    applyingDiscounts: new Set(),
    removingDiscounts: new Set(),
  });

  // Transaction state for rollback capability
  const transactionState = useRef<TransactionState>({
    subscriptionSnapshots: new Map(),
    operationId: null,
  });

  // Get the active subscription (first active one)
  const activeSubscription = subscriptions.find(sub => sub.status === 'active') || null;

  useEffect(() => {
    if (isAuthenticated && user) {
      refreshSubscriptions();
    } else {
      setSubscriptions([]);
    }
  }, [isAuthenticated, user]);

  const refreshSubscriptions = useCallback(async () => {
    if (!isAuthenticated) {
      setSubscriptions([]);
      setError('Please log in to view subscriptions');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await SubscriptionAPI.getUserSubscriptions();
      console.log(response,'=response===')
      // Handle different response structures - response could be the data directly or nested
      const subscriptionsData = response?.subscriptions || response?.data?.subscriptions || [];
      setSubscriptions(subscriptionsData);
    } catch (error: any) {
      console.error('Failed to fetch subscriptions:', error);
      if (error.statusCode === 401) {
        setError('Please log in to view subscriptions');
      } else {
        setError('Failed to load subscriptions');
      }
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const createSubscription = useCallback(async (data: any): Promise<Subscription | null> => {
    if (!isAuthenticated) {
      toast.error('Please log in to create a subscription');
      return null;
    }

    try {
      const response = await SubscriptionAPI.createSubscription(data);
      // Handle different response structures - response could be the data directly or nested
      const newSubscription = response?.data || response;
      
      // Optimistically update the state
      setSubscriptions(prev => [...prev, newSubscription]);
      toast.success('Subscription created successfully!');
      return newSubscription;
    } catch (error) {
      console.error('Failed to create subscription:', error);
      toast.error('Failed to create subscription');
      return null;
    }
  }, [isAuthenticated]);

  const updateSubscription = useCallback(async (subscriptionId: string, data: any): Promise<Subscription | null> => {
    if (!isAuthenticated) {
      toast.error('Please log in to update subscription');
      return null;
    }

    try {
      const response = await SubscriptionAPI.updateSubscription(subscriptionId, data);
      // Handle different response structures - response could be the data directly or nested
      const updatedSubscription = response?.data || response;
      
      // Optimistically update the state
      setSubscriptions(prev => 
        prev.map(sub => sub.id === subscriptionId ? updatedSubscription : sub)
      );
      toast.success('Subscription updated successfully!');
      return updatedSubscription;
    } catch (error) {
      console.error('Failed to update subscription:', error);
      toast.error('Failed to update subscription');
      // Refresh to get the correct state
      refreshSubscriptions();
      return null;
    }
  }, [isAuthenticated, refreshSubscriptions]);

  const cancelSubscription = useCallback(async (subscriptionId: string, reason?: string): Promise<boolean> => {
    if (!isAuthenticated) {
      toast.error('Please log in to cancel subscription');
      return false;
    }

    try {
      await SubscriptionAPI.cancelSubscription(subscriptionId, reason);
      
      // Optimistically update the state
      setSubscriptions(prev => prev.filter(sub => sub.id !== subscriptionId));
      toast.success('Subscription cancelled successfully');
      return true;
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
      toast.error('Failed to cancel subscription');
      // Refresh to get the correct state
      refreshSubscriptions();
      return false;
    }
  }, [isAuthenticated, refreshSubscriptions]);

  const activateSubscription = useCallback(async (subscriptionId: string): Promise<boolean> => {
    if (!isAuthenticated) {
      toast.error('Please log in to activate subscription');
      return false;
    }

    try {
      await SubscriptionAPI.activateSubscription(subscriptionId);
      
      // Optimistically update the state
      setSubscriptions(prev => 
        prev.map(sub => sub.id === subscriptionId ? { ...sub, status: 'active' } : sub)
      );
      toast.success('Subscription activated successfully');
      return true;
    } catch (error) {
      console.error('Failed to activate subscription:', error);
      toast.error('Failed to activate subscription');
      // Refresh to get the correct state
      refreshSubscriptions();
      return false;
    }
  }, [isAuthenticated, refreshSubscriptions]);

  const pauseSubscription = useCallback(async (subscriptionId: string, reason?: string): Promise<boolean> => {
    if (!isAuthenticated) {
      toast.error('Please log in to pause subscription');
      return false;
    }

    try {
      await SubscriptionAPI.pauseSubscription(subscriptionId, reason);
      
      // Optimistically update the state
      setSubscriptions(prev => 
        prev.map(sub => sub.id === subscriptionId ? { ...sub, status: 'paused' } : sub)
      );
      toast.success('Subscription paused successfully');
      return true;
    } catch (error) {
      console.error('Failed to pause subscription:', error);
      toast.error('Failed to pause subscription');
      // Refresh to get the correct state
      refreshSubscriptions();
      return false;
    }
  }, [isAuthenticated, refreshSubscriptions]);

  const resumeSubscription = useCallback(async (subscriptionId: string): Promise<boolean> => {
    if (!isAuthenticated) {
      toast.error('Please log in to resume subscription');
      return false;
    }

    try {
      await SubscriptionAPI.resumeSubscription(subscriptionId);
      
      // Optimistically update the state
      setSubscriptions(prev => 
        prev.map(sub => sub.id === subscriptionId ? { ...sub, status: 'active' } : sub)
      );
      toast.success('Subscription resumed successfully');
      return true;
    } catch (error) {
      console.error('Failed to resume subscription:', error);
      toast.error('Failed to resume subscription');
      // Refresh to get the correct state
      refreshSubscriptions();
      return false;
    }
  }, [isAuthenticated, refreshSubscriptions]);

  const addProductsToSubscription = useCallback(async (subscriptionId: string, variantIds: string[]): Promise<boolean> => {
    if (!isAuthenticated) {
      toast.error('Please log in to modify subscription');
      return false;
    }

    try {
      const response = await SubscriptionAPI.addProductsToSubscription(subscriptionId, variantIds);
      // Handle different response structures - response could be the data directly or nested
      const updatedSubscription = response?.data || response;
      
      // Optimistically update the state
      setSubscriptions(prev => 
        prev.map(sub => sub.id === subscriptionId ? updatedSubscription : sub)
      );
      toast.success(`Added ${variantIds.length} product(s) to subscription!`);
      return true;
    } catch (error) {
      console.error('Failed to add products to subscription:', error);
      toast.error('Failed to add products to subscription');
      // Refresh to get the correct state
      refreshSubscriptions();
      return false;
    }
  }, [isAuthenticated, refreshSubscriptions]);

  const removeProductsFromSubscription = useCallback(async (subscriptionId: string, variantIds: string[]): Promise<boolean> => {
    if (!isAuthenticated) {
      toast.error('Please log in to modify subscription');
      return false;
    }

    try {
      const response = await SubscriptionAPI.removeProductsFromSubscription(subscriptionId, variantIds);
      // Handle different response structures - response could be the data directly or nested
      const updatedSubscription = response?.data || response;
      
      // Optimistically update the state
      setSubscriptions(prev => 
        prev.map(sub => sub.id === subscriptionId ? updatedSubscription : sub)
      );
      toast.success(`Removed ${variantIds.length} product(s) from subscription!`);
      return true;
    } catch (error) {
      console.error('Failed to remove products from subscription:', error);
      toast.error('Failed to remove products from subscription');
      // Refresh to get the correct state
      refreshSubscriptions();
      return false;
    }
  }, [isAuthenticated, refreshSubscriptions]);

  // Transaction management methods
  const startTransaction = useCallback((subscriptionId: string): string => {
    const operationId = `${subscriptionId}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // Create snapshot of current subscription state
    const subscription = subscriptions.find(sub => sub.id === subscriptionId);
    if (subscription) {
      transactionState.current.subscriptionSnapshots.set(subscriptionId, { ...subscription });
      transactionState.current.operationId = operationId;
    }
    
    return operationId;
  }, [subscriptions]);

  const commitTransaction = useCallback((operationId: string) => {
    if (transactionState.current.operationId === operationId) {
      // Clear snapshots and reset transaction state
      transactionState.current.subscriptionSnapshots.clear();
      transactionState.current.operationId = null;
    }
  }, []);

  const rollbackTransaction = useCallback((operationId: string) => {
    if (transactionState.current.operationId === operationId) {
      // Restore subscription state from snapshots
      const snapshots = transactionState.current.subscriptionSnapshots;
      
      setSubscriptions(prev => 
        prev.map(sub => {
          const snapshot = snapshots.get(sub.id);
          return snapshot || sub;
        })
      );
      
      // Clear optimistic state
      setOptimisticState({
        removingProducts: new Set(),
        applyingDiscounts: new Set(),
        removingDiscounts: new Set(),
      });
      
      // Clear transaction state
      transactionState.current.subscriptionSnapshots.clear();
      transactionState.current.operationId = null;
    }
  }, []);

  // Enhanced product removal with optimistic updates
  const removeProduct = useCallback(async (subscriptionId: string, productId: string): Promise<boolean> => {
    if (!isAuthenticated) {
      toast.error('Please log in to modify subscription');
      return false;
    }

    // Start transaction
    const operationId = startTransaction(subscriptionId);

    try {
      // Optimistic update - mark product as being removed
      setOptimisticState(prev => ({
        ...prev,
        removingProducts: new Set([...prev.removingProducts, productId])
      }));

      // Optimistically remove product from UI
      setSubscriptions(prev => 
        prev.map(sub => {
          if (sub.id === subscriptionId) {
            const updatedProducts = sub.products.filter(p => p.id !== productId);
            // Recalculate totals optimistically (simplified calculation)
            const subtotal = updatedProducts.reduce((sum, p) => sum + p.total_price, 0);
            return {
              ...sub,
              products: updatedProducts,
              subtotal,
              total: subtotal + (sub.tax_amount || 0) + (sub.shipping_cost || 0) - (sub.discounts?.reduce((sum, d) => sum + d.discount_amount, 0) || 0)
            };
          }
          return sub;
        })
      );

      // Make API call
      const updatedSubscription = await SubscriptionAPI.removeProduct(subscriptionId, productId);
      
      // Update with server response
      setSubscriptions(prev => 
        prev.map(sub => sub.id === subscriptionId ? updatedSubscription : sub)
      );

      // Commit transaction
      commitTransaction(operationId);
      
      toast.success('Product removed from subscription');
      return true;
    } catch (error) {
      console.error('Failed to remove product from subscription:', error);
      toast.error('Failed to remove product from subscription');
      
      // Rollback transaction
      rollbackTransaction(operationId);
      return false;
    } finally {
      // Clear optimistic state
      setOptimisticState(prev => ({
        ...prev,
        removingProducts: new Set([...prev.removingProducts].filter(id => id !== productId))
      }));
    }
  }, [isAuthenticated, startTransaction, commitTransaction, rollbackTransaction]);

  // Get subscription details for modal
  const getSubscriptionDetails = useCallback(async (subscriptionId: string): Promise<SubscriptionAPI.SubscriptionDetailsResponse | null> => {
    if (!isAuthenticated) {
      toast.error('Please log in to view subscription details');
      return null;
    }

    try {
      const details = await SubscriptionAPI.getSubscriptionDetails(subscriptionId);
      return details;
    } catch (error) {
      console.error('Failed to fetch subscription details:', error);
      toast.error('Failed to load subscription details');
      return null;
    }
  }, [isAuthenticated]);

  // Apply discount with optimistic updates
  const applyDiscount = useCallback(async (subscriptionId: string, discountCode: string): Promise<boolean> => {
    if (!isAuthenticated) {
      toast.error('Please log in to apply discount');
      return false;
    }

    // Start transaction
    const operationId = startTransaction(subscriptionId);

    try {
      // Optimistic update - mark discount as being applied
      setOptimisticState(prev => ({
        ...prev,
        applyingDiscounts: new Set([...prev.applyingDiscounts, discountCode])
      }));

      // Make API call
      const response = await SubscriptionAPI.applyDiscount(subscriptionId, discountCode);
      
      // Update with server response
      setSubscriptions(prev => 
        prev.map(sub => sub.id === subscriptionId ? response.updated_subscription : sub)
      );

      // Commit transaction
      commitTransaction(operationId);
      
      toast.success(`Discount "${discountCode}" applied successfully`);
      return true;
    } catch (error: any) {
      console.error('Failed to apply discount:', error);
      const errorMessage = error.message || 'Failed to apply discount';
      toast.error(errorMessage);
      
      // Rollback transaction
      rollbackTransaction(operationId);
      return false;
    } finally {
      // Clear optimistic state
      setOptimisticState(prev => ({
        ...prev,
        applyingDiscounts: new Set([...prev.applyingDiscounts].filter(code => code !== discountCode))
      }));
    }
  }, [isAuthenticated, startTransaction, commitTransaction, rollbackTransaction]);

  // Remove discount with optimistic updates
  const removeDiscount = useCallback(async (subscriptionId: string, discountId: string): Promise<boolean> => {
    if (!isAuthenticated) {
      toast.error('Please log in to remove discount');
      return false;
    }

    // Start transaction
    const operationId = startTransaction(subscriptionId);

    try {
      // Optimistic update - mark discount as being removed
      setOptimisticState(prev => ({
        ...prev,
        removingDiscounts: new Set([...prev.removingDiscounts, discountId])
      }));

      // Optimistically remove discount from UI
      setSubscriptions(prev => 
        prev.map(sub => {
          if (sub.id === subscriptionId) {
            const updatedDiscounts = sub.discounts?.filter(d => d.id !== discountId) || [];
            const discountAmount = sub.discounts?.find(d => d.id === discountId)?.discount_amount || 0;
            return {
              ...sub,
              discounts: updatedDiscounts,
              total: (sub.total || 0) + discountAmount // Add back the discount amount
            };
          }
          return sub;
        })
      );

      // Make API call
      const updatedSubscription = await SubscriptionAPI.removeDiscount(subscriptionId, discountId);
      
      // Update with server response
      setSubscriptions(prev => 
        prev.map(sub => sub.id === subscriptionId ? updatedSubscription : sub)
      );

      // Commit transaction
      commitTransaction(operationId);
      
      toast.success('Discount removed from subscription');
      return true;
    } catch (error) {
      console.error('Failed to remove discount:', error);
      toast.error('Failed to remove discount');
      
      // Rollback transaction
      rollbackTransaction(operationId);
      return false;
    } finally {
      // Clear optimistic state
      setOptimisticState(prev => ({
        ...prev,
        removingDiscounts: new Set([...prev.removingDiscounts].filter(id => id !== discountId))
      }));
    }
  }, [isAuthenticated, startTransaction, commitTransaction, rollbackTransaction]);

  const value: SubscriptionContextType = {
    subscriptions,
    activeSubscription,
    loading,
    error,
    optimisticState,
    refreshSubscriptions,
    createSubscription,
    updateSubscription,
    cancelSubscription,
    activateSubscription,
    pauseSubscription,
    resumeSubscription,
    addProductsToSubscription,
    removeProductsFromSubscription,
    // Enhanced product management methods
    removeProduct,
    getSubscriptionDetails,
    // Discount management methods
    applyDiscount,
    removeDiscount,
    // Transaction management
    startTransaction,
    commitTransaction,
    rollbackTransaction,
  };

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
};