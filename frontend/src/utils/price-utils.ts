// Price utilities for formatting and calculations
import { formatCurrency } from '../i18n';

export const formatPrice = (price: number, currency: string = 'USD'): string => {
  return formatCurrency(price, currency);
};

export const calculateDiscount = (originalPrice: number, discountPrice: number): number => {
  return originalPrice - discountPrice;
};

export const calculateDiscountPercentage = (originalPrice: number, discountPrice: number): number => {
  if (originalPrice === 0) return 0;
  return ((originalPrice - discountPrice) / originalPrice) * 100;
};

export const applyDiscount = (price: number, discountPercent: number): number => {
  return price * (1 - discountPercent / 100);
};

export const getBestPrice = (variant: any): number => {
  // Return the best available price for a variant
  if (variant.current_price) return variant.current_price;
  if (variant.discount_price) return variant.discount_price;
  if (variant.base_price) return variant.base_price;
  if (variant.price) return variant.price;
  return 0;
};

export const formatPriceWithFallback = (price: number | undefined | null, currency: string = 'USD'): string => {
  if (typeof price !== 'number' || isNaN(price)) {
    return formatCurrency(0, currency);
  }
  return formatCurrency(price, currency);
};
