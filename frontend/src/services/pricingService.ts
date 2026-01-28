/**
 * Frontend Pricing Service
 * Handles price validation and formatting for checkout
 * NOTE: All actual pricing calculations are done server-side
 */

export interface PriceBreakdown {
  subtotal: number;
  shipping: {
    method_id: string;
    method_name: string;
    cost: number;
  };
  tax: {
    rate: number;
    amount: number;
    location: string;
  };
  discount?: {
    code: string;
    type: string;
    value: number;
    amount: number;
  };
  total: number;
  currency: string;
  calculated_at: string;
}

export interface PriceValidationResult {
  isValid: boolean;
  discrepancies: PriceDiscrepancy[];
  warnings: string[];
}

export interface PriceDiscrepancy {
  field: string;
  frontend: number;
  backend: number;
  difference: number;
  percentage: number;
}

export class PricingService {
  private static readonly TOLERANCE = 0.01; // 1 cent tolerance for rounding differences

  /**
   * Validate frontend prices against backend calculations
   * This is a security measure to detect price tampering
   */
  static validatePrices(
    frontendPricing: Partial<PriceBreakdown>,
    backendPricing: PriceBreakdown
  ): PriceValidationResult {
    const discrepancies: PriceDiscrepancy[] = [];
    const warnings: string[] = [];

    // Check subtotal
    if (frontendPricing.subtotal !== undefined) {
      const diff = Math.abs(frontendPricing.subtotal - backendPricing.subtotal);
      if (diff > this.TOLERANCE) {
        discrepancies.push({
          field: 'subtotal',
          frontend: frontendPricing.subtotal,
          backend: backendPricing.subtotal,
          difference: diff,
          percentage: (diff / backendPricing.subtotal) * 100
        });
      }
    }

    // Check shipping cost
    if (frontendPricing.shipping?.cost !== undefined) {
      const diff = Math.abs(frontendPricing.shipping.cost - backendPricing.shipping.cost);
      if (diff > this.TOLERANCE) {
        discrepancies.push({
          field: 'shipping',
          frontend: frontendPricing.shipping.cost,
          backend: backendPricing.shipping.cost,
          difference: diff,
          percentage: backendPricing.shipping.cost > 0 ? (diff / backendPricing.shipping.cost) * 100 : 0
        });
      }
    }

    // Check tax amount
    if (frontendPricing.tax?.amount !== undefined) {
      const diff = Math.abs(frontendPricing.tax.amount - backendPricing.tax.amount);
      if (diff > this.TOLERANCE) {
        discrepancies.push({
          field: 'tax',
          frontend: frontendPricing.tax.amount,
          backend: backendPricing.tax.amount,
          difference: diff,
          percentage: backendPricing.tax.amount > 0 ? (diff / backendPricing.tax.amount) * 100 : 0
        });
      }
    }

    // Check total
    if (frontendPricing.total !== undefined) {
      const diff = Math.abs(frontendPricing.total - backendPricing.total);
      if (diff > this.TOLERANCE) {
        discrepancies.push({
          field: 'total',
          frontend: frontendPricing.total,
          backend: backendPricing.total,
          difference: diff,
          percentage: (diff / backendPricing.total) * 100
        });
      }
    }

    // Generate warnings for significant discrepancies
    discrepancies.forEach(disc => {
      if (disc.percentage > 1) { // More than 1% difference
        warnings.push(
          `${disc.field} price mismatch: Frontend shows ${this.formatCurrency(disc.frontend)}, ` +
          `but backend calculated ${this.formatCurrency(disc.backend)} (${disc.percentage.toFixed(1)}% difference)`
        );
      }
    });

    return {
      isValid: discrepancies.length === 0,
      discrepancies,
      warnings
    };
  }

