/**
 * CORRECTED: Products API endpoints with all required methods
 * Fixes: Issue 1.5 - Missing getRecommendedProducts method
 * 
 * ACCESS LEVELS:
 * - Public: Product listings, search, categories, variants, recommendations
 * - Authenticated: Product reviews, availability checks
 * - Supplier/Admin: Product management, inventory updates, image uploads
 * - Admin Only: Product moderation, featured product management
 */

import { apiClient } from './client';

export class ProductsAPI {
  /**
   * Get all products with optional filters
   * ACCESS: Public - No authentication required
   */
  static async getProducts(params: any) {
    const queryParams = new URLSearchParams();
    
    if (params?.q) queryParams.append('q', params.q);
    if (params?.category) queryParams.append('category', params.category);
    if (params?.min_price) queryParams.append('min_price', params.min_price.toString());
    if (params?.max_price) queryParams.append('max_price', params.max_price.toString());
    if (params?.min_rating) queryParams.append('min_rating', params.min_rating.toString());
    if (params?.max_rating) queryParams.append('max_rating', params.max_rating.toString());
    if (params?.availability !== undefined) queryParams.append('availability', params.availability.toString());
    if (params?.sort_by) queryParams.append('sort_by', params.sort_by);
    if (params?.sort_order) queryParams.append('sort_order', params.sort_order);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/products${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get product by ID
   * ACCESS: Public - No authentication required
   */
  static async getProduct(productId: string) {
    return await apiClient.get(`/products/${productId}`);
  }

  /**
   * Search products (advanced search with fuzzy matching)
   * ACCESS: Public - No authentication required
   */
  static async searchProducts(query: string, filters: any) {
    // Ensure query is provided and not empty
    if (!query || query.trim().length < 2) {
      return { data: { products: [], count: 0 } };
    }

    const params = new URLSearchParams({ q: query.trim() });
    
    if (filters?.category_id) params.append('category_id', filters.category_id);
    if (filters?.min_price !== undefined) params.append('min_price', filters.min_price.toString());
    if (filters?.max_price !== undefined) params.append('max_price', filters.max_price.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());

    return await apiClient.get(`/products/search?${params.toString()}`);
  }

  /**
   * Search categories (advanced search with fuzzy matching)
   * ACCESS: Public - No authentication required
   */
  static async searchCategories(query: string, limit = 20) {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString()
    });
    
    return await apiClient.get(`/products/categories/search?${params.toString()}`);
  }

  /**
   * Get all home page data in one request
   * ACCESS: Public - No authentication required
   */
  static async getHomeData() {
    return await apiClient.get('/products/home');
  }

  /**
   * Get product variants
   * ACCESS: Public - No authentication required
   */
  static async getProductVariants(productId: string) {
    return await apiClient.get(`/products/${productId}/variants`);
  }

  /**
   * Get variant by ID
   * ACCESS: Public - No authentication required
   */
  static async getVariant(variantId: string) {
    return await apiClient.get(`/products/variants/${variantId}`);
  }

  /**
   * Get variant QR code
   * ACCESS: Public - No authentication required
   */
  static async getVariantQRCode(variantId: string) {
    return await apiClient.get(`/products/variants/${variantId}/qrcode`);
  }

  /**
   * Get variant barcode
   * ACCESS: Public - No authentication required
   */
  static async getVariantBarcode(variantId: string) {
    return await apiClient.get(`/products/variants/${variantId}/barcode`);
  }

  /**
   * Generate barcode and QR code for variant
   * ACCESS: Supplier/Admin - Requires supplier or admin role
   */
  static async generateVariantCodes(variantId: string) {
    return await apiClient.post(`/products/variants/${variantId}/codes/generate`);
  }

  /**
   * Update barcode and/or QR code for variant
   * ACCESS: Supplier/Admin - Requires supplier or admin role
   */
  static async updateVariantCodes(variantId: string, codes: any) {
    return await apiClient.put(`/products/variants/${variantId}/codes`, codes);
  }

  /**
   * Get featured products
   * ACCESS: Public - No authentication required
   */
  static async getFeaturedProducts(limit = 10) {
    return await apiClient.get(`/products/featured?limit=${limit}`);
  }
  
  /**
   * Get popular products
   * ACCESS: Public - No authentication required
   */
  static async getPopularProducts(limit = 10) {
    return await apiClient.get(`/products/popular?limit=${limit}`);
  }

  /**
   * FIXED: Get recommended/related products for a specific product
   * ACCESS: Public - No authentication required
   * Issue 1.5: This method was missing and called from ProductDetails.tsx line 148
   * 
   * @param productId - The product ID to get recommendations for
   * @param limit - Number of recommendations to return (default: 4)
   */
  static async getRecommendedProducts(productId: string, limit = 4) {
    return await apiClient.get(`/products/${productId}/recommended?limit=${limit}`);
  }

  /**
   * Get categories
   * ACCESS: Public - No authentication required
   */
  static async getCategories(params?: any) {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.sort) queryParams.append('sort', params.sort);

    const url = `/products/categories${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get single category
   * ACCESS: Public - No authentication required
   */
  static async getCategory(categoryId: string) {
    return await apiClient.get(`/products/categories/${categoryId}`);
  }

  /**
   * Get products in category
   * ACCESS: Public - No authentication required
   */
  static async getProductsByCategory(categoryId: string, params?: any) {
    const queryParams = new URLSearchParams({ category: categoryId });
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.sort_by) queryParams.append('sort_by', params.sort_by);
    if (params?.sort_order) queryParams.append('sort_order', params.sort_order);

    return await apiClient.get(`/products?${queryParams.toString()}`);
  }

  /**
   * Get product images
   * ACCESS: Public - No authentication required
   */
  static async getProductImages(productId: string) {
    return await apiClient.get(`/products/${productId}/images`);
  }
}

/**
 * Categories API endpoints
 */
export class CategoriesAPI {
  static async getCategories(params?: any) {
    return ProductsAPI.getCategories(params);
  }

  static async getCategory(categoryId: string) {
    return ProductsAPI.getCategory(categoryId);
  }
}
