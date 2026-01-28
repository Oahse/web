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
import { PauseSubscriptionModal } from './PauseSubscriptionModal';
import { ResumeSubscriptionModal } from './ResumeSubscriptionModal';
import { CancelSubscriptionModal } from './CancelSubscriptionModal';

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
  onCancel?: (subscriptionId: string, reason?: string) => void;
  onPause?: (subscriptionId: string, reason?: string) => void;
  onResume?: (subscriptionId: string) => void;
  onActivate?: (subscriptionId: string) => void;
  showActions?: boolean;
  compact?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const SubscriptionCard: React.FC<SubscriptionCardProps> = ({
  subscription,
  onUpdate,
  onCancel,
  onPause,
  onResume,
  showActions = true,
  compact = false,
  size = 'md',
  className = ''
}) => {
  const getSizeClasses = (size: 'sm' | 'md' | 'lg') => {
    switch (size) {
      case 'sm':
        return {
          card: 'text-sm',
          padding: 'p-3',
          headerPadding: 'p-3 pb-2',
          title: 'text-sm font-semibold',
          spacing: 'gap-2',
          iconSize: 'w-3 h-3',
        };
      case 'lg':
        return {
          card: 'text-base',
          padding: 'p-6',
          headerPadding: 'p-6 pb-4',
          title: 'text-xl font-bold',
          spacing: 'gap-4',
          iconSize: 'w-5 h-5',
        };
      default: // md
        return {
          card: 'text-sm sm:text-base',
          padding: 'p-4 sm:p-5',
          headerPadding: 'p-4 sm:p-6 pb-4',
          title: 'text-base sm:text-lg lg:text-xl font-bold',
          spacing: 'gap-3 sm:gap-4',
          iconSize: 'w-3 h-3 sm:w-4 sm:h-4',
        };
    }
  };

  const sizeClasses = getSizeClasses(size);
  const [isUpdating, setIsUpdating] = useState(false);
  const [showPauseModal, setShowPauseModal] = useState(false);
  const [showResumeModal, setShowResumeModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [isPausing, setIsPausing] = useState(false);
  const [isResuming, setIsResuming] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
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

  const handlePauseConfirm = async (reason?: string) => {
    if (!onPause) return;
    
    setIsPausing(true);
    try {
      await onPause(subscription.id, reason);
      setShowPauseModal(false);
    } finally {
      setIsPausing(false);
    }
  };

  const handleResumeConfirm = async () => {
    if (!onResume) return;
    
    setIsResuming(true);
    try {
      await onResume(subscription.id);
      setShowResumeModal(false);
    } finally {
      setIsResuming(false);
    }
  };

  const handleCancelConfirm = async (reason?: string) => {
    if (!onCancel) return;
    
    setIsCancelling(true);
    try {
      await onCancel(subscription.id, reason);
      setShowCancelModal(false);
    } finally {
      setIsCancelling(false);
    }
  };

  if (compact) {
    return (
      <div className={combineThemeClasses(
        themeClasses.card.base,
        sizeClasses.card,
        sizeClasses.padding,
        'hover:shadow-md transition-shadow duration-200',
        className
      )}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div>
              <h3 className={combineThemeClasses(themeClasses.text.heading, 'font-medium')}>
                {subscription.plan_id} Plan
              </h3>
              <div className={combineThemeClasses('flex items-center space-x-2 mt-1', sizeClasses.spacing)}>
                <span className={combineThemeClasses(themeClasses.text.secondary, 'text-sm')}>
                  {formatCurrency(subscription.price, subscription.currency)} / {formatBillingCycle(subscription.billing_cycle)}
                </span>
                <span className={`px-2 py-0.5 text-xs rounded-full border ${getStatusColor(subscription.status)}`}>
                  {subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}
                </span>
              </div>
              
              {/* Compact cost info */}
              {(subscription.tax_amount || subscription.delivery_cost_applied) && (
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-xs">
                  {subscription.tax_amount && (
                    <span className={themeClasses.text.muted}>
                      Tax: {formatCurrency(subscription.tax_amount, subscription.currency)}
                    </span>
                  )}
                  {subscription.delivery_cost_applied && (
                    <span className={themeClasses.text.muted}>
                      Shipping: {formatCurrency(subscription.delivery_cost_applied, subscription.currency)}
                    </span>
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
      sizeClasses.card,
      'overflow-hidden hover:shadow-lg transition-all duration-300',
      className
    )}>
      {/* Header */}
      <div className={sizeClasses.headerPadding}>
        <div className={combineThemeClasses('flex flex-col sm:flex-row sm:items-start sm:justify-between mb-4', sizeClasses.spacing)}>
          {/* Left: Plan info */}
          <div className="min-w-0 flex-1">
            <h3
              className={combineThemeClasses(
                themeClasses.text.heading,
                sizeClasses.title,
                'mb-1 truncate'
              )}
            >
              {subscription.plan_id.charAt(0).toUpperCase() +
                subscription.plan_id.slice(1)}{" "}
              Plan
            </h3>

            <div className={combineThemeClasses('flex flex-wrap items-center gap-x-3 sm:gap-x-4 gap-y-1 text-xs sm:text-sm', sizeClasses.spacing)}>
              <div className="flex items-center gap-1">
                <CreditCardIcon
                  className={combineThemeClasses(themeClasses.text.muted, sizeClasses.iconSize)}
                />
                <span className={themeClasses.text.secondary}>
                  {formatCurrency(subscription.price, subscription.currency)} /{" "}
                  {formatBillingCycle(subscription.billing_cycle)}
                </span>
              </div>

              {subscription.products && (
                <div className="flex items-center gap-1">
                  <ShoppingBagIcon
                    className={combineThemeClasses(themeClasses.text.muted, sizeClasses.iconSize)}
                  />
                  <span className={themeClasses.text.secondary}>
                    {subscription.products.length} products
                  </span>
                </div>
              )}
            </div>

            {/* Cost Breakdown */}
            {(subscription.cost_breakdown || subscription.tax_amount || subscription.delivery_cost_applied) && (
              <div className={combineThemeClasses(
                'mt-3 p-1 rounded-lg border w-auto inline-block',
                themeClasses.background.elevated,
                themeClasses.border.light
              )}>
                <div className="flex items-center gap-2 mb-2 sm:mb-3">
                  <ReceiptIcon className={combineThemeClasses(themeClasses.text.muted, 'w-4 h-4')} />
                  <h4 className={combineThemeClasses(themeClasses.text.heading, 'text-sm sm:text-base font-medium')}>
                    Cost Breakdown
                  </h4>
                </div>
                <div className="space-y-1 sm:space-y-2 text-xs sm:text-sm min-w-max">
                  {/* Subtotal */}
                  {subscription.cost_breakdown?.subtotal && (
                    <div className="flex justify-between items-center gap-4">
                      <span className={themeClasses.text.secondary}>Subtotal:</span>
                      <span className={combineThemeClasses(themeClasses.text.primary, 'font-medium')}>
                        {formatCurrency(subscription.cost_breakdown.subtotal, subscription.currency)}
                      </span>
                    </div>
                  )}
                  
                  {/* Tax */}
                  {(subscription.cost_breakdown?.tax_amount || subscription.tax_amount) && (
                    <div className="flex justify-between items-center gap-4">
                      <div className="flex items-center gap-1">
                        <PercentIcon className={combineThemeClasses(themeClasses.text.muted, 'w-3 h-3 flex-shrink-0')} />
                        <span className={themeClasses.text.secondary}>
                          Tax {subscription.cost_breakdown?.tax_rate ? `(${(subscription.cost_breakdown.tax_rate * 100).toFixed(1)}%)` : 
                               subscription.tax_rate_applied ? `(${(subscription.tax_rate_applied * 100).toFixed(1)}%)` : ''}:
                        </span>
                      </div>
                      <span className={combineThemeClasses(themeClasses.text.primary, 'font-medium')}>
                        {formatCurrency(
                          subscription.cost_breakdown?.tax_amount || subscription.tax_amount || 0, 
                          subscription.currency
                        )}
                      </span>
                    </div>
                  )}
                  
                  {/* Shipping */}
                  {(subscription.cost_breakdown?.delivery_cost || subscription.delivery_cost_applied) && (
                    <div className="flex justify-between items-center gap-4">
                      <div className="flex items-center gap-1">
                        <TruckIcon className={combineThemeClasses(themeClasses.text.muted, 'w-3 h-3 flex-shrink-0')} />
                        <span className={themeClasses.text.secondary}>
                          Shipping {subscription.cost_breakdown?.delivery_type ? `(${subscription.cost_breakdown.delivery_type})` : ''}:
                        </span>
                      </div>
                      <span className={combineThemeClasses(themeClasses.text.primary, 'font-medium')}>
                        {formatCurrency(
                          subscription.cost_breakdown?.delivery_cost || subscription.delivery_cost_applied || 0, 
                          subscription.currency
                        )}
                      </span>
                    </div>
                  )}
                  
                  {/* Loyalty Discount */}
                  {subscription.cost_breakdown?.loyalty_discount && subscription.cost_breakdown.loyalty_discount > 0 && (
                    <div className="flex justify-between items-center gap-4">
                      <span className={themeClasses.text.secondary}>Loyalty Discount:</span>
                      <span className={combineThemeClasses(themeClasses.text.success, 'font-medium')}>
                        -{formatCurrency(subscription.cost_breakdown.loyalty_discount, subscription.currency)}
                      </span>
                    </div>
                  )}
                  
                  {/* Total */}
                  {subscription.cost_breakdown?.total_amount && (
                    <div className={combineThemeClasses(
                      'flex justify-between items-center gap-4 pt-1 border-t font-medium',
                      themeClasses.border.light
                    )}>
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
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between sm:justify-end gap-3">
            {/* Status badge */}
            <span
              className={combineThemeClasses(
                'px-2 sm:px-3 py-1 text-xs sm:text-[11px] font-medium rounded-full border whitespace-nowrap',
                getStatusColor(subscription.status)
              )}
            >
              {subscription.status.charAt(0).toUpperCase() +
                subscription.status.slice(1)}
            </span>

            {showActions && (
              <div className="flex items-center gap-1 sm:gap-2">
                {/* Pause/Resume Button */}
                {subscription.status === 'active' && onPause && (
                  <button
                    onClick={() => setShowPauseModal(true)}
                    className={combineThemeClasses(
                      'p-1.5 sm:p-2 rounded-md transition-colors border',
                      themeClasses.text.warning,
                      themeClasses.background.surface,
                      themeClasses.border.warning,
                      themeClasses.interactive.hover
                    )}
                    title="Pause Subscription"
                  >
                    <PauseIcon className="w-3 h-3 sm:w-4 sm:h-4" />
                  </button>
                )}

                {subscription.status === 'paused' && onResume && (
                  <button
                    onClick={() => setShowResumeModal(true)}
                    className={combineThemeClasses(
                      'p-1.5 sm:p-2 rounded-md transition-colors border',
                      themeClasses.text.success,
                      themeClasses.background.surface,
                      themeClasses.border.success,
                      themeClasses.interactive.hover
                    )}
                    title="Resume Subscription"
                  >
                    <PlayIcon className="w-3 h-3 sm:w-4 sm:h-4" />
                  </button>
                )}

                {/* Cancel Button */}
                {(subscription.status === 'active' || subscription.status === 'paused') && onCancel && (
                  <button
                    onClick={() => setShowCancelModal(true)}
                    className={combineThemeClasses(
                      'p-1.5 sm:p-2 rounded-md transition-colors border',
                      themeClasses.text.error,
                      themeClasses.background.surface,
                      themeClasses.border.error,
                      themeClasses.interactive.hover
                    )}
                    title="Cancel Subscription"
                  >
                    <TrashIcon className="w-3 h-3 sm:w-4 sm:h-4" />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>


        {/* Next Billing Date */}
        {subscription.next_billing_date && subscription.status === 'active' && (
          <div className="flex items-center gap-1 sm:gap-2 mb-3 sm:mb-4">
            <CalendarIcon className={combineThemeClasses(themeClasses.text.muted, 'w-3 h-3 sm:w-4 sm:h-4')} />
            <span className={combineThemeClasses(themeClasses.text.secondary, 'text-xs sm:text-sm')}>
              Next billing: {formatDate(subscription.next_billing_date)}
            </span>
          </div>
        )}

        {/* Auto-Renew Toggle */}
        {subscription.status === 'active' && onUpdate && (
          <div className="mb-2">
            <AutoRenewToggle
              isEnabled={subscription.auto_renew}
              onToggle={handleAutoRenewToggle}
              loading={isUpdating}
              nextBillingDate={subscription.next_billing_date}
              billingCycle={subscription.billing_cycle}
              showDetails={false}
              size="sm"
            />
          </div>
        )}
      </div>

      {/* Product Preview */}
      {subscription.products && subscription.products.length > 0 && (
        <div className={combineThemeClasses(
          themeClasses.background.elevated, 
          'p-3 sm:p-4 border-t', 
          themeClasses.border.light
        )}>
          <h4 className={combineThemeClasses(themeClasses.text.heading, 'font-medium text-sm sm:text-base mb-3')}>
            Products ({subscription.products.length})
          </h4>
          <div className="flex items-center gap-2 sm:gap-3 overflow-x-auto pb-1">
            {subscription.products.slice(0, 4).map((product, index) => {
              const imageUrl = getPrimaryImage(product);
              return (
                <div key={product.id || index} className="flex-shrink-0 flex items-center gap-2 min-w-0">
                  {imageUrl ? (
                    <img
                      src={imageUrl}
                      alt={product.name}
                      className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg object-cover"
                    />
                  ) : (
                    <div className={combineThemeClasses(
                      'w-8 h-8 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center border-2 border-dashed',
                      themeClasses.border.light,
                      themeClasses.background.surface
                    )}>
                      <PackageIcon className={combineThemeClasses(themeClasses.text.muted, 'w-3 h-3 sm:w-4 sm:h-4')} />
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <p className={combineThemeClasses(themeClasses.text.primary, 'text-xs truncate max-w-16 sm:max-w-20')}>
                      {product.name}
                    </p>
                    <p className={combineThemeClasses(themeClasses.text.muted, 'text-xs')}>
                      {(() => {
                        const price = product.current_price || product.base_price || product.price || 0;
                        return price > 0 
                          ? formatCurrency(price, subscription.currency)
                          : 'Price not set';
                      })()}
                    </p>
                  </div>
                </div>
              );
            })}
            {subscription.products.length > 4 && (
              <div className={combineThemeClasses(themeClasses.text.muted, 'text-xs flex-shrink-0 ml-2')}>
                +{subscription.products.length - 4} more
              </div>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className={combineThemeClasses(
        themeClasses.background.elevated, 
        'p-3 sm:p-4 border-t', 
        themeClasses.border.light
      )}>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <span className={combineThemeClasses(themeClasses.text.muted, 'text-xs')}>
            Created {formatDate(subscription.created_at)}
          </span>
          <Link
            to={`/subscription/${subscription.id}/manage`}
            className={combineThemeClasses(getButtonClasses('primary'), 'text-sm w-full sm:w-auto text-center')}
          >
            Manage Subscription
          </Link>
        </div>
      </div>

      {/* Pause Subscription Modal */}
      <PauseSubscriptionModal
        isOpen={showPauseModal}
        onClose={() => setShowPauseModal(false)}
        onConfirm={handlePauseConfirm}
        subscriptionId={subscription.id}
        planName={subscription.plan_id.charAt(0).toUpperCase() + subscription.plan_id.slice(1)}
        loading={isPausing}
      />

      {/* Resume Subscription Modal */}
      <ResumeSubscriptionModal
        isOpen={showResumeModal}
        onClose={() => setShowResumeModal(false)}
        onConfirm={handleResumeConfirm}
        subscriptionId={subscription.id}
        planName={subscription.plan_id.charAt(0).toUpperCase() + subscription.plan_id.slice(1)}
        nextBillingDate={subscription.next_billing_date}
        loading={isResuming}
      />

      {/* Cancel Subscription Modal */}
      <CancelSubscriptionModal
        isOpen={showCancelModal}
        onClose={() => setShowCancelModal(false)}
        onConfirm={handleCancelConfirm}
        subscriptionId={subscription.id}
        planName={subscription.plan_id.charAt(0).toUpperCase() + subscription.plan_id.slice(1)}
        loading={isCancelling}
      />
    </div>
  );
};