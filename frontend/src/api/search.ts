/**
 * Search API endpoints
 * 
 * ACCESS LEVELS:
 * - Public: Product and category search, autocomplete suggestions
 * - Admin: User search functionality
 */

import { apiClient } from './client';

export class SearchAPI {
  /**
   * Get autocomplete suggestions for search queries
   * ACCESS: Public - No authentication required for product/category suggestions
   * ACCESS: Admin - Authentication required for user suggestions
   */
  static async getAutocompleteSuggestions(query: string, type: 'product' | 'user' | 'category' = 'product', limit: number = 10) {
    const params = new URLSearchParams({
      q: query,
      type,
      limit: limit.toString()
    });
    
    return await apiClient.get(`/v1/search/autocomplete?${params.toString()}`);
  }

  /**
   * Advanced search for products (distributed to products API)
   * ACCESS: Public - No authentication required
   */
  static async searchProducts(query: string, filters?: {
    category_id?: string;
    min_price?: number;
    max_price?: number;
    limit?: number;
  }) {
    const params = new URLSearchParams({ q: query });
    
    if (filters?.category_id) params.append('category_id', filters.category_id);
    if (filters?.min_price !== undefined) params.append('min_price', filters.min_price.toString());
    if (filters?.max_price !== undefined) params.append('max_price', filters.max_price.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());
    
    return await apiClient.get(`/v1/products/search?${params.toString()}`);
  }

  /**
   * Advanced search for users (distributed to users API)
   * ACCESS: Admin - Requires admin authentication
   */
  static async searchUsers(query: string, filters?: {
    role?: 'Customer' | 'Supplier' | 'Admin';
    limit?: number;
  }) {
    const params = new URLSearchParams({ q: query });
    
    if (filters?.role) params.append('role', filters.role);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    
    return await apiClient.get(`/v1/users/search?${params.toString()}`);
  }

  /**
   * Advanced search for categories (distributed to products API)
   * ACCESS: Public - No authentication required
   */
  static async searchCategories(query: string, limit: number = 20) {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString()
    });
    
    return await apiClient.get(`/v1/products/categories/search?${params.toString()}`);
  }

  /**
   * Universal search across all types
   * ACCESS: Mixed - Public for products/categories, Admin for users
   */
  static async universalSearch(query: string, options?: {
    includeProducts?: boolean;
    includeUsers?: boolean;
    includeCategories?: boolean;
    limit?: number;
  }) {
    const {
      includeProducts = true,
      includeUsers = false,
      includeCategories = true,
      limit = 10
    } = options || {};

    const promises = [];
    
    if (includeProducts) {
      promises.push(
        this.searchProducts(query, { limit }).catch(() => ({ data: { products: [] } }))
      );
    }
    
    if (includeUsers) {
      promises.push(
        this.searchUsers(query, { limit }).catch(() => ({ data: { users: [] } }))
      );
    }
    
    if (includeCategories) {
      promises.push(
        this.searchCategories(query, limit).catch(() => ({ data: { categories: [] } }))
      );
    }

    const results = await Promise.all(promises);
    
    return {
      success: true,
      data: {
        query,
        products: includeProducts ? results[0]?.data?.products || [] : [],
        users: includeUsers ? results[includeProducts ? 1 : 0]?.data?.users || [] : [],
        categories: includeCategories ? results[includeProducts && includeUsers ? 2 : includeProducts || includeUsers ? 1 : 0]?.data?.categories || [] : []
      }
    };
  }
}

export default SearchAPI;