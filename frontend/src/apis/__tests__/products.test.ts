import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProductsAPI } from '../products';
import { apiClient } from '../client';

// Mock the API client
vi.mock('../client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('ProductsAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getProducts', () => {
    it('calls API with correct parameters', async () => {
      const mockResponse = {
        success: true,
        data: {
          data: [],
          total: 0,
          page: 1,
          per_page: 10,
        },
      };

      (apiClient.get as any).mockResolvedValue(mockResponse);

      const params = {
        q: 'test',
        category: 'electronics',
        min_price: 10,
        max_price: 100,
        page: 1,
        limit: 10,
      };

      await ProductsAPI.getProducts(params);

      expect(apiClient.get).toHaveBeenCalledWith(
        '/products?q=test&category=electronics&min_price=10&max_price=100&page=1&limit=10'
      );
    });

    it('handles empty parameters', async () => {
      const mockResponse = { success: true, data: [] };
      (apiClient.get as any).mockResolvedValue(mockResponse);

      await ProductsAPI.getProducts({});

      expect(apiClient.get).toHaveBeenCalledWith('/products');
    });

    it('filters out undefined parameters', async () => {
      const mockResponse = { success: true, data: [] };
      (apiClient.get as any).mockResolvedValue(mockResponse);

      const params = {
        q: 'test',
        category: undefined,
        min_price: 10,
        max_price: undefined,
      };

      await ProductsAPI.getProducts(params);

      expect(apiClient.get).toHaveBeenCalledWith('/products?q=test&min_price=10');
    });
  });

  describe('getProduct', () => {
    it('calls API with product ID', async () => {
      const mockProduct = {
        id: 'product-1',
        name: 'Test Product',
        variants: [],
      };

      (apiClient.get as any).mockResolvedValue({
        success: true,
        data: mockProduct,
      });

      const result = await ProductsAPI.getProduct('product-1');

      expect(apiClient.get).toHaveBeenCalledWith('/products/product-1');
      expect(result.data).toEqual(mockProduct);
    });
  });

  describe('getVariant', () => {
    it('calls API with variant ID', async () => {
      const mockVariant = {
        id: 'variant-1',
        name: 'Test Variant',
        barcode: 'data:image/png;base64,barcode_data',
        qr_code: 'data:image/png;base64,qr_code_data',
      };

      (apiClient.get as any).mockResolvedValue({
        success: true,
        data: mockVariant,
      });

      const result = await ProductsAPI.getVariant('variant-1');

      expect(apiClient.get).toHaveBeenCalledWith('/products/variants/variant-1');
      expect(result.data).toEqual(mockVariant);
    });
  });

  describe('generateVariantCodes', () => {
    it('calls API to generate barcode and QR code', async () => {
      const mockCodes = {
        variant_id: 'variant-1',
        barcode: 'data:image/png;base64,new_barcode_data',
        qr_code: 'data:image/png;base64,new_qr_code_data',
      };

      (apiClient.post as any).mockResolvedValue({
        success: true,
        data: mockCodes,
      });

      const result = await ProductsAPI.generateVariantCodes('variant-1');

      expect(apiClient.post).toHaveBeenCalledWith('/products/variants/variant-1/codes/generate');
      expect(result.data).toEqual(mockCodes);
    });

    it('handles generation errors', async () => {
      (apiClient.post as any).mockRejectedValue({
        message: 'Failed to generate codes',
      });

      await expect(ProductsAPI.generateVariantCodes('variant-1')).rejects.toThrow();
    });
  });

  describe('updateVariantCodes', () => {
    it('calls API to update codes', async () => {
      const updateData = {
        barcode: 'data:image/png;base64,updated_barcode',
        qr_code: 'data:image/png;base64,updated_qr_code',
      };

      const mockResponse = {
        success: true,
        data: {
          variant_id: 'variant-1',
          ...updateData,
        },
      };

      (apiClient.put as any).mockResolvedValue(mockResponse);

      const result = await ProductsAPI.updateVariantCodes('variant-1', updateData);

      expect(apiClient.put).toHaveBeenCalledWith(
        '/products/variants/variant-1/codes',
        updateData
      );
      expect(result.data).toEqual(mockResponse.data);
    });

    it('handles partial updates', async () => {
      const updateData = {
        barcode: 'data:image/png;base64,updated_barcode',
      };

      const mockResponse = {
        success: true,
        data: {
          variant_id: 'variant-1',
          barcode: updateData.barcode,
          qr_code: 'existing_qr_code',
        },
      };

      (apiClient.put as any).mockResolvedValue(mockResponse);

      await ProductsAPI.updateVariantCodes('variant-1', updateData);

      expect(apiClient.put).toHaveBeenCalledWith(
        '/products/variants/variant-1/codes',
        updateData
      );
    });
  });

  describe('getVariantQRCode', () => {
    it('calls API to get QR code', async () => {
      const mockResponse = {
        success: true,
        data: {
          qr_code_url: 'data:image/png;base64,qr_code_data',
        },
      };

      (apiClient.get as any).mockResolvedValue(mockResponse);

      const result = await ProductsAPI.getVariantQRCode('variant-1');

      expect(apiClient.get).toHaveBeenCalledWith('/products/variants/variant-1/qrcode');
      expect(result.data.qr_code_url).toBeDefined();
    });
  });

  describe('getVariantBarcode', () => {
    it('calls API to get barcode', async () => {
      const mockResponse = {
        success: true,
        data: {
          barcode_url: 'data:image/png;base64,barcode_data',
        },
      };

      (apiClient.get as any).mockResolvedValue(mockResponse);

      const result = await ProductsAPI.getVariantBarcode('variant-1');

      expect(apiClient.get).toHaveBeenCalledWith('/products/variants/variant-1/barcode');
      expect(result.data.barcode_url).toBeDefined();
    });
  });

  describe('getHomeData', () => {
    it('calls API to get home page data', async () => {
      const mockHomeData = {
        categories: [],
        featured: [],
        popular: [],
        deals: [],
      };

      (apiClient.get as any).mockResolvedValue({
        success: true,
        data: mockHomeData,
      });

      const result = await ProductsAPI.getHomeData();

      expect(apiClient.get).toHaveBeenCalledWith('/products/home');
      expect(result.data).toEqual(mockHomeData);
    });
  });

  describe('searchProducts', () => {
    it('calls API with search query and filters', async () => {
      const mockResponse = {
        success: true,
        data: {
          data: [],
          total: 0,
        },
      };

      (apiClient.get as any).mockResolvedValue(mockResponse);

      const filters = {
        category: 'electronics',
        min_price: 10,
      };

      await ProductsAPI.searchProducts('test query', filters);

      expect(apiClient.get).toHaveBeenCalledWith(
        '/products?q=test+query&category=electronics&min_price=10'
      );
    });
  });

  describe('createProduct', () => {
    it('calls API to create product', async () => {
      const productData = {
        name: 'New Product',
        description: 'Product description',
        category_id: 'cat-1',
        variants: [
          {
            name: 'Standard',
            base_price: 99.99,
            stock: 10,
            sku: 'SKU-001',
          },
        ],
      };

      const mockResponse = {
        success: true,
        data: {
          id: 'product-1',
          ...productData,
        },
      };

      (apiClient.post as any).mockResolvedValue(mockResponse);

      const result = await ProductsAPI.createProduct(productData);

      expect(apiClient.post).toHaveBeenCalledWith('/products', productData);
      expect(result.data.id).toBeDefined();
    });
  });

  describe('updateProduct', () => {
    it('calls API to update product', async () => {
      const updateData = {
        name: 'Updated Product Name',
        description: 'Updated description',
      };

      const mockResponse = {
        success: true,
        data: {
          id: 'product-1',
          ...updateData,
        },
      };

      (apiClient.put as any).mockResolvedValue(mockResponse);

      const result = await ProductsAPI.updateProduct('product-1', updateData);

      expect(apiClient.put).toHaveBeenCalledWith('/products/product-1', updateData);
      expect(result.data).toEqual(mockResponse.data);
    });
  });

  describe('deleteProduct', () => {
    it('calls API to delete product', async () => {
      const mockResponse = {
        success: true,
        message: 'Product deleted successfully',
      };

      (apiClient.delete as any).mockResolvedValue(mockResponse);

      const result = await ProductsAPI.deleteProduct('product-1');

      expect(apiClient.delete).toHaveBeenCalledWith('/products/product-1');
      expect(result.success).toBe(true);
    });
  });

  describe('getRecommendedProducts', () => {
    it('calls API with product ID and limit', async () => {
      const mockProducts = [
        { id: 'product-2', name: 'Related Product 1' },
        { id: 'product-3', name: 'Related Product 2' },
      ];

      (apiClient.get as any).mockResolvedValue({
        success: true,
        data: mockProducts,
      });

      const result = await ProductsAPI.getRecommendedProducts('product-1', 4);

      expect(apiClient.get).toHaveBeenCalledWith('/products/product-1/recommendations?limit=4');
      expect(result.data).toEqual(mockProducts);
    });

    it('uses default limit when not specified', async () => {
      (apiClient.get as any).mockResolvedValue({
        success: true,
        data: [],
      });

      await ProductsAPI.getRecommendedProducts('product-1');

      expect(apiClient.get).toHaveBeenCalledWith('/products/product-1/recommendations?limit=10');
    });
  });

  describe('error handling', () => {
    it('propagates API errors', async () => {
      const mockError = {
        message: 'Network error',
        code: 500,
      };

      (apiClient.get as any).mockRejectedValue(mockError);

      await expect(ProductsAPI.getProduct('invalid-id')).rejects.toEqual(mockError);
    });

    it('handles validation errors', async () => {
      const validationError = {
        message: 'Validation failed',
        code: 422,
        details: {
          name: ['Name is required'],
          price: ['Price must be positive'],
        },
      };

      (apiClient.post as any).mockRejectedValue(validationError);

      await expect(ProductsAPI.createProduct({} as any)).rejects.toEqual(validationError);
    });
  });
});