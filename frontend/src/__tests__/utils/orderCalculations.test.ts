/**
 * Tests for Order Calculations - Comprehensive test suite aligned with backend reality
 */
import { describe, it, expect } from 'vitest';
import {
  calculateOrderTotal,
  formatCurrency,
  getShippingCost,
  validateOrderCalculation,
  getTaxRate,
  formatTaxRate,
  OrderCalculationInput,
  OrderCalculationResult
} from '../../utils/orderCalculations';

describe('Order Calculations', () => {
  describe('calculateOrderTotal', () => {
    it('should calculate order total correctly with all components', () => {
      const input: OrderCalculationInput = {
        subtotal: 100.00,
        shipping_cost: 9.99,
        tax_rate: 0.08,
        discount_amount: 10.00
      };

      const result = calculateOrderTotal(input);

      expect(result.subtotal).toBe(100.00);
      expect(result.shipping_cost).toBe(9.99);
      expect(result.tax_rate).toBe(0.08);
      expect(result.tax_amount).toBe(8.00); // 8% of subtotal
      expect(result.discount_amount).toBe(10.00);
      expect(result.total_amount).toBe(107.99); // 100 + 9.99 + 8 - 10
    });

    it('should calculate order total without discount', () => {
      const input: OrderCalculationInput = {
        subtotal: 50.00,
        shipping_cost: 5.99,
        tax_rate: 0.10
      };

      const result = calculateOrderTotal(input);

      expect(result.subtotal).toBe(50.00);
      expect(result.shipping_cost).toBe(5.99);
      expect(result.tax_amount).toBe(5.00); // 10% of subtotal
      expect(result.discount_amount).toBe(0);
      expect(result.total_amount).toBe(60.99); // 50 + 5.99 + 5
    });

    it('should handle zero tax rate', () => {
      const input: OrderCalculationInput = {
        subtotal: 75.00,
        shipping_cost: 0,
        tax_rate: 0
      };

      const result = calculateOrderTotal(input);

      expect(result.tax_amount).toBe(0);
      expect(result.total_amount).toBe(75.00);
    });

    it('should handle free shipping', () => {
      const input: OrderCalculationInput = {
        subtotal: 150.00,
        shipping_cost: 0,
        tax_rate: 0.08,
        discount_amount: 15.00
      };

      const result = calculateOrderTotal(input);

      expect(result.shipping_cost).toBe(0);
      expect(result.tax_amount).toBe(12.00); // 8% of 150
      expect(result.total_amount).toBe(147.00); // 150 + 0 + 12 - 15
    });

    it('should round tax amount to nearest cent', () => {
      const input: OrderCalculationInput = {
        subtotal: 33.33,
        shipping_cost: 5.00,
        tax_rate: 0.0825 // 8.25%
      };

      const result = calculateOrderTotal(input);

      expect(result.tax_amount).toBe(2.75); // 33.33 * 0.0825 = 2.749725, rounded to 2.75
      expect(result.total_amount).toBe(41.08); // 33.33 + 5.00 + 2.75
    });

    it('should round total amount to nearest cent', () => {
      const input: OrderCalculationInput = {
        subtotal: 99.99,
        shipping_cost: 7.77,
        tax_rate: 0.0875, // 8.75%
        discount_amount: 5.55
      };

      const result = calculateOrderTotal(input);

      expect(result.tax_amount).toBe(8.75); // 99.99 * 0.0875 = 8.749125, rounded to 8.75
      expect(result.total_amount).toBe(110.96); // 99.99 + 7.77 + 8.75 - 5.55 = 110.96
    });

    it('should handle large discount amounts', () => {
      const input: OrderCalculationInput = {
        subtotal: 100.00,
        shipping_cost: 10.00,
        tax_rate: 0.08,
        discount_amount: 50.00
      };

      const result = calculateOrderTotal(input);

      expect(result.total_amount).toBe(68.00); // 100 + 10 + 8 - 50
    });

    it('should handle discount larger than subtotal', () => {
      const input: OrderCalculationInput = {
        subtotal: 50.00,
        shipping_cost: 5.00,
        tax_rate: 0.08,
        discount_amount: 75.00
      };

      const result = calculateOrderTotal(input);

      expect(result.total_amount).toBe(-16.00); // 50 + 5 + 4 - 75 = -16 (negative total)
    });

    it('should handle decimal precision correctly', () => {
      const input: OrderCalculationInput = {
        subtotal: 123.456,
        shipping_cost: 12.345,
        tax_rate: 0.0825,
        discount_amount: 10.111
      };

      const result = calculateOrderTotal(input);

      // Tax should be calculated on exact subtotal, then rounded
      expect(result.tax_amount).toBe(10.19); // 123.456 * 0.0825 = 10.185120, rounded to 10.19
      expect(result.total_amount).toBe(135.69); // All components rounded to nearest cent
    });
  });

  describe('formatCurrency', () => {
    it('should format USD currency by default', () => {
      expect(formatCurrency(99.99)).toBe('$99.99');
      expect(formatCurrency(0)).toBe('$0.00');
      expect(formatCurrency(1234.56)).toBe('$1,234.56');
    });

    it('should format different currencies', () => {
      expect(formatCurrency(99.99, 'EUR')).toBe('€99.99');
      expect(formatCurrency(99.99, 'GBP')).toBe('£99.99');
      expect(formatCurrency(99.99, 'CAD')).toBe('CA$99.99');
    });

    it('should handle negative amounts', () => {
      expect(formatCurrency(-25.50)).toBe('-$25.50');
    });

    it('should handle large amounts with commas', () => {
      expect(formatCurrency(1234567.89)).toBe('$1,234,567.89');
    });
  });

  describe('getShippingCost', () => {
    it('should get shipping_cost from order', () => {
      const order = {
        subtotal: 100,
        shipping_cost: 9.99,
        total: 109.99
      };

      expect(getShippingCost(order)).toBe(9.99);
    });

    it('should fallback to shipping_amount for backward compatibility', () => {
      const order = {
        subtotal: 100,
        shipping_amount: 12.50, // Legacy field name
        total: 112.50
      };

      expect(getShippingCost(order)).toBe(12.50);
    });

    it('should prefer shipping_cost over shipping_amount', () => {
      const order = {
        subtotal: 100,
        shipping_cost: 9.99,
        shipping_amount: 12.50, // Should be ignored
        total: 109.99
      };

      expect(getShippingCost(order)).toBe(9.99);
    });

    it('should return 0 for orders without shipping fields', () => {
      const order = {
        subtotal: 100,
        total: 100
      };

      expect(getShippingCost(order)).toBe(0);
    });

    it('should handle null/undefined orders', () => {
      expect(getShippingCost(null)).toBe(0);
      expect(getShippingCost(undefined)).toBe(0);
      expect(getShippingCost({})).toBe(0);
    });
  });

  describe('validateOrderCalculation', () => {
    it('should validate correct order calculations', () => {
      const order = {
        subtotal: 100.00,
        shipping_cost: 9.99,
        tax_amount: 8.00,
        discount_amount: 5.00,
        total_amount: 112.99 // 100 + 9.99 + 8 - 5
      };

      expect(validateOrderCalculation(order)).toBe(true);
    });

    it('should validate with legacy shipping_amount field', () => {
      const order = {
        subtotal: 100.00,
        shipping_amount: 9.99, // Legacy field
        tax_amount: 8.00,
        total_amount: 117.99 // 100 + 9.99 + 8
      };

      expect(validateOrderCalculation(order)).toBe(true);
    });

    it('should reject incorrect calculations', () => {
      const order = {
        subtotal: 100.00,
        shipping_cost: 9.99,
        tax_amount: 8.00,
        discount_amount: 5.00,
        total_amount: 120.00 // Incorrect total (should be 112.99)
      };

      expect(validateOrderCalculation(order)).toBe(false);
    });

    it('should allow small rounding differences', () => {
      const order = {
        subtotal: 100.00,
        shipping_cost: 9.99,
        tax_amount: 8.00,
        total_amount: 117.98 // Off by 1 cent (should be 117.99)
      };

      expect(validateOrderCalculation(order)).toBe(true); // Within tolerance
    });

    it('should handle missing fields gracefully', () => {
      const order = {
        subtotal: 100.00,
        total_amount: 100.00
      };

      expect(validateOrderCalculation(order)).toBe(true);
    });

    it('should handle orders with only required fields', () => {
      const order = {
        subtotal: 50.00,
        total_amount: 50.00
      };

      expect(validateOrderCalculation(order)).toBe(true);
    });

    it('should reject calculations with large discrepancies', () => {
      const order = {
        subtotal: 100.00,
        shipping_cost: 10.00,
        tax_amount: 8.00,
        total_amount: 150.00 // Way off (should be 118.00)
      };

      expect(validateOrderCalculation(order)).toBe(false);
    });
  });

  describe('getTaxRate', () => {
    it('should return tax_rate when available', () => {
      const order = {
        tax_rate: 0.08,
        tax_amount: 8.00,
        subtotal: 100.00
      };

      expect(getTaxRate(order)).toBe(0.08);
    });

    it('should calculate tax rate from tax_amount and subtotal', () => {
      const order = {
        tax_amount: 8.50,
        subtotal: 100.00
      };

      expect(getTaxRate(order)).toBe(0.085);
    });

    it('should return 0 when no tax information is available', () => {
      const order = {
        subtotal: 100.00,
        total_amount: 100.00
      };

      expect(getTaxRate(order)).toBe(0);
    });

    it('should return 0 when subtotal is 0', () => {
      const order = {
        tax_amount: 5.00,
        subtotal: 0
      };

      expect(getTaxRate(order)).toBe(0);
    });

    it('should handle missing tax_amount', () => {
      const order = {
        subtotal: 100.00
      };

      expect(getTaxRate(order)).toBe(0);
    });

    it('should prefer explicit tax_rate over calculated', () => {
      const order = {
        tax_rate: 0.10, // Explicit rate
        tax_amount: 8.00, // Would calculate to 0.08
        subtotal: 100.00
      };

      expect(getTaxRate(order)).toBe(0.10);
    });
  });

  describe('formatTaxRate', () => {
    it('should format tax rate as percentage', () => {
      expect(formatTaxRate(0.08)).toBe('8.0%');
      expect(formatTaxRate(0.0825)).toBe('8.3%');
      expect(formatTaxRate(0.10)).toBe('10.0%');
    });

    it('should handle zero tax rate', () => {
      expect(formatTaxRate(0)).toBe('0.0%');
    });

    it('should handle high precision tax rates', () => {
      expect(formatTaxRate(0.08375)).toBe('8.4%'); // Rounded to 1 decimal
      expect(formatTaxRate(0.123456)).toBe('12.3%');
    });

    it('should handle very small tax rates', () => {
      expect(formatTaxRate(0.001)).toBe('0.1%');
      expect(formatTaxRate(0.0001)).toBe('0.0%');
    });

    it('should handle large tax rates', () => {
      expect(formatTaxRate(0.25)).toBe('25.0%');
      expect(formatTaxRate(1.0)).toBe('100.0%');
    });
  });

  describe('Integration Tests', () => {
    it('should handle complete order flow', () => {
      // Calculate order
      const input: OrderCalculationInput = {
        subtotal: 129.99,
        shipping_cost: 12.50,
        tax_rate: 0.0875,
        discount_amount: 15.00
      };

      const result = calculateOrderTotal(input);

      // Validate calculation
      expect(validateOrderCalculation(result)).toBe(true);

      // Format currency
      expect(formatCurrency(result.total_amount)).toContain('$');

      // Get tax rate
      expect(getTaxRate(result)).toBe(0.0875);

      // Format tax rate
      expect(formatTaxRate(result.tax_rate)).toBe('8.8%');
    });

    it('should handle order with legacy fields', () => {
      const legacyOrder = {
        subtotal: 100.00,
        shipping_amount: 8.99, // Legacy field
        tax_amount: 8.00,
        discount_amount: 10.00,
        total_amount: 106.99
      };

      expect(validateOrderCalculation(legacyOrder)).toBe(true);
      expect(getShippingCost(legacyOrder)).toBe(8.99);
      expect(getTaxRate(legacyOrder)).toBe(0.08);
    });

    it('should handle free shipping and no tax scenario', () => {
      const input: OrderCalculationInput = {
        subtotal: 200.00,
        shipping_cost: 0, // Free shipping
        tax_rate: 0, // No tax
        discount_amount: 20.00
      };

      const result = calculateOrderTotal(input);

      expect(result.shipping_cost).toBe(0);
      expect(result.tax_amount).toBe(0);
      expect(result.total_amount).toBe(180.00);
      expect(validateOrderCalculation(result)).toBe(true);
    });

    it('should handle international order with high tax', () => {
      const input: OrderCalculationInput = {
        subtotal: 500.00,
        shipping_cost: 25.00,
        tax_rate: 0.20, // 20% VAT
        discount_amount: 0
      };

      const result = calculateOrderTotal(input);

      expect(result.tax_amount).toBe(100.00); // 20% of 500
      expect(result.total_amount).toBe(625.00);
      expect(formatTaxRate(result.tax_rate)).toBe('20.0%');
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle negative subtotal', () => {
      const input: OrderCalculationInput = {
        subtotal: -50.00,
        shipping_cost: 10.00,
        tax_rate: 0.08
      };

      const result = calculateOrderTotal(input);

      expect(result.tax_amount).toBe(-4.00); // 8% of -50
      expect(result.total_amount).toBe(-44.00);
    });

    it('should handle very large numbers', () => {
      const input: OrderCalculationInput = {
        subtotal: 999999.99,
        shipping_cost: 100.00,
        tax_rate: 0.08,
        discount_amount: 10000.00
      };

      const result = calculateOrderTotal(input);

      expect(result.tax_amount).toBe(80000.00);
      expect(result.total_amount).toBe(1070099.99);
    });

    it('should handle very small numbers', () => {
      const input: OrderCalculationInput = {
        subtotal: 0.01,
        shipping_cost: 0.01,
        tax_rate: 0.08
      };

      const result = calculateOrderTotal(input);

      expect(result.tax_amount).toBe(0.00); // Rounds to 0
      expect(result.total_amount).toBe(0.02);
    });

    it('should handle extreme tax rates', () => {
      const input: OrderCalculationInput = {
        subtotal: 100.00,
        shipping_cost: 0,
        tax_rate: 2.0 // 200% tax rate
      };

      const result = calculateOrderTotal(input);

      expect(result.tax_amount).toBe(200.00);
      expect(result.total_amount).toBe(300.00);
    });

    it('should handle null/undefined order in validation', () => {
      expect(validateOrderCalculation(null)).toBe(true); // No validation needed
      expect(validateOrderCalculation(undefined)).toBe(true);
      expect(validateOrderCalculation({})).toBe(true);
    });

    it('should handle precision issues with floating point arithmetic', () => {
      const input: OrderCalculationInput = {
        subtotal: 0.1 + 0.2, // 0.30000000000000004 in JavaScript
        shipping_cost: 0.1,
        tax_rate: 0.1
      };

      const result = calculateOrderTotal(input);

      // Should handle floating point precision correctly
      expect(result.subtotal).toBeCloseTo(0.3, 10);
      expect(result.total_amount).toBeCloseTo(0.43, 2);
    });
  });
});