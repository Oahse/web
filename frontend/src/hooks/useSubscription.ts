import { useAuth } from '../store/AuthContext';
import { useSubscription as useSubscriptionContext } from '../store/SubscriptionContext';
import { toast } from 'react-hot-toast';

export const useSubscription = () => {
  const context = useSubscriptionContext();
  return context;
};

export const useSubscriptionAction = () => {
  const { isAuthenticated, setIntendedDestination } = useAuth();
  const { subscriptions, addProductsToSubscription } = useSubscriptionContext();

  const addToSubscription = async (subscriptionId: string, variantIds: string[], quantity: number = 1) => {
    if (!isAuthenticated) {
      setIntendedDestination({
        path: window.location.pathname,
        action: 'add product to subscription'
      });
      toast.error('Please log in to add products to subscriptions');
      window.location.href = '/login';
      return;
    }

    const activeSubscriptions = subscriptions.filter(sub => sub.status === 'active');
    if (activeSubscriptions.length === 0) {
      toast.error('You need an active subscription to add products');
      return;
    }

    try {
      const variantIdsWithQuantity = Array(quantity).fill(variantIds).flat();
      await addProductsToSubscription(subscriptionId, variantIdsWithQuantity);
      toast.success(`Added ${quantity} item(s) to subscription!`);
    } catch (error) {
      console.error('Failed to add product to subscription:', error);
      toast.error('Failed to add product to subscription');
    }
  };

  const getActiveSubscriptions = () => {
    return subscriptions.filter(sub => sub.status === 'active');
  };

  return {
    addToSubscription,
    getActiveSubscriptions,
    hasActiveSubscriptions: getActiveSubscriptions().length > 0,
    isAuthenticated
  };
};