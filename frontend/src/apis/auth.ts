/**
 * Authentication API endpoints
 */

import { apiClient, TokenManager } from './client';

interface RegisterData {
  email: string;
  password: string;
  firstname: string;
  lastname: string;
}

interface LoginData {
  email: string;
  password: string;
}

interface ProfileData {
  firstname?: string;
  lastname?: string;
  email?: string;
}

interface ChangePasswordData {
  current_password: string;
  new_password: string;
}

interface ResetPasswordData {
  token: string;
  password: string;
}


export class AuthAPI {
  /**
   * Register a new user
   */
  static async register(data: RegisterData) {
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
  static async login(data: LoginData) {
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
  static async updateProfile(data: ProfileData) {
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
  static async changePassword(data: ChangePasswordData) {
    return await apiClient.put('/auth/change-password', data);
  }

  /**
   * Request password reset
   */
  static async requestPasswordReset(email: string) {
    return await apiClient.post('/auth/forgot-password', { email });
  }

  /**
   * Forgot password - alias for requestPasswordReset
   */
  static async forgotPassword(email: string) {
    return await this.requestPasswordReset(email);
  }

  /**
   * Reset password with token
   */
  static async resetPassword(data: ResetPasswordData) {
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
    return await apiClient.get(`/auth/addresses`);
  }

  /**
   * Create new address
   */
  static async createAddress(address) {
    return await apiClient.post('/auth/addresses', address);
  }

  /**
   * Update address
   */
  static async updateAddress(addressId, address) {
    return await apiClient.put(`/auth/addresses/${addressId}`, address);
  }

  /**
   * Delete address
   */
  static async deleteAddress(addressId) {
    return await apiClient.delete(`/auth/addresses/${addressId}`);
  }

  /**
   * Get user's payment methods
   */
  static async getPaymentMethods() {
    return await apiClient.get('/users/me/payment-methods');
  }

  /**
   * Add payment method
   */
  static async addPaymentMethod(paymentMethod) {
    return await apiClient.post('/users/payment-methods', paymentMethod);
  }

  /**
   * Update payment method
   */
  static async updatePaymentMethod(paymentMethodId, paymentMethod) {
    return await apiClient.put(`/users/payment-methods/${paymentMethodId}`, paymentMethod);
  }

  /**
   * Delete payment method
   */
  static async deletePaymentMethod(paymentMethodId) {
    return await apiClient.delete(`/users/payment-methods/${paymentMethodId}`);
  }

  /**
   * Set default payment method
   */
  static async setDefaultPaymentMethod(paymentMethodId) {
    return await apiClient.put(`/users/payment-methods/${paymentMethodId}/default`);
  }

  /**
   * Get user's default payment method
   */
  static async getDefaultPaymentMethod() {
    return await apiClient.get('/users/me/payment-methods/default');
  }
}

export default AuthAPI;