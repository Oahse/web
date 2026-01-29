/**
 * CORRECTED: Cart API endpoints with all missing methods
 * Fixes: Issue 1.3 - Missing checkBulkStock method
 * 
 * ACCESS LEVELS:
 * - Authenticated: All cart operations require user login
 * - Public: Stock checking (no authentication required)
 */

import { apiClient } from './client';

export class CartAPI {
  /**
   * Get user's cart
   * ACCESS: Authenticated - Requires user login
   */
  static async getCart(country?: string, province?: string) {
    const params = new URLSearchParams();
    if (country) params.append('country', country);
    if (province && province !== 'null' && province !== 'undefined') {
      params.append('province', province);
    }
    
    const queryString = params.toString();
    const url = queryString ? `/cart?${queryString}` : '/cart';
    
    return await apiClient.get(url);
  }

  /**
   * Add item to cart
   * ACCESS: Authenticated - Requires user login
   */
  static async addToCart(item: any, country?: string, province?: string) {
    const _country = country || localStorage.getItem('detected_country') || 'US';
    const _province = province || localStorage.getItem('detected_province');
    
    const params = new URLSearchParams();
    if (_country) params.append('country', _country);
    if (_province && _province !== 'null' && _province !== 'undefined') {
      params.append('province', _province);
    }
    
    const queryString = params.toString();
    const url = queryString ? `/cart/add?${queryString}` : '/cart/add';
    
    return await apiClient.post(url, item);
  }

  /**
   * Update cart item quantity
   * ACCESS: Authenticated - Requires user login
   */
  static async updateCartItem(itemId: string, quantity: number, country?: string, province?: string) {
    const _country = country || localStorage.getItem('detected_country') || 'US';
    const _province = province || localStorage.getItem('detected_province');
    
    const params = new URLSearchParams();
    if (_country) params.append('country', _country);
    if (_province && _province !== 'null' && _province !== 'undefined') {
      params.append('province', _province);
    }
    
    const queryString = params.toString();
    const url = queryString ? `/cart/items/${itemId}?${queryString}` : `/cart/items/${itemId}`;
    
    return await apiClient.put(url, { quantity });
  }

  /**
   * Remove item from cart
   * ACCESS: Authenticated - Requires user login
   */
  static async removeFromCart(itemId: string) {
    return await apiClient.delete(`/cart/items/${itemId}`);
  }

  /**
   * Clear entire cart
   * ACCESS: Authenticated - Requires user login
   */
  static async clearCart() {
    return await apiClient.post('/cart/clear', {});
  }

  /**
   * Apply promo code to cart
   * ACCESS: Authenticated - Requires user login
   */
  static async applyPromocode(code: string) {
    return await apiClient.post('/cart/promocode', { code });
  }

  /**
   * FIXED: Check stock availability for multiple variants
   * ACCESS: Public - No authentication required
   * Issue 1.3: This method was missing and called from Checkout.tsx
   */
  static async checkBulkStock(items: Array<{ variant_id: string; quantity: number }>) {
    return await apiClient.post('/cart/check-stock', { items });
  }

  /**
   * Validate cart for checkout
   * ACCESS: Authenticated - Requires user login
   */
  static async validateCart() {
    return await apiClient.post('/cart/validate', {});
  }

  /**
   * Get shipping methods available for cart
   * ACCESS: Public - No authentication required
   */
  static async getShippingMethods(country?: string, province?: string) {
    const params = new URLSearchParams();
    if (country) params.append('country', country);
    if (province) params.append('province', province);
    
    const queryString = params.toString();
    const url = queryString ? `/cart/shipping-methods?${queryString}` : '/cart/shipping-methods';
    
    return await apiClient.get(url);
  }
}
