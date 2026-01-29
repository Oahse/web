/**
 * Categories API endpoints
 * 
 * ACCESS LEVELS:
 * - Public: View categories and category details
 * - Admin: Create, update, delete categories (backend implementation)
 */

import { apiClient } from './client';

export class CategoriesAPI {
  /**
   * Get all categories
   * ACCESS: Public - No authentication required
   */
  static async getCategories() {
    return await apiClient.get('/v1/products/categories');
  }

  /**
   * Get category by ID
   * ACCESS: Public - No authentication required
   */
  static async getCategory(categoryId: string) {
    return await apiClient.get(`/v1/products/categories/${categoryId}`);
  }
}

export default CategoriesAPI;
