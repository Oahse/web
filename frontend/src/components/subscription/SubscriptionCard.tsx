import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  CalendarIcon, 
  CreditCardIcon, 
  ShoppingBagIcon, 
  PauseIcon,
  PlayIcon,
  TrashIcon,
  PackageIcon,
  ReceiptIcon,
  TruckIcon,
  PercentIcon
} from 'lucide-react';
import { themeClasses, combineThemeClasses, getButtonClasses } from '../../lib/themeClasses';
import { useLocale } from '../../contexts/LocaleContext';
import { AutoRenewToggle } from './AutoRenewToggle';

interface SubscriptionCardProps {
  subscription: {
    id: string;
    plan_id: string;
    status: 'active' | 'cancelled' | 'expired' | 'paused';
    price: number;
    currency: string;
    billing_cycle: 'weekly' | 'monthly' | 'yearly';
    auto_renew: boolean;
    next_billing_date?: string;
    current_period_end?: string;
    tax_rate_applied?: number;
    tax_amount?: number;
    delivery_cost_applied?: number;
    cost_breakdown?: {
      subtotal: number;
      tax_amount: number;
      tax_rate: number;
      delivery_cost: number;
      delivery_type: string;
      total_amount: number;
      admin_fee?: number;
      loyalty_discount?: number;
    };
    products?: Array<{
      id: string;
      name: string;
      price: number;
      current_price?: number;
      base_price?: number;
      sale_price?: number;
      image?: string;
      primary_image?: { url: string };
      images?: Array<{ url: string; is_primary?: boolean }>;
    }>;
    created_at: string;
  };
  onUpdate?: (subscriptionId: string, data: any) => void;
  onCancel?: (subscriptionId: string) => void;
  onPause?: (subscriptionId: string) => void;
  onResume?: (subscriptionId: string) => void;
  onActivate?: (subscriptionId: string) => void;
  showActions?: boolean;
  compact?: boolean;
}

export const SubscriptionCard: React.FC<SubscriptionCardProps> = ({
  subscription,
  onUpdate,
  onCancel,
  onPause,
  onResume,
  showActions = true,
  compact = false
}) => {
  const [isUpdating, setIsUpdating] = useState(false);
  const { formatCurrency } = useLocale();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'cancelled':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'expired':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatBillingCycle = (cycle: string) => {
    return cycle.charAt(0).toUpperCase() + cycle.slice(1);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getPrimaryImage = (product: any) => {
    if (product.images && product.images.length > 0) {
      const primaryImage = product.images.find((img: any) => img.is_primary);
      if (primaryImage?.url) return primaryImage.url;
      if (product.images[0]?.url) return product.images[0].url;
    }
    if (product.primary_image?.url) return product.primary_image.url;
    if (product.image) return product.image;
    return null;
  };

  const handleAutoRenewToggle = async (enabled: boolean) => {
    if (!onUpdate) return;
    
    setIsUpdating(true);
    try {
      onUpdate(subscription.id, { auto_renew: enabled });
    } finally {
      setIsUpdating(false);
    }
  };

  if (compact) {
    return (
      <div className={combineThemeClasses(
        themeClasses.card.base,
        'p-4 hover:shadow-md transition-shadow duration-200'
      )}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div>
              <h3 className={combineThemeClasses(themeClasses.text.heading, 'font-medium')}>
                {subscription.plan_id} Plan
              </h3>
              <div className="flex items-center space-x-2 mt-1">
                <span className={combineThemeClasses(themeClasses.text.secondary, 'text-sm')}>
                  {formatCurrency(subscription.price, subscription.currency)} / {formatBillingCycle(subscription.billing_cycle)}
                </span>
                <span className={`px-2 py-0.5 text-xs rounded-full border ${getStatusColor(subscription.status)}`}>
                  {subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}
                </span>
              </div>
              
              {/* Compact cost info */}
              {(subscription.tax_amount || subscription.delivery_cost_applied) && (
                <div className="flex items-center space-x-3 mt-1 text-xs text-gray-600">
                  {subscription.tax_amount && (
                    <span>Tax: {formatCurrency(subscription.tax_amount, subscription.currency)}</span>
                  )}
                  {subscription.delivery_cost_applied && (
                    <span>Shipping: {formatCurrency(subscription.delivery_cost_applied, subscription.currency)}</span>
                  )}
                </div>
              )}
            </div>
          </div>
          
          <Link
            to={`/subscription/${subscription.id}/manage`}
            className={combineThemeClasses(getButtonClasses('outline'), 'text-sm')}
          >
            Manage
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className={combineThemeClasses(
      themeClasses.card.base,
      'overflow-hidden hover:shadow-lg transition-all duration-300'
    )}>
      {/* Header */}
      <div className="p-6 pb-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-4">
          {/* Left: Plan info */}
          <div className="min-w-0">
            <h3
              className={combineThemeClasses(
                themeClasses.text.heading,
                'text-lg sm:text-xl font-bold mb-1 truncate'
              )}
            >
              {subscription.plan_id.charAt(0).toUpperCase() +
                subscription.plan_id.slice(1)}{" "}
              Plan
            </h3>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
              <div className="flex items-center gap-1">
                <CreditCardIcon
                  className={combineThemeClasses(themeClasses.text.muted, 'w-4 h-4')}
                />
                <span className={themeClasses.text.secondary}>
                  {formatCurrency(subscription.price, subscription.currency)} /{" "}
                  {formatBillingCycle(subscription.billing_cycle)}
                </span>
              </div>

              {subscription.products && (
                <div className="flex items-center gap-1">
                  <ShoppingBagIcon
                    className={combineThemeClasses(themeClasses.text.muted, 'w-4 h-4')}
                  />
                  <span className={themeClasses.text.secondary}>
                    {subscription.products.length} products
                  </span>
                </div>
              )}
            </div>

            {/* Cost Breakdown */}
            {(subscription.cost_breakdown || subscription.tax_amount || subscription.delivery_cost_applied) && (
              <div className="mt-3 p-3 bg-gray-50 rounded-lg border">
                <div className="flex items-center gap-2 mb-2">
                  <ReceiptIcon className={combineThemeClasses(themeClasses.text.muted, 'w-4 h-4')} />
                  <h4 className={combineThemeClasses(themeClasses.text.heading, 'text-sm font-medium')}>
                    Cost Breakdown
                  </h4>
                </div>
                <div className="space-y-1 text-xs">
                  {/* Subtotal */}
                  {subscription.cost_breakdown?.subtotal && (
                    <div className="flex justify-between items-center">
                      <span className={themeClasses.text.secondary}>Subtotal:</span>
                      <span className={themeClasses.text.primary}>
                        {formatCurrency(subscription.cost_breakdown.subtotal, subscription.currency)}
                      </span>
                    </div>
                  )}
                  
                  {/* Tax */}
                  {(subscription.cost_breakdown?.tax_amount || subscription.tax_amount) && (
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-1">
                        <PercentIcon className="w-3 h-3 text-gray-500" />
                        <span className={themeClasses.text.secondary}>
                          Tax {subscription.cost_breakdown?.tax_rate ? `(${(subscription.cost_breakdown.tax_rate * 100).toFixed(1)}%)` : 
                               subscription.tax_rate_applied ? `(${(subscription.tax_rate_applied * 100).toFixed(1)}%)` : ''}:
                        </span>
                      </div>
                      <span className={themeClasses.text.primary}>
                        {formatCurrency(
                          subscription.cost_breakdown?.tax_amount || subscription.tax_amount || 0, 
                          subscription.currency
                        )}
                      </span>
                    </div>
                  )}
                  
                  {/* Shipping */}
                  {(subscription.cost_breakdown?.delivery_cost || subscription.delivery_cost_applied) && (
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-1">
                        <TruckIcon className="w-3 h-3 text-gray-500" />
                        <span className={themeClasses.text.secondary}>
                          Shipping {subscription.cost_breakdown?.delivery_type ? `(${subscription.cost_breakdown.delivery_type})` : ''}:
                        </span>
                      </div>
                      <span className={themeClasses.text.primary}>
                        {formatCurrency(
                          subscription.cost_breakdown?.delivery_cost || subscription.delivery_cost_applied || 0, 
                          subscription.currency
                        )}
                      </span>
                    </div>
                  )}
                  
                  {/* Admin Fee */}
                  {subscription.cost_breakdown?.admin_fee && subscription.cost_breakdown.admin_fee > 0 && (
                    <div className="flex justify-between items-center">
                      <span className={themeClasses.text.secondary}>Admin Fee:</span>
                      <span className={themeClasses.text.primary}>
                        {formatCurrency(subscription.cost_breakdown.admin_fee, subscription.currency)}
                      </span>
                    </div>
                  )}
                  
                  {/* Loyalty Discount */}
                  {subscription.cost_breakdown?.loyalty_discount && subscription.cost_breakdown.loyalty_discount > 0 && (
                    <div className="flex justify-between items-center">
                      <span className={themeClasses.text.secondary}>Loyalty Discount:</span>
                      <span className="text-green-600">
                        -{formatCurrency(subscription.cost_breakdown.loyalty_discount, subscription.currency)}
                      </span>
                    </div>
                  )}
                  
                  {/* Total */}
                  {subscription.cost_breakdown?.total_amount && (
                    <div className="flex justify-between items-center pt-1 border-t border-gray-200 font-medium">
                      <span className={themeClasses.text.primary}>Total:</span>
                      <span className={themeClasses.text.primary}>
                        {formatCurrency(subscription.cost_breakdown.total_amount, subscription.currency)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right: Status + Actions */}
          <div className="flex items-center justify-between sm:justify-end gap-3">
            {/* Status badge */}
            <span
              className={combineThemeClasses(
                'px-2 py-0.5 text-[11px] font-medium rounded-full border whitespace-nowrap',
                getStatusColor(subscription.status)
              )}
            >
              {subscription.status.charAt(0).toUpperCase() +
                subscription.status.slice(1)}
            </span>

            {showActions && (
              <div className="flex items-center gap-2">
                {/* Pause/Resume Button */}
                {subscription.status === 'active' && onPause && (
                  <button
                    onClick={() => onPause(subscription.id)}
                    className={combineThemeClasses(
                      'p-2 rounded-md transition-colors',
                      'text-yellow-600 hover:bg-yellow-50',
                      'border border-yellow-200 hover:border-yellow-300'
                    )}
                    title="Pause Subscription"
                  >
                    <PauseIcon className="w-4 h-4" />
                  </button>
                )}

                {subscription.status === 'paused' && onResume && (
                  <button
                    onClick={() => onResume(subscription.id)}
                    className={combineThemeClasses(
                      'p-2 rounded-md transition-colors',
                      'text-green-600 hover:bg-green-50',
                      'border border-green-200 hover:border-green-300'
                    )}
                    title="Resume Subscription"
                  >
                    <PlayIcon className="w-4 h-4" />
                  </button>
                )}

                {/* Cancel Button */}
                {(subscription.status === 'active' || subscription.status === 'paused') && onCancel && (
                  <button
                    onClick={() => {
                      if (window.confirm('Are you sure you want to cancel this subscription? This action cannot be undone.')) {
                        onCancel(subscription.id);
                      }
                    }}
                    className={combineThemeClasses(
                      'p-2 rounded-md transition-colors',
                      'text-red-600 hover:bg-red-50',
                      'border border-red-200 hover:border-red-300'
                    )}
                    title="Cancel Subscription"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>


        {/* Next Billing Date */}
        {subscription.next_billing_date && subscription.status === 'active' && (
          <div className="flex items-center space-x-1 mb-4">
            <CalendarIcon className={combineThemeClasses(themeClasses.text.muted, 'w-4 h-4')} />
            <span className={combineThemeClasses(themeClasses.text.secondary, 'text-sm')}>
              Next billing: {formatDate(subscription.next_billing_date)}
            </span>
          </div>
        )}

        {/* Auto-Renew Toggle */}
        {subscription.status === 'active' && onUpdate && (
          <AutoRenewToggle
            isEnabled={subscription.auto_renew}
            onToggle={handleAutoRenewToggle}
            loading={isUpdating}
            nextBillingDate={subscription.next_billing_date}
            billingCycle={subscription.billing_cycle}
            showDetails={false}
            size="sm"
          />
        )}
      </div>

      {/* Product Preview */}
      {subscription.products && subscription.products.length > 0 && (
        <div className={combineThemeClasses(themeClasses.background.elevated, 'p-4 border-t', themeClasses.border.light)}>
          <h4 className={combineThemeClasses(themeClasses.text.heading, 'font-medium text-sm mb-3')}>
            Products ({subscription.products.length})
          </h4>
          <div className="flex items-center space-x-3 overflow-x-auto">
            {subscription.products.slice(0, 4).map((product, index) => {
              const imageUrl = getPrimaryImage(product);
              return (
                <div key={product.id || index} className="flex-shrink-0 flex items-center space-x-2">
                  {imageUrl ? (
                    <img
                      src={imageUrl}
                      alt={product.name}
                      className="w-10 h-10 rounded-lg object-cover"
                    />
                  ) : (
                    <div className={combineThemeClasses(
                      'w-10 h-10 rounded-lg flex items-center justify-center border-2 border-dashed',
                      themeClasses.border.light,
                      themeClasses.background.surface
                    )}>
                      <PackageIcon className={combineThemeClasses(themeClasses.text.muted, 'w-4 h-4')} />
                    </div>
                  )}
                  <div className="min-w-0">
                    <p className={combineThemeClasses(themeClasses.text.primary, 'text-xs truncate max-w-20')}>
                      {product.name}
                    </p>
                    <p className={combineThemeClasses(themeClasses.text.muted, 'text-xs')}>
                      {formatCurrency(product.current_price || product.base_price || product.price || 0, subscription.currency)}
                    </p>
                  </div>
                </div>
              );
            })}
            {subscription.products.length > 4 && (
              <div className={combineThemeClasses(themeClasses.text.muted, 'text-xs flex-shrink-0')}>
                +{subscription.products.length - 4} more
              </div>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className={combineThemeClasses(themeClasses.background.elevated, 'p-4 border-t', themeClasses.border.light)}>
        <div className="flex items-center justify-between">
          <span className={combineThemeClasses(themeClasses.text.muted, 'text-xs')}>
            Created {formatDate(subscription.created_at)}
          </span>
          <Link
            to={`/subscription/${subscription.id}/manage`}
            className={combineThemeClasses(getButtonClasses('primary'), 'text-sm')}
          >
            Manage Subscription
          </Link>
        </div>
      </div>
    </div>
  );
};