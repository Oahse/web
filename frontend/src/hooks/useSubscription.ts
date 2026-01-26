import { useAuth } from '../contexts/AuthContext';
import { useSubscription } from '../contexts/SubscriptionContext';
import { toast } from 'react-hot-toast';

export const useSubscriptionAction = () => {
  const { isAuthenticated, setIntendedDestination } = useAuth();
  const { subscriptions, addProductsToSubscription } = useSubscription();

  const executeWithSubscription = async (
    action: () => Promise<void>,
    options: {
      requireAuth?: boolean;
      requireActiveSubscription?: boolean;
      redirectPath?: string;
      actionName?: string;
    } = {}
  ) => {
    const {
      requireAuth = true,
      requireActiveSubscription = false,
      redirectPath = '/login',
      actionName = 'perform this action'
    } = options;

    // Check authentication
    if (requireAuth && !isAuthenticated) {
      setIntendedDestination({
        path: window.location.pathname,
        action: actionName
      });
      toast.error('Please log in to add products to subscriptions');
      window.location.href = redirectPath;
      return;
    }

    // Check for active subscriptions
    if (requireActiveSubscription) {
      const activeSubscriptions = subscriptions.filter(sub => sub.status === 'active');
      if (activeSubscriptions.length === 0) {
        toast.error('You need an active subscription to add products');
        return;
      }
    }

    try {
      await action();
    } catch (error) {
      console.error(`Failed to ${actionName}:`, error);
      toast.error(`Failed to ${actionName}`);
    }
  };

  const addToSubscription = async (subscriptionId: string, variantIds: string[], quantity: number = 1) => {
    await executeWithSubscription(
      async () => {
        // For now, we'll add the variant once per quantity
        // In a more sophisticated system, you might want to track quantities separately
        const variantIdsWithQuantity = Array(quantity).fill(variantIds).flat();
        await addProductsToSubscription(subscriptionId, variantIdsWithQuantity);
        toast.success(`Added ${quantity} item(s) to subscription!`);
      },
      {
        requireAuth: true,
        requireActiveSubscription: true,
        actionName: 'add product to subscription'
      }
    );
  };

  const getActiveSubscriptions = () => {
    return subscriptions.filter(sub => sub.status === 'active');
  };

  return {
    executeWithSubscription,
    addToSubscription,
    getActiveSubscriptions,
    hasActiveSubscriptions: getActiveSubscriptions().length > 0,
    isAuthenticated
  };
};