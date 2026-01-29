/**
 * Tests for API Client - Comprehensive test suite aligned with backend reality
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock axios first before importing anything else
const mockAxiosInstance = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
  interceptors: {
    request: { use: vi.fn() },
    response: { use: vi.fn() }
  }
};

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockAxiosInstance),
    isAxiosError: vi.fn()
  }
}));

// Mock environment
vi.mock('../../config/environment', () => ({
  config: {
    apiBaseUrl: 'http://localhost:8000/v1',
    stripePublicKey: 'pk_test_123',
    environment: 'test'
  }
}));

// Now import the modules after mocking
import { apiClient, TokenManager } from '../../api/client';

// Mock localStorage and sessionStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
};

const mockSessionStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
};

Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });
Object.defineProperty(window, 'sessionStorage', { value: mockSessionStorage });

describe('TokenManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Token Storage', () => {
    it('should store tokens in localStorage when remember me is true', () => {
      mockLocalStorage.getItem.mockReturnValue('true');
      
      TokenManager.setRememberMe(true);
      TokenManager.setToken('test_token');
      TokenManager.setRefreshToken('refresh_token');
      
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('banwee_remember_me', 'true');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('banwee_access_token', 'test_token');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('banwee_refresh_token', 'refresh_token');
    });

    it('should store tokens in sessionStorage when remember me is false', () => {
      mockLocalStorage.getItem.mockReturnValue('false');
      
      TokenManager.setRememberMe(false);
      TokenManager.setToken('test_token');
      
      expect(mockSessionStorage.setItem).toHaveBeenCalledWith('banwee_access_token', 'test_token');
    });

    it('should retrieve tokens from correct storage', () => {
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'banwee_remember_me') return 'true';
        if (key === 'banwee_access_token') return 'stored_token';
        return null;
      });
      
      const token = TokenManager.getToken();
      expect(token).toBe('stored_token');
    });

    it('should clear tokens from both storages', () => {
      TokenManager.clearTokens();
      
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('banwee_access_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('banwee_refresh_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('banwee_user');
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('banwee_access_token');
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('banwee_refresh_token');
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('banwee_user');
    });
  });

  describe('User Management', () => {
    it('should store and retrieve user data', () => {
      const userData = { id: '123', email: 'test@example.com', first_name: 'Test' };
      mockLocalStorage.getItem.mockReturnValue('true'); // remember me
      
      TokenManager.setUser(userData);
      
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('banwee_user', JSON.stringify(userData));
    });

    it('should return null for invalid user data', () => {
      mockLocalStorage.getItem.mockReturnValue('invalid_json');
      
      const user = TokenManager.getUser();
      expect(user).toBeNull();
    });
  });
});

describe('APIClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('HTTP Methods', () => {
    it('should make GET requests correctly', async () => {
      const responseData = { success: true, data: { id: '123' } };
      mockAxiosInstance.get.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.get('/test');
      
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test', undefined);
      expect(result).toEqual(responseData);
    });

    it('should make POST requests correctly', async () => {
      const requestData = { name: 'test' };
      const responseData = { success: true, data: { id: '123' } };
      mockAxiosInstance.post.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.post('/test', requestData);
      
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/test', requestData, undefined);
      expect(result).toEqual(responseData);
    });

    it('should make PUT requests correctly', async () => {
      const requestData = { name: 'updated' };
      const responseData = { success: true, data: { id: '123' } };
      mockAxiosInstance.put.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.put('/test/123', requestData);
      
      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/test/123', requestData, undefined);
      expect(result).toEqual(responseData);
    });

    it('should make DELETE requests correctly', async () => {
      const responseData = { success: true, message: 'Deleted' };
      mockAxiosInstance.delete.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.delete('/test/123');
      
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/test/123', undefined);
      expect(result).toEqual(responseData);
    });
  });

  describe('Authentication Methods', () => {
    it('should login with correct backend format', async () => {
      const credentials = { email: 'test@example.com', password: 'password123' };
      const responseData = {
        success: true,
        data: {
          access_token: 'token123',
          refresh_token: 'refresh123',
          user: { id: '123', email: 'test@example.com' }
        }
      };
      mockAxiosInstance.post.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.login(credentials);
      
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/login', credentials);
      expect(result).toEqual(responseData);
    });

    it('should register with correct backend format', async () => {
      const userData = {
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'Test',
        last_name: 'User',
        password: 'password123'
      };
      const responseData = {
        success: true,
        data: { id: '123', email: 'test@example.com' },
        message: 'User registered successfully'
      };
      mockAxiosInstance.post.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.register(userData);
      
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/register', userData);
      expect(result).toEqual(responseData);
    });

    it('should refresh token with correct format', async () => {
      const responseData = {
        success: true,
        data: { access_token: 'new_token' }
      };
      mockAxiosInstance.post.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.refreshToken();
      
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/refresh', {});
      expect(result).toEqual(responseData);
    });
  });

  describe('Cart Methods', () => {
    it('should get cart with correct endpoint', async () => {
      const responseData = {
        success: true,
        data: {
          id: 'cart123',
          items: [],
          total: 0
        }
      };
      mockAxiosInstance.get.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.getCart();
      
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/cart');
      expect(result).toEqual(responseData);
    });

    it('should add to cart with correct endpoint and format', async () => {
      const responseData = {
        success: true,
        data: { id: 'cart123', items: [{ id: 'item123' }] }
      };
      mockAxiosInstance.post.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.addToCart('variant123', 2);
      
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/cart/add', {
        variant_id: 'variant123',
        quantity: 2
      });
      expect(result).toEqual(responseData);
    });

    it('should update cart item with correct endpoint', async () => {
      const responseData = { success: true, data: { id: 'item123', quantity: 3 } };
      mockAxiosInstance.put.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.updateCartItem('item123', 3);
      
      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/cart/items/item123', { quantity: 3 });
      expect(result).toEqual(responseData);
    });

    it('should clear cart with correct endpoint', async () => {
      const responseData = { success: true, message: 'Cart cleared' };
      mockAxiosInstance.delete.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.clearCart();
      
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/cart/clear');
      expect(result).toEqual(responseData);
    });
  });

  describe('Product Methods', () => {
    it('should get products with correct query parameters', async () => {
      const params = {
        page: 1,
        limit: 12,
        category: 'electronics',
        min_price: 10,
        max_price: 100,
        sort: 'price_asc'
      };
      const responseData = {
        success: true,
        data: {
          products: [],
          total: 0,
          page: 1,
          totalPages: 1
        }
      };
      mockAxiosInstance.get.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.getProducts(params);
      
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/products?page=1&limit=12&category=electronics&min_price=10&max_price=100&sort=price_asc'
      );
      expect(result).toEqual(responseData);
    });

    it('should search products with correct endpoint', async () => {
      const query = 'laptop';
      const responseData = {
        success: true,
        data: { products: [], total: 0 }
      };
      mockAxiosInstance.get.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.searchProducts(query);
      
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/products/search?q=laptop');
      expect(result).toEqual(responseData);
    });

    it('should get product details with variants and reviews', async () => {
      const productId = 'product123';
      const responseData = {
        success: true,
        data: {
          id: productId,
          name: 'Test Product',
          variants: [],
          reviews: []
        }
      };
      mockAxiosInstance.get.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.getProductWithDetails(productId);
      
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/products/product123?include_variants=true&include_reviews=true'
      );
      expect(result).toEqual(responseData);
    });
  });

  describe('Order Methods', () => {
    it('should create order with correct format', async () => {
      const orderData = {
        shipping_address: { street: '123 Main St' },
        payment_method: { type: 'card' },
        items: [{ variant_id: 'var123', quantity: 1 }]
      };
      const responseData = {
        success: true,
        data: { id: 'order123', status: 'pending' }
      };
      mockAxiosInstance.post.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.createOrder(orderData);
      
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/orders', orderData);
      expect(result).toEqual(responseData);
    });

    it('should get orders with pagination', async () => {
      const params = { page: 1, limit: 10, status: 'completed' };
      const responseData = {
        success: true,
        data: { orders: [], total: 0, page: 1 }
      };
      mockAxiosInstance.get.mockResolvedValue({ data: responseData });
      
      const result = await apiClient.getOrders(params);
      
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/orders?page=1&limit=10&status=completed');
      expect(result).toEqual(responseData);
    });
  });

  describe('Error Handling', () => {
    it('should handle 401 errors correctly', async () => {
      const error = {
        response: {
          status: 401,
          data: { message: 'Unauthorized' }
        }
      };
      mockAxiosInstance.get.mockRejectedValue(error);
      
      await expect(apiClient.get('/protected')).rejects.toMatchObject({
        statusCode: 401,
        message: 'Unauthorized'
      });
    });

    it('should handle validation errors (422)', async () => {
      const error = {
        response: {
          status: 422,
          data: {
            message: 'Validation error',
            details: { email: ['Invalid email format'] }
          }
        }
      };
      mockAxiosInstance.post.mockRejectedValue(error);
      
      await expect(apiClient.post('/test', {})).rejects.toMatchObject({
        statusCode: 422,
        message: 'Validation error'
      });
    });

    it('should handle network errors', async () => {
      const error = { request: {}, code: 'ECONNABORTED' };
      mockAxiosInstance.get.mockRejectedValue(error);
      
      await expect(apiClient.get('/test')).rejects.toMatchObject({
        message: 'Request timed out. Please try again.',
        code: 'TIMEOUT_ERROR'
      });
    });

    it('should handle offline errors', async () => {
      // Mock navigator.onLine
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false
      });
      
      const error = { request: {} };
      mockAxiosInstance.get.mockRejectedValue(error);
      
      await expect(apiClient.get('/test')).rejects.toMatchObject({
        message: 'No internet connection. Please check your network and try again.',
        code: 'OFFLINE_ERROR'
      });
    });
  });

  describe('Request Caching', () => {
    it('should cache GET requests', async () => {
      const responseData = { success: true, data: { id: '123' } };
      mockAxiosInstance.get.mockResolvedValue({ data: responseData });
      
      // First request
      await apiClient.get('/test');
      // Second request (should use cache)
      await apiClient.get('/test');
      
      // Should only make one actual HTTP request
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1);
    });

    it('should not cache POST requests', async () => {
      const responseData = { success: true, data: { id: '123' } };
      mockAxiosInstance.post.mockResolvedValue({ data: responseData });
      
      // Multiple POST requests
      await apiClient.post('/test', {});
      await apiClient.post('/test', {});
      
      // Should make multiple HTTP requests
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(2);
    });
  });

  describe('File Upload', () => {
    it('should upload files with correct format', async () => {
      const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
      const responseData = { success: true, data: { url: 'uploaded.jpg' } };
      mockAxiosInstance.post.mockResolvedValue({ data: responseData });
      
      const onProgress = vi.fn();
      const result = await apiClient.upload('/upload', file, onProgress);
      
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/upload',
        expect.any(FormData),
        expect.objectContaining({
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: expect.any(Function)
        })
      );
      expect(result).toEqual(responseData);
    });
  });
});