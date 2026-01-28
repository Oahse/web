/**
 * Analytics API endpoints for business metrics
 */
import { apiClient } from './client';

export class AnalyticsAPI {
  /**
   * Track an analytics event
   */
  static async trackEvent(eventData: {

    event_type: string;
    data?: any;
    page_url?: string;
    page_title?: string;
    order_id?: string;
    product_id?: string;
    revenue?: number;
  }) {
    return await apiClient.post('/analytics/track', eventData, {});
  }

  /**
   * Get conversion rate metrics
   */
  static async getConversionRates(params?: {
    start_date?: string;
    end_date?: string;
    traffic_source?: string;
    days?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.traffic_source) queryParams.append('traffic_source', params.traffic_source);
    if (params?.days) queryParams.append('days', params.days.toString());

    const url = `/analytics/conversion-rates${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Get cart abandonment metrics
   */
  static async getCartAbandonment(params?: {
    start_date?: string;
    end_date?: string;
    days?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.days) queryParams.append('days', params.days.toString());

    const url = `/analytics/cart-abandonment${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Get time to purchase metrics
   */
  static async getTimeToPurchase(params?: {
    start_date?: string;
    end_date?: string;
    days?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.days) queryParams.append('days', params.days.toString());

    const url = `/analytics/time-to-purchase${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Get refund rate metrics
   */
  static async getRefundRates(params?: {
    start_date?: string;
    end_date?: string;
    days?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.days) queryParams.append('days', params.days.toString());

    const url = `/analytics/refund-rates${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Get repeat customer metrics
   */
  static async getRepeatCustomers(params?: {
    start_date?: string;
    end_date?: string;
    days?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.days) queryParams.append('days', params.days.toString());

    const url = `/analytics/repeat-customers${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Get comprehensive dashboard data
   */
  static async getDashboardData(params?: {
    start_date?: string;
    end_date?: string;
    days?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.days) queryParams.append('days', params.days.toString());

    const url = `/analytics/dashboard${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Get sales overview data for dashboard
   */
  static async getSalesOverview(params?: {
    start_date?: string;
    end_date?: string;
    days?: number;
    granularity?: 'daily' | 'weekly' | 'monthly';
    categories?: string[];
    regions?: string[];
    sales_channels?: string[];
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.days) queryParams.append('days', params.days.toString());
    if (params?.granularity) queryParams.append('granularity', params.granularity);
    if (params?.categories?.length) queryParams.append('categories', params.categories.join(','));
    if (params?.regions?.length) queryParams.append('regions', params.regions.join(','));
    if (params?.sales_channels?.length) queryParams.append('sales_channels', params.sales_channels.join(','));

    const url = `/analytics/sales-overview${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Get key performance indicators
   */
  static async getKPIs(params?: {
    start_date?: string;
    end_date?: string;
    days?: number;
    compare_previous?: boolean;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.days) queryParams.append('days', params.days.toString());
    if (params?.compare_previous !== undefined) queryParams.append('compare_previous', params.compare_previous.toString());

    const url = `/analytics/kpis${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url, {});
  }

  /**
   * Get recent activity (placeholder - uses admin stats for now)
   */
  static async getRecentActivity(params?: {
    limit?: number;
  }) {
    // For now, return empty data since this endpoint doesn't exist
    return { data: [] };
  }

  /**
   * Export analytics data (placeholder)
   */
  static async exportAnalytics(params: {
    type: string;
    format: string;
    filters?: any;
  }) {
    // For now, just show a message since this endpoint doesn't exist
    throw new Error('Export functionality not yet implemented');
  }
}

export default AnalyticsAPI;