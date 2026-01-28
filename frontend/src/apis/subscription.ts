import { apiClient } from './client';

interface SubscriptionData {
  plan_id: string;
  billing_cycle: string;
  product_variant_ids: string[];
  delivery_type: string;
  currency: string;
  auto_renew: boolean;
  delivery_address_id?: string;
  payment_method_id?: string;
  variant_quantities?: { [key: string]: number };
}

interface SubscriptionUpdateData {
  billing_cycle?: string;
  delivery_type?: string;
  delivery_address_id?: string;
  payment_method_id?: string;
  product_variant_ids?: string[];
}

class SubscriptionAPI {
  async createSubscription(data: SubscriptionData) {
    return apiClient.post('/subscriptions/', data);
  }

  async getUserSubscriptions(page = 1, limit = 10) {
    return apiClient.get(`/subscriptions/?page=${page}&limit=${limit}`);
  }

  async getSubscription(subscriptionId: string) {
    return apiClient.get(`/subscriptions/${subscriptionId}`);
  }

  async updateSubscription(subscriptionId: string, data: SubscriptionUpdateData) {
    return apiClient.put(`/subscriptions/${subscriptionId}`, data);
  }

  async deleteSubscription(subscriptionId: string) {
    return apiClient.delete(`/subscriptions/${subscriptionId}`);
  }

  async addProductsToSubscription(subscriptionId: string, variantIds: string[]) {
    return apiClient.post(`/subscriptions/${subscriptionId}/products`, variantIds);
  }

  async removeProductsFromSubscription(subscriptionId: string, variantIds: string[]) {
    return apiClient.delete(`/subscriptions/${subscriptionId}/products`, { data: variantIds });
  }

  async activateSubscription(subscriptionId: string) {
    return apiClient.post(`/subscriptions/${subscriptionId}/resume`);
  }

  async pauseSubscription(subscriptionId: string, reason?: string) {
    return apiClient.post(`/subscriptions/${subscriptionId}/pause`, { pause_reason: reason });
  }

  async resumeSubscription(subscriptionId: string) {
    return apiClient.post(`/subscriptions/${subscriptionId}/resume`);
  }

  // New methods for fetching shipping methods and calculating tax
  async getShippingMethods() {
    return apiClient.get('/admin/shipping-methods');
  }

  async calculateSubscriptionCost(data: any) {
    return apiClient.post('/subscriptions/calculate-cost', data);
  }

  async getSubscriptionOrders(subscriptionId: string, page = 1, limit = 10) {
    return apiClient.get(`/subscriptions/${subscriptionId}/orders?page=${page}&limit=${limit}`);
  }
}

// Export an instance instead of the class
export default new SubscriptionAPI();