/**
 * Shopping Cart API endpoints
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
  static async getCart(access_token: string, country?: string, province?: string) {
    const params = new URLSearchParams();
    if (country) params.append('country', country);
    if (province && province !== 'null' && province !== 'undefined') {
      params.append('province', province);
    }
    
    const queryString = params.toString();
    const url = queryString ? `/v1/cart?${queryString}` : '/v1/cart';
    
    return await apiClient.get(url, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  /**
   * Add item to cart
   * ACCESS: Authenticated - Requires user login
   */
  static async addToCart(item: any, access_token: string) {
    const country = localStorage.getItem('detected_country') || 'US';
    const province = localStorage.getItem('detected_province');
    
    const params = new URLSearchParams();
    if (country) params.append('country', country);
    if (province && province !== 'null' && province !== 'undefined') {
      params.append('province', province);
    }
    
    const queryString = params.toString();
    const url = queryString ? `/v1/cart/add?${queryString}` : '/v1/cart/add';
    
    return await apiClient.post(url, item, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  /**
   * Update cart item quantity
   * ACCESS: Authenticated - Requires user login
   */
  static async updateCartItem(itemId: string, quantity: number, access_token: string) {
    const country = localStorage.getItem('detected_country') || 'US';
    const province = localStorage.getItem('detected_province');
    
    const params = new URLSearchParams();
    if (country) params.append('country', country);
    if (province && province !== 'null' && province !== 'undefined') {
      params.append('province', province);
    }
    
    const queryString = params.toString();
    const url = queryString ? `/v1/cart/items/${itemId}?${queryString}` : `/v1/cart/items/${itemId}`;
    
    return await apiClient.put(url, { quantity }, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  /**
   * Remove item from cart
   * ACCESS: Authenticated - Requires user login
   */
  static async removeFromCart(itemId: string, access_token: string) {
    return await apiClient.delete(`/v1/cart/items/${itemId}`, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  /**
   * Clear entire cart
   * ACCESS: Authenticated - Requires user login
   */
  static async clearCart(access_token: string) {
    return await apiClient.post('/v1/cart/clear', {}, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  /**
   * Apply promo code to cart
   * ACCESS: Authenticated - Requires user login
   */
  static async applyPromocode(code: string, access_token: string) {
    return await apiClient.post('/v1/cart/promocode', { code }, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  /**
   * Remove promo code from cart
   * ACCESS: Authenticated - Requires user login
   */
  static async removePromocode(access_token: string) {
    return await apiClient.delete('/v1/cart/promocode', {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  /**
   * Check stock availability for a variant
   * ACCESS: Public - No authentication required
   */
  static async checkStock(variantId, quantity) {
    // Guard against undefined/null variantId
    if (!variantId || variantId === 'undefined' || variantId === 'null') {
      throw new Error('Invalid variant ID provided');
    }
    
    return await apiClient.get(`/v1/inventory/check-stock/${variantId}?quantity=${quantity}`);
  }

  /**
   * Check stock for multiple items at once (for Checkout)
   * ACCESS: Public - No authentication required
   */
  static async checkBulkStock(items) {
    // Validate items array
    if (!Array.isArray(items) || items.length === 0) {
      throw new Error('Invalid items array provided');
    }
    
    // Validate each item
    const validatedItems = items.map(item => {
      if (!item.variant_id || !item.quantity) {
        throw new Error('Each item must have variant_id and quantity');
      }
      return {
        variant_id: item.variant_id,
        quantity: item.quantity
      };
    });
    
    return await apiClient.post('/v1/inventory/check-stock/bulk', validatedItems);
  }

  /**
   * Get cart item count
   * ACCESS: Authenticated - Requires user login
   */
  static async getCartItemCount(access_token) {
    return await apiClient.get('/v1/cart/count', {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async validateCart(access_token) {
    const country = localStorage.getItem('detected_country') || 'US';
    const province = localStorage.getItem('detected_province');
    
    const params = new URLSearchParams();
    if (country) params.append('country', country);
    if (province && province !== 'null' && province !== 'undefined') {
      params.append('province', province);
    }
    
    const queryString = params.toString();
    const url = queryString ? `/v1/cart/validate?${queryString}` : '/v1/cart/validate';
    
    return await apiClient.post(url, {}, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async getShippingOptions(address, access_token) {
    return await apiClient.post('/cart/shipping-options', address, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async calculateTotals(data, access_token) {
    return await apiClient.post('/cart/calculate', data, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async saveForLater(itemId, access_token) {
    return await apiClient.post(`/cart/items/${itemId}/save-for-later`, {}, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async moveToCart(itemId, access_token) {
    return await apiClient.post(`/cart/items/${itemId}/move-to-cart`, {}, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async getSavedItems(access_token) {
    return await apiClient.get('/cart/saved-items', {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async mergeCart(guestCartItems, access_token) {
    return await apiClient.post('/cart/merge', { items: guestCartItems }, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async getCheckoutSummary(access_token) {
    return await apiClient.get('/cart/checkout-summary', {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }
}

export default CartAPI;