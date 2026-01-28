import { apiClient } from './client';

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
    shipping_cost: number; // Updated field name
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
  // Simplified cost fields - using new field names
  shipping_cost?: number; // Updated field name
  tax_amount?: number;
  tax_rate?: number;
  // Enhanced fields for product management
  discounts?: AppliedDiscount[];
  subtotal?: number;
  total?: number;
}

// Subscription product interface
export interface SubscriptionProduct {
  id: string;
  subscription_id: string;
  product_id: string;
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

// Discount application request
export interface DiscountApplicationRequest {
  discount_code: string;
}

// Discount application response
export interface DiscountResponse {
  success: boolean;
  discount: AppliedDiscount;
  updated_subscription: Subscription;
  message?: string;
}

// Subscription details response for modal
export interface SubscriptionDetailsResponse {
  subscription: Subscription;
  products: SubscriptionProduct[];
  discounts: AppliedDiscount[];
}

// Create subscription request
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

// Update subscription request
export interface UpdateSubscriptionRequest {
  plan_id?: string;
  product_variant_ids?: string[];
  delivery_type?: 'standard' | 'express' | 'overnight';
  delivery_address_id?: string;
  billing_cycle?: 'weekly' | 'monthly' | 'yearly';
  auto_renew?: boolean;
  pause_reason?: string;
}

// Cost calculation request
export interface CostCalculationRequest {
  variant_ids: string[];
  delivery_type?: 'standard' | 'express' | 'overnight';
  delivery_address_id?: string;
  currency?: string;
}

// === ADMIN ENDPOINTS ===

// Trigger order processing (admin only)
export const triggerOrderProcessing = async () => {
  const response = await apiClient.post('/subscriptions/trigger-order-processing', {}, {});
  return response;
};

// Trigger notifications (admin only)
export const triggerNotifications = async () => {
  const response = await apiClient.post('/subscriptions/trigger-notifications', {}, {});
  return response;
};

// === COST CALCULATION ===

// Calculate subscription cost
export const calculateCost = async (request: CostCalculationRequest) => {
  const response = await apiClient.post('/subscriptions/calculate-cost', request, {});
  return response;
};

// === SUBSCRIPTION CRUD ===

// Create subscription
export const createSubscription = async (request: CreateSubscriptionRequest) => {
  try {
    const response = await apiClient.post('/subscriptions', request, {});
    return response; // Return response directly since apiClient already extracts .data
  } catch (error) {
    console.error('Error creating subscription:', error);
    throw error;
  }
};

// Get all subscriptions
export const getSubscriptions = async (page: number = 1, limit: number = 10): Promise<{
  subscriptions: Subscription[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}> => {
  const response = await apiClient.get('/subscriptions', { params: { page, limit } });
  return response; // Backend returns { subscriptions: [...], total: 10, page: 1, limit: 10, has_more: false }
};

// Get user subscriptions
export const getUserSubscriptions = async (page: number = 1, limit: number = 10) => {
  try {
    const response = await apiClient.get('/subscriptions', { params: { page, limit } });
    console.log(response,'response===+++')
    return response;
  } catch (error) {
    console.error('Error fetching user subscriptions:', error);
    throw error;
  }
};

// Get one subscription
export const getSubscription = async (id: string): Promise<Subscription> => {
  return withErrorHandling(async () => {
    const response = await apiClient.get(`/subscriptions/${id}`, {});
    console.log(response,'response===+++')
    return response;
  });
};

// Update subscription
export const updateSubscription = async (id: string, request: UpdateSubscriptionRequest) => {
  return withErrorHandling(async () => {
    const response = await apiClient.put(`/subscriptions/${id}`, request, {});
    return response; // Return response directly since apiClient already extracts .data
  });
};

// Delete/Cancel subscription
export const cancelSubscription = async (id: string, reason?: string) => {
  return withErrorHandling(async () => {
    const data = reason ? { reason } : {};
    const response = await apiClient.delete(`/subscriptions/${id}`, { data });
    return response;
  });
};

// Activate subscription (uses resume endpoint which handles both resume and activate)
export const activateSubscription = async (id: string) => {
  const response = await apiClient.post(`/subscriptions/${id}/resume`, {}, {});
  return response;
};

// Deprecated aliases - use addProducts and removeProducts directly
export const addProductsToSubscription = addProducts;
export const removeProductsFromSubscription = removeProducts;

// === PRODUCT MANAGEMENT ===

// Add products to subscription
export const addProducts = async (id: string, variantIds: string[]) => {
  const response = await apiClient.post(`/subscriptions/${id}/products`, { 
    variant_ids: variantIds 
  }, {});
  return response; // Return response directly since apiClient already extracts .data
};

// Remove products from subscription
export const removeProducts = async (id: string, variantIds: string[]) => {
  const response = await apiClient.delete(`/subscriptions/${id}/products`, { 
    data: { variant_ids: variantIds } 
  });
  return response; // Return response directly since apiClient already extracts .data
};

// Remove single product from subscription (new method for product management)
export const removeProduct = async (subscriptionId: string, productId: string): Promise<Subscription> => {
  return withErrorHandling(async () => {
    const response = await apiClient.delete(`/subscriptions/${subscriptionId}/products/${productId}`, {});
    return response;
  });
};

// Get subscription details for modal (new method)
export const getSubscriptionDetails = async (subscriptionId: string): Promise<SubscriptionDetailsResponse> => {
  return withErrorHandling(async () => {
    const response = await apiClient.get(`/subscriptions/${subscriptionId}/details`, {});
    return response;
  });
};

// === DISCOUNT MANAGEMENT ===

// Apply discount to subscription (new method)
export const applyDiscount = async (subscriptionId: string, discountCode: string): Promise<DiscountResponse> => {
  return withErrorHandling(async () => {
    const response = await apiClient.post(`/subscriptions/${subscriptionId}/discounts`, {
      discount_code: discountCode
    }, {});
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
};

// Remove discount from subscription (new method)
export const removeDiscount = async (subscriptionId: string, discountId: string): Promise<Subscription> => {
  return withErrorHandling(async () => {
    const response = await apiClient.delete(`/subscriptions/${subscriptionId}/discounts/${discountId}`, {});
    return response;
  });
};

// === QUANTITY MANAGEMENT ===

// Update variant quantity (set specific amount)
export const updateQuantity = async (id: string, variantId: string, quantity: number) => {
  const response = await apiClient.put(`/subscriptions/${id}/products/quantity`, {
    variant_id: variantId,
    quantity: quantity
  }, {});
  return response;
};

// Change variant quantity (increment/decrement)
export const changeQuantity = async (id: string, variantId: string, change: number) => {
  const response = await apiClient.patch(`/subscriptions/${id}/products/quantity`, {
    variant_id: variantId,
    change: change
  }, {});
  return response;
};

// Get all variant quantities
export const getQuantities = async (id: string) => {
  const response = await apiClient.get(`/subscriptions/${id}/products/quantities`, {});
  return response;
};

// === AUTO-RENEW MANAGEMENT ===

// Toggle auto-renew
export const toggleAutoRenew = async (id: string, autoRenew: boolean) => {
  const response = await apiClient.patch(`/subscriptions/${id}/auto-renew`, {}, { 
    params: { auto_renew: autoRenew } 
  });
  return response;
};

// === SUBSCRIPTION LIFECYCLE ===

// Pause subscription
export const pauseSubscription = async (id: string, reason?: string) => {
  const params = reason ? { pause_reason: reason } : {};
  const response = await apiClient.post(`/subscriptions/${id}/pause`, {}, { params });
  return response;
};

// Resume subscription
export const resumeSubscription = async (id: string) => {
  const response = await apiClient.post(`/subscriptions/${id}/resume`, {}, {});
  return response;
};

// === ORDERS & SHIPMENTS ===

// Process subscription shipment
export const processShipment = async (id: string) => {
  const response = await apiClient.post(`/subscriptions/${id}/process-shipment`, {}, {});
  return response;
};

// Get subscription orders
export const getOrders = async (id: string, page: number = 1, limit: number = 10) => {
  const response = await apiClient.get(`/subscriptions/${id}/orders`, { params: { page, limit } });
  return response;
};

// === CONVENIENCE FUNCTIONS ===

// Increment quantity by 1
export const incrementQuantity = async (id: string, variantId: string) => {
  return changeQuantity(id, variantId, 1);
};

// Decrement quantity by 1
export const decrementQuantity = async (id: string, variantId: string) => {
  return changeQuantity(id, variantId, -1);
};

// Default export for backwards compatibility
const SubscriptionAPI = {
  // Admin
  triggerOrderProcessing,
  triggerNotifications,
  
  // Cost calculation
  calculateCost,
  
  // CRUD
  createSubscription,
  getSubscriptions,
  getUserSubscriptions,
  getSubscription,
  updateSubscription,
  cancelSubscription,
  activateSubscription,
  
  // Products
  addProducts,
  removeProducts,
  addProductsToSubscription,
  removeProductsFromSubscription,
  removeProduct, // New method
  getSubscriptionDetails, // New method
  
  // Discounts
  applyDiscount, // New method
  removeDiscount, // New method
  
  // Quantities
  updateQuantity,
  changeQuantity,
  getQuantities,
  incrementQuantity,
  decrementQuantity,
  
  // Auto-renew
  toggleAutoRenew,
  
  // Lifecycle
  pauseSubscription,
  resumeSubscription,
  
  // Orders
  processShipment,
  getOrders,
};

export { SubscriptionAPI };
export default SubscriptionAPI;