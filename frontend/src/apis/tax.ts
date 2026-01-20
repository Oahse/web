import { apiClient } from './client';

export interface TaxRate {
  id: string;
  country_code: string;
  country_name: string;
  province_code?: string;
  province_name?: string;
  tax_rate: number;
  tax_percentage: number;
  tax_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface TaxRateCreate {
  country_code: string;
  country_name: string;
  province_code?: string;
  province_name?: string;
  tax_rate: number;
  tax_name?: string;
  is_active: boolean;
}

export interface TaxRateUpdate {
  country_name?: string;
  province_name?: string;
  tax_rate?: number;
  tax_name?: string;
  is_active?: boolean;
}

export interface TaxType {
  value: string;
  label: string;
  usage_count: number;
}

export interface Country {
  country_code: string;
  country_name: string;
  rate_count: number;
}

export interface TaxCalculationRequest {
  subtotal: number;
  shipping?: number;
  shipping_address_id?: string;
  country_code?: string;
  state_code?: string;
  product_type?: string;
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
   * Calculate tax for checkout
   */
  static async calculateTax(taxData: TaxCalculationRequest): Promise<TaxCalculationResponse> {
    const response = await apiClient.post('/tax/calculate', taxData);
    return response.data;
  }

  /**
   * Get all tax rates (admin only)
   */
  static async getTaxRates(params?: {
    country_code?: string;
    province_code?: string;
    is_active?: boolean;
    search?: string;
    page?: number;
    per_page?: number;
  }): Promise<TaxRate[]> {
    const response = await apiClient.get('/tax/admin/tax-rates', { params });
    return response.data;
  }

  /**
   * Get countries with tax rates configured
   */
  static async getCountriesWithTaxRates(): Promise<Country[]> {
    const response = await apiClient.get('/tax/admin/tax-rates/countries');
    return response.data;
  }

  /**
   * Get available tax types from database
   */
  static async getAvailableTaxTypes(): Promise<TaxType[]> {
    const response = await apiClient.get('/tax/admin/tax-rates/tax-types');
    return response.data;
  }

  /**
   * Create new tax rate
   */
  static async createTaxRate(data: TaxRateCreate): Promise<TaxRate> {
    const response = await apiClient.post('/tax/admin/tax-rates', data);
    return response.data;
  }

  /**
   * Update existing tax rate
   */
  static async updateTaxRate(id: string, data: TaxRateUpdate): Promise<TaxRate> {
    const response = await apiClient.put(`/tax/admin/tax-rates/${id}`, data);
    return response.data;
  }

  /**
   * Delete tax rate
   */
  static async deleteTaxRate(id: string): Promise<void> {
    await apiClient.delete(`/tax/admin/tax-rates/${id}`);
  }
}

export default TaxAPI;