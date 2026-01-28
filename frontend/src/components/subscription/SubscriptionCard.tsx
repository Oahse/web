import React, { useEffect, useState } from 'react';
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
  MinusIcon,
  ChevronDownIcon
} from 'lucide-react';
import { themeClasses, combineThemeClasses, getButtonClasses } from '../../lib/themeClasses';
import { toggleAutoRenew, Subscription } from '../../apis/subscription';
import { formatCurrency, formatTaxRate } from '../../utils/orderCalculations';
import { toast } from 'react-hot-toast';

interface SubscriptionCardProps {
  subscription: Subscription;
  onUpdate?: (id: string, updates: any) => void;
  onPause?: (id: string) => void;
  onResume?: (id: string) => void;
  onCancel?: (id: string) => void;
  onActivate?: (id: string) => void;
  onAddProducts?: (subscription: any) => void;
  onRemoveProduct?: (subscriptionId: string, variantId: string) => void;
  showActions?: boolean;
}

export const SubscriptionCard: React.FC<SubscriptionCardProps> = ({
  subscription,
  onUpdate,
  onPause,
  onResume,
  onCancel,
  onActivate,
  onAddProducts,
  onRemoveProduct,
  showActions = true
}) => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [showBillingSummary, setShowBillingSummary] = useState(false);

  const [editData, setEditData] = useState({
    billing_cycle: subscription.billing_cycle as 'weekly' | 'monthly' | 'yearly',
    plan_id: subscription.plan_id
  });
    useEffect(() => {
    if (subscription.cost_breakdown) {
      setShowBillingSummary(true);
    }
  }, [subscription.cost_breakdown]);


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
      onUpdate?.(subscription.id, editData);
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
                  Subscription Plan
                </label>
                <select
                  value={editData.plan_id}
                  onChange={(e) => setEditData({ ...editData, plan_id: e.target.value })}
                  className={combineThemeClasses(themeClasses.input.base, themeClasses.input.default, 'text-sm')}
                >
                  <option value="basic">Basic Subscription</option>
                  <option value="premium">Premium Subscription</option>
                  <option value="enterprise">Enterprise Subscription</option>
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
                {subscription.plan_id.charAt(0).toUpperCase() + subscription.plan_id.slice(1)} Subscription
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
            Next billing date: {formatDate(subscription.next_billing_date)}
          </span>
        </div>
      )}

      
      {subscription.products && subscription.products.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className={combineThemeClasses(themeClasses.text.primary, 'font-medium text-sm')}>
              Subscription Items ({subscription.products.length})
            </h4>
            {subscription.status !== 'cancelled' && onAddProducts && (
              <button
                onClick={() => onAddProducts(subscription)}
                className={combineThemeClasses(
                  'text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1'
                )}
              >
                <PlusIcon className="w-3 h-3" />
                Add Items
              </button>
            )}
          </div>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {subscription.products.map((product: any, index: number) => {
              // Get total quantity for this product from variant_quantities
              const productQuantities = subscription.variant_quantities ? 
                Object.entries(subscription.variant_quantities).reduce((total, [variantId, quantity]) => {
                  // For now, we'll show the total quantity across all variants
                  // In a more sophisticated setup, you'd match variants to products
                  return total + (quantity as number);
                }, 0) : 0;
              
              return (
                <div key={product.id || index} className="flex items-center justify-between p-2 rounded text-sm">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {product.image && (
                      <img 
                        src={product.image} 
                        alt={product.name}
                        className="w-6 h-6 rounded object-cover flex-shrink-0"
                      />
                    )}
                    <div className="flex flex-col flex-1 min-w-0">
                      <span className={combineThemeClasses(themeClasses.text.primary, 'truncate font-medium')}>
                        {product.name}
                      </span>
                      {productQuantities > 0 && (
                        <span className={combineThemeClasses(themeClasses.text.muted, 'text-xs')}>
                          Total items: {productQuantities}
                        </span>
                      )}
                    </div>
                    <div className="flex flex-col items-end">
                      <span className={combineThemeClasses(themeClasses.text.secondary, 'flex-shrink-0')}>
                        {formatCurrency(product.current_price || product.price, subscription.currency)}
                      </span>
                      <span className={combineThemeClasses(themeClasses.text.muted, 'text-xs')}>
                        per item
                      </span>
                    </div>
                  </div>
                  {subscription.status !== 'cancelled' && onRemoveProduct && (
                    <button
                      onClick={() => onRemoveProduct(subscription.id, product.id)}
                      className="text-red-600 hover:text-red-700 p-1 flex-shrink-0 ml-2"
                      title="Remove from subscription"
                    >
                      <MinusIcon className="w-3 h-3" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
      {/* Billing Summary */}
      {(subscription.cost_breakdown || subscription.shipping_cost || subscription.tax_amount) && (
        <div className="space-y-2">
          <button
            type="button"
            onClick={() => setShowBillingSummary(v => !v)}
            className="w-full flex items-center justify-between text-left"
          >
            <h4 className={combineThemeClasses(themeClasses.text.primary, 'font-medium text-sm')}>
              Billing Summary
            </h4>

            <ChevronDownIcon
              className={combineThemeClasses(
                'w-4 h-4 transition-transform',
                showBillingSummary ? 'rotate-180' : 'rotate-0'
              )}
            />
          </button>
          
          {showBillingSummary && (
          <div className="space-y-2 rounded-lg p-3">
            {/* Subscription Items */}
            {subscription.cost_breakdown?.product_variants && subscription.cost_breakdown.product_variants.length > 0 && (
              <div className="space-y-1">
                <span className={combineThemeClasses(themeClasses.text.secondary, 'text-xs font-medium')}>
                  Items in subscription:
                </span>
                {subscription.cost_breakdown.product_variants.map((variant, index) => {
                  return (
                    <div key={variant.variant_id || index} className="flex items-center justify-between text-sm pl-2">
                      <div className="flex flex-col flex-1 min-w-0">
                        <span className={combineThemeClasses(themeClasses.text.primary, 'font-medium truncate')}>
                          {variant.name}
                        </span>
                        <div className="flex items-center gap-2 text-xs">
                          <span className={themeClasses.text.muted}>
                            {formatCurrency(variant.price, subscription.currency)} each
                          </span>
                          {variant.quantity > 1 && (
                            <span className={themeClasses.text.muted}>
                              × {variant.quantity}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className={combineThemeClasses(themeClasses.text.primary, 'font-medium')}>
                          {formatCurrency(variant.price * variant.quantity, subscription.currency)}
                        </span>
                        <span className={combineThemeClasses(themeClasses.text.muted, 'text-xs')}>
                          total
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Items Subtotal */}
            {subscription.cost_breakdown?.subtotal && (
              <div className="flex items-center justify-between text-sm pt-2 border-t border-gray-200">
                <span className={combineThemeClasses(themeClasses.text.secondary, 'font-medium')}>Items Subtotal</span>
                <span className={combineThemeClasses(themeClasses.text.primary, 'font-medium')}>
                  {formatCurrency(subscription.cost_breakdown.subtotal, subscription.currency)}
                </span>
              </div>
            )}

            {/* Shipping Cost */}
            {(subscription.cost_breakdown?.shipping_cost || subscription.shipping_cost) && (
              <div className="flex items-center justify-between text-sm">
                <span className={themeClasses.text.secondary}>Shipping & Handling</span>
                <span className={themeClasses.text.primary}>
                  {formatCurrency(
                    subscription.cost_breakdown?.shipping_cost || subscription.shipping_cost || 0, 
                    subscription.currency
                  )}
                </span>
              </div>
            )}

            {/* Tax Amount */}
            {(subscription.cost_breakdown?.tax_amount !== undefined ||
                subscription.tax_amount !== undefined
                ) && (
                    <div className="flex items-center justify-between text-sm">
                      <span className={themeClasses.text.secondary}>Tax</span>
                        {(subscription.cost_breakdown?.tax_rate !== undefined || subscription.tax_rate !== undefined) && (
                          <span className={combineThemeClasses(themeClasses.text.muted, 'text-xs')}>
                            ({((subscription.cost_breakdown?.tax_rate || subscription.tax_rate || 0) * 100).toFixed(1)})%
                          </span>
                        )}
                      <span className={themeClasses.text.primary}>
                        {formatCurrency(
                          subscription.cost_breakdown?.tax_amount || subscription.tax_amount || 0, 
                          subscription.currency
                        )}
                      </span>
                    </div>
            )}

            {/* Total Amount */}
            {subscription.cost_breakdown?.total_amount && (
              <div className="flex items-center justify-between text-sm font-semibold pt-2 border-t border-gray-200">
                <span className={themeClasses.text.primary}>Total per {subscription.billing_cycle}</span>
                <span className={themeClasses.text.primary}>
                  {formatCurrency(subscription.cost_breakdown.total_amount, subscription.currency)}
                </span>
              </div>
            )}
          </div>)}
        </div>
      )}

      {/* Auto-Renew Settings */}
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
                Automatic Renewal
              </span>
              <p
                className={combineThemeClasses(
                  themeClasses.text.secondary,
                  'text-sm break-words'
                )}
              >
                {subscription.auto_renew
                  ? `Subscription will automatically renew every ${subscription.billing_cycle}`
                  : 'Subscription will not renew automatically and will expire after current period'}
              </p>
            </div>
          </div>

          {isUpdating && (
            <div className="self-start sm:self-center w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          )}
        </div>
      )}

      {/* Subscription Actions */}
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
              Reactivate
            </button>
          )}
        </div>
      )}
    </div>
  );
};