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
}

export default new SubscriptionAPI();