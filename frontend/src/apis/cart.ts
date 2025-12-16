/**
 * Shopping Cart API endpoints
 */

import { apiClient } from './client';




export class CartAPI {
  static async getCart(access_token) {
    return await apiClient.get('/cart', {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async addToCart(item, access_token) {
    return await apiClient.post('/cart/add', item, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async updateCartItem(itemId, quantity, access_token) {
    return await apiClient.put(`/cart/update/${itemId}`, { quantity }, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async removeFromCart(itemId, access_token) {
    return await apiClient.delete(`/cart/remove/${itemId}`, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async clearCart(access_token) {
    return await apiClient.post('/cart/clear', {}, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async applyPromocode(code, access_token) {
    return await apiClient.post('/cart/promocode', { code }, {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async removePromocode(access_token) {
    return await apiClient.delete('/cart/promocode', {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async getCartItemCount(access_token) {
    return await apiClient.get('/cart/count', {
      headers: { 'Authorization': `Bearer ${access_token}` },
    });
  }

  static async validateCart(access_token) {
    return await apiClient.post('/cart/validate', {}, {
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