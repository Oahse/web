/**
 * Authentication API endpoints
 */

import { apiClient, TokenManager } from './client';
// import { 
//   User, 
//   LoginRequest, 
//   RegisterRequest, 
//   AuthResponse,
//   APIResponse, 
//   Address


export class AuthAPI {
  /**
   * Register a new user
   */
  static async register(data) {
    const response = await apiClient.post('/auth/register', data);
    
    if (response.data.access_token) {
      TokenManager.setToken(response.data.access_token);
      if (response.data.refresh_token) {
        TokenManager.setRefreshToken(response.data.refresh_token);
      }
      TokenManager.setUser(response.data.user);
    }
    
    return response;
  }

  /**
   * Login user
   */
  static async login(data) {
    const response = await apiClient.post('/auth/login', data);
    
    if (response.data.access_token) {
      TokenManager.setToken(response.data.access_token);
      if (response.data.refresh_token) {
        TokenManager.setRefreshToken(response.data.refresh_token);
      }
      TokenManager.setUser(response.data.user);
    }
    
    return response;
  }

  /**
   * Logout user
   */
  static async logout() {
    try {
      // Call logout endpoint if it exists
      await apiClient.post('/auth/logout');
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error);
    } finally {
      TokenManager.clearTokens();
    }
  }

  /**
   * Get current user profile
   */
  static async getProfile() {
    return await apiClient.get('/auth/profile');
  }

  /**
   * Update user profile
   */
  static async updateProfile(data) {
    const response = await apiClient.put('/auth/profile', data);
    
    // Update stored user data
    if (response.data) {
      TokenManager.setUser(response.data);
    }
    
    return response;
  }

  /**
   * Change password
   */
  static async changePassword(data) {
    return await apiClient.put('/auth/change-password', data);
  }

  /**
   * Request password reset
   */
  static async requestPasswordReset(email) {
    return await apiClient.post('/auth/forgot-password', { email });
  }

  /**
   * Reset password with token
   */
  static async resetPassword(data) {
    return await apiClient.post('/auth/reset-password', data);
  }

  /**
   * Verify email with token
   */
  static async verifyEmail(token) {
    return await apiClient.post('/auth/verify-email', { token });
  }

  /**
   * Resend email verification
   */
  static async resendVerification() {
    return await apiClient.post('/users/resend-verification');
  }

  /**
   * Social authentication
   */
  static async socialLogin(token, provider) {
    const response = await apiClient.post(`/auth/social/${provider}`, { token });
    
    if (response.data.access_token) {
      TokenManager.setToken(response.data.access_token);
      if (response.data.refresh_token) {
        TokenManager.setRefreshToken(response.data.refresh_token);
      }
      TokenManager.setUser(response.data.user);
    }
    
    return response;
  }

  /**
   * Refresh access token
   */
  static async refreshToken() {
    try {
      const refreshToken = TokenManager.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await apiClient.post('/auth/refresh', {
        refresh_token: refreshToken,
      });

      if (response.data.access_token) {
        TokenManager.setToken(response.data.access_token);
      }

      return response;
    } catch (error) {
      TokenManager.clearTokens();
      throw error;
    }
  }

  /**
   * Check if user is authenticated
   */
  static isAuthenticated() {
    return TokenManager.isAuthenticated();
  }

  /**
   * Get current user from storage
   */
  static getCurrentUser() {
    return TokenManager.getUser();
  }

  /**
   * Delete user account
   */
  static async deleteAccount(password) {
    const response = await apiClient.delete('/users', {
      data: { password }
    });
    
    // Clear tokens after successful deletion
    TokenManager.clearTokens();
    
    return response;
  }

  /**
   * Update notification preferences
   */
  static async updateNotificationPreferences(preferences) {
    return await apiClient.put('/users/notification-preferences', preferences);
  }

  /**
   * Get user's addresses
   */
  static async getAddresses() {
    return await apiClient.get(`/users/me/addresses`);
  }

  /**
   * Add new address
   */
  static async addAddress(address) {
    return await apiClient.post('/users/addresses', address);
  }

  /**
   * Update address
   */
  static async updateAddress(addressId, address) {
    return await apiClient.put(`/users/addresses/${addressId}`, address);
  }

  /**
   * Delete address
   */
  static async deleteAddress(addressId) {
    return await apiClient.delete(`/users/addresses/${addressId}`);
  }
}

export default AuthAPI;