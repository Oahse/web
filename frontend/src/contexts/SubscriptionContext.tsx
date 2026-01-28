import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import * as SubscriptionAPI from '../apis/subscription';
import { toast } from 'react-hot-toast';

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
  products: any[];
  created_at: string;
  updated_at: string;
}

interface SubscriptionContextType {
  subscriptions: Subscription[];
  activeSubscription: Subscription | null;
  loading: boolean;
  error: string | null;
  refreshSubscriptions: () => Promise<void>;
  createSubscription: (data: any) => Promise<Subscription | null>;
  updateSubscription: (subscriptionId: string, data: any) => Promise<Subscription | null>;
  cancelSubscription: (subscriptionId: string, reason?: string) => Promise<boolean>;
  activateSubscription: (subscriptionId: string) => Promise<boolean>;
  pauseSubscription: (subscriptionId: string, reason?: string) => Promise<boolean>;
  resumeSubscription: (subscriptionId: string) => Promise<boolean>;
  addProductsToSubscription: (subscriptionId: string, variantIds: string[]) => Promise<boolean>;
  removeProductsFromSubscription: (subscriptionId: string, variantIds: string[]) => Promise<boolean>;
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
    if (!isAuthenticated) return;

    setLoading(true);
    setError(null);
    try {
      const response = await SubscriptionAPI.getUserSubscriptions();
      setSubscriptions(response.data?.subscriptions || []);
    } catch (error) {
      console.error('Failed to fetch subscriptions:', error);
      setError('Failed to load subscriptions');
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
      const newSubscription = response.data.data; // Extract from nested structure
      
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
      const updatedSubscription = response.data.data; // Extract from nested structure
      
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
      const updatedSubscription = response.data.data; // Extract from nested structure
      
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
      const updatedSubscription = response.data.data; // Extract from nested structure
      
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

  const value: SubscriptionContextType = {
    subscriptions,
    activeSubscription,
    loading,
    error,
    refreshSubscriptions,
    createSubscription,
    updateSubscription,
    cancelSubscription,
    activateSubscription,
    pauseSubscription,
    resumeSubscription,
    addProductsToSubscription,
    removeProductsFromSubscription,
  };

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
};