  /**
   * Format currency value for display
   */
  static formatCurrency(amount: number, currency: string = 'USD'): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  }

  /**
   * Calculate percentage discount
   */
  static calculateDiscountPercentage(originalPrice: number, discountedPrice: number): number {
    if (originalPrice <= 0) return 0;
    return Math.round(((originalPrice - discountedPrice) / originalPrice) * 100);
  }

  /**
   * Validate cart item pricing
   */
  static validateCartItemPricing(item: any): { isValid: boolean; issues: string[] } {
    const issues: string[] = [];

    // Check if unit price is positive
    if (item.unit_price <= 0) {
      issues.push(`Invalid unit price for ${item.variant?.name || 'item'}: ${item.unit_price}`);
    }

    // Check if quantity is positive
    if (item.quantity <= 0) {
      issues.push(`Invalid quantity for ${item.variant?.name || 'item'}: ${item.quantity}`);
    }

    // Check if total price calculation is correct
    const expectedTotal = item.unit_price * item.quantity;
    const actualTotal = item.total_price;
    const diff = Math.abs(expectedTotal - actualTotal);
    
    if (diff > this.TOLERANCE) {
      issues.push(
        `Price calculation error for ${item.variant?.name || 'item'}: ` +
        `Expected ${this.formatCurrency(expectedTotal)}, got ${this.formatCurrency(actualTotal)}`
      );
    }

    // Check for sale price consistency
    if (item.variant?.on_sale && item.variant?.sale_price) {
      if (Math.abs(item.unit_price - item.variant.sale_price) > this.TOLERANCE) {
        issues.push(
          `Sale price mismatch for ${item.variant.name}: ` +
          `Expected ${this.formatCurrency(item.variant.sale_price)}, got ${this.formatCurrency(item.unit_price)}`
        );
      }
    } else if (!item.variant?.on_sale && item.variant?.base_price) {
      if (Math.abs(item.unit_price - item.variant.base_price) > this.TOLERANCE) {
        issues.push(
          `Base price mismatch for ${item.variant.name}: ` +
          `Expected ${this.formatCurrency(item.variant.base_price)}, got ${this.formatCurrency(item.unit_price)}`
        );
      }
    }

    return {
      isValid: issues.length === 0,
      issues
    };
  }

  /**
   * Calculate estimated total from cart items (for display only)
   * NOTE: This is for UI purposes only - actual calculations are done server-side
   */
  static calculateEstimatedTotal(
    cartItems: any[],
    shippingCost: number = 0,
    taxRate: number = 0,
    discountAmount: number = 0
  ): number {
    const subtotal = cartItems.reduce((sum, item) => {
      return sum + (item.unit_price * item.quantity);
    }, 0);

    const taxAmount = subtotal * taxRate;
    const total = subtotal + shippingCost + taxAmount - discountAmount;

    return Math.max(0, total); // Ensure total is never negative
  }

  /**
   * Format price breakdown for display
   */
  static formatPriceBreakdown(pricing: PriceBreakdown): {
    subtotal: string;
    shipping: string;
    tax: string;
    discount?: string;
    total: string;
  } {
    return {
      subtotal: this.formatCurrency(pricing.subtotal, pricing.currency),
      shipping: this.formatCurrency(pricing.shipping.cost, pricing.currency),
      tax: this.formatCurrency(pricing.tax.amount, pricing.currency),
      discount: pricing.discount ? this.formatCurrency(pricing.discount.amount, pricing.currency) : undefined,
      total: this.formatCurrency(pricing.total, pricing.currency)
    };
  }

  /**
   * Check if pricing data is stale (older than 5 minutes)
   */
  static isPricingStale(calculatedAt: string): boolean {
    const calculatedTime = new Date(calculatedAt).getTime();
    const now = Date.now();
    const fiveMinutes = 5 * 60 * 1000; // 5 minutes in milliseconds

    return (now - calculatedTime) > fiveMinutes;
  }

  /**
   * Generate pricing summary text
   */
  static generatePricingSummary(pricing: PriceBreakdown): string {
    const formatted = this.formatPriceBreakdown(pricing);
    let summary = `Subtotal: ${formatted.subtotal}`;
    
    if (pricing.shipping.cost > 0) {
      summary += `, Shipping: ${formatted.shipping}`;
    }
    
    if (pricing.tax.amount > 0) {
      summary += `, Tax: ${formatted.tax}`;
    }
    
    if (pricing.discount) {
      summary += `, Discount: -${formatted.discount}`;
    }
    
    summary += `, Total: ${formatted.total}`;
    
    return summary;
  }
}

export default PricingService;