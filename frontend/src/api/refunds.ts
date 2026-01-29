/**
 * Refunds API endpoints
 * 
 * ACCESS LEVELS:
 * - Authenticated: Check eligibility, request refunds, view own refunds
 * - Admin: View all refunds, process refunds, refund statistics
 */

import { apiClient } from './client';

export interface RefundRequest {
  reason: string;
  items?: Array<{
    order_item_id: string;
    quantity: number;
    reason?: string;
  }>;
  amount?: number;
  return_required?: boolean;
  customer_notes?: string;
}

export class RefundsAPI {
  /**
   * Check refund eligibility for an order
   * ACCESS: Authenticated - Requires user login and ownership of order
   */
  static async checkRefundEligibility(orderId: string) {
    return await apiClient.get(`/v1/refunds/orders/${orderId}/eligibility`);
  }

  /**
   * Request a refund for an order
   * ACCESS: Authenticated - Requires user login and ownership of order
   */
  static async requestRefund(orderId: string, refundRequest: RefundRequest) {
    return await apiClient.post(`/v1/refunds/orders/${orderId}/request`, refundRequest);
  }

  /**
   * Get user's refunds
   * ACCESS: Authenticated - Requires user login, returns only user's refunds
   */
  static async getRefunds(params?: {
    status?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/v1/refunds${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get refund details
   * ACCESS: Authenticated - Requires user login and ownership of refund
   */
  static async getRefund(refundId: string) {
    return await apiClient.get(`/v1/refunds/${refundId}`);
  }

  /**
   * Cancel a refund request
   * ACCESS: Authenticated - Requires user login and ownership of refund
   */
  static async cancelRefund(refundId: string) {
    return await apiClient.put(`/v1/refunds/${refundId}/cancel`);
  }

  /**
   * Get refund statistics
   * ACCESS: Admin - Requires admin authentication
   */
  static async getRefundStats() {
    return await apiClient.get('/v1/refunds/stats/summary');
  }
}

export default RefundsAPI;