/**
 * Tests for Products API - Comprehensive test suite aligned with backend reality
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProductsAPI } from '../../api/products';
import { apiClient } from '../../api/client';

// Mock the API client
vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    upload: vi.fn()
  }
}));

const mockApiClient = vi.mocked(apiClient);

describe('ProductsAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getProducts', () => {
    it('should get products with query parameters', async () => {
      const params = {
        q: 'laptop',
        category: 'electronics',
        min_price: 100,
        max_price: 1000,
        min_rating: 4,
        max_rating: 5,
        availability: true,
        sort_by: 'price',
        sort_order: 'asc',
        page: 1,
        limit: 12
      };

      const mockResponse = {
        success: true,
        data: {
          data: [
            { id: 'prod123', name: 'Gaming Laptop', price: 899 }
          ],
          total: 1,
          page: 1,
          per_page: 12,
          total_pages: 1
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await ProductsAPI.getProducts(params);

      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/v1/products?q=laptop&category=electronics&min_price=100&max_price=1000&min_rating=4&max_rating=5&availability=true&sort_by=price&sort_order=asc&page=1&limit=12'
      );
      expect(result).toEqual(mockResponse);
    });

    it('should get products without query parameters', async () => {
      const mockResponse = {
        success: true,
        data: { data: [], total: 0 }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await ProductsAPI.getProducts({});

      expect(mockApiClient.get).toHaveBeenCalledWith('/v1/products');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getProduct', () => {
    it('should get product by ID', async () => {
      const productId = 'prod123';
      const mockResponse = {
        success: true,
        data: {
          id: productId,
          name: 'Gaming Laptop',
          description: 'High-performance gaming laptop',
          variants: [],
          reviews: []
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await ProductsAPI.getProduct(productId);

      expect(mockApiClient.get).toHaveBeenCalledWith(`/v1/products/${productId}`);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('searchProducts', () => {
    it('should search products with advanced fuzzy matching', async () => {
      const query = 'gaming laptop';
      const filters = {
        category_id: 'cat123',
        min_price: 500,
        max_price: 2000,
        limit: 20
      };

      const mockResponse = {
        success: true,
        data: {
          query: query,
          filters: filters,
          products: [
            { id: 'prod123', name: 'Gaming Laptop Pro', relevance_score: 0.95 }
          ],
          count: 1
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await ProductsAPI.searchProducts(query, filters);

      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/v1/products/search?q=gaming+laptop&category_id=cat123&min_price=500&max_price=2000&limit=20'
      );
      expect(result).toEqual(mockResponse);
    });

    it('should return empty results for short queries', async () => {
      const result = await ProductsAPI.searchProducts('a', {});

      expect(result).toEqual({ data: { products: [], count: 0 } });
      expect(mockApiClient.get).not.toHaveBeenCalled();
    });

    it('should handle empty query', async () => {
      const result = await ProductsAPI.searchProducts('', {});

      expect(result).toEqual({ data: { products: [], count: 0 } });
      expect(mockApiClient.get).not.toHaveBeenCalled();
    });
  });

  describe('searchCategories', () => {
    it('should search categories with fuzzy matching', async () => {
      const query = 'electron';
      const limit = 10;

      const mockResponse = {
        success: true,
        data: {
          query: query,
          categories: [
            { id: 'cat123', name: 'Electronics', relevance_score: 0.9 }
          ],
          count: 1
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await ProductsAPI.searchCategories(query, limit);

      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/v1/products/categories/search?q=electron&limit=10'
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getHomeData', () => {
    it('should get all home page data in one request', async () => {
      const mockResponse = {
        success: true,
        data: {
          categories: [
            { id: 'cat123', name: 'Electronics' }
          ],
          featured: [
            { id: 'prod123', name: 'Featured Product' }
          ],
          popular: [
            { id: 'prod456', name: 'Popular Product' }
          ],
          deals: [
            { id: 'prod789', name: 'Deal Product', on_sale: true }
          ]
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await ProductsAPI.getHomeData();

      expect(mockApiClient.get).toHaveBeenCalledWith('/v1/products/home');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Product Variants', () => {
    describe('getProductVariants', () => {
      it('should get all variants for a product', async () => {
        const productId = 'prod123';
        const mockResponse = {
          success: true,
          data: [
            { id: 'var123', name: 'Red - Large', price: 99.99 },
            { id: 'var456', name: 'Blue - Medium', price: 89.99 }
          ]
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.getProductVariants(productId);

        expect(mockApiClient.get).toHaveBeenCalledWith(`/v1/products/${productId}/variants`);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('getVariant', () => {
      it('should get specific variant by ID', async () => {
        const variantId = 'var123';
        const mockResponse = {
          success: true,
          data: {
            id: variantId,
            name: 'Red - Large',
            price: 99.99,
            stock_quantity: 10
          }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.getVariant(variantId);

        expect(mockApiClient.get).toHaveBeenCalledWith(`/v1/products/variants/${variantId}`);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('getVariantQRCode', () => {
      it('should get QR code for variant', async () => {
        const variantId = 'var123';
        const mockResponse = {
          success: true,
          data: { qr_code_url: 'https://example.com/qr/var123.png' }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.getVariantQRCode(variantId);

        expect(mockApiClient.get).toHaveBeenCalledWith(`/v1/products/variants/${variantId}/qrcode`);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('getVariantBarcode', () => {
      it('should get barcode for variant', async () => {
        const variantId = 'var123';
        const mockResponse = {
          success: true,
          data: { barcode_url: 'https://example.com/barcode/var123.png' }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.getVariantBarcode(variantId);

        expect(mockApiClient.get).toHaveBeenCalledWith(`/v1/products/variants/${variantId}/barcode`);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('generateVariantCodes', () => {
      it('should generate barcode and QR code for variant', async () => {
        const variantId = 'var123';
        const mockResponse = {
          success: true,
          data: {
            variant_id: variantId,
            barcode: 'https://example.com/barcode/var123.png',
            qr_code: 'https://example.com/qr/var123.png'
          },
          message: 'Codes generated successfully'
        };

        mockApiClient.post.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.generateVariantCodes(variantId);

        expect(mockApiClient.post).toHaveBeenCalledWith(`/v1/products/variants/${variantId}/codes/generate`);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('updateVariantCodes', () => {
      it('should update barcode and QR code for variant', async () => {
        const variantId = 'var123';
        const codes = {
          barcode: 'new-barcode-url',
          qr_code: 'new-qr-url'
        };

        const mockResponse = {
          success: true,
          data: {
            variant_id: variantId,
            barcode: codes.barcode,
            qr_code: codes.qr_code
          },
          message: 'Codes updated successfully'
        };

        mockApiClient.put.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.updateVariantCodes(variantId, codes);

        expect(mockApiClient.put).toHaveBeenCalledWith(`/v1/products/variants/${variantId}/codes`, codes);
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Product Recommendations', () => {
    describe('getRecommendedProducts', () => {
      it('should get recommended products based on a product', async () => {
        const productId = 'prod123';
        const limit = 4;

        const mockResponse = {
          success: true,
          data: [
            { id: 'prod456', name: 'Related Product 1' },
            { id: 'prod789', name: 'Related Product 2' }
          ]
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.getRecommendedProducts(productId, limit);

        expect(mockApiClient.get).toHaveBeenCalledWith(`/v1/products/${productId}/recommendations?limit=${limit}`);
        expect(result).toEqual(mockResponse);
      });

      it('should return empty results when no productId provided', async () => {
        const result = await ProductsAPI.getRecommendedProducts(null, 4);

        expect(result).toEqual({ data: [] });
        expect(mockApiClient.get).not.toHaveBeenCalled();
      });
    });
  });

  describe('Product Reviews', () => {
    describe('getProductReviews', () => {
      it('should get product reviews with pagination', async () => {
        const productId = 'prod123';
        const page = 1;
        const limit = 10;

        const mockResponse = {
          success: true,
          data: {
            reviews: [
              { id: 'rev123', rating: 5, comment: 'Great product!' }
            ],
            total: 1,
            page: 1
          }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.getProductReviews(productId, page, limit);

        expect(mockApiClient.get).toHaveBeenCalledWith(`/v1/reviews/product/${productId}?page=${page}&limit=${limit}`);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('addProductReview', () => {
      it('should add product review', async () => {
        const productId = 'prod123';
        const review = {
          rating: 5,
          comment: 'Excellent product!',
          title: 'Love it!'
        };

        const mockResponse = {
          success: true,
          data: {
            id: 'rev123',
            product_id: productId,
            ...review
          },
          message: 'Review added successfully'
        };

        mockApiClient.post.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.addProductReview(productId, review);

        expect(mockApiClient.post).toHaveBeenCalledWith('/v1/reviews', {
          ...review,
          product_id: productId
        });
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Inventory', () => {
    describe('checkAvailability', () => {
      it('should check product variant availability', async () => {
        const variantId = 'var123';
        const quantity = 2;

        const mockResponse = {
          success: true,
          data: {
            variant_id: variantId,
            available: true,
            stock_quantity: 10
          }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.checkAvailability(variantId, quantity);

        expect(mockApiClient.get).toHaveBeenCalledWith(`/v1/inventory/check-stock/${variantId}?quantity=${quantity}`);
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Supplier/Admin Endpoints', () => {
    describe('createProduct', () => {
      it('should create new product', async () => {
        const product = {
          name: 'New Product',
          description: 'Product description',
          category_id: 'cat123'
        };

        const mockResponse = {
          success: true,
          data: {
            id: 'prod123',
            ...product
          },
          message: 'Product created successfully'
        };

        mockApiClient.post.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.createProduct(product);

        expect(mockApiClient.post).toHaveBeenCalledWith('/v1/products', product);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('updateProduct', () => {
      it('should update existing product', async () => {
        const productId = 'prod123';
        const updates = {
          name: 'Updated Product Name',
          description: 'Updated description'
        };

        const mockResponse = {
          success: true,
          data: {
            id: productId,
            ...updates
          },
          message: 'Product updated successfully'
        };

        mockApiClient.put.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.updateProduct(productId, updates);

        expect(mockApiClient.put).toHaveBeenCalledWith(`/v1/products/${productId}`, updates);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('deleteProduct', () => {
      it('should delete product', async () => {
        const productId = 'prod123';
        const mockResponse = {
          success: true,
          message: 'Product deleted successfully'
        };

        mockApiClient.delete.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.deleteProduct(productId);

        expect(mockApiClient.delete).toHaveBeenCalledWith(`/v1/products/${productId}`);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('uploadProductImage', () => {
      it('should upload product image', async () => {
        const variantId = 'var123';
        const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
        const isPrimary = true;
        const onProgress = vi.fn();

        const mockResponse = {
          success: true,
          data: {
            image_id: 'img123',
            url: 'https://example.com/images/img123.jpg'
          }
        };

        mockApiClient.upload.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.uploadProductImage(variantId, file, isPrimary, onProgress);

        expect(mockApiClient.upload).toHaveBeenCalledWith(
          `/products/variants/${variantId}/images`,
          file,
          onProgress
        );
        expect(result).toEqual(mockResponse);
      });
    });

    describe('updateInventory', () => {
      it('should update variant inventory', async () => {
        const variantId = 'var123';
        const stock = 50;

        const mockResponse = {
          success: true,
          data: {
            variant_id: variantId,
            stock_quantity: stock
          },
          message: 'Inventory updated successfully'
        };

        mockApiClient.put.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.updateInventory(variantId, stock);

        expect(mockApiClient.put).toHaveBeenCalledWith(`/products/variants/${variantId}/inventory`, { stock });
        expect(result).toEqual(mockResponse);
      });
    });

    describe('getSupplierProducts', () => {
      it('should get supplier products with filters', async () => {
        const params = {
          q: 'laptop',
          category: 'electronics',
          page: 1,
          limit: 20
        };

        const mockResponse = {
          success: true,
          data: {
            products: [
              { id: 'prod123', name: 'Supplier Product' }
            ],
            total: 1
          }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.getSupplierProducts(params);

        expect(mockApiClient.get).toHaveBeenCalledWith(
          '/suppliers/products?q=laptop&category=electronics&page=1&limit=20'
        );
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Featured and Popular Products', () => {
    describe('getFeaturedProducts', () => {
      it('should get featured products', async () => {
        const limit = 5;
        const mockResponse = {
          success: true,
          data: [
            { id: 'prod123', name: 'Featured Product', featured: true }
          ]
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.getFeaturedProducts(limit);

        expect(mockApiClient.get).toHaveBeenCalledWith(`/v1/products/featured?limit=${limit}`);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('getPopularProducts', () => {
      it('should get popular products', async () => {
        const limit = 8;
        const mockResponse = {
          success: true,
          data: [
            { id: 'prod456', name: 'Popular Product', popular: true }
          ]
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await ProductsAPI.getPopularProducts(limit);

        expect(mockApiClient.get).toHaveBeenCalledWith(`/v1/products/popular?limit=${limit}`);
        expect(result).toEqual(mockResponse);
      });
    });
  });
});