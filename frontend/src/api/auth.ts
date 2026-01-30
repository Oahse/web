/**
 * Authentication API endpoints
 * 
 * ACCESS LEVELS:
 * - Public: Registration, login, password reset, email verification
 * - Authenticated: Profile management, password change, address management, logout
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
  phone?: string | undefined;
  age?: string | undefined;
  gender?: string | undefined;
  country?: string | undefined;
  language?: string | undefined;
  timezone?: string | undefined;
  is_active?: boolean | undefined;
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
   * ACCESS: Public - No authentication required
   */
  static async register(data: RegisterData) {
    const response = await apiClient.post('/auth/register', data);
    
    // Don't set tokens here - let the AuthContext handle it
    // The response structure from backend is: { success: true, data: { access_token, refresh_token, user } }
    
    return response;
  }

  /**
   * Login user
   * ACCESS: Public - No authentication required
   */
  static async login(data: LoginData) {
    const response = await apiClient.post('/auth/login', data);
    
    // Don't set tokens here - let the AuthContext handle it
    // The response structure from backend is: { success: true, data: { access_token, refresh_token, user } }
    
    return response;
  }

  /**
   * Logout user
   * ACCESS: Authenticated - Requires user login
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
   * ACCESS: Authenticated - Requires user login
   */
  static async getProfile() {
    return await apiClient.get('/auth/profile');
  }

  /**
   * Update user profile
   * ACCESS: Authenticated - Requires user login
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
   * ACCESS: Authenticated - Requires user login
   */
  static async changePassword(data: ChangePasswordData) {
    return await apiClient.put('/auth/change-password', data);
  }

  /**
   * Request password reset
   * ACCESS: Public - No authentication required
   */
  static async requestPasswordReset(email: string) {
    return await apiClient.post('/auth/forgot-password', { email });
  }

  /**
   * Forgot password - alias for requestPasswordReset
   * ACCESS: Public - No authentication required
   */
  static async forgotPassword(email: string) {
    return await this.requestPasswordReset(email);
  }

  /**
   * Reset password with token
   * ACCESS: Public - No authentication required (uses token)
   */
  static async resetPassword(data: ResetPasswordData) {
    return await apiClient.post('/auth/reset-password', data);
  }

  /**
   * Verify email with token
   * ACCESS: Public - No authentication required (uses token)
   */
  static async verifyEmail(token: string) {
    return await apiClient.get(`/auth/verify-email?token=${token}`);
  }

  /**
   * Resend email verification
   * ACCESS: Authenticated - Requires user login
   */
  static async resendVerification() {
    return await apiClient.post('/users/resend-verification');
  }

  /**
   * Social authentication
   * ACCESS: Public - No authentication required
   */
  static async socialLogin(token: string, provider: string) {
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
   * ACCESS: Public - Uses refresh token for authentication
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
   * ACCESS: Authenticated - Requires user login and password confirmation
   */
  static async deleteAccount(password: string) {
    const response = await apiClient.delete('/users', {
      data: { password }
    });
    
    // Clear tokens after successful deletion
    TokenManager.clearTokens();
    
    return response;
  }

  /**
   * Get user's addresses
   * ACCESS: Authenticated - Requires user login
   */
  static async getAddresses() {
    return await apiClient.get(`/auth/addresses`);
  }

  /**
   * Create new address
   * ACCESS: Authenticated - Requires user login
   */
  static async createAddress(address: any) {
    return await apiClient.post('/auth/addresses', address);
  }

  /**
   * Update address
   * ACCESS: Authenticated - Requires user login
   */
  static async updateAddress(addressId: string, address: any) {
    return await apiClient.put(`/auth/addresses/${addressId}`, address);
  }

  /**
   * Delete address
   * ACCESS: Authenticated - Requires user login
   */
  static async deleteAddress(addressId: string) {
    return await apiClient.delete(`/auth/addresses/${addressId}`);
  }


}

export default AuthAPI;