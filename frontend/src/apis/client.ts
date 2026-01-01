/**
 * API Client Configuration and Base Setup
 * Handles authentication, error handling, and request/response interceptors
 */

import axios from 'axios';
import { toast } from 'react-hot-toast';
import { config } from '../config/environment';

// API Configuration
export const API_CONFIG = {
  baseURL: config.apiBaseUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
};

// Token management
class TokenManager {
  static TOKEN_KEY = 'banwee_access_token';
  static REFRESH_TOKEN_KEY = 'banwee_refresh_token';
  static USER_KEY = 'banwee_user';

  static getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  static setToken(token: string) {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  static getRefreshToken() {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  static setRefreshToken(token: string) {
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
  }

  static getUser() {
    const user = localStorage.getItem(this.USER_KEY);
    return user ? JSON.parse(user) : null;
  }

  static setUser(user: any) {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  static setTokens(tokens: { access_token?: string; refresh_token?: string; }) {
    if (tokens.access_token) {
      this.setToken(tokens.access_token);
    }
    if (tokens.refresh_token) {
      this.setRefreshToken(tokens.refresh_token);
    }
  }

  static clearTokens() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  static isAuthenticated(): boolean {
    return !!this.getToken();
  }
}

let isToastVisible = false;

// API Client class
class APIClient {
  constructor() {
    this.client = axios.create(API_CONFIG);
    this.isRefreshing = false;
    this.failedQueue = [];
    this.setupInterceptors();
  }

  setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Check if this is a public endpoint
        const isPublic = this.isPublicEndpoint(config.url || '');
        
        const token = TokenManager.getToken();
        if (token && !isPublic) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request ID for tracking
        config.headers['X-Request-ID'] = this.generateRequestId();

        return config;
      },
      (error) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            }).then((token) => {
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${token}`;
              }
              return this.client(originalRequest);
            }).catch((err) => {
              return Promise.reject(err);
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const refreshToken = TokenManager.getRefreshToken();
            if (refreshToken) {
              const response = await this.client.post('/auth/refresh', {
                refresh_token: refreshToken,
              });

              const { access_token } = response.data;
              TokenManager.setToken(access_token);

              this.processQueue(null, access_token);

              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${access_token}`;
              }

              return this.client(originalRequest);
            }
          } catch (refreshError) {
            this.processQueue(refreshError, null);
            TokenManager.clearTokens();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        // Check if this is a public endpoint that shouldn't show login toasts
        const isPublic = this.isPublicEndpoint(error.config?.url || '');
        return this.handleError(error, isPublic);
      }
    );
  }

  processQueue(error, token) {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error);
      } else {
        resolve(token);
      }
    });

    this.failedQueue = [];
  }

  handleError(error, suppressToasts = false) {
    const apiError = {
      message: 'An unexpected error occurred',
      code: error.response?.status?.toString(),
      statusCode: error.response?.status,
    };

    if (error.response?.data) {
      const errorData = error.response.data;
      
      // Handle backend error structure
      if (errorData.message) {
        apiError.message = errorData.message;
      } else if (errorData.detail) {
        apiError.message = errorData.detail;
      }
      
      // Handle validation errors
      if (errorData.details || errorData.errors) {
        const validationErrors = errorData.details || errorData.errors;
        
        // If it's a string, use it directly
        if (typeof validationErrors === 'string') {
          apiError.message = validationErrors;
        } 
        // If it's an object, extract the first error message
        else if (validationErrors && typeof validationErrors === 'object') {
          const firstError = Object.values(validationErrors)[0];
          if (Array.isArray(firstError) && firstError.length > 0) {
            apiError.message = firstError[0];
          } else if (typeof firstError === 'string') {
            apiError.message = firstError;
          } else {
            // Fallback: stringify the object
            apiError.message = 'Validation error occurred';
          }
        }
      }
    } else if (error.request) {
      // This block is executed when the request was made but no response was received.
      // This often indicates a network issue or a server that closed the connection prematurely.
      if (error.code === 'ECONNABORTED') { // Timeout error
        apiError.message = 'Request timed out. Please try again.';
        apiError.code = 'TIMEOUT_ERROR';
      } else if (!navigator.onLine) {
        // Network is offline
        apiError.message = 'No internet connection. Please check your network and try again.';
        apiError.code = 'OFFLINE_ERROR';
      } else {
        apiError.message = 'Failed to connect to the server. Please ensure the backend is running and accessible.';
        apiError.code = 'CONNECTION_ERROR';
      }
    }

    // Map HTTP status codes to user-friendly messages
    if (apiError.statusCode) {
      switch (apiError.statusCode) {
        case 401:
          // Handled by auth interceptor, redirect to login
          if (!suppressToasts) {
            apiError.message = 'Your session has expired. Please log in again.';
          }
          break;
        case 403:
          apiError.message = 'You don\'t have permission to perform this action.';
          break;
        case 404:
          apiError.message = 'The requested resource was not found.';
          break;
        case 422:
          // Keep the specific validation message from backend
          break;
        case 429:
          apiError.message = 'Too many requests. Please wait a moment and try again.';
          break;
        case 500:
        case 502:
        case 503:
        case 504:
          apiError.message = 'Server error. Please try again later.';
          break;
      }
    }

    // Show user-friendly error messages (will be suppressed for public endpoints)
    this.showErrorToast(apiError, suppressToasts);

    // Log error in development
    if (import.meta.env.DEV) {
      console.error('❌ API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        message: apiError.message,
        details: apiError.details,
      });
    }

    return Promise.reject(apiError);
  }

  showErrorToast(error, suppressToasts = false) {
    // Don't show toast if suppressed or if it's a 401 error on homepage/public endpoints
    if (suppressToasts || this.shouldSuppressErrorToast(error)) {
      return;
    }

    if (isToastVisible) {
      return;
    }

    isToastVisible = true;
    setTimeout(() => {
      isToastVisible = false;
    }, 30000); // Reset after 30 seconds

    // Use the already mapped message from handleError
    const message = error.message || 'An unexpected error occurred';

    toast.error(message, {
      duration: error.code === 'OFFLINE_ERROR' ? 5000 : 4000,
      icon: error.code === 'OFFLINE_ERROR' ? '📡' : '❌',
    });
  }

  generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
  }

  isPublicEndpoint(url) {
    // List of public endpoints that shouldn't show login prompts
    const publicEndpoints = [
      '/v1/products/featured',
      '/v1/products/popular',
      '/v1/products',
      '/v1/products/categories',
      '/v1/auth/refresh',
      '/v1/users/profile',
      '/v1/orders/track/'  // Public order tracking
    ];

    return publicEndpoints.some(endpoint => url.includes(endpoint));
  }

  shouldSuppressErrorToast(error) {
    // Suppress 401 errors for public endpoints that don't require authentication
    if (error.code === '401') {
      return true; // Let the auth interceptor handle 401s
    }

    return false;
  }

  // HTTP Methods
  async get(url, config) {
    const response = await this.client.get(url, config);
    return response.data;
  }

  async post(url, data, config) {
    const response = await this.client.post(url, data, config);
    return response.data;
  }

  async put(url, data, config) {
    const response = await this.client.put(url, data, config);
    return response.data;
  }

  async patch(url, data, config) {
    const response = await this.client.patch(url, data, config);
    return response.data;
  }

  async delete(url, config) {
    const response = await this.client.delete(url, config);
    return response.data;
  }

  // File upload
  async upload(url, file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    };

    const response = await this.client.post(url, formData, config);
    return response.data;
  }

  // Download file
  async download(url, filename) {
    const response = await this.client.get(url, {
      responseType: 'blob',
    });

    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  // Get raw axios instance for advanced usage
  getClient() {
    return this.client;
  }

  // ==================== CONSOLIDATED API METHODS ====================

  // Auth methods
  async login(credentials) {
    return this.post('/auth/login', credentials);
  }

  async register(userData) {
    return this.post('/auth/register', userData);
  }

  async logout() {
    return this.post('/auth/logout', {});
  }

  async refreshToken() {
    return this.post('/auth/refresh', {});
  }

  // User methods
  async getCurrentUser() {
    return this.get('/users/me');
  }

  async updateProfile(updates) {
    return this.put('/users/me', updates);
  }

  async changePassword(data) {
    return this.put('/users/me/password', data);
  }

  // Address methods
  async getUserAddresses() {
    return this.get('/users/me/addresses');
  }

  async createAddress(address) {
    return this.post('/users/me/addresses', address);
  }

  async updateAddress(id, updates) {
    return this.put(`/users/me/addresses/${id}`, updates);
  }

  async deleteAddress(id) {
    return this.delete(`/users/me/addresses/${id}`);
  }

  async setDefaultAddress(id) {
    return this.put(`/users/me/addresses/${id}/default`, {});
  }

  // Product methods
  async getProducts(params) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            queryParams.append(key, value.join(','));
          } else {
            queryParams.append(key, value.toString());
          }
        }
      });
    }
    const url = `/products${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return this.get(url);
  }

  async getProduct(id) {
    return this.get(`/products/${id}`);
  }

  async getProductWithDetails(id) {
    return this.get(`/products/${id}?include_variants=true&include_reviews=true`);
  }

  async getFeaturedProducts(limit = 10) {
    return this.get(`/products/featured?limit=${limit}`);
  }

  async searchProducts(query) {
    return this.get(`/products/search?q=${encodeURIComponent(query)}`);
  }

  // Category methods
  async getCategories() {
    return this.get('/categories');
  }

  async getCategory(id) {
    return this.get(`/categories/${id}`);
  }

  async getCategoryProducts(id, page = 1, limit = 20) {
    return this.get(`/categories/${id}/products?page=${page}&limit=${limit}`);
  }

  // Cart methods
  async getCart() {
    return this.get('/cart');
  }

  async addToCart(variantId, quantity) {
    return this.post('/cart/items', { variant_id: variantId, quantity });
  }

  async updateCartItem(itemId, quantity) {
    return this.put(`/cart/items/${itemId}`, { quantity });
  }

  async removeFromCart(itemId) {
    return this.delete(`/cart/items/${itemId}`);
  }

  async clearCart() {
    return this.delete('/cart');
  }

  // Order methods
  async getOrders(params) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }
    const url = `/orders${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return this.get(url);
  }

  async getOrder(id) {
    return this.get(`/orders/${id}`);
  }

  async createOrder(orderData) {
    return this.post('/orders', orderData);
  }

  async cancelOrder(id) {
    return this.put(`/orders/${id}/cancel`, {});
  }

  async trackOrder(id) {
    return this.get(`/orders/${id}/tracking`);
  }

  // Review methods
  async getProductReviews(productId, page = 1, limit = 10) {
    return this.get(`/products/${productId}/reviews?page=${page}&limit=${limit}`);
  }

  async createReview(review) {
    return this.post('/reviews', review);
  }

  async updateReview(id, updates) {
    return this.put(`/reviews/${id}`, updates);
  }

  async deleteReview(id) {
    return this.delete(`/reviews/${id}`);
  }

  // Wishlist methods
  async getWishlists() {
    return this.get('/wishlists');
  }

  async getWishlist(id) {
    return this.get(`/wishlists/${id}`);
  }

  async createWishlist(data) {
    return this.post('/wishlists', data);
  }

  async addToWishlist(wishlistId, productId, quantity = 1) {
    return this.post(`/wishlists/${wishlistId}/items`, { product_id: productId, quantity });
  }

  async removeFromWishlist(wishlistId, itemId) {
    return this.delete(`/wishlists/${wishlistId}/items/${itemId}`);
  }

  // Payment methods
  async getPaymentMethods() {
    return this.get('/payment-methods');
  }

  async createPaymentMethod(method) {
    return this.post('/payment-methods', method);
  }

  async deletePaymentMethod(id) {
    return this.delete(`/payment-methods/${id}`);
  }

  async setDefaultPaymentMethod(id) {
    return this.put(`/payment-methods/${id}/default`, {});
  }

  // Shipping methods
  async getShippingMethods() {
    return this.get('/shipping-methods');
  }

  async calculateShipping(addressId, items) {
    return this.post('/shipping/calculate', { address_id: addressId, items });
  }

  // Promocode methods
  async validatePromocode(code, orderTotal) {
    return this.post('/promocodes/validate', { code, order_total: orderTotal });
  }

  // Negotiation methods
  async startNegotiation(buyerConfig, sellerConfig) {
    return this.post('/negotiate/start', {
      buyer_config: buyerConfig,
      seller_config: sellerConfig,
    });
  }

  async stepNegotiation(negotiationId, buyerNewTarget = null, sellerNewTarget = null) {
    return this.post('/negotiate/step', {
      negotiation_id: negotiationId,
      buyer_new_target: buyerNewTarget,
      seller_new_target: sellerNewTarget,
    });
  }

  async getNegotiationState(negotiationId) {
    return this.get(`/negotiate/${negotiationId}`);
  }

  async deleteNegotiation(negotiationId) {
    return this.delete(`/negotiate/${negotiationId}`);
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export { TokenManager };
export default apiClient;