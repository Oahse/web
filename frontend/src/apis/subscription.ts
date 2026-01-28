import { apiClient } from './client';

// Simple subscription interface
export interface Subscription {
  id: string;
  plan_id: string;
  status: 'active' | 'cancelled' | 'paused';
  price: number;
  currency: string;
  billing_cycle: 'monthly' | 'yearly';
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
    tax_amount: number;
    delivery_cost: number;
    total_amount: number;
  };
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
}

// Update subscription request
export interface UpdateSubscriptionRequest {
  plan_id?: string;
  product_variant_ids?: string[];
  delivery_type?: 'standard' | 'express' | 'overnight';
  delivery_address_id?: string;
  billing_cycle?: 'monthly' | 'yearly';
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
  return response.data;
};

// Trigger notifications (admin only)
export const triggerNotifications = async () => {
  const response = await apiClient.post('/subscriptions/trigger-notifications', {}, {});
  return response.data;
};

// === COST CALCULATION ===

// Calculate subscription cost
export const calculateCost = async (request: CostCalculationRequest) => {
  const response = await apiClient.post('/subscriptions/calculate-cost', request, {});
  return response.data;
};

// === SUBSCRIPTION CRUD ===

// Create subscription
export const createSubscription = async (request: CreateSubscriptionRequest) => {
  try {
    const response = await apiClient.post('/subscriptions', request, {});
    return response.data;
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
  return response.data;
};

// Get user subscriptions (alias for getSubscriptions for backwards compatibility)
export const getUserSubscriptions = async (page: number = 1, limit: number = 10) => {
  try {
    const response = await apiClient.get('/subscriptions', { params: { page, limit } });
    return {
      data: response.data.data // Extract the nested data structure from backend
    };
  } catch (error) {
    console.error('Error fetching user subscriptions:', error);
    throw error;
  }
};

// Get one subscription
export const getSubscription = async (id: string): Promise<Subscription> => {
  const response = await apiClient.get(`/subscriptions/${id}`, {});
  return response.data;
};

// Update subscription
export const updateSubscription = async (id: string, request: UpdateSubscriptionRequest) => {
  const response = await apiClient.put(`/subscriptions/${id}`, request, {});
  return response.data;
};

// Delete/Cancel subscription
export const cancelSubscription = async (id: string, reason?: string) => {
  const data = reason ? { reason } : {};
  const response = await apiClient.delete(`/subscriptions/${id}`, { data });
  return response.data;
};

// Activate subscription (uses resume endpoint which handles both resume and activate)
export const activateSubscription = async (id: string) => {
  const response = await apiClient.post(`/subscriptions/${id}/resume`, {}, {});
  return response.data;
};

// Add products to subscription (alias for addProducts)
export const addProductsToSubscription = async (id: string, variantIds: string[]) => {
  return addProducts(id, variantIds);
};

// Remove products from subscription (alias for removeProducts)
export const removeProductsFromSubscription = async (id: string, variantIds: string[]) => {
  return removeProducts(id, variantIds);
};

// === PRODUCT MANAGEMENT ===

// Add products to subscription
export const addProducts = async (id: string, variantIds: string[]) => {
  const response = await apiClient.post(`/subscriptions/${id}/products`, { 
    variant_ids: variantIds 
  }, {});
  return response.data;
};

// Remove products from subscription
export const removeProducts = async (id: string, variantIds: string[]) => {
  const response = await apiClient.delete(`/subscriptions/${id}/products`, { 
    data: { variant_ids: variantIds } 
  });
  return response.data;
};

// === QUANTITY MANAGEMENT ===

// Update variant quantity (set specific amount)
export const updateQuantity = async (id: string, variantId: string, quantity: number) => {
  const response = await apiClient.put(`/subscriptions/${id}/products/quantity`, {
    variant_id: variantId,
    quantity: quantity
  }, {});
  return response.data;
};

// Change variant quantity (increment/decrement)
export const changeQuantity = async (id: string, variantId: string, change: number) => {
  const response = await apiClient.patch(`/subscriptions/${id}/products/quantity`, {
    variant_id: variantId,
    change: change
  }, {});
  return response.data;
};

// Get all variant quantities
export const getQuantities = async (id: string) => {
  const response = await apiClient.get(`/subscriptions/${id}/products/quantities`, {});
  return response.data;
};

// === AUTO-RENEW MANAGEMENT ===

// Toggle auto-renew
export const toggleAutoRenew = async (id: string, autoRenew: boolean) => {
  const response = await apiClient.patch(`/subscriptions/${id}/auto-renew`, {}, { 
    params: { auto_renew: autoRenew } 
  });
  return response.data;
};

// === SUBSCRIPTION LIFECYCLE ===

// Pause subscription
export const pauseSubscription = async (id: string, reason?: string) => {
  const params = reason ? { pause_reason: reason } : {};
  const response = await apiClient.post(`/subscriptions/${id}/pause`, {}, { params });
  return response.data;
};

// Resume subscription
export const resumeSubscription = async (id: string) => {
  const response = await apiClient.post(`/subscriptions/${id}/resume`, {}, {});
  return response.data;
};

// === ORDERS & SHIPMENTS ===

// Process subscription shipment
export const processShipment = async (id: string) => {
  const response = await apiClient.post(`/subscriptions/${id}/process-shipment`, {}, {});
  return response.data;
};

// Get subscription orders
export const getOrders = async (id: string, page: number = 1, limit: number = 10) => {
  const response = await apiClient.get(`/subscriptions/${id}/orders`, { params: { page, limit } });
  return response.data;
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

export default SubscriptionAPI;