import React, { useState } from 'react';
import { EyeIcon, TagIcon, PackageIcon } from 'lucide-react';
import { themeClasses, combineThemeClasses } from '../../utils/themeClasses';
import { formatCurrency } from '../../utils/orderCalculations';
import { Subscription } from '../../api/subscription';

interface SubscriptionItemProps {
  subscription: Subscription;
  isExpanded?: boolean;
  onToggle?: () => void;
}

export const SubscriptionItem: React.FC<SubscriptionItemProps> = ({
  subscription,
  isExpanded = false,
  onToggle
}) => {
  const [showProducts, setShowProducts] = useState(false);
  const [showBillingSummary, setShowBillingSummary] = useState(false);

  return (
    <div className="border-t pt-4 space-y-4">
      {/* Products Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className={combineThemeClasses(themeClasses.text.primary, 'font-medium text-sm')}>
            Products & Services
          </h4>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowProducts(!showProducts);
            }}
            className="text-xs text-primary hover:text-primary-dark flex items-center gap-1"
          >
            <EyeIcon size={12} />
            {showProducts ? 'Hide' : 'Show'} Details
          </button>
        </div>
        
        {showProducts && subscription.products && subscription.products.length > 0 && (
          <div className="space-y-3 bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            {subscription.products.map((product: any, index: number) => (
              <div key={index} className="flex items-start gap-4 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
                {/* Product Image */}
                <div className="flex-shrink-0">
                  {product.images && product.images.length > 0 ? (
                    <img
                      src={product.images[0].url}
                      alt={product.name}
                      className="w-12 h-12 rounded-lg object-cover"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-lg bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                      <PackageIcon size={20} className="text-gray-400" />
                    </div>
                  )}
                </div>
                
                {/* Product Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <h4 className={combineThemeClasses(themeClasses.text.primary, 'font-medium text-sm')}>
                        {product.name}
                      </h4>
                      {/* Show variant name if available */}
                      {(product.variant?.name || product.variant_name || product.size || product.color) && (
                        <span className={combineThemeClasses(themeClasses.text.muted, 'text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-md')}>
                          {product.variant?.name || product.variant_name || product.size || product.color}
                        </span>
                      )}
                    </div>
                    
                    {/* Variant Information */}
                    {(product.variant?.sku || product.sku) && (
                      <div className="flex flex-wrap gap-2">
                        <span className={combineThemeClasses(themeClasses.text.muted, 'text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 rounded-md font-medium')}>
                          SKU: {product.variant?.sku || product.sku}
                        </span>
                      </div>
                    )}
                    
                    {/* Product Attributes */}
                    {product.attributes && Object.keys(product.attributes).length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(product.attributes).map(([key, value]: [string, any]) => (
                          <span key={key} className={combineThemeClasses(themeClasses.text.muted, 'text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-md')}>
                            {key}: {String(value)}
                          </span>
                        ))}
                      </div>
                    )}
                    
                    {/* SKU fallback */}
                    {!(product.variant?.sku || product.sku) && (product.variant?.name || product.variant_name || product.size || product.color) && (
                      <span className={combineThemeClasses(themeClasses.text.muted, 'text-xs')}>
                        {product.variant?.name || product.variant_name || product.size || product.color}
                      </span>
                    )}
                  </div>
                  
                  {/* Price and Quantity */}
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center gap-3">
                      <span className={combineThemeClasses(themeClasses.text.secondary, 'text-sm font-medium')}>
                        {formatCurrency(product.current_price || product.price, subscription.currency)}
                      </span>
                      <span className="inline-flex items-center px-2 py-1 bg-primary text-white text-xs font-medium rounded-full shadow-sm">
                        <PackageIcon size={12} className="mr-1" />
                        Qty: {product.quantity || 1}
                      </span>
                    </div>
                    
                    {/* Total for this item */}
                    {(product.quantity && product.quantity > 1) || (product.quantity || 1) > 1 ? (
                      <span className={combineThemeClasses(themeClasses.text.primary, 'text-sm font-bold')}>
                        {formatCurrency((product.current_price || product.price) * (product.quantity || 1), subscription.currency)}
                      </span>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
            
            {subscription.products.length === 0 && (
              <div className="text-center py-6">
                <PackageIcon size={32} className="text-gray-400 mx-auto mb-3" />
                <p className={combineThemeClasses(themeClasses.text.muted, 'text-sm')}>
                  No products in this subscription
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Billing Summary Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className={combineThemeClasses(themeClasses.text.primary, 'font-medium text-sm')}>
            Billing Summary
          </h4>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowBillingSummary(!showBillingSummary);
            }}
            className="text-xs text-primary hover:text-primary-dark flex items-center gap-1"
          >
            <TagIcon size={12} />
            {showBillingSummary ? 'Hide' : 'Show'} Details
          </button>
        </div>
        
        {showBillingSummary && (
          <div className="space-y-2 bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
            <div className="flex justify-between text-sm">
              <span className={combineThemeClasses(themeClasses.text.secondary)}>Subtotal (Products)</span>
              <span className={combineThemeClasses(themeClasses.text.primary)}>
                {formatCurrency(subscription.subtotal || 0, subscription.currency)}
              </span>
            </div>
            
            <div className="flex justify-between text-sm">
              <span className={combineThemeClasses(themeClasses.text.secondary)}>
                Tax ({(subscription.tax_rate || 0) * 100}%)
              </span>
              <span className={combineThemeClasses(themeClasses.text.primary)}>
                {formatCurrency(subscription.tax_amount || 0, subscription.currency)}
              </span>
            </div>
            
            <div className="flex justify-between text-sm">
              <span className={combineThemeClasses(themeClasses.text.secondary)}>Shipping & Handling</span>
              <span className={combineThemeClasses(themeClasses.text.primary)}>
                {formatCurrency(subscription.shipping_cost || 0, subscription.currency)}
              </span>
            </div>
            
            <div className="flex justify-between text-sm">
              <span className={combineThemeClasses(themeClasses.text.secondary)}>Discounts Applied</span>
              <span className="text-green-600 dark:text-green-400">
                -{formatCurrency(subscription.discount_amount || 0, subscription.currency)}
              </span>
            </div>
            
            <div className="flex justify-between text-sm font-bold border-t pt-2">
              <span className={combineThemeClasses(themeClasses.text.primary)}>Total Monthly Amount</span>
              <span className={combineThemeClasses(themeClasses.text.primary)}>
                {formatCurrency(subscription.total || 0, subscription.currency)}
              </span>
            </div>
            
            {/* Billing Cycle Info */}
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
              <div className="flex justify-between text-xs">
                <span className={combineThemeClasses(themeClasses.text.secondary)}>Billing Cycle</span>
                <span className={combineThemeClasses(themeClasses.text.primary)}>
                  {subscription.billing_cycle?.charAt(0).toUpperCase() + subscription.billing_cycle?.slice(1)}
                </span>
              </div>
              <div className="flex justify-between text-xs mt-1">
                <span className={combineThemeClasses(themeClasses.text.secondary)}>Auto-renew</span>
                <span className={combineThemeClasses(themeClasses.text.primary)}>
                  {subscription.auto_renew ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              {subscription.next_billing_date && (
                <div className="flex justify-between text-xs mt-1">
                  <span className={combineThemeClasses(themeClasses.text.secondary)}>Next Billing</span>
                  <span className={combineThemeClasses(themeClasses.text.primary)}>
                    {new Date(subscription.next_billing_date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SubscriptionItem;
