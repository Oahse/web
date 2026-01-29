/**
 * Admin API endpoints
 * 
 * ACCESS LEVELS:
 * - Admin Only: All endpoints require admin role
 */

import { apiClient } from './client';

export class AdminAPI {
  /**
   * Get admin dashboard statistics
   * ACCESS: Admin Only - Requires admin role
   */
  static async getAdminStats() {
    return await apiClient.get('/v1/admin/stats', {});
  }

  /**
   * Get platform overview
   * ACCESS: Admin Only - Requires admin role
   */
  static async getPlatformOverview() {
    return await apiClient.get('/v1/admin/overview', {});
  }

  // User Management
  /**
   * Get all users with filters
   * ACCESS: Admin Only - Requires admin role
   */
  static async getUsers(params: {
    page?: number;
    limit?: number;
    role?: string;
    search?: string;
    status?: string;
    verified?: boolean;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.role) queryParams.append('role', params.role);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.verified !== undefined) queryParams.append('verified', params.verified.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/v1/admin/users${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Get user details
   */
  static async getUser(userId: string) {
    return await apiClient.get(`/v1/admin/users/${userId}`, {});
  }

  /**
   * Update user
   */
  static async updateUser(userId: string, updates: any) {
    return await apiClient.put(`/v1/admin/users/${userId}`, updates, {});
  }

  /**
   * Activate/Deactivate user
   */
  static async toggleUserStatus(userId: string, active: boolean) {
    return await apiClient.put(`/v1/admin/users/${userId}/status`, { active }, {});
  }

  /**
   * Verify user
   */
  static async verifyUser(userId: string) {
    return await apiClient.put(`/v1/admin/users/${userId}/verify`, {}, {});
  }

  /**
   * Delete user
   */
  static async deleteUser(userId: string) {
    return await apiClient.delete(`/v1/admin/users/${userId}`, {});
  }

  /**
   * Get user activity log
   */
  static async getUserActivity(userId: string, params: { page?: number; limit?: number }) {
    const queryParams = new URLSearchParams();
    
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/users/${userId}/activity${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Create a new user (admin only)
   */
  static async createUser(userData: any) {
    return await apiClient.post('/admin/users', userData, {});
  }

  // Product Management
  /**
   * Get all products for admin review
   */
  static async getAllProducts(params: {
    status?: string;
    category?: string;
    supplier?: string;
    search?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.category) queryParams.append('category', params.category);
    if (params?.supplier) queryParams.append('supplier', params.supplier);
    if (params?.search) queryParams.append('search', params.search);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/products${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Approve/Reject product
   */
  static async moderateProduct(productId: string, action: string, reason: string) {
    return await apiClient.put(`/admin/products/${productId}/moderate`, { action, reason }, {});
  }

  /**
   * Feature/Unfeature product
   */
  static async toggleProductFeature(productId: string, featured: boolean) {
    return await apiClient.put(`/admin/products/${productId}/feature`, { featured }, {});
  }

  // Order Management
  /**
   * Get all orders for admin oversight
   */
  static async getAllOrders(params: {
    status?: string;
    q?: string;
    supplier?: string;
    customer?: string;
    date_from?: string;
    date_to?: string;
    min_price?: number;
    max_price?: number;
    page?: number;
    limit?: number;
  }) {
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

    const url = `/v1/admin/orders${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Get all product variants for admin oversight
   */
  static async getAllVariants(params: {
    product_id?: string;
    search?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.product_id) queryParams.append('product_id', params.product_id);
    if (params?.search) queryParams.append('search', params.search);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/variants${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Update variant stock
   */
  static async updateVariantStock(variantId: string, stock: number) {
    return await apiClient.put(`/admin/variants/${variantId}/stock`, { stock }, {});
  }

  /**
   * Get order details
   */
  static async getOrder(orderId: string) {
    return await apiClient.get(`/v1/admin/orders/${orderId}`, {});
  }

  /**
   * Update order status
   */
  static async updateOrderStatus(orderId: string, status: string) {
    return await apiClient.put(`/v1/admin/orders/${orderId}/status`, { status }, {});
  }

  /**
   * Get order invoice (admin)
   */
  static async getOrderInvoice(orderId: string) {
    await apiClient.download(`/v1/admin/orders/${orderId}/invoice`, `invoice-${orderId}.pdf`);
  }

  /**
   * Get order disputes
   */
  static async getOrderDisputes(params: {
    status?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/disputes${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Resolve order dispute
   */
  static async resolveDispute(disputeId: string, resolution: any) {
    return await apiClient.put(`/admin/disputes/${disputeId}/resolve`, resolution, {});
  }

  // System Management
  static async getSalesTrend(days: number) {
    return await apiClient.get(`/analytics/sales-trend?days=${days}`, {});
  }

  /**
   * Get system health
   */
  static async getSystemHealth() {
    return await apiClient.get('/admin/system/health', {});
  }

  /**
   * Get system logs
   */
  static async getSystemLogs(params: {
    level?: string;
    service?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.level) queryParams.append('level', params.level);
    if (params?.service) queryParams.append('service', params.service);
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/system/logs${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Get audit logs
   */
  static async getAuditLogs(params: {
    user_id?: string;
    action?: string;
    resource?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.user_id) queryParams.append('user_id', params.user_id);
    if (params?.action) queryParams.append('action', params.action);
    if (params?.resource) queryParams.append('resource', params.resource);
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/admin/audit-logs${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Get addresses for a specific user
   */
  static async getAddressesByUser(userId: string) {
    return await apiClient.get(`/admin/users/${userId}/addresses`, {});
  }

  /**
   * Create a new address for a specific user
   */
  static async createAddressForUser(userId: string, addressData: any) {
    return await apiClient.post(`/admin/users/${userId}/addresses`, addressData, {});
  }

  /**
   * Update an address for a specific user
   */
  static async updateAddressForUser(userId: string, addressId: string, addressData: any) {
    return await apiClient.put(`/admin/users/${userId}/addresses/${addressId}`, addressData, {});
  }

  /**
   * Delete an address for a specific user
   */
  static async deleteAddressForUser(userId: string, addressId: string) {
    return await apiClient.delete(`/admin/users/${userId}/addresses/${addressId}`, {});
  }

  /**
   * Reset user password (admin action)
   */
  static async resetUserPassword(userId: string) {
    return await apiClient.post(`/admin/users/${userId}/reset-password`, {}, {});
  }

  /**
   * Deactivate user account (admin action)
   */
  static async deactivateUser(userId: string) {
    return await apiClient.post(`/admin/users/${userId}/deactivate`, {}, {});
  }

  /**
   * Activate user account (admin action)
   */
  static async activateUser(userId: string) {
    return await apiClient.post(`/admin/users/${userId}/activate`, {}, {});
  }

  // Inventory Management
  /**
   * Get all inventory items with filters
   */
  static async getInventoryItems(params: {
    page?: number;
    limit?: number;
    product_id?: string;
    location_id?: string;
    low_stock?: boolean;
    search?: string;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.product_id) queryParams.append('product_id', params.product_id);
    if (params?.location_id) queryParams.append('location_id', params.location_id);
    if (params?.low_stock !== undefined) queryParams.append('low_stock', params.low_stock.toString());
    if (params?.search) queryParams.append('search', params.search);

    const url = `/inventory${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Get inventory item by ID
   */
  static async getInventoryItem(inventoryId: string) {
    return await apiClient.get(`/inventory/${inventoryId}`, {});
  }

  /**
   * Get warehouse locations
   */
  static async getWarehouseLocations() {
    return await apiClient.get('/inventory/locations', {});
  }

  /**
   * Get warehouse location by ID
   */
  static async getWarehouseLocationById(locationId: string) {
    return await apiClient.get(`/inventory/locations/${locationId}`, {});
  }

  /**
   * Create warehouse location
   */
  static async createWarehouseLocation(locationData: any) {
    return await apiClient.post('/inventory/locations', locationData, {});
  }

  /**
   * Update warehouse location
   */
  static async updateWarehouseLocation(locationId: string, locationData: any) {
    return await apiClient.put(`/inventory/locations/${locationId}`, locationData, {});
  }

  /**
   * Delete warehouse location
   */
  static async deleteWarehouseLocation(locationId: string) {
    return await apiClient.delete(`/inventory/locations/${locationId}`, {});
  }

  /**
   * Create inventory item
   */
  static async createInventoryItem(inventoryData: any) {
    return await apiClient.post('/inventory', inventoryData, {});
  }

  /**
   * Update inventory item
   */
  static async updateInventoryItem(inventoryId: string, inventoryData: any) {
    return await apiClient.put(`/inventory/${inventoryId}`, inventoryData, {});
  }

  /**
   * Delete inventory item
   */
  static async deleteInventoryItem(inventoryId: string) {
    return await apiClient.delete(`/inventory/${inventoryId}`, {});
  }

  /**
   * Adjust stock
   */
  static async adjustStock(adjustmentData: any) {
    return await apiClient.post('/inventory/adjustments', adjustmentData, {});
  }

  /**
   * Get stock adjustments for inventory item
   */
  static async getStockAdjustments(inventoryId: string) {
    return await apiClient.get(`/inventory/${inventoryId}/adjustments`, {});
  }

  /**
   * Get all stock adjustments across all inventory items
   */
  static async getAllStockAdjustments() {
    return await apiClient.get(`/inventory/adjustments/all`, {});
  }

  // Shipping Methods Management
  /**
   * Get all shipping methods
   */
  static async getShippingMethods() {
    return await apiClient.get('/admin/shipping-methods', {});
  }

  /**
   * Get shipping method by ID
   */
  static async getShippingMethod(methodId: string) {
    return await apiClient.get(`/admin/shipping-methods/${methodId}`, {});
  }

  /**
   * Create shipping method
   */
  static async createShippingMethod(methodData: any) {
    return await apiClient.post('/admin/shipping-methods', methodData, {});
  }

  /**
   * Update shipping method
   */
  static async updateShippingMethod(methodId: string, methodData: any) {
    return await apiClient.put(`/admin/shipping-methods/${methodId}`, methodData, {});
  }

  /**
   * Delete shipping method
   */
  static async deleteShippingMethod(methodId: string) {
    return await apiClient.delete(`/admin/shipping-methods/${methodId}`, {});
  }
}

export default AdminAPI;
