import React from 'react';
import { useLocale } from '../../store/LocaleContext';

interface PriceDisplayProps {
  /** The price amount to display */
  amount: number;
  /** Optional sale/discount price */
  saleAmount?: number | null;
  /** Show discount percentage badge */
  showDiscount?: boolean;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg' | 'xl';
  /** Additional CSS classes */
  className?: string;
  /** Show currency symbol only (no formatting) */
  symbolOnly?: boolean;
}

/**
 * Consistent price display component that handles:
 * - Currency formatting with locale support
 * - Sale price display with strikethrough
 * - Discount percentage calculation
 * - Multiple size variants
 */
export const PriceDisplay: React.FC<PriceDisplayProps> = ({
  amount,
  saleAmount,
  showDiscount = true,
  size = 'md',
  className = '',
  symbolOnly = false,
}) => {
  const { formatCurrency } = useLocale();

  // Calculate discount percentage
  const discountPercentage = saleAmount && amount > saleAmount 
    ? Math.round(((amount - saleAmount) / amount) * 100)
    : 0;

  // Size classes
  const sizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
  };

  const saleSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
    xl: 'text-lg',
  };

  const displayPrice = saleAmount || amount;
  const hasDiscount = saleAmount && saleAmount < amount;

  if (symbolOnly) {
    return (
      <span className={`font-bold text-primary ${sizeClasses[size]} ${className}`}>
        {formatCurrency(displayPrice)}
      </span>
    );
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Current/Sale Price */}
      <span className={`font-bold text-primary ${sizeClasses[size]}`}>
        {formatCurrency(displayPrice)}
      </span>

      {/* Original Price (if on sale) */}
      {hasDiscount && (
        <span className={`text-copy-light line-through ${saleSizeClasses[size]}`}>
          {formatCurrency(amount)}
        </span>
      )}

      {/* Discount Badge */}
      {hasDiscount && showDiscount && discountPercentage > 0 && (
        <span className="bg-error text-white text-xs font-medium px-2 py-1 rounded-full">
          -{discountPercentage}%
        </span>
      )}
    </div>
  );
};

/**
 * Simple price display without discount logic
 */
export const SimplePriceDisplay: React.FC<{
  amount: number;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}> = ({ amount, size = 'md', className = '' }) => {
  const { formatCurrency } = useLocale();

  const sizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
  };

  return (
    <span className={`${sizeClasses[size]} ${className}`}>
      {formatCurrency(amount)}
    </span>
  );
};