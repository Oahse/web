/**
 * Price Component
 * 
 * Automatically converts and formats prices based on user's locale
 */

import React from 'react';
import { useLocale } from '../../hooks/useLocale';

interface PriceProps {
  amount: number;
  sourceCurrency?: string;
  className?: string;
  showCurrency?: boolean;
}

export const Price: React.FC<PriceProps> = ({
  amount,
  sourceCurrency = 'USD',
  className = '',
  showCurrency = true,
}) => {
  const { formatCurrency } = useLocale();

  const formattedPrice = formatCurrency(amount, sourceCurrency);

  if (!showCurrency) {
    // Extract just the number part
    const numberOnly = formattedPrice.replace(/[^\d.,]/g, '');
    return <span className={className}>{numberOnly}</span>;
  }

  return <span className={className}>{formattedPrice}</span>;
};
