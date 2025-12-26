/**
 * Refund API endpoints for painless refund processing
 */
import { apiClient } from './client';

export class RefundsAPI {
  /**
   * Check if an order is eligible for refund
   */
  static async checkRefundEligibility(orderId: string) {
    return await apiClient.get(`/refunds/orders/${orderId}/eligibility`);
  }

  /**
   * Request a refund for an order
   */
  static async requestRefund(orderId: string, refundData: any) {
    return await apiClient.post(`/refunds/orders/${orderId}/request`, refundData);
  }

  /**
   * Get user's refund history
   */
  static async getUserRefunds(params?: {
    status?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/refunds${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get detailed refund information
   */
  static async getRefundDetails(refundId: string) {
    return await apiClient.get(`/refunds/${refundId}`);
  }

  /**
   * Cancel a pending refund request
   */
  static async cancelRefund(refundId: string) {
    return await apiClient.put(`/refunds/${refundId}/cancel`);
  }

  /**
   * Get user's refund statistics
   */
  static async getRefundStats() {
    return await apiClient.get('/refunds/stats/summary');
  }
}

export default RefundsAPI;