/**
 * Order calculation utilities for simplified pricing structure
 */

export interface OrderCalculationInput {
  subtotal: number;
  shipping_cost: number;
  tax_rate: number;
  discount_amount?: number;
}

export interface OrderCalculationResult {
  subtotal: number;
  shipping_cost: number;
  tax_rate: number;
  tax_amount: number;
  discount_amount: number;
  total_amount: number;
}

/**
 * Calculate order total using simplified pricing structure.
 * Formula: subtotal + shipping + tax - discount = total
 * 
 * @param input - Order calculation input
 * @returns Calculated order breakdown
 */
export function calculateOrderTotal(input: OrderCalculationInput): OrderCalculationResult {
  const { subtotal, shipping_cost, tax_rate, discount_amount = 0 } = input;
  
  // Calculate tax on subtotal only (not including shipping)
  const tax_amount = Math.round(subtotal * tax_rate * 100) / 100;
  
  // Calculate final total: subtotal + shipping + tax - discount
  const total_amount = Math.round((subtotal + shipping_cost + tax_amount - discount_amount) * 100) / 100;
  
  return {
    subtotal,
    shipping_cost,
    tax_rate,
    tax_amount,
    discount_amount,
    total_amount
  };
}

/**
 * Format currency amount
 */
export function formatCurrency(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency
  }).format(amount);
}

/**
 * Get shipping cost with backward compatibility
 */
export function getShippingCost(order: any): number {
  return order?.shipping_cost || order?.shipping_amount || 0;
}

/**
 * Validate order calculation
 */
export function validateOrderCalculation(order: any): boolean {
  const subtotal = order.subtotal || 0;
  const shipping = getShippingCost(order);
  const tax = order.tax_amount || 0;
  const discount = order.discount_amount || 0;
  const total = order.total_amount || 0;
  
  const expectedTotal = subtotal + shipping + tax - discount;
  const difference = Math.abs(total - expectedTotal);
  
  // Allow for small rounding differences (1 cent)
  return difference < 0.01;
}

/**
 * Get tax rate from order
 */
export function getTaxRate(order: any): number {
  if (order.tax_rate) {
    return order.tax_rate;
  }
  
  // Calculate tax rate from tax amount and subtotal if available
  if (order.tax_amount && order.subtotal && order.subtotal > 0) {
    return order.tax_amount / order.subtotal;
  }
  
  return 0;
}

/**
 * Format tax rate as percentage
 */
export function formatTaxRate(taxRate: number): string {
  return `${(taxRate * 100).toFixed(1)}%`;
}