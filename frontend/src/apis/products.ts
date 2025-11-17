/**
 * Products API endpoints
 */

import { apiClient } from './client';
// import {
//   Product,
//   ProductVariant, 
//   ProductFilters,
//   PaginatedResponse,
//   ApiResponse,
//   Review

export class ProductsAPI {
  /**
   * Get all products with optional filters
   */
  static async getProducts(params) {
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
   */
  static async getProduct(productId) {
    return await apiClient.get(`/products/${productId}`);
  }

  /**
   * Search products
   */
  static async searchProducts(query, filters) {
    const params = { q: query, ...filters };
    return await this.getProducts(params);
  }

  /**
   * Get all home page data in one request
   */
  static async getHomeData() {
    return await apiClient.get('/products/home');
  }

  /**
   * Get product variants
   */
  static async getProductVariants(productId) {
    return await apiClient.get(`/products/${productId}/variants`);
  }

  /**
   * Get variant by ID
   */
  static async getVariant(variantId) {
    return await apiClient.get(`/products/variants/${variantId}`);
  }

  /**
   * Get variant QR code
   */
  static async getVariantQRCode(variantId) {
    return await apiClient.get(`/products/variants/${variantId}/qrcode`);
  }

  /**
   * Get variant barcode
   */
  static async getVariantBarcode(variantId) {
    return await apiClient.get(`/products/variants/${variantId}/barcode`);
  }

  /**
   * Get featured products
   */
  static async getFeaturedProducts(limit = 10) {
    return await apiClient.get(`/products/featured?limit=${limit}`);
  }
  
  static async getPopularProducts(limit = 10) {
    return await apiClient.get(`/products/popular?limit=${limit}`);
  }

  /**
   * Get recommended products
   */
  static async getRecommendedProducts(productId, limit = 10) {
    const url = productId 
      ? `/products/${productId}/recommendations?limit=${limit}`
      : `/products/recommendations?limit=${limit}`;
    return await apiClient.get(url);
  }

  /**
   * Get product reviews
   */
  static async getProductReviews(productId, page = 1, limit = 10) {
    return await apiClient.get(`/products/${productId}/reviews?page=${page}&limit=${limit}`);
  }

  /**
   * Add product review
   */
  static async addProductReview(productId, review) {
    return await apiClient.post(`/products/${productId}/reviews`, review);
  }

  /**
   * Get product availability
   */
  static async checkAvailability(variantId, quantity = 1) {
    return await apiClient.get(`/products/variants/${variantId}/availability?quantity=${quantity}`);
  }

  // Supplier/Admin endpoints
  /**
   * Create new product (Supplier/Admin only)
   */
  static async createProduct(product) {
    return await apiClient.post('/products', product);
  }

  /**
   * Update product (Supplier/Admin only)
   */
  static async updateProduct(productId, updates) {
    return await apiClient.put(`/products/${productId}`, updates);
  }

  /**
   * Delete product (Supplier/Admin only)
   */
  static async deleteProduct(productId) {
    return await apiClient.delete(`/products/${productId}`);
  }

  /**
   * Create product variant (Supplier/Admin only)
   */
  static async createVariant(productId, variant) {
    return await apiClient.post(`/products/${productId}/variants`, variant);
  }

  /**
   * Update product variant (Supplier/Admin only)
   */
  static async updateVariant(variantId, updates) {
    return await apiClient.put(`/products/variants/${variantId}`, updates);
  }

  /**
   * Delete product variant (Supplier/Admin only)
   */
  static async deleteVariant(variantId) {
    return await apiClient.delete(`/products/variants/${variantId}`);
  }

  /**
   * Upload product images (Supplier/Admin only)
   */
  static async uploadProductImage(
    variantId, 
    file, 
    isPrimary = false,
    onProgress
  ) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('is_primary', isPrimary.toString());

    return await apiClient.upload(`/products/variants/${variantId}/images`, file, onProgress);
  }

  /**
   * Delete product image (Supplier/Admin only)
   */
  static async deleteProductImage(imageId) {
    return await apiClient.delete(`/products/images/${imageId}`);
  }

  /**
   * Update inventory (Supplier/Admin only)
   */
  static async updateInventory(variantId, stock) {
    return await apiClient.put(`/products/variants/${variantId}/inventory`, { stock });
  }

  /**
   * Get supplier products (Supplier only)
   */
  static async getSupplierProducts(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.q) queryParams.append('q', params.q);
    if (params?.category) queryParams.append('category', params.category);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/suppliers/products${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }
}

export default ProductsAPI;