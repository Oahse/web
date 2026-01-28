import React, { useState } from 'react';
import { 
  CalendarIcon, 
  ToggleLeftIcon,
  ToggleRightIcon,
  PauseIcon,
  PlayIcon,
  XIcon
} from 'lucide-react';
import { themeClasses, combineThemeClasses, getButtonClasses } from '../../lib/themeClasses';
import { toggleAutoRenew, Subscription } from '../../apis/subscription';
import { toast } from 'react-hot-toast';

interface SubscriptionCardProps {
  subscription: Subscription;
  onUpdate?: (id: string, updates: any) => void;
  onPause?: (id: string) => void;
  onResume?: (id: string) => void;
  onCancel?: (id: string) => void;
  onActivate?: (id: string) => void;
  onProductsUpdated?: () => void;
  showActions?: boolean;
  compact?: boolean;
}

export const SubscriptionCard: React.FC<SubscriptionCardProps> = ({
  subscription,
  onUpdate,
  onPause,
  onResume,
  onCancel,
  onActivate,
  onProductsUpdated,
  showActions = true,
  compact = false
}) => {
  const [isUpdating, setIsUpdating] = useState(false);

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'cancelled':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const handleAutoRenewToggle = async () => {
    setIsUpdating(true);
    try {
      const newValue = !subscription.auto_renew;
      const result = await toggleAutoRenew(subscription.id, newValue);
      
      // Handle the response structure from backend
      const updatedData = result.data || result;
      onUpdate?.(subscription.id, { auto_renew: updatedData.auto_renew });
      toast.success(`Auto-renew ${updatedData.auto_renew ? 'enabled' : 'disabled'}`);
    } catch (error) {
      console.error('Failed to update auto-renew:', error);
      toast.error('Failed to update auto-renew');
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className={combineThemeClasses(
      themeClasses.card.base,
      'p-6 space-y-4'
    )}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className={combineThemeClasses(themeClasses.text.heading, 'text-lg font-semibold')}>
            {subscription.plan_id.charAt(0).toUpperCase() + subscription.plan_id.slice(1)} Plan
          </h3>
          <div className="flex items-center gap-2 mt-1">
            <span className={combineThemeClasses(themeClasses.text.primary, 'font-medium')}>
              {formatCurrency(subscription.price, subscription.currency)}
            </span>
            <span className={themeClasses.text.secondary}>
              / {subscription.billing_cycle}
            </span>
          </div>
        </div>
        
        <span className={combineThemeClasses(
          'px-3 py-1 text-sm font-medium rounded-full border',
          getStatusColor(subscription.status)
        )}>
          {subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}
        </span>
      </div>

      {/* Next Billing */}
      {subscription.next_billing_date && subscription.status === 'active' && (
        <div className="flex items-center gap-2">
          <CalendarIcon className={combineThemeClasses(themeClasses.text.muted, 'w-4 h-4')} />
          <span className={combineThemeClasses(themeClasses.text.secondary, 'text-sm')}>
            Next billing: {formatDate(subscription.next_billing_date)}
          </span>
        </div>
      )}

      {/* Auto-Renew Toggle */}
      {subscription.status !== 'cancelled' && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 rounded-lg border border-gray-200 bg-gray-50">
          <div className="flex items-center gap-3">
            <button
              onClick={handleAutoRenewToggle}
              disabled={isUpdating}
              className={combineThemeClasses(
                'transition-colors',
                isUpdating ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
              )}
            >
              {subscription.auto_renew ? (
                <ToggleRightIcon className="w-6 h-6 text-green-600" />
              ) : (
                <ToggleLeftIcon className="w-6 h-6 text-gray-400" />
              )}
            </button>

            <div className="min-w-0">
              <span className={combineThemeClasses(themeClasses.text.primary, 'font-medium')}>
                Auto-Renew
              </span>
              <p
                className={combineThemeClasses(
                  themeClasses.text.secondary,
                  'text-sm break-words'
                )}
              >
                {subscription.auto_renew
                  ? 'Your subscription will renew automatically'
                  : 'Your subscription will not renew automatically'}
              </p>
            </div>
          </div>

          {isUpdating && (
            <div className="self-start sm:self-center w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          )}
        </div>
      )}


      {/* Actions */}
      {showActions && (
        <div className="flex items-center gap-2 pt-2 border-t border-gray-200">
          {subscription.status === 'active' && (
            <>
              {onPause && (
                <button
                  onClick={() => onPause(subscription.id)}
                  className={combineThemeClasses(
                    getButtonClasses('outline'),
                    'text-sm flex items-center gap-1'
                  )}
                >
                  <PauseIcon className="w-4 h-4" />
                  Pause
                </button>
              )}
              {onCancel && (
                <button
                  onClick={() => onCancel(subscription.id)}
                  className={combineThemeClasses(
                    'px-3 py-1 text-sm rounded-md border border-red-300 text-red-700 hover:bg-red-50 transition-colors flex items-center gap-1'
                  )}
                >
                  <XIcon className="w-4 h-4" />
                  Cancel
                </button>
              )}
            </>
          )}
          
          {subscription.status === 'paused' && onResume && (
            <button
              onClick={() => onResume(subscription.id)}
              className={combineThemeClasses(
                getButtonClasses('primary'),
                'text-sm flex items-center gap-1'
              )}
            >
              <PlayIcon className="w-4 h-4" />
              Resume
            </button>
          )}

          {subscription.status === 'cancelled' && onActivate && (
            <button
              onClick={() => onActivate(subscription.id)}
              className={combineThemeClasses(
                getButtonClasses('primary'),
                'text-sm flex items-center gap-1'
              )}
            >
              <PlayIcon className="w-4 h-4" />
              Activate
            </button>
          )}
        </div>
      )}
    </div>
  );
};