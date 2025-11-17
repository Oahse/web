/**
 * Orders API endpoints
 */

import { apiClient } from './client';
// import {
//   Order, 
//   CreateOrderRequest, 
//   OrderStatus,
//   PaginatedResponse,
//   APIResponse 

export class OrdersAPI {
  /**
   * Create new order
   */
  static async createOrder(orderData) {
    return await apiClient.post('/orders', orderData);
  }

  /**
   * Checkout - Place order from cart
   */
  static async checkout(checkoutData) {
    return await apiClient.post('/orders/checkout', checkoutData);
  }

  /**
   * Get user's orders
   */
  static async getOrders(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);

    const url = `/orders${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get order by ID
   */
  static async getOrder(orderId) {
    return await apiClient.get(`/orders/${orderId}`);
  }

  /**
   * Get order tracking information
   */
  static async getOrderTracking(orderId) {
    return await apiClient.get(`/orders/${orderId}/tracking`);
  }

  /**
   * Cancel order
   */
  static async cancelOrder(orderId, reason) {
    return await apiClient.put(`/orders/${orderId}/cancel`, { reason });
  }

  /**
   * Request order refund
   */
  static async requestRefund(orderId, data) {
    return await apiClient.post(`/orders/${orderId}/refund`, data);
  }

  /**
   * Get order invoice
   */
  static async getOrderInvoice(orderId) {
    await apiClient.download(`/orders/${orderId}/invoice`, `invoice-${orderId}.pdf`);
  }

  /**
   * Reorder (create new order from existing order)
   */
  static async reorder(orderId) {
    return await apiClient.post(`/orders/${orderId}/reorder`);
  }

  /**
   * Add order note
   */
  static async addOrderNote(orderId, note) {
    return await apiClient.post(`/orders/${orderId}/notes`, { note });
  }

  /**
   * Get order notes
   */
  static async getOrderNotes(orderId) {
    return await apiClient.get(`/orders/${orderId}/notes`);
  }

  // Supplier endpoints
  /**
   * Get supplier orders (Supplier only)
   */
  static async getSupplierOrders(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);

    return await apiClient.get(url);
  }

  /**
   * Update order status (Supplier/Admin only)
   */
  static async updateOrderStatus(orderId, data) {
    return await apiClient.put(`/orders/${orderId}/status`, data);
  }

  /**
   * Mark order as shipped (Supplier only)
   */
  static async markAsShipped(orderId, data) {
    return await apiClient.put(`/orders/${orderId}/ship`, data);
  }

  /**
   * Mark order as delivered (Supplier only)
   */
  static async markAsDelivered(orderId, data) {
    return await apiClient.put(`/orders/${orderId}/deliver`, data || {});
  }

  /**
   * Process refund (Supplier/Admin only)
   */
  static async processRefund(refundId, data) {
    return await apiClient.put(`/refunds/${refundId}/process`, data);
  }

  // Admin endpoints
  /**
   * Get all orders (Admin only)
   */
  static async getAllOrders(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.supplier_id) queryParams.append('supplier_id', params.supplier_id);
    if (params?.customer_id) queryParams.append('customer_id', params.customer_id);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);

    const url = `/admin/orders${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get order statistics (Admin only)
   */
  static async getOrderStatistics(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);
    if (params?.group_by) queryParams.append('group_by', params.group_by);

    const url = `/admin/orders/statistics${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Export orders (Admin only)
   */
  static async exportOrders(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.format) queryParams.append('format', params.format);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);

    const url = `/admin/orders/export${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const filename = `orders-export-${new Date().toISOString().split('T')[0]}.${params?.format || 'csv'}`;
    
    await apiClient.download(url, filename);
  }
}

export default OrdersAPI;