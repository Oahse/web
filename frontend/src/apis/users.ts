/**
 * Users API endpoints (placeholder - functionality moved to auth.ts)
 */

import { apiClient   } from './client';


export class UsersAPI {
  /**
   * Get user profile
   */
  static async getProfile() {
    return await apiClient.get('/users/profile');
  }

  /**
   * Update user profile
   */
  static async updateProfile(data) {
    return await apiClient.put('/users/profile', data);
  }
}

export default UsersAPI;