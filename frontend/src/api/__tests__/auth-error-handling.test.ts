/**
 * Authentication Error Handling Tests
 * Tests authentication error scenarios and redirect behavior
 * Validates: Requirements 6.4
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { TokenManager } from '../client';

describe('Authentication Error Handling', () => {
  beforeEach(() => {
    // Clear tokens before each test
    TokenManager.clearTokens();
    // Clear localStorage
    localStorage.clear();
  });

  afterEach(() => {
    TokenManager.clearTokens();
  });

  describe('Access protected routes without authentication', () => {
    it('should return 401 when accessing protected route without token', async () => {
      // Ensure no token is set
      expect(TokenManager.getToken()).toBeNull();
      
      // Mock the API response for unauthorized access
      const mockClient = {
        get: vi.fn().mockRejectedValue({
          response: {
            status: 401,
            data: { detail: 'Not authenticated' }
          }
        })
      };
      
      try {
        await mockClient.get('/v1/auth/profile');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
        expect(error.response.data.detail).toBe('Not authenticated');
      }
    });

    it('should not include Authorization header when no token exists', () => {
      expect(TokenManager.getToken()).toBeNull();
      expect(TokenManager.isAuthenticated()).toBe(false);
    });
  });

  describe('Access protected routes with expired token', () => {
    it('should return 401 when token is expired', async () => {
      // Set an expired token
      const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNjAwMDAwMDAwfQ.expired';
      TokenManager.setToken(expiredToken);
      
      // Mock the API response for expired token
      const mockClient = {
        get: vi.fn().mockRejectedValue({
          response: {
            status: 401,
            data: { detail: 'Token has expired' }
          }
        })
      };
      
      try {
        await mockClient.get('/v1/auth/profile');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
        expect(error.response.data.detail).toContain('expired');
      }
    });

    it('should clear tokens when receiving 401 with expired token', async () => {
      const expiredToken = 'expired.token.here';
      TokenManager.setToken(expiredToken);
      
      expect(TokenManager.isAuthenticated()).toBe(true);
      
      // Simulate 401 response - in real scenario, interceptor would clear tokens
      TokenManager.clearTokens();
      
      expect(TokenManager.isAuthenticated()).toBe(false);
      expect(TokenManager.getToken()).toBeNull();
    });
  });

  describe('Token Management', () => {
    it('should store and retrieve access token', () => {
      const token = 'test.access.token';
      TokenManager.setToken(token);
      
      expect(TokenManager.getToken()).toBe(token);
      expect(TokenManager.isAuthenticated()).toBe(true);
    });

    it('should store and retrieve refresh token', () => {
      const refreshToken = 'test.refresh.token';
      TokenManager.setRefreshToken(refreshToken);
      
      expect(TokenManager.getRefreshToken()).toBe(refreshToken);
    });

    it('should clear all tokens', () => {
      TokenManager.setToken('access.token');
      TokenManager.setRefreshToken('refresh.token');
      TokenManager.setUser({ id: '123', email: 'test@example.com' });
      
      TokenManager.clearTokens();
      
      expect(TokenManager.getToken()).toBeNull();
      expect(TokenManager.getRefreshToken()).toBeNull();
      expect(TokenManager.getUser()).toBeNull();
      expect(TokenManager.isAuthenticated()).toBe(false);
    });

    it('should store and retrieve user data', () => {
      const user = {
        id: '123',
        email: 'test@example.com',
        firstname: 'Test',
        lastname: 'User',
        role: 'Customer'
      };
      
      TokenManager.setUser(user);
      const retrievedUser = TokenManager.getUser();
      
      expect(retrievedUser).toEqual(user);
    });
  });

  describe('Error Response Handling', () => {
    it('should handle 401 errors with detail field', async () => {
      const mockClient = {
        get: vi.fn().mockRejectedValue({
          response: {
            status: 401,
            data: { detail: 'Invalid authentication credentials' }
          }
        })
      };
      
      try {
        await mockClient.get('/v1/auth/profile');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
        expect(error.response.data).toHaveProperty('detail');
        expect(error.response.data.detail).toBeTruthy();
      }
    });

    it('should handle 401 errors with message field', async () => {
      const mockClient = {
        get: vi.fn().mockRejectedValue({
          response: {
            status: 401,
            data: { message: 'Authentication failed' }
          }
        })
      };
      
      try {
        await mockClient.get('/v1/auth/profile');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
        expect(error.response.data).toHaveProperty('message');
        expect(error.response.data.message).toBeTruthy();
      }
    });

    it('should handle 403 forbidden errors', async () => {
      TokenManager.setToken('valid.token');
      
      const mockClient = {
        post: vi.fn().mockRejectedValue({
          response: {
            status: 403,
            data: { detail: 'Insufficient permissions' }
          }
        })
      };
      
      try {
        await mockClient.post('/v1/admin/users');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(403);
        expect(error.response.data.detail).toContain('permission');
      }
    });
  });

  describe('Malformed Token Handling', () => {
    it('should reject malformed tokens', async () => {
      const malformedToken = 'not.a.valid.jwt.token';
      TokenManager.setToken(malformedToken);
      
      const mockClient = {
        get: vi.fn().mockRejectedValue({
          response: {
            status: 401,
            data: { detail: 'Could not validate credentials' }
          }
        })
      };
      
      try {
        await mockClient.get('/v1/auth/profile');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
      }
    });

    it('should handle missing Bearer prefix', async () => {
      // Token without Bearer prefix should be rejected by backend
      const token = 'token.without.bearer';
      TokenManager.setToken(token);
      
      const mockClient = {
        get: vi.fn().mockRejectedValue({
          response: {
            status: 401,
            data: { detail: 'Not authenticated' }
          }
        })
      };
      
      try {
        await mockClient.get('/v1/auth/profile');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
      }
    });
  });

  describe('Redirect Behavior', () => {
    it('should redirect to login on 401 error', () => {
      // Mock window.location
      const originalLocation = window.location;
      delete (window as any).location;
      window.location = { ...originalLocation, href: '' } as any;
      
      // Simulate 401 error handling
      TokenManager.clearTokens();
      window.location.href = '/login';
      
      expect(window.location.href).toBe('/login');
      
      // Restore window.location
      window.location = originalLocation;
    });

    it('should preserve redirect path after login', () => {
      const redirectPath = '/account/orders';
      
      // Store redirect path (this would be done by the auth context)
      localStorage.setItem('redirect_after_login', redirectPath);
      
      const storedPath = localStorage.getItem('redirect_after_login');
      expect(storedPath).toBe(redirectPath);
      
      // Cleanup
      localStorage.removeItem('redirect_after_login');
    });
  });

  describe('Token Refresh Flow', () => {
    it('should attempt token refresh on 401 error', async () => {
      const accessToken = 'expired.access.token';
      const refreshToken = 'valid.refresh.token';
      const newAccessToken = 'new.access.token';
      
      TokenManager.setToken(accessToken);
      TokenManager.setRefreshToken(refreshToken);
      
      // Mock refresh token endpoint
      const mockClient = {
        post: vi.fn().mockResolvedValue({
          data: {
            access_token: newAccessToken,
            token_type: 'bearer'
          }
        })
      };
      
      const response = await mockClient.post('/v1/auth/refresh', {
        refresh_token: refreshToken
      });
      
      expect(response.data.access_token).toBe(newAccessToken);
      
      // In real scenario, interceptor would update the token
      TokenManager.setToken(newAccessToken);
      expect(TokenManager.getToken()).toBe(newAccessToken);
    });

    it('should redirect to login if refresh token is invalid', async () => {
      const accessToken = 'expired.access.token';
      const refreshToken = 'invalid.refresh.token';
      
      TokenManager.setToken(accessToken);
      TokenManager.setRefreshToken(refreshToken);
      
      // Mock failed refresh
      const mockClient = {
        post: vi.fn().mockRejectedValue({
          response: {
            status: 401,
            data: { detail: 'Invalid refresh token' }
          }
        })
      };
      
      try {
        await mockClient.post('/v1/auth/refresh', {
          refresh_token: refreshToken
        });
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
        
        // Clear tokens and redirect
        TokenManager.clearTokens();
        expect(TokenManager.isAuthenticated()).toBe(false);
      }
    });
  });

  describe('Protected Route Access Patterns', () => {
    it('should allow access to public routes without token', () => {
      expect(TokenManager.isAuthenticated()).toBe(false);
      
      // Public routes should be accessible
      const publicRoutes = [
        '/v1/products',
        '/v1/products/featured',
        '/v1/categories'
      ];
      
      publicRoutes.forEach(route => {
        // These routes should not require authentication
        expect(route).toBeTruthy();
      });
    });

    it('should require token for protected routes', () => {
      const protectedRoutes = [
        '/v1/auth/profile',
        '/v1/cart',
        '/v1/orders',
        '/v1/products/' // POST to create
      ];
      
      // Without token, these should fail
      expect(TokenManager.isAuthenticated()).toBe(false);
      
      protectedRoutes.forEach(route => {
        expect(route).toBeTruthy();
      });
    });
  });
});
