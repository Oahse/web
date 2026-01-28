import React, { useState } from 'react';
import { 
  TagIcon, 
  XIcon, 
  CheckIcon, 
  AlertCircleIcon,
  LoaderIcon,
  PlusIcon
} from 'lucide-react';
import { themeClasses, combineThemeClasses, getButtonClasses } from '../../utils/themeClasses';
import { formatCurrency } from '../../utils/orderCalculations';
import { toast } from 'react-hot-toast';

interface AppliedDiscount {
  id: string;
  code: string;
  type: 'percentage' | 'fixed_amount' | 'free_shipping';
  value: number;
  discount_amount: number;
  applied_at: string;
}

interface DiscountManagerProps {
  subscriptionId: string;
  currentDiscounts: AppliedDiscount[];
  onDiscountApply: (code: string) => Promise<void>;
  onDiscountRemove: (discountId: string) => Promise<void>;
  currency?: string;
  isLoading?: boolean;
}

export const DiscountManager: React.FC<DiscountManagerProps> = ({
  subscriptionId,
  currentDiscounts,
  onDiscountApply,
  onDiscountRemove,
  currency = 'USD',
  isLoading = false
}) => {
  const [showDiscountInput, setShowDiscountInput] = useState(false);
  const [discountCode, setDiscountCode] = useState('');
  const [isApplying, setIsApplying] = useState(false);
  const [removingDiscountId, setRemovingDiscountId] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleApplyDiscount = async () => {
    if (!discountCode.trim()) {
      setValidationError('Please enter a discount code');
      return;
    }

    // Basic validation
    if (discountCode.trim().length < 3) {
      setValidationError('Discount code must be at least 3 characters');
      return;
    }

    // Check if discount is already applied
    const isAlreadyApplied = currentDiscounts.some(
      discount => discount.code.toLowerCase() === discountCode.trim().toLowerCase()
    );

    if (isAlreadyApplied) {
      setValidationError('This discount code is already applied');
      return;
    }

    setIsApplying(true);
    setValidationError(null);

    try {
      await onDiscountApply(discountCode.trim());
      setDiscountCode('');
      setShowDiscountInput(false);
      toast.success('Discount applied successfully');
    } catch (error: any) {
      console.error('Failed to apply discount:', error);
      
      // Handle specific error messages
      const errorMessage = error?.message || error?.response?.data?.message || 'Failed to apply discount';
      
      if (errorMessage.toLowerCase().includes('invalid') || errorMessage.toLowerCase().includes('not found')) {
        setValidationError('Invalid discount code');
      } else if (errorMessage.toLowerCase().includes('expired')) {
        setValidationError('This discount code has expired');
      } else if (errorMessage.toLowerCase().includes('limit')) {
        setValidationError('This discount code has reached its usage limit');
      } else {
        setValidationError(errorMessage);
      }
      
      toast.error('Failed to apply discount');
    } finally {
      setIsApplying(false);
    }
  };

  const handleRemoveDiscount = async (discountId: string) => {
    setRemovingDiscountId(discountId);
    
    try {
      await onDiscountRemove(discountId);
      toast.success('Discount removed successfully');
    } catch (error) {
      console.error('Failed to remove discount:', error);
      toast.error('Failed to remove discount');
    } finally {
      setRemovingDiscountId(null);
    }
  };

  const formatDiscountValue = (discount: AppliedDiscount) => {
    switch (discount.type) {
      case 'percentage':
        return `${discount.value}% off`;
      case 'fixed_amount':
        return `${formatCurrency(discount.value, currency)} off`;
      case 'free_shipping':
        return 'Free shipping';
      default:
        return `${formatCurrency(discount.discount_amount, currency)} off`;
    }
  };

  const getDiscountIcon = (type: string) => {
    switch (type) {
      case 'free_shipping':
        return '🚚';
      case 'percentage':
        return '📊';
      case 'fixed_amount':
        return '💰';
      default:
        return '🏷️';
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleApplyDiscount();
    } else if (e.key === 'Escape') {
      setShowDiscountInput(false);
      setDiscountCode('');
      setValidationError(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className={combineThemeClasses(themeClasses.text.primary, 'font-medium text-sm')}>
          Discounts {currentDiscounts.length > 0 && `(${currentDiscounts.length})`}
        </h4>
        {!showDiscountInput && !isLoading && (
          <button
            onClick={() => setShowDiscountInput(true)}
            className={combineThemeClasses(
              'text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1 px-2 py-1 rounded hover:bg-blue-50 transition-colors'
            )}
          >
            <PlusIcon className="w-3 h-3" />
            Add Code
          </button>
        )}
      </div>

      {/* Applied Discounts */}
      {currentDiscounts.length > 0 ? (
        <div className="space-y-2">
          {currentDiscounts.map((discount) => (
            <div
              key={discount.id}
              className={combineThemeClasses(
                themeClasses.card.base,
                'p-3 flex items-center justify-between'
              )}
            >
              <div className="flex items-center gap-3">
                <span className="text-lg" role="img" aria-label="discount">
                  {getDiscountIcon(discount.type)}
                </span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={combineThemeClasses(
                      themeClasses.text.primary,
                      'font-medium text-sm'
                    )}>
                      {discount.code.toUpperCase()}
                    </span>
                    <CheckIcon className={combineThemeClasses(
                      themeClasses.text.success,
                      'w-4 h-4'
                    )} />
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={combineThemeClasses(
                      themeClasses.text.secondary,
                      'text-xs'
                    )}>
                      {formatDiscountValue(discount)}
                    </span>
                    <span className={combineThemeClasses(
                      themeClasses.text.muted,
                      'text-xs'
                    )}>
                      •
                    </span>
                    <span className={combineThemeClasses(
                      themeClasses.text.success,
                      'text-xs font-medium'
                    )}>
                      Saving {formatCurrency(discount.discount_amount, currency)}
                    </span>
                  </div>
                </div>
              </div>
              
              <button
                onClick={() => handleRemoveDiscount(discount.id)}
                disabled={removingDiscountId === discount.id}
                className={combineThemeClasses(
                  'text-red-600 hover:text-red-700 p-1 rounded hover:bg-red-50 transition-colors',
                  removingDiscountId === discount.id ? 'opacity-50 cursor-not-allowed' : ''
                )}
                title="Remove discount"
              >
                {removingDiscountId === discount.id ? (
                  <LoaderIcon className="w-4 h-4 animate-spin" />
                ) : (
                  <XIcon className="w-4 h-4" />
                )}
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className={combineThemeClasses(
          themeClasses.text.muted,
          'text-sm py-2'
        )}>
          No discounts applied
        </div>
      )}

      {/* Discount Input */}
      {showDiscountInput && (
        <div className={combineThemeClasses(
          themeClasses.card.base,
          'p-4 space-y-3'
        )}>
          <div className="flex items-center gap-2">
            <TagIcon className={combineThemeClasses(
              themeClasses.text.muted,
              'w-4 h-4'
            )} />
            <span className={combineThemeClasses(
              themeClasses.text.primary,
              'font-medium text-sm'
            )}>
              Apply Discount Code
            </span>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={discountCode}
                onChange={(e) => {
                  setDiscountCode(e.target.value);
                  setValidationError(null);
                }}
                onKeyPress={handleKeyPress}
                placeholder="Enter discount code"
                className={combineThemeClasses(
                  themeClasses.input.base,
                  validationError ? themeClasses.input.error : themeClasses.input.default,
                  'flex-1 text-sm uppercase'
                )}
                disabled={isApplying}
                autoFocus
              />
              <button
                onClick={handleApplyDiscount}
                disabled={isApplying || !discountCode.trim()}
                className={combineThemeClasses(
                  getButtonClasses('primary'),
                  'text-sm px-4 py-2',
                  (isApplying || !discountCode.trim()) ? 'opacity-50 cursor-not-allowed' : ''
                )}
              >
                {isApplying ? (
                  <div className="flex items-center gap-2">
                    <LoaderIcon className="w-4 h-4 animate-spin" />
                    Applying...
                  </div>
                ) : (
                  'Apply'
                )}
              </button>
              <button
                onClick={() => {
                  setShowDiscountInput(false);
                  setDiscountCode('');
                  setValidationError(null);
                }}
                disabled={isApplying}
                className={combineThemeClasses(
                  'text-gray-600 hover:text-gray-700 p-2 rounded hover:bg-gray-50 transition-colors',
                  isApplying ? 'opacity-50 cursor-not-allowed' : ''
                )}
              >
                <XIcon className="w-4 h-4" />
              </button>
            </div>

            {/* Validation Error */}
            {validationError && (
              <div className="flex items-center gap-2 text-sm text-red-600">
                <AlertCircleIcon className="w-4 h-4" />
                <span>{validationError}</span>
              </div>
            )}

            {/* Help Text */}
            <div className={combineThemeClasses(
              themeClasses.text.muted,
              'text-xs'
            )}>
              Enter a valid discount code to apply savings to your subscription.
              Press Enter to apply or Escape to cancel.
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-4">
          <LoaderIcon className={combineThemeClasses(
            themeClasses.text.muted,
            'w-5 h-5 animate-spin'
          )} />
          <span className={combineThemeClasses(
            themeClasses.text.secondary,
            'ml-2 text-sm'
          )}>
            Loading discounts...
          </span>
        </div>
      )}

      {/* Total Savings Summary */}
      {currentDiscounts.length > 0 && (
        <div className={combineThemeClasses(
          themeClasses.background.elevated,
          'rounded-lg p-3 border-l-4 border-green-500'
        )}>
          <div className="flex items-center justify-between">
            <span className={combineThemeClasses(
              themeClasses.text.primary,
              'font-medium text-sm'
            )}>
              Total Savings
            </span>
            <span className={combineThemeClasses(
              themeClasses.text.success,
              'font-bold text-sm'
            )}>
              {formatCurrency(
                currentDiscounts.reduce((total, discount) => total + discount.discount_amount, 0),
                currency
              )}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};