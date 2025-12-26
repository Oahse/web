/**
 * API Service with Dynamic URL Configuration
 * Handles all HTTP requests to the backend API
 */

import axios from 'axios';
import { config } from '../config/environment.js';

// Create axios instance with dynamic base URL
const api = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token and session ID
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add session ID for guest users
    const sessionId = localStorage.getItem('session_id') || generateSessionId();
    if (sessionId && !token) {
      config.headers['X-Session-ID'] = sessionId;
      localStorage.setItem('session_id', sessionId);
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

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    if (config.debugMode) {
      console.log('API Response:', response.status, response.config.url, response.data);
    }
    return response;
  },
  (error) => {
    if (config.debugMode) {
      console.error('API Error:', error.response?.status, error.config?.url, error.response?.data);
    }

    // Handle token expiration
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      // Redirect to login or emit event
      window.dispatchEvent(new CustomEvent('auth:logout'));
    }

    return Promise.reject(error);
  }
);

// Generate session ID for guest users
function generateSessionId() {
  return 'sess_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
}

// API methods
export const apiService = {
  // Auth
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout'),
  refreshToken: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),

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

  // User
  getProfile: () => api.get('/user/profile'),
  updateProfile: (profileData) => api.put('/user/profile', profileData),
  getAddresses: () => api.get('/user/addresses'),
  addAddress: (addressData) => api.post('/user/addresses', addressData),

  // Notifications
  getNotifications: (params) => api.get('/notifications/', { params }),
  markNotificationRead: (id) => api.put(`/notifications/${id}/read`),
  markAllNotificationsRead: () => api.put('/notifications/mark-all-read'),

  // Wishlist
  getWishlist: () => api.get('/wishlist/'),
  addToWishlist: (productId) => api.post('/wishlist/add', { product_id: productId }),
  removeFromWishlist: (productId) => api.delete(`/wishlist/remove/${productId}`),

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