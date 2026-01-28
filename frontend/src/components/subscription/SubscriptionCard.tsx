import React, { useState } from 'react';
import { 
  CalendarIcon, 
  ToggleLeftIcon,
  ToggleRightIcon,
  PauseIcon,
  PlayIcon,
  XIcon,
  EditIcon,
  SaveIcon,
  XCircleIcon,
  PlusIcon,
  MinusIcon
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
  onAddProducts?: (subscription: any) => void;
  onRemoveProduct?: (subscriptionId: string, variantId: string) => void;
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
  onAddProducts,
  onRemoveProduct,
  showActions = true,
  compact = false
}) => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    billing_cycle: subscription.billing_cycle as 'weekly' | 'monthly' | 'yearly',
    plan_id: subscription.plan_id
  });

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

  const handleSaveEdit = async () => {
    setIsUpdating(true);
    try {
      await onUpdate?.(subscription.id, editData);
      setIsEditing(false);
      toast.success('Subscription updated successfully');
    } catch (error) {
      console.error('Failed to update subscription:', error);
      toast.error('Failed to update subscription');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleCancelEdit = () => {
    setEditData({
      billing_cycle: subscription.billing_cycle as 'weekly' | 'monthly' | 'yearly',
      plan_id: subscription.plan_id
    });
    setIsEditing(false);
  };

  return (
    <div className={combineThemeClasses(
      themeClasses.card.base,
      'p-6 space-y-4'
    )}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {isEditing ? (
            <div className="space-y-3">
              <div>
                <label className={combineThemeClasses(themeClasses.text.primary, 'block text-sm font-medium mb-1')}>
                  Plan
                </label>
                <select
                  value={editData.plan_id}
                  onChange={(e) => setEditData({ ...editData, plan_id: e.target.value })}
                  className={combineThemeClasses(themeClasses.input.base, themeClasses.input.default, 'text-sm')}
                >
                  <option value="basic">Basic Plan</option>
                  <option value="premium">Premium Plan</option>
                  <option value="enterprise">Enterprise Plan</option>
                </select>
              </div>
              <div>
                <label className={combineThemeClasses(themeClasses.text.primary, 'block text-sm font-medium mb-1')}>
                  Billing Cycle
                </label>
                <select
                  value={editData.billing_cycle}
                  onChange={(e) => setEditData({ ...editData, billing_cycle: e.target.value as 'weekly' | 'monthly' | 'yearly' })}
                  className={combineThemeClasses(themeClasses.input.base, themeClasses.input.default, 'text-sm')}
                >
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
            </div>
          ) : (
            <>
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
            </>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {subscription.status !== 'cancelled' && (
            <>
              {isEditing ? (
                <div className="flex items-center gap-1">
                  <button
                    onClick={handleSaveEdit}
                    disabled={isUpdating}
                    className={combineThemeClasses(
                      'p-1 rounded text-green-600 hover:bg-green-50 transition-colors',
                      isUpdating ? 'opacity-50 cursor-not-allowed' : ''
                    )}
                    title="Save changes"
                  >
                    <SaveIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    disabled={isUpdating}
                    className="p-1 rounded text-gray-600 hover:bg-gray-50 transition-colors"
                    title="Cancel editing"
                  >
                    <XCircleIcon className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="p-1 rounded text-gray-600 hover:bg-gray-50 transition-colors"
                  title="Edit subscription"
                >
                  <EditIcon className="w-4 h-4" />
                </button>
              )}
            </>
          )}
          
          <span className={combineThemeClasses(
            'px-3 py-1 text-sm font-medium rounded-full border',
            getStatusColor(subscription.status)
          )}>
            {subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}
          </span>
        </div>
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

      
      {subscription.products && subscription.products.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className={combineThemeClasses(themeClasses.text.primary, 'font-medium text-sm')}>
              Products ({subscription.products.length})
            </h4>
            {subscription.status !== 'cancelled' && onAddProducts && (
              <button
                onClick={() => onAddProducts(subscription)}
                className={combineThemeClasses(
                  'text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1'
                )}
              >
                <PlusIcon className="w-3 h-3" />
                Add Products
              </button>
            )}
          </div>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {subscription.products.map((product: any, index: number) => (
              <div key={product.id || index} className="flex items-center justify-between p-2 rounded text-sm">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  {product.image && (
                    <img 
                      src={product.image} 
                      alt={product.name}
                      className="w-6 h-6 rounded object-cover flex-shrink-0"
                    />
                  )}
                  <span className={combineThemeClasses(themeClasses.text.primary, 'truncate')}>
                    {product.name}
                  </span>
                  <span className={combineThemeClasses(themeClasses.text.secondary, 'flex-shrink-0')}>
                    {formatCurrency(product.current_price || product.price, subscription.currency)}
                  </span>
                </div>
                {subscription.status !== 'cancelled' && onRemoveProduct && (
                  <button
                    onClick={() => onRemoveProduct(subscription.id, product.id)}
                    className="text-red-600 hover:text-red-700 p-1 flex-shrink-0"
                    title="Remove product"
                  >
                    <MinusIcon className="w-3 h-3" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      {/* Shipping and Tax Section */}
      {(subscription.cost_breakdown || subscription.delivery_cost_applied || subscription.tax_amount) && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className={combineThemeClasses(themeClasses.text.primary, 'font-medium text-sm')}>
              Cost Breakdown
            </h4>
          </div>
          <div className="space-y-1 max-h-32 overflow-y-auto rounded-lg p-3">
            {/* Subtotal */}
            {subscription.cost_breakdown?.subtotal && (
              <div className="flex items-center justify-between text-sm">
                <span className={themeClasses.text.secondary}>Subtotal</span>
                <span className={themeClasses.text.primary}>
                  {formatCurrency(subscription.cost_breakdown.subtotal, subscription.currency)}
                </span>
              </div>
            )}

            {/* Shipping Cost */}
            {(subscription.cost_breakdown?.delivery_cost || subscription.delivery_cost_applied) && (
              <div className="flex items-center justify-between text-sm">
                <span className={themeClasses.text.secondary}>Shipping</span>
                <span className={themeClasses.text.primary}>
                  {formatCurrency(
                    subscription.cost_breakdown?.delivery_cost || subscription.delivery_cost_applied || 0, 
                    subscription.currency
                  )}
                </span>
              </div>
            )}

            {/* Tax Cost */}
            {(subscription.cost_breakdown?.tax_amount || subscription.tax_amount) && (
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-1">
                  <span className={themeClasses.text.secondary}>Tax</span>
                  {subscription.tax_rate_applied && (
                    <span className={combineThemeClasses(themeClasses.text.muted, 'text-xs')}>
                      ---({(subscription.tax_rate_applied * 100).toFixed(1)}%)
                    </span>
                  )}
                </div>
                <span className={themeClasses.text.primary}>
                  {formatCurrency(
                    subscription.cost_breakdown?.tax_amount || subscription.tax_amount || 0, 
                    subscription.currency
                  )}
                </span>
              </div>
            )}

            {/* Loyalty Discount */}
            {(subscription.cost_breakdown?.loyalty_discount || subscription.loyalty_discount_applied) && (
              <div className="flex items-center justify-between text-sm">
                <span className={themeClasses.text.secondary}>Loyalty Discount</span>
                <span className="text-green-600">
                  -{formatCurrency(
                    subscription.cost_breakdown?.loyalty_discount || subscription.loyalty_discount_applied || 0, 
                    subscription.currency
                  )}
                </span>
              </div>
            )}

            {/* Admin Percentage */}
            {subscription.admin_percentage_applied && (
              <div className="flex items-center justify-between text-sm">
                <span className={themeClasses.text.secondary}>Service Fee</span>
                <span className={themeClasses.text.primary}>
                  {formatCurrency(subscription.admin_percentage_applied, subscription.currency)}
                </span>
              </div>
            )}

            {/* Total */}
            {subscription.cost_breakdown?.total_amount && (
              <>
                <div className="border-t border-gray-200 my-2"></div>
                <div className="flex items-center justify-between text-sm font-semibold">
                  <span className={themeClasses.text.primary}>Total</span>
                  <span className={themeClasses.text.primary}>
                    {formatCurrency(subscription.cost_breakdown.total_amount, subscription.currency)}
                  </span>
                </div>
              </>
            )}

            {/* Loyalty Points Earned */}
            {subscription.loyalty_points_earned && subscription.loyalty_points_earned > 0 && (
              <div className="flex items-center justify-between text-sm pt-2 border-t border-gray-200">
                <span className={themeClasses.text.secondary}>Points Earned</span>
                <span className="text-blue-600 font-medium">
                  +{subscription.loyalty_points_earned} pts
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Auto-Renew Toggle */}
      {subscription.status !== 'cancelled' && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 rounded-lg border border-gray-200">
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