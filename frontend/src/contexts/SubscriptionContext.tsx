import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import SubscriptionAPI from '../apis/subscription';
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
  cancelSubscription: (subscriptionId: string) => Promise<boolean>;
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

  const refreshSubscriptions = async () => {
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
  };

  const createSubscription = async (data: any): Promise<Subscription | null> => {
    if (!isAuthenticated) {
      toast.error('Please log in to create a subscription');
      return null;
    }

    try {
      const response = await SubscriptionAPI.createSubscription(data);
      const newSubscription = response.data;
      setSubscriptions(prev => [...prev, newSubscription]);
      toast.success('Subscription created successfully!');
      return newSubscription;
    } catch (error) {
      console.error('Failed to create subscription:', error);
      toast.error('Failed to create subscription');
      return null;
    }
  };

  const updateSubscription = async (subscriptionId: string, data: any): Promise<Subscription | null> => {
    if (!isAuthenticated) {
      toast.error('Please log in to update subscription');
      return null;
    }

    try {
      const response = await SubscriptionAPI.updateSubscription(subscriptionId, data);
      const updatedSubscription = response.data;
      setSubscriptions(prev => 
        prev.map(sub => sub.id === subscriptionId ? updatedSubscription : sub)
      );
      toast.success('Subscription updated successfully!');
      return updatedSubscription;
    } catch (error) {
      console.error('Failed to update subscription:', error);
      toast.error('Failed to update subscription');
      return null;
    }
  };

  const cancelSubscription = async (subscriptionId: string): Promise<boolean> => {
    if (!isAuthenticated) {
      toast.error('Please log in to cancel subscription');
      return false;
    }

    try {
      await SubscriptionAPI.deleteSubscription(subscriptionId);
      setSubscriptions(prev => prev.filter(sub => sub.id !== subscriptionId));
      toast.success('Subscription cancelled successfully');
      return true;
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
      toast.error('Failed to cancel subscription');
      return false;
    }
  };

  const addProductsToSubscription = async (subscriptionId: string, variantIds: string[]): Promise<boolean> => {
    if (!isAuthenticated) {
      toast.error('Please log in to modify subscription');
      return false;
    }

    try {
      const response = await SubscriptionAPI.addProductsToSubscription(subscriptionId, variantIds);
      const updatedSubscription = response.data;
      setSubscriptions(prev => 
        prev.map(sub => sub.id === subscriptionId ? updatedSubscription : sub)
      );
      toast.success(`Added ${variantIds.length} product(s) to subscription!`);
      return true;
    } catch (error) {
      console.error('Failed to add products to subscription:', error);
      toast.error('Failed to add products to subscription');
      return false;
    }
  };

  const removeProductsFromSubscription = async (subscriptionId: string, variantIds: string[]): Promise<boolean> => {
    if (!isAuthenticated) {
      toast.error('Please log in to modify subscription');
      return false;
    }

    try {
      const response = await SubscriptionAPI.removeProductsFromSubscription(subscriptionId, variantIds);
      const updatedSubscription = response.data;
      setSubscriptions(prev => 
        prev.map(sub => sub.id === subscriptionId ? updatedSubscription : sub)
      );
      toast.success(`Removed ${variantIds.length} product(s) from subscription!`);
      return true;
    } catch (error) {
      console.error('Failed to remove products from subscription:', error);
      toast.error('Failed to remove products from subscription');
      return false;
    }
  };

  const value: SubscriptionContextType = {
    subscriptions,
    activeSubscription,
    loading,
    error,
    refreshSubscriptions,
    createSubscription,
    updateSubscription,
    cancelSubscription,
    addProductsToSubscription,
    removeProductsFromSubscription,
  };

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
};