import { apiClient } from './client';

export interface ShippingMethod {
  id: string;
  name: string;
  description?: string;
  price: number;
  estimated_days: number;
  is_active: boolean;
  available_countries?: string[];
  restricted_countries?: string[];
  regions?: string[];
  min_order_amount?: number;
  max_weight_kg?: number;
  price_per_kg?: number;
  base_weight_kg: number;
  carrier?: string;
  tracking_url_template?: string;
  created_at: string;
  updated_at: string;
}

export interface ShippingMethodAvailability {
  method: ShippingMethod;
  available: boolean;
  reason?: string;
  calculated_price: number;
}

export interface ShippingCostCalculation {
  shipping_cost: number;
  country_code: string;
  order_amount: number;
  total_weight_kg: number;
  shipping_method_id?: string;
}

class ShippingAPI {
  /**
   * Get available shipping methods for a specific country
   */
  async getAvailableShippingMethods(
    countryCode: string,
    orderAmount: number = 0,
    totalWeightKg: number = 1.0
  ): Promise<ShippingMethodAvailability[]> {
    const params = new URLSearchParams({
      country_code: countryCode.toUpperCase(),
      order_amount: orderAmount.toString(),
      total_weight_kg: totalWeightKg.toString(),
    });

    const response = await apiClient.get(`/shipping/methods?${params}`);
    return response.data.data;
  }

  /**
   * Get all active shipping methods (no country filtering)
   */
  async getAllShippingMethods(): Promise<ShippingMethod[]> {
    const response = await apiClient.get('/shipping/methods');
    return response.data.data;
  }

  /**
   * Get a specific shipping method by ID
   */
  async getShippingMethod(methodId: string): Promise<ShippingMethod> {
    const response = await apiClient.get(`/shipping/methods/${methodId}`);
    return response.data.data;
  }

  /**
   * Calculate shipping cost for specific parameters
   */
  async calculateShippingCost(
    countryCode: string,
    orderAmount: number,
    totalWeightKg: number = 1.0,
    shippingMethodId?: string
  ): Promise<ShippingCostCalculation> {
    const params = new URLSearchParams({
      country_code: countryCode.toUpperCase(),
      order_amount: orderAmount.toString(),
      total_weight_kg: totalWeightKg.toString(),
    });

    if (shippingMethodId) {
      params.append('shipping_method_id', shippingMethodId);
    }

    const response = await apiClient.post(`/shipping/calculate?${params}`);
    return response.data.data;
  }

  /**
   * Create a new shipping method (Admin only)
   */
  async createShippingMethod(methodData: Partial<ShippingMethod>): Promise<ShippingMethod> {
    const response = await apiClient.post('/shipping/methods', methodData);
    return response.data.data;
  }

  /**
   * Update a shipping method (Admin only)
   */
  async updateShippingMethod(
    methodId: string,
    methodData: Partial<ShippingMethod>
  ): Promise<ShippingMethod> {
    const response = await apiClient.put(`/shipping/methods/${methodId}`, methodData);
    return response.data.data;
  }

  /**
   * Delete a shipping method (Admin only)
   */
  async deleteShippingMethod(methodId: string): Promise<{ deleted: boolean }> {
    const response = await apiClient.delete(`/shipping/methods/${methodId}`);
    return response.data.data;
  }
}

export default new ShippingAPI();