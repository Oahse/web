import { apiClient   } from './client';


export class PaymentsAPI {
  static async getPaymentMethods() {
    return await apiClient.get('/users/me/payment-methods');
  }

  static async addPaymentMethod(data) {
    return await apiClient.post('/users/payment-methods', data);
  }

  static async updatePaymentMethod(paymentMethodId, data) {
    return await apiClient.put(`/users/payment-methods/${paymentMethodId}`, data);
  }

  static async deletePaymentMethod(paymentMethodId) {
    return await apiClient.delete(`/users/payment-methods/${paymentMethodId}`);
  }

  static async setDefaultPaymentMethod(paymentMethodId) {
    return await apiClient.put(`/users/payment-methods/${paymentMethodId}/default`);
  }
}

export default PaymentsAPI;
