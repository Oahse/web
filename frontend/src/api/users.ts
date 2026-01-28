/**
 * Users API endpoints
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

  /**
   * Search users (advanced search with fuzzy matching)
   */
  static async searchUsers(query, filters) {
    const params = new URLSearchParams({ q: query });
    
    if (filters?.role) params.append('role', filters.role);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    return await apiClient.get(`/users/search?${params.toString()}`);
  }

  /**
   * Get users list (for admin)
   */
  static async getUsers(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.role) queryParams.append('role', params.role);
    if (params?.q) queryParams.append('q', params.q);
    if (params?.search_mode) queryParams.append('search_mode', params.search_mode);

    const url = `/users${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }
}

export default UsersAPI;