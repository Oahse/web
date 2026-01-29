/**
 * Consolidated Subscription API
 * Handles all subscription-related API calls with comprehensive error handling and retry logic
 * 
 * ACCESS LEVELS:
 * - Authenticated: All subscription CRUD operations, product management, quantity updates
 * - Admin: Trigger order processing, trigger notifications, advanced subscription management
 */

import { apiClient } from './client';

// === INTERFACES ===

// API Error interface
export interface APIError {
  message: string;
  code?: string;
  statusCode?: number;
  data?: any;
}

// Loading state interface
export interface LoadingState {
  isLoading: boolean;
  error: APIError | null;
}

// Retry configuration
interface RetryConfig {
  maxRetries: number;
  retryDelay: number;
  retryCondition?: (error: APIError) => boolean;
}

// Enhanced subscription interface with product management support
export interface Subscription {
  id: string;
  plan_id: string;
  status: 'active' | 'cancelled' | 'paused';
  price: number;
  currency: string;
  billing_cycle: 'weekly' | 'monthly' | 'yearly';
  auto_renew: boolean;
  next_billing_date?: string;
  created_at: string;
  updated_at?: string;
  products?: Array<{
    id: string;
    name: string;
    price: number;
    current_price?: number;
    image?: string;
  }>;
  variant_quantities?: { [variantId: string]: number };
  cost_breakdown?: {
    subtotal: number;
    shipping_cost: number;
    tax_amount: number;
    tax_rate: number;
    total_amount: number;
    currency: string;
    product_variants?: Array<{
      variant_id: string;
      name: string;
      price: number;
      quantity: number;
    }>;
  };
  // Simplified cost fields
  shipping_cost?: number;
  tax_amount?: number;
  tax_rate?: number;
  discounts?: AppliedDiscount[];
  subtotal?: number;
  total?: number;
}

// Subscription product interface
export interface SubscriptionProduct {
  id: string;
  subscription_id: string;
  product_id: string;
  variant_id: string;
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  image?: string;
  added_at: string;
}

// Applied discount interface
export interface AppliedDiscount {
  id: string;
  subscription_id: string;
  discount_id: string;
  discount_code: string;
  discount_type: 'PERCENTAGE' | 'FIXED_AMOUNT' | 'FREE_SHIPPING';
  discount_amount: number;
  applied_at: string;
}

// Request interfaces
export interface CreateSubscriptionRequest {
  plan_id: string;
  product_variant_ids: string[];
  variant_quantities?: { [variantId: string]: number };
  delivery_type?: 'standard' | 'express' | 'overnight';
  delivery_address_id?: string;
  payment_method_id?: string;
  currency?: string;
  billing_cycle?: 'weekly' | 'monthly' | 'yearly';
  auto_renew?: boolean;
}

export interface UpdateSubscriptionRequest {
  plan_id?: string;
  product_variant_ids?: string[];
  delivery_type?: 'standard' | 'express' | 'overnight';
  delivery_address_id?: string;
  billing_cycle?: 'weekly' | 'monthly' | 'yearly';
  auto_renew?: boolean;
  pause_reason?: string;
}

export interface CostCalculationRequest {
  variant_ids: string[];
  delivery_type?: 'standard' | 'express' | 'overnight';
  delivery_address_id?: string;
  currency?: string;
}

// Response interfaces
export interface SubscriptionDetailsResponse {
  subscription: Subscription;
  products: SubscriptionProduct[];
  discounts: AppliedDiscount[];
}

export interface DiscountResponse {
  success: boolean;
  discount: AppliedDiscount;
  updated_subscription: Subscription;
  message?: string;
}

export interface SubscriptionListResponse {
  subscriptions: Subscription[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

// === UTILITY FUNCTIONS ===

// Default retry configuration
const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  retryCondition: (error) => {
    // Retry on network errors and 5xx server errors
    return !!(error.code === 'CONNECTION_ERROR' || 
           error.code === 'TIMEOUT_ERROR' || 
           (error.statusCode && error.statusCode >= 500));
  }
};

// Utility function for API calls with error handling and retry logic
async function withErrorHandling<T>(
  apiCall: () => Promise<T>,
  retryConfig: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<T> {
  let lastError: APIError;
  
  for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
    try {
      return await apiCall();
    } catch (error: any) {
      lastError = error as APIError;
      
      // Don't retry on the last attempt or if retry condition is not met
      if (attempt === retryConfig.maxRetries || 
          !retryConfig.retryCondition?.(lastError)) {
        throw lastError;
      }
      
      // Wait before retrying with exponential backoff
      const delay = retryConfig.retryDelay * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError!;
}

// === SUBSCRIPTION API CLASS ===

export class SubscriptionAPI {
  // === ADMIN ENDPOINTS ===

  /**
   * Trigger order processing (admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async triggerOrderProcessing() {
    return await apiClient.post('/subscriptions/trigger-order-processing', {});
  }

  /**
   * Trigger notifications (admin only)
   * ACCESS: Admin - Requires admin authentication
   */
  static async triggerNotifications() {
    return await apiClient.post('/subscriptions/trigger-notifications', {});
  }

  // === COST CALCULATION ===

  /**
   * Calculate subscription cost
   * ACCESS: Authenticated - Requires user login
   */
  static async calculateCost(request: CostCalculationRequest) {
    return await apiClient.post('/subscriptions/calculate-cost', request);
  }

  // === SUBSCRIPTION CRUD ===

  /**
   * Create new subscription
   * ACCESS: Authenticated - Requires user login
   */
  static async createSubscription(request: CreateSubscriptionRequest): Promise<Subscription> {
    return withErrorHandling(async () => {
      const response = await apiClient.post('/subscriptions', request);
      return response;
    });
  }

  /**
   * Get all user subscriptions with pagination
   * ACCESS: Authenticated - Requires user login, returns only user's subscriptions
   */
  static async getSubscriptions(params?: {
    page?: number;
    limit?: number;
  }): Promise<SubscriptionListResponse> {
    const queryParams = {
      page: params?.page || 1,
      limit: params?.limit || 10
    };

    return await apiClient.get('/subscriptions', { params: queryParams });
  }

  /**
   * Get subscription by ID
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async getSubscription(subscriptionId: string): Promise<Subscription> {
    return withErrorHandling(async () => {
      const response = await apiClient.get(`/subscriptions/${subscriptionId}`);
      return response;
    });
  }

  /**
   * Update subscription
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async updateSubscription(subscriptionId: string, request: UpdateSubscriptionRequest): Promise<Subscription> {
    return withErrorHandling(async () => {
      const response = await apiClient.put(`/subscriptions/${subscriptionId}`, request);
      return response;
    });
  }

  /**
   * Cancel subscription
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async cancelSubscription(subscriptionId: string, reason?: string) {
    return withErrorHandling(async () => {
      const data = reason ? { reason } : {};
      const response = await apiClient.delete(`/subscriptions/${subscriptionId}`, { data });
      return response;
    });
  }

  // === SUBSCRIPTION LIFECYCLE ===

  /**
   * Pause subscription
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async pauseSubscription(subscriptionId: string, reason?: string) {
    const data = reason ? { pause_reason: reason } : {};
    return await apiClient.post(`/subscriptions/${subscriptionId}/pause`, data);
  }

  /**
   * Resume subscription
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async resumeSubscription(subscriptionId: string) {
    return await apiClient.post(`/subscriptions/${subscriptionId}/resume`, {});
  }

  /**
   * Activate subscription (alias for resume)
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async activateSubscription(subscriptionId: string) {
    return this.resumeSubscription(subscriptionId);
  }

  // === PRODUCT MANAGEMENT ===

  /**
   * Add products to subscription
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async addProducts(subscriptionId: string, variantIds: string[]): Promise<Subscription> {
    return withErrorHandling(async () => {
      const response = await apiClient.post(`/subscriptions/${subscriptionId}/products`, { 
        variant_ids: variantIds 
      });
      return response;
    });
  }

  /**
   * Remove products from subscription
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async removeProducts(subscriptionId: string, variantIds: string[]): Promise<Subscription> {
    return withErrorHandling(async () => {
      const response = await apiClient.delete(`/subscriptions/${subscriptionId}/products`, { 
        data: { variant_ids: variantIds } 
      });
      return response;
    });
  }

  /**
   * Remove single product from subscription
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async removeProduct(subscriptionId: string, productId: string): Promise<Subscription> {
    return withErrorHandling(async () => {
      const response = await apiClient.delete(`/subscriptions/${subscriptionId}/products/${productId}`);
      return response;
    });
  }

  /**
   * Get subscription details with products and discounts
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async getSubscriptionDetails(subscriptionId: string): Promise<SubscriptionDetailsResponse> {
    return withErrorHandling(async () => {
      const response = await apiClient.get(`/subscriptions/${subscriptionId}/details`);
      return response;
    });
  }

  // === QUANTITY MANAGEMENT ===

  /**
   * Update variant quantity (set specific amount)
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async updateVariantQuantity(subscriptionId: string, variantId: string, quantity: number): Promise<Subscription> {
    return withErrorHandling(async () => {
      const response = await apiClient.put(`/subscriptions/${subscriptionId}/products/quantity`, {
        variant_id: variantId,
        quantity: quantity
      });
      return response;
    });
  }

  /**
   * Change variant quantity (increment/decrement)
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async changeVariantQuantity(subscriptionId: string, variantId: string, change: number): Promise<Subscription> {
    return withErrorHandling(async () => {
      const response = await apiClient.patch(`/subscriptions/${subscriptionId}/products/quantity`, {
        variant_id: variantId,
        change: change
      });
      return response;
    });
  }

  /**
   * Get variant quantities
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async getVariantQuantities(subscriptionId: string) {
    return await apiClient.get(`/subscriptions/${subscriptionId}/products/quantities`);
  }

  /**
   * Increment quantity by 1
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async incrementQuantity(subscriptionId: string, variantId: string): Promise<Subscription> {
    return this.changeVariantQuantity(subscriptionId, variantId, 1);
  }

  /**
   * Decrement quantity by 1
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async decrementQuantity(subscriptionId: string, variantId: string): Promise<Subscription> {
    return this.changeVariantQuantity(subscriptionId, variantId, -1);
  }

  // === DISCOUNT MANAGEMENT ===

  /**
   * Apply discount to subscription
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async applyDiscount(subscriptionId: string, discountCode: string): Promise<DiscountResponse> {
    return withErrorHandling(async () => {
      const response = await apiClient.post(`/subscriptions/${subscriptionId}/discounts`, {
        discount_code: discountCode
      });
      return response;
    }, {
      ...DEFAULT_RETRY_CONFIG,
      retryCondition: (error) => {
        // Don't retry on validation errors (400, 422) or not found (404)
        if (error.statusCode === 400 || error.statusCode === 422 || error.statusCode === 404) {
          return false;
        }
        return DEFAULT_RETRY_CONFIG.retryCondition!(error);
      }
    });
  }

  /**
   * Remove discount from subscription
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async removeDiscount(subscriptionId: string, discountId: string): Promise<Subscription> {
    return withErrorHandling(async () => {
      const response = await apiClient.delete(`/subscriptions/${subscriptionId}/discounts/${discountId}`);
      return response;
    });
  }

  // === AUTO-RENEW MANAGEMENT ===

  /**
   * Toggle auto-renew
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async toggleAutoRenew(subscriptionId: string, autoRenew: boolean): Promise<Subscription> {
    return withErrorHandling(async () => {
      const response = await apiClient.patch(`/subscriptions/${subscriptionId}/auto-renew`, { 
        auto_renew: autoRenew 
      });
      return response;
    });
  }

  // === ORDERS & SHIPMENTS ===

  /**
   * Get subscription orders
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async getSubscriptionOrders(subscriptionId: string, params?: {
    page?: number;
    limit?: number;
  }) {
    const queryParams = {
      page: params?.page || 1,
      limit: params?.limit || 10
    };

    return await apiClient.get(`/subscriptions/${subscriptionId}/orders`, { params: queryParams });
  }

  /**
   * Process subscription shipment manually
   * ACCESS: Authenticated - Requires user login and ownership of subscription
   */
  static async processShipment(subscriptionId: string) {
    return await apiClient.post(`/subscriptions/${subscriptionId}/process-shipment`, {});
  }
}

// === FUNCTIONAL API EXPORTS (for backward compatibility) ===

// Admin functions
export const triggerOrderProcessing = SubscriptionAPI.triggerOrderProcessing;
export const triggerNotifications = SubscriptionAPI.triggerNotifications;

// Cost calculation
export const calculateCost = SubscriptionAPI.calculateCost;

// CRUD operations
export const createSubscription = SubscriptionAPI.createSubscription;
export const getSubscriptions = SubscriptionAPI.getSubscriptions;
export const getUserSubscriptions = SubscriptionAPI.getSubscriptions; // Alias
export const getSubscription = SubscriptionAPI.getSubscription;
export const updateSubscription = SubscriptionAPI.updateSubscription;
export const cancelSubscription = SubscriptionAPI.cancelSubscription;

// Lifecycle management
export const pauseSubscription = SubscriptionAPI.pauseSubscription;
export const resumeSubscription = SubscriptionAPI.resumeSubscription;
export const activateSubscription = SubscriptionAPI.activateSubscription;

// Product management
export const addProducts = SubscriptionAPI.addProducts;
export const removeProducts = SubscriptionAPI.removeProducts;
export const removeProduct = SubscriptionAPI.removeProduct;
export const getSubscriptionDetails = SubscriptionAPI.getSubscriptionDetails;

// Deprecated aliases (for backward compatibility)
export const addProductsToSubscription = SubscriptionAPI.addProducts;
export const removeProductsFromSubscription = SubscriptionAPI.removeProducts;

// Quantity management
export const updateQuantity = SubscriptionAPI.updateVariantQuantity;
export const updateVariantQuantity = SubscriptionAPI.updateVariantQuantity;
export const changeQuantity = SubscriptionAPI.changeVariantQuantity;
export const changeVariantQuantity = SubscriptionAPI.changeVariantQuantity;
export const getQuantities = SubscriptionAPI.getVariantQuantities;
export const getVariantQuantities = SubscriptionAPI.getVariantQuantities;
export const incrementQuantity = SubscriptionAPI.incrementQuantity;
export const decrementQuantity = SubscriptionAPI.decrementQuantity;

// Discount management
export const applyDiscount = SubscriptionAPI.applyDiscount;
export const removeDiscount = SubscriptionAPI.removeDiscount;

// Auto-renew management
export const toggleAutoRenew = SubscriptionAPI.toggleAutoRenew;

// Orders and shipments
export const getOrders = SubscriptionAPI.getSubscriptionOrders;
export const getSubscriptionOrders = SubscriptionAPI.getSubscriptionOrders;
export const processShipment = SubscriptionAPI.processShipment;

// Default export
export default SubscriptionAPI;