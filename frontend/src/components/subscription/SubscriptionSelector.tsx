import React, { useState } from 'react';
import { XIcon, CalendarIcon, CreditCardIcon, PlusIcon } from 'lucide-react';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { useSubscriptionAction } from '../../hooks/useSubscription';
import { formatCurrency } from '../../lib/locale-config';
import { themeClasses, getButtonClasses } from '../../lib/themeClasses';

interface SubscriptionSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  productName: string;
  variantId: string;
  quantity?: number;
  onSuccess?: () => void;
}

export const SubscriptionSelector: React.FC<SubscriptionSelectorProps> = ({
  isOpen,
  onClose,
  productName,
  variantId,
  quantity = 1,
  onSuccess
}) => {
  const { subscriptions } = useSubscription();
  const { addToSubscription } = useSubscriptionAction();
  const [selectedSubscriptionId, setSelectedSubscriptionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const activeSubscriptions = subscriptions.filter(sub => sub.status === 'active');

  const handleAddToSubscription = async () => {
    if (!selectedSubscriptionId) {
      return;
    }

    setIsLoading(true);
    try {
      // The API expects an array of variant IDs
      await addToSubscription(selectedSubscriptionId, [variantId], quantity);
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Failed to add to subscription:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatBillingCycle = (cycle: string) => {
    return cycle.charAt(0).toUpperCase() + cycle.slice(1);
  };

  const formatNextBilling = (date: string) => {
    return new Date(date).toLocaleDateString();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
      <div className={`${themeClasses.surface} rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-6 border-b border-border-light">
          <h2 className={`text-lg sm:text-xl font-semibold ${themeClasses.text}`}>
            Add to Subscription
          </h2>
          <button
            onClick={onClose}
            className={`p-2 rounded-lg ${themeClasses.textMuted} hover:${themeClasses.surface} transition-colors`}
          >
            <XIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 sm:p-6">
          <div className="mb-4 sm:mb-6">
            <p className={`${themeClasses.textMuted} mb-2 text-sm sm:text-base`}>Product:</p>
            <p className={`font-medium ${themeClasses.text} text-sm sm:text-base`}>{productName}</p>
            {quantity > 1 && (
              <p className={`text-xs sm:text-sm ${themeClasses.textMuted}`}>Quantity: {quantity}</p>
            )}
          </div>

          {activeSubscriptions.length === 0 ? (
            <div className="text-center py-6 sm:py-8">
              <div className={`w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-4 rounded-full ${themeClasses.surface} flex items-center justify-center`}>
                <PlusIcon className={`w-6 h-6 sm:w-8 sm:h-8 ${themeClasses.textMuted}`} />
              </div>
              <h3 className={`text-base sm:text-lg font-medium ${themeClasses.text} mb-2`}>
                No Active Subscriptions
              </h3>
              <p className={`${themeClasses.textMuted} mb-4 text-sm sm:text-base`}>
                You need an active subscription to add products.
              </p>
              <button
                onClick={() => window.location.href = '/account/subscriptions'}
                className={getButtonClasses('primary')}
              >
                Create Subscription
              </button>
            </div>
          ) : (
            <>
              <div className="mb-4 sm:mb-6">
                <label className={`block text-sm font-medium ${themeClasses.text} mb-3`}>
                  Select Subscription:
                </label>
                <div className="space-y-2 sm:space-y-3">
                  {activeSubscriptions.map((subscription) => (
                    <label
                      key={subscription.id}
                      className={`block cursor-pointer p-3 sm:p-4 rounded-lg border-2 transition-colors ${
                        selectedSubscriptionId === subscription.id
                          ? 'border-primary bg-primary/5'
                          : `border-border-light hover:border-border`
                      }`}
                    >
                      <input
                        type="radio"
                        name="subscription"
                        value={subscription.id}
                        checked={selectedSubscriptionId === subscription.id}
                        onChange={(e) => setSelectedSubscriptionId(e.target.value)}
                        className="sr-only"
                      />
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0 mr-2">
                          <div className={`font-medium ${themeClasses.text} text-sm sm:text-base truncate`}>
                            {subscription.plan_id} Plan
                          </div>
                          <div className={`text-xs sm:text-sm ${themeClasses.textMuted} flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4 mt-1`}>
                            <span className="flex items-center gap-1">
                              <CreditCardIcon className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" />
                              <span className="truncate">{formatCurrency(subscription.price || 0)} / {formatBillingCycle(subscription.billing_cycle)}</span>
                            </span>
                            {subscription.next_billing_date && (
                              <span className="flex items-center gap-1">
                                <CalendarIcon className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" />
                                <span className="truncate">Next: {formatNextBilling(subscription.next_billing_date)}</span>
                              </span>
                            )}
                          </div>
                        </div>
                        <div className={`w-4 h-4 rounded-full border-2 flex-shrink-0 ${
                          selectedSubscriptionId === subscription.id
                            ? 'border-primary bg-primary'
                            : 'border-border'
                        }`}>
                          {selectedSubscriptionId === subscription.id && (
                            <div className="w-full h-full rounded-full bg-white scale-50"></div>
                          )}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                <button
                  onClick={onClose}
                  className={`${getButtonClasses('secondary')} w-full sm:w-auto`}
                  disabled={isLoading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddToSubscription}
                  disabled={!selectedSubscriptionId || isLoading}
                  className={`${getButtonClasses('primary')} w-full sm:w-auto`}
                >
                  {isLoading ? 'Adding...' : 'Add to Subscription'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};