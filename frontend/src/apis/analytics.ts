/**
 * Analytics API endpoints for business metrics
 */
import { apiClient } from './client';

export class AnalyticsAPI {
  /**
   * Track an analytics event
   */
  static async trackEvent(eventData: {
    session_id: string;
    event_type: string;
    data?: any;
    page_url?: string;
    page_title?: string;
    order_id?: string;
    product_id?: string;
    revenue?: number;
  }) {
    return await apiClient.post('/analytics/track', eventData);
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
    return await apiClient.get(url);
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
    return await apiClient.get(url);
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
    return await apiClient.get(url);
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
    return await apiClient.get(url);
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
    return await apiClient.get(url);
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
    return await apiClient.get(url);
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
    return await apiClient.get(url);
  }
}

export default AnalyticsAPI;