import { apiClient, TokenManager } from './client';


export class PaymentsAPI {
  static async getPaymentMethods() {
    console.log('PaymentsAPI: Making request to /payments/methods');
    console.log('PaymentsAPI: Token available:', !!TokenManager.getToken());
    try {
      const response = await apiClient.get('/payments/methods', {});
      console.log('PaymentsAPI.getPaymentMethods response:', response);
      return response;
    } catch (error) {
      console.error('PaymentsAPI: Error fetching payment methods:', error);
      throw error;
    }
  }

  static async addPaymentMethod(data: any) {
    return await apiClient.post('/payments/methods', data, {});
  }

  static async updatePaymentMethod(paymentMethodId: string, data: any) {
    return await apiClient.put(`/payments/methods/${paymentMethodId}`, data, {});
  }

  static async deletePaymentMethod(paymentMethodId: string) {
    return await apiClient.delete(`/payments/methods/${paymentMethodId}`, {});
  }

  static async setDefaultPaymentMethod(paymentMethodId: string) {
    return await apiClient.put(`/payments/methods/${paymentMethodId}/default`, {}, {});
  }
}

export default PaymentsAPI;
