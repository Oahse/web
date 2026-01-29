/**
 * Tax API endpoints
 * 
 * ACCESS LEVELS:
 * - Public: Tax calculation for orders
 * - Admin: Tax rate management, configuration
 */

import { apiClient } from './client';

export interface TaxCalculationRequest {
  subtotal: number;
  shipping: number;
  country_code?: string;
  state_code?: string;
  currency?: string;
}

export interface TaxCalculationResponse {
  tax_amount: number;
  tax_rate: number;
  tax_type: string;
  jurisdiction: string;
  currency: string;
  breakdown: any[];
}

export class TaxAPI {
  /**
   * Calculate tax for an order
   * ACCESS: Public - No authentication required
   */
  static async calculateTax(request: TaxCalculationRequest): Promise<TaxCalculationResponse> {
    const response = await apiClient.post('/v1/tax/calculate', request);
    return response.data;
  }

  /**
   * Get tax rates for a location (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async getTaxRates(params?: {
    country_code?: string;
    province_code?: string;
    is_active?: boolean;
    search?: string;
    page?: number;
    per_page?: number;
  }) {
    const queryParams = new URLSearchParams();
    
    if (params?.country_code) queryParams.append('country_code', params.country_code);
    if (params?.province_code) queryParams.append('province_code', params.province_code);
    if (params?.is_active !== undefined) queryParams.append('is_active', params.is_active.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.per_page) queryParams.append('per_page', params.per_page.toString());

    const url = `/v1/tax/admin/tax-rates${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Create tax rate (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async createTaxRate(data: {
    country_code: string;
    country_name: string;
    province_code?: string;
    province_name?: string;
    tax_rate: number;
    tax_name?: string;
    is_active?: boolean;
  }) {
    return await apiClient.post('/v1/tax/admin/tax-rates', data);
  }

  /**
   * Update tax rate (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async updateTaxRate(taxRateId: string, data: {
    country_name?: string;
    province_name?: string;
    tax_rate?: number;
    tax_name?: string;
    is_active?: boolean;
  }) {
    return await apiClient.put(`/v1/tax/admin/tax-rates/${taxRateId}`, data);
  }

  /**
   * Delete tax rate (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async deleteTaxRate(taxRateId: string) {
    return await apiClient.delete(`/v1/tax/admin/tax-rates/${taxRateId}`);
  }

  /**
   * Get countries with tax rates (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async getCountriesWithTaxRates() {
    return await apiClient.get('/v1/tax/admin/tax-rates/countries');
  }

  /**
   * Get available tax types (Admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async getAvailableTaxTypes() {
    return await apiClient.get('/v1/tax/admin/tax-rates/tax-types');
  }
}

export default TaxAPI;