/**
 * API Service with Dynamic URL Configuration and v1 API versioning
 * Handles all HTTP requests to the backend API
 */

import axios from 'axios';
import { config } from '../config/environment.js';

// Create axios instance with dynamic base URL and v1 API versioning
const api = axios.create({
  baseURL: `${config.apiBaseUrl}/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    if (config.debugMode) {
      console.log('API Request:', config.method?.toUpperCase(), config.url, config.data);
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response) => {
    if (config.debugMode) {
      console.log('API Response:', response.status, response.config.url, response.data);
    }
    return response;
  },
  async (error) => {
    if (config.debugMode) {
      console.error('API Error:', error.response?.status, error.config?.url, error.response?.data);
    }

    const originalRequest = error.config;

    // Handle token expiration with refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      
      if (refreshToken) {
        try {
          // Attempt to refresh the access token
          const response = await axios.post(`${config.apiBaseUrl}/v1/auth/refresh`, {
            refresh_token: refreshToken
          });

          const { access_token } = response.data.data;
          
          // Update stored token
          localStorage.setItem('access_token', access_token);
          
          // Update the authorization header for the original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          
          // Retry the original request
          return api(originalRequest);
          
        } catch (refreshError) {
          // Refresh failed, logout user
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.dispatchEvent(new CustomEvent('auth:logout'));
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token available, logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.dispatchEvent(new CustomEvent('auth:logout'));
      }
    }

    return Promise.reject(error);
  }
);




// API methods
export const apiService = {
  // Auth
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout'),
  refreshToken: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
  revokeRefreshToken: (refreshToken) => api.post('/auth/revoke', { refresh_token: refreshToken }),

  // Cart
  getCart: () => api.get('/cart/'),
  addToCart: (variantId, quantity) => api.post('/cart/add', { variant_id: variantId, quantity }),
  updateCartItem: (itemId, quantity) => api.put(`/cart/update/${itemId}`, { quantity }),
  removeFromCart: (itemId) => api.delete(`/cart/remove/${itemId}`),
  clearCart: () => api.post('/cart/clear'),
  getCartCount: () => api.get('/cart/count'),
  validateCart: () => api.post('/cart/validate'),
  mergeCart: () => api.post('/cart/merge'),
  applyPromocode: (code) => api.post('/cart/promocode', { code }),
  removePromocode: () => api.delete('/cart/promocode'),

  // Products
  getProducts: (params) => api.get('/products/', { params }),
  getProduct: (id) => api.get(`/products/${id}`),
  searchProducts: (query, params) => api.get('/search/products', { params: { q: query, ...params } }),

  // Orders
  getOrders: (params) => api.get('/orders/', { params }),
  getOrder: (id) => api.get(`/orders/${id}`),
  createOrder: (orderData) => api.post('/orders/', orderData),

  // Payments
  createPaymentIntent: (amount, currency = 'USD') => api.post('/payments/create-intent', { amount, currency }),
  confirmPayment: (paymentIntentId, paymentMethodId) => api.post('/payments/confirm', { 
    payment_intent_id: paymentIntentId, 
    payment_method_id: paymentMethodId 
  }),
  
  // Payment Failures
  getPaymentFailureStatus: (paymentIntentId) => api.get(`/payments/failures/${paymentIntentId}/status`),
  retryFailedPayment: (paymentIntentId, newPaymentMethodId = null) => 
    api.post(`/payments/failures/${paymentIntentId}/retry`, { new_payment_method_id: newPaymentMethodId }),
  getUserFailedPayments: (params) => api.get('/payments/failures/user/failed-payments', { params }),
  abandonFailedPayment: (paymentIntentId) => api.post(`/payments/failures/${paymentIntentId}/abandon`),
  getFailureAnalytics: () => api.get('/payments/failures/analytics/failure-reasons'),

  // User
  getProfile: () => api.get('/users/profile'),
  updateProfile: (profileData) => api.put('/users/profile', profileData),
  getAddresses: () => api.get('/users/addresses'),
  // User Management
  addAddress: (addressData) => api.post('/users/addresses', addressData),

  // Wishlist
  getWishlist: () => api.get('/users/wishlist/'),
  addToWishlist: (productId) => api.post('/users/wishlist/add', { product_id: productId }),
  removeFromWishlist: (productId) => api.delete(`/users/wishlist/remove/${productId}`),

  // Health
  healthCheck: () => api.get('/health/'),
};

// Environment-specific configurations
if (config.isDevelopment) {
  // Add development-specific configurations
  api.defaults.timeout = 60000; // Longer timeout for development
}

if (config.isProduction) {
  // Add production-specific configurations
  api.defaults.timeout = 15000; // Shorter timeout for production
}

export default api;