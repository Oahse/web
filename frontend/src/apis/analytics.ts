/**
 * Analytics API endpoints
 */

import { apiClient } from './client';
// import { 
//   DashboardData, 
//   AnalyticsFilters,
//   APIResponse 
// } from './types/analytics';

export class AnalyticsAPI {
  /**
   * Get dashboard data
   */
  static async getDashboardData(filters) {
    const queryParams = new URLSearchParams();
      
    if (typeof filters?.date_range === 'string') {
      queryParams.append('date_range', filters.date_range);
    } else if (filters?.date_range) {
      if (filters.date_range.start) queryParams.append('date_from', filters.date_range.start);
      if (filters.date_range.end) queryParams.append('date_to', filters.date_range.end);
    }
    if (filters?.category) queryParams.append('category', filters.category);
    if (filters?.supplier) queryParams.append('supplier', filters.supplier);

    const url = `/analytics/dashboard${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get real-time metrics
   */
  static async getRealTimeMetrics() {
    return await apiClient.get('/analytics/real-time');
  }

  /**
   * Get sales analytics
   */
  static async getSalesAnalytics(filters) {
    const queryParams = new URLSearchParams();
      
    if (filters?.date_range?.start) queryParams.append('date_from', filters.date_range.start);
    if (filters?.date_range?.end) queryParams.append('date_to', filters.date_range.end);
    if (filters?.category) queryParams.append('category', filters.category);
    if (filters?.supplier) queryParams.append('supplier', filters.supplier);
    if (filters?.group_by) queryParams.append('group_by', filters.group_by);

    const url = `/analytics/sales${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get user analytics
   */
  static async getUserAnalytics(filters) {
    const queryParams = new URLSearchParams();
      
    if (filters?.date_range?.start) queryParams.append('date_from', filters.date_range.start);
    if (filters?.date_range?.end) queryParams.append('date_to', filters.date_range.end);

    const url = `/analytics/users${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get product analytics
   */
  static async getProductAnalytics(filters) {
    const queryParams = new URLSearchParams();
      
    if (filters?.category) queryParams.append('category', filters.category);
    if (filters?.supplier) queryParams.append('supplier', filters.supplier);

    const url = `/analytics/products${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get conversion funnel analytics
   */
  static async getConversionFunnel(filters) {
    const queryParams = new URLSearchParams();
      
    if (filters?.date_range?.start) queryParams.append('date_from', filters.date_range.start);
    if (filters?.date_range?.end) queryParams.append('date_to', filters.date_range.end);

    const url = `/analytics/conversion-funnel${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get geographic analytics
   */
  static async getGeographicAnalytics(filters) {
    const queryParams = new URLSearchParams();
      
    if (filters?.date_range?.start) queryParams.append('date_from', filters.date_range.start);
    if (filters?.date_range?.end) queryParams.append('date_to', filters.date_range.end);

    const url = `/analytics/geo${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  // Supplier Analytics
  /**
   * Get supplier dashboard data
   */
  static async getSupplierDashboard(filters) {
    const queryParams = new URLSearchParams();
      
    if (filters?.date_range?.start) queryParams.append('date_from', filters.date_range.start);
    if (filters?.date_range?.end) queryParams.append('date_to', filters.date_range.end);

    const url = `/analytics/supplier${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get supplier product performance
   */
  static async getSupplierProductPerformance(filters) {
    const queryParams = new URLSearchParams();
      
    if (filters?.date_range?.start) queryParams.append('date_from', filters.date_range.start);
    if (filters?.date_range?.end) queryParams.append('date_to', filters.date_range.end);

    const url = `/analytics/supplier/products${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Export analytics data
   */
  static async exportAnalytics(data) {
    const queryParams = new URLSearchParams();
      
    queryParams.append('type', data.type);
    queryParams.append('format', data.format);
    
    if (data.filters?.date_range?.start) queryParams.append('date_from', data.filters.date_range.start);
    if (data.filters?.date_range?.end) queryParams.append('date_to', data.filters.date_range.end);
    if (data.filters?.category) queryParams.append('category', data.filters.category);
    if (data.filters?.supplier) queryParams.append('supplier', data.filters.supplier);

    const url = `/analytics/export?${queryParams.toString()}`;
    const filename = `${data.type}-analytics-${new Date().toISOString().split('T')[0]}.${data.format}`;
    
    await apiClient.download(url, filename);
  }

  /**
   * Track custom event
   */
  static async trackEvent(event) {
    return await apiClient.post('/analytics/events', event);
  }

  /**
   * Get performance metrics
   */
  static async getPerformanceMetrics() {
    return await apiClient.get('/analytics/performance');
  }
}

export default AnalyticsAPI;