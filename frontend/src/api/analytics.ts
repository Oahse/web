/**
 * Analytics API endpoints
 * 
 * ACCESS LEVELS:
 * - Public: Event tracking (with user consent)
 * - Admin: All analytics data, reports, and insights
 */

import { apiClient } from './client';

export class AnalyticsAPI {
  /**
   * Track an event
   * ACCESS: Public - No authentication required (anonymous tracking allowed)
   */
  static async trackEvent(eventData: {
    event_type: string;
    user_id?: string;
    session_id?: string;
    properties?: Record<string, any>;
    timestamp?: string;
  }) {
    return await apiClient.post('/v1/analytics/track', eventData);
  }

  /**
   * Get conversion rates (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async getConversionRates(params?: {
    start_date?: string;
    end_date?: string;
    funnel_type?: string;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.funnel_type) queryParams.append('funnel_type', params.funnel_type);

    const url = `/v1/analytics/conversion-rates${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get cart abandonment data (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async getCartAbandonment(params?: {
    start_date?: string;
    end_date?: string;
    segment?: string;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.segment) queryParams.append('segment', params.segment);

    const url = `/v1/analytics/cart-abandonment${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get time to purchase analytics (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async getTimeToPurchase(params?: {
    start_date?: string;
    end_date?: string;
    segment?: string;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.segment) queryParams.append('segment', params.segment);

    const url = `/v1/analytics/time-to-purchase${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get refund rates (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async getRefundRates(params?: {
    start_date?: string;
    end_date?: string;
    product_category?: string;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.product_category) queryParams.append('product_category', params.product_category);

    const url = `/v1/analytics/refund-rates${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get repeat customers data (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async getRepeatCustomers(params?: {
    start_date?: string;
    end_date?: string;
    cohort_period?: string;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.cohort_period) queryParams.append('cohort_period', params.cohort_period);

    const url = `/v1/analytics/repeat-customers${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get dashboard data (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async getDashboardData(params?: {
    start_date?: string;
    end_date?: string;
    metrics?: string[];
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.metrics) {
      params.metrics.forEach(metric => queryParams.append('metrics', metric));
    }

    const url = `/v1/analytics/dashboard${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get sales trend (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async getSalesTrend(days: number = 30) {
    return await apiClient.get(`/v1/analytics/sales-trend?days=${days}`);
  }

  /**
   * Get sales overview (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async getSalesOverview(params?: {
    start_date?: string;
    end_date?: string;
    group_by?: string;
    include_refunds?: boolean;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.group_by) queryParams.append('group_by', params.group_by);
    if (params?.include_refunds !== undefined) queryParams.append('include_refunds', params.include_refunds.toString());

    const url = `/v1/analytics/sales-overview${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get KPIs (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async getKPIs(params?: {
    start_date?: string;
    end_date?: string;
    compare_period?: boolean;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.compare_period !== undefined) queryParams.append('compare_period', params.compare_period.toString());

    const url = `/v1/analytics/kpis${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }
}

export default AnalyticsAPI;