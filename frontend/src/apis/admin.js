/**
 * Admin API endpoints
 */

import { apiClient } from './client';


export class AdminAPI {
  /**
   * Get admin dashboard statistics
   */
  static async getAdminStats() {
    return await apiClient.get('/admin/stats');
  }

  /**
   * Get platform overview
   */
  static async getPlatformOverview() {
    return await apiClient.get('/admin/overview');
  }

  // User Management
  /**
   * Get all users with filters
   */
  static async getUsers(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.role) queryParams.append('role', params.role);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.verified !== undefined) queryParams.append('verified', params.verified.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/users${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get user details
   */
  static async getUser(userId) {
        return await apiClient.get(`/admin/users/${userId}`);  }

  /**
   * Update user
   */
  static async updateUser(userId, updates) {
    return await apiClient.put(`/admin/users/${userId}`, updates);
  }

  /**
   * Activate/Deactivate user
   */
  static async toggleUserStatus(userId, active) {
    return await apiClient.put(`/admin/users/${userId}/status`, { active });
  }

  /**
   * Verify user
   */
  static async verifyUser(userId) {
    return await apiClient.put(`/admin/users/${userId}/verify`);
  }

  /**
   * Delete user
   */
  static async deleteUser(userId) {
    return await apiClient.delete(`/admin/users/${userId}`);
  }

  /**
   * Get user activity log
   */
  static async getUserActivity(userId, params) {
    const queryParams = new URLSearchParams();
    
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/users/${userId}/activity${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Create a new user (admin only)
   */
  static async createUser(userData) {
    return await apiClient.post('/admin/users', userData);
  }

  // Product Management
  /**
   * Get all products for admin review
   */
  static async getAllProducts(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.category) queryParams.append('category', params.category);
    if (params?.supplier) queryParams.append('supplier', params.supplier);
    if (params?.search) queryParams.append('search', params.search);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/products${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Approve/Reject product
   */
  static async moderateProduct(productId, action, reason) {
    return await apiClient.put(`/admin/products/${productId}/moderate`, { action, reason });
  }

  /**
   * Feature/Unfeature product
   */
  static async toggleProductFeature(productId, featured) {
    return await apiClient.put(`/admin/products/${productId}/feature`, { featured });
  }

  // Order Management
  /**
   * Get all orders for admin oversight
   */
  static async getAllOrders(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.q) queryParams.append('q', params.q);
    if (params?.supplier) queryParams.append('supplier', params.supplier);
    if (params?.customer) queryParams.append('customer', params.customer);
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);
    if (params?.min_price) queryParams.append('min_price', params.min_price.toString());
    if (params?.max_price) queryParams.append('max_price', params.max_price.toString());
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/orders${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get all product variants for admin oversight
   */
  static async getAllVariants(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.product_id) queryParams.append('product_id', params.product_id);
    if (params?.search) queryParams.append('search', params.search);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/variants${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get order details
   */
  static async getOrder(orderId) {
    return await apiClient.get(`/admin/orders/${orderId}`);
  }  /**
   * Get order disputes
   */
  static async getOrderDisputes(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/disputes${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }



  /**
   * Resolve order dispute
   */
  static async resolveDispute(disputeId, resolution) {
    return await apiClient.put(`/admin/disputes/${disputeId}/resolve`, resolution);
  }

  // System Management
  static async getSalesTrend(days) {
    return await apiClient.get(`/analytics/sales-trend?days=${days}`);
  }

  /**
   * Get system health
   */
  static async getSystemHealth() {
    return await apiClient.get('/admin/system/health');
  }

  /**
   * Get system logs
   */
  static async getSystemLogs(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.level) queryParams.append('level', params.level);
    if (params?.service) queryParams.append('service', params.service);
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/system/logs${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get audit logs
   */
  static async getAuditLogs(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.user_id) queryParams.append('user_id', params.user_id);
    if (params?.action) queryParams.append('action', params.action);
    if (params?.resource) queryParams.append('resource', params.resource);
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/audit-logs${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Update system settings
   */
  static async updateSystemSettings(settings) {
    return await apiClient.put('/admin/system/settings', settings);
  }

  /**
   * Get system settings
   */
  static async getSystemSettings() {
    return await apiClient.get('/admin/system/settings');
  }

  /**
   * Export data
   */
  static async exportData(data) {
    const queryParams = new URLSearchParams();
    
    queryParams.append('type', data.type);
    queryParams.append('format', data.format);
    
    if (data.filters) {
      Object.entries(data.filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }

    const url = `/admin/export?${queryParams.toString()}`;
    const filename = `${data.type}-export-${new Date().toISOString().split('T')[0]}.${data.format}`;
    
    await apiClient.download(url, filename);
  }

  /**
   * Send system notification
   */
  static async sendSystemNotification(notification) {
    return await apiClient.post('/admin/notifications/send', notification);
  }
}

export default AdminAPI;