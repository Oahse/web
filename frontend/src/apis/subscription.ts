import { apiClient } from './client';

class SubscriptionAPI {
  async createSubscription(data) {
    return apiClient.post('/subscriptions/', data);
  }

  async getUserSubscriptions(page = 1, limit = 10) {
    return apiClient.get(`/subscriptions/?page=${page}&limit=${limit}`);
  }

  async getSubscription(subscriptionId) {
    return apiClient.get(`/subscriptions/${subscriptionId}`);
  }

  async updateSubscription(subscriptionId, data) {
    return apiClient.put(`/subscriptions/${subscriptionId}`, data);
  }

  async deleteSubscription(subscriptionId) {
    return apiClient.delete(`/subscriptions/${subscriptionId}`);
  }

  async addProductsToSubscription(subscriptionId, variantIds) {
    return apiClient.post(`/subscriptions/${subscriptionId}/products`, variantIds);
  }

  async removeProductsFromSubscription(subscriptionId, variantIds) {
    return apiClient.delete(`/subscriptions/${subscriptionId}/products`, { data: variantIds });
  }
}

// Export an instance instead of the class
export default new SubscriptionAPI();