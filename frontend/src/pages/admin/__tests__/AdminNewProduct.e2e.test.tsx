/**
 * End-to-end tests for product creation flow
 * 
 * These tests verify:
 * - Form rendering and validation
 * - Image upload UI
 * - Form submission
 * - Product appears in list
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AdminNewProduct } from '../AdminNewProduct';
import * as ProductsAPI from '../../../apis/products';
import * as CategoriesAPI from '../../../apis/categories';
import * as githubLib from '../../../lib/github';

// Mock dependencies
vi.mock('../../../apis/products');
vi.mock('../../../apis/categories');
vi.mock('../../../lib/github');
vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(),
  },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('AdminNewProduct - End-to-End Tests', () => {
  const mockCategories = [
    { id: 'cat-1', name: 'Electronics', description: 'Electronic items' },
    { id: 'cat-2', name: 'Clothing', description: 'Apparel' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock categories API
    vi.mocked(CategoriesAPI.getCategories).mockResolvedValue({
      data: mockCategories,
    });
  });

  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <AdminNewProduct />
      </BrowserRouter>
    );
  };

  describe('5.1 Form Rendering and Validation', () => {
    it('should render the product creation form correctly', async () => {
      renderComponent();

      // Verify page title
      expect(screen.getByText('Add New Product')).toBeInTheDocument();
      expect(screen.getByText('Create a new product with variants')).toBeInTheDocument();

      // Verify form sections
      expect(screen.getByText('Product Information')).toBeInTheDocument();
      expect(screen.getByText('Product Variants')).toBeInTheDocument();

      // Verify form fields
      expect(screen.getByLabelText(/Product Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Description/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Category/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Active/i)).toBeInTheDocument();

      // Verify variant fields
      expect(screen.getByLabelText(/Variant Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Base Price/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Sale Price/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Stock Quantity/i)).toBeInTheDocument();

      // Verify action buttons
      expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Create Product/i })).toBeInTheDocument();
    });

    it('should load and display categories', async () => {
      renderComponent();

      await waitFor(() => {
        expect(CategoriesAPI.getCategories).toHaveBeenCalled();
      });

      const categorySelect = screen.getByLabelText(/Category/i);
      expect(categorySelect).toBeInTheDocument();

      // Categories should be loaded
      await waitFor(() => {
        const options = within(categorySelect as HTMLElement).getAllByRole('option');
        expect(options.length).toBeGreaterThan(1); // Including placeholder
      });
    });

    it('should validate required fields', async () => {
      const user = userEvent.setup();
      renderComponent();

      // Try to submit without filling required fields
      const submitButton = screen.getByRole('button', { name: /Create Product/i });
      await user.click(submitButton);

      // Should show validation error (toast)
      await waitFor(() => {
        const toast = require('react-hot-toast').toast;
        expect(toast.error).toHaveBeenCalledWith('Product name is required');
      });
    });

    it('should validate base price is required', async () => {
      const user = userEvent.setup();
      renderComponent();

      // Fill product name but not base price
      const nameInput = screen.getByLabelText(/Product Name/i);
      await user.type(nameInput, 'Test Product');

      // Clear base price
      const basePriceInput = screen.getByLabelText(/Base Price/i);
      await user.clear(basePriceInput);

      // Try to submit
      const submitButton = screen.getByRole('button', { name: /Create Product/i });
      await user.click(submitButton);

      // Should show validation error
      await waitFor(() => {
        const toast = require('react-hot-toast').toast;
        expect(toast.error).toHaveBeenCalledWith('All variants must have a base price');
      });
    });

    it('should perform real-time validation on product name', async () => {
      const user = userEvent.setup();
      renderComponent();

      const nameInput = screen.getByLabelText(/Product Name/i);
      
      // Type and verify input updates
      await user.type(nameInput, 'Test Product');
      expect(nameInput).toHaveValue('Test Product');

      // Clear and verify validation
      await user.clear(nameInput);
      expect(nameInput).toHaveValue('');
    });
  });

  describe('5.2 Image Upload UI', () => {
    it('should display image upload area', () => {
      renderComponent();

      // Verify upload area exists
      expect(screen.getByText(/Click to upload/i)).toBeInTheDocument();
      expect(screen.getByText(/PNG, JPG, GIF up to 10MB/i)).toBeInTheDocument();
    });

    it('should show preview images after selection', async () => {
      const user = userEvent.setup();
      renderComponent();

      // Mock file upload
      const file = new File(['test'], 'test-image.png', { type: 'image/png' });
      const fileInput = screen.getByLabelText(/Click to upload/i).querySelector('input[type="file"]');

      if (fileInput) {
        await user.upload(fileInput as HTMLInputElement, file);

        // Should show preview
        await waitFor(() => {
          const preview = screen.queryByAltText(/Preview/i);
          expect(preview).toBeInTheDocument();
        });
      }
    });

    it('should show upload progress indicator', async () => {
      const user = userEvent.setup();
      
      // Mock upload function to simulate delay
      vi.mocked(githubLib.uploadMultipleFiles).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve([
          { name: 'test.png', url: 'https://cdn.jsdelivr.net/gh/owner/repo@main/test.png', githubPath: 'test/test.png' }
        ]), 100))
      );

      renderComponent();

      const file = new File(['test'], 'test-image.png', { type: 'image/png' });
      const fileInput = screen.getByLabelText(/Click to upload/i).querySelector('input[type="file"]');

      if (fileInput) {
        await user.upload(fileInput as HTMLInputElement, file);

        // Should show loading toast
        await waitFor(() => {
          const toast = require('react-hot-toast').toast;
          expect(toast.loading).toHaveBeenCalledWith('Uploading images to CDN...', expect.any(Object));
        });
      }
    });

    it('should store CDN URLs in form state after upload', async () => {
      const user = userEvent.setup();
      
      const mockCdnUrl = 'https://cdn.jsdelivr.net/gh/owner/repo@main/products/test.png';
      vi.mocked(githubLib.uploadMultipleFiles).mockResolvedValue([
        { name: 'test.png', url: mockCdnUrl, githubPath: 'products/test.png' }
      ]);

      renderComponent();

      // Fill product name first
      const nameInput = screen.getByLabelText(/Product Name/i);
      await user.type(nameInput, 'Test Product');

      // Upload image
      const file = new File(['test'], 'test-image.png', { type: 'image/png' });
      const fileInput = screen.getByLabelText(/Click to upload/i).querySelector('input[type="file"]');

      if (fileInput) {
        await user.upload(fileInput as HTMLInputElement, file);

        // Wait for upload to complete
        await waitFor(() => {
          expect(githubLib.uploadMultipleFiles).toHaveBeenCalled();
        });

        // Verify success toast
        await waitFor(() => {
          const toast = require('react-hot-toast').toast;
          expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('uploaded successfully'), expect.any(Object));
        });
      }
    });

    it('should mark first image as primary', async () => {
      const user = userEvent.setup();
      
      vi.mocked(githubLib.uploadMultipleFiles).mockResolvedValue([
        { name: 'img1.png', url: 'https://cdn.jsdelivr.net/gh/owner/repo@main/img1.png', githubPath: 'products/img1.png' },
        { name: 'img2.png', url: 'https://cdn.jsdelivr.net/gh/owner/repo@main/img2.png', githubPath: 'products/img2.png' }
      ]);

      renderComponent();

      const nameInput = screen.getByLabelText(/Product Name/i);
      await user.type(nameInput, 'Test Product');

      const files = [
        new File(['test1'], 'img1.png', { type: 'image/png' }),
        new File(['test2'], 'img2.png', { type: 'image/png' })
      ];
      
      const fileInput = screen.getByLabelText(/Click to upload/i).querySelector('input[type="file"]');

      if (fileInput) {
        await user.upload(fileInput as HTMLInputElement, files);

        await waitFor(() => {
          expect(githubLib.uploadMultipleFiles).toHaveBeenCalled();
        });

        // Should show "Primary" badge on first image
        await waitFor(() => {
          const primaryBadge = screen.queryByText('Primary');
          expect(primaryBadge).toBeInTheDocument();
        });
      }
    });
  });

  describe('5.3 Form Submission', () => {
    it('should submit form with all required fields', async () => {
      const user = userEvent.setup();
      
      const mockProduct = {
        id: 'prod-123',
        name: 'Test Product',
        description: 'Test description',
        variants: [
          {
            id: 'var-1',
            name: 'Default',
            base_price: 19.99,
            sku: 'TES-12345678-0',
            images: []
          }
        ]
      };

      vi.mocked(ProductsAPI.createProduct).mockResolvedValue({
        success: true,
        data: mockProduct
      });

      renderComponent();

      // Fill in required fields
      const nameInput = screen.getByLabelText(/Product Name/i);
      await user.type(nameInput, 'Test Product');

      const descInput = screen.getByLabelText(/Description/i);
      await user.type(descInput, 'Test description');

      const basePriceInput = screen.getByLabelText(/Base Price/i);
      await user.clear(basePriceInput);
      await user.type(basePriceInput, '19.99');

      // Submit form
      const submitButton = screen.getByRole('button', { name: /Create Product/i });
      await user.click(submitButton);

      // Verify API was called
      await waitFor(() => {
        expect(ProductsAPI.createProduct).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Test Product',
            description: 'Test description',
            variants: expect.arrayContaining([
              expect.objectContaining({
                base_price: 19.99
              })
            ])
          })
        );
      });
    });

    it('should show success message after submission', async () => {
      const user = userEvent.setup();
      
      vi.mocked(ProductsAPI.createProduct).mockResolvedValue({
        success: true,
        data: { id: 'prod-123', name: 'Test Product', variants: [] }
      });

      renderComponent();

      // Fill and submit
      const nameInput = screen.getByLabelText(/Product Name/i);
      await user.type(nameInput, 'Test Product');

      const basePriceInput = screen.getByLabelText(/Base Price/i);
      await user.clear(basePriceInput);
      await user.type(basePriceInput, '19.99');

      const submitButton = screen.getByRole('button', { name: /Create Product/i });
      await user.click(submitButton);

      // Verify success toast
      await waitFor(() => {
        const toast = require('react-hot-toast').toast;
        expect(toast.success).toHaveBeenCalledWith('Product created successfully!');
      });
    });

    it('should redirect to product list after successful submission', async () => {
      const user = userEvent.setup();
      
      vi.mocked(ProductsAPI.createProduct).mockResolvedValue({
        success: true,
        data: { id: 'prod-123', name: 'Test Product', variants: [] }
      });

      renderComponent();

      // Fill and submit
      const nameInput = screen.getByLabelText(/Product Name/i);
      await user.type(nameInput, 'Test Product');

      const basePriceInput = screen.getByLabelText(/Base Price/i);
      await user.clear(basePriceInput);
      await user.type(basePriceInput, '19.99');

      const submitButton = screen.getByRole('button', { name: /Create Product/i });
      await user.click(submitButton);

      // Verify navigation
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/admin/products');
      });
    });

    it('should upload images before submission', async () => {
      const user = userEvent.setup();
      
      const mockCdnUrl = 'https://cdn.jsdelivr.net/gh/owner/repo@main/products/test.png';
      vi.mocked(githubLib.uploadMultipleFiles).mockResolvedValue([
        { name: 'test.png', url: mockCdnUrl, githubPath: 'products/test.png' }
      ]);

      vi.mocked(ProductsAPI.createProduct).mockResolvedValue({
        success: true,
        data: { id: 'prod-123', name: 'Test Product', variants: [] }
      });

      renderComponent();

      // Fill form
      const nameInput = screen.getByLabelText(/Product Name/i);
      await user.type(nameInput, 'Test Product');

      const basePriceInput = screen.getByLabelText(/Base Price/i);
      await user.clear(basePriceInput);
      await user.type(basePriceInput, '19.99');

      // Upload image
      const file = new File(['test'], 'test.png', { type: 'image/png' });
      const fileInput = screen.getByLabelText(/Click to upload/i).querySelector('input[type="file"]');

      if (fileInput) {
        await user.upload(fileInput as HTMLInputElement, file);

        await waitFor(() => {
          expect(githubLib.uploadMultipleFiles).toHaveBeenCalled();
        });
      }

      // Submit
      const submitButton = screen.getByRole('button', { name: /Create Product/i });
      await user.click(submitButton);

      // Verify product creation includes image URLs
      await waitFor(() => {
        expect(ProductsAPI.createProduct).toHaveBeenCalledWith(
          expect.objectContaining({
            variants: expect.arrayContaining([
              expect.objectContaining({
                image_urls: expect.arrayContaining([mockCdnUrl])
              })
            ])
          })
        );
      });
    });

    it('should prevent submission while images are uploading', async () => {
      const user = userEvent.setup();
      
      // Mock slow upload
      vi.mocked(githubLib.uploadMultipleFiles).mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve([
          { name: 'test.png', url: 'https://cdn.jsdelivr.net/gh/owner/repo@main/test.png', githubPath: 'test/test.png' }
        ]), 1000))
      );

      renderComponent();

      const nameInput = screen.getByLabelText(/Product Name/i);
      await user.type(nameInput, 'Test Product');

      const basePriceInput = screen.getByLabelText(/Base Price/i);
      await user.clear(basePriceInput);
      await user.type(basePriceInput, '19.99');

      // Start upload
      const file = new File(['test'], 'test.png', { type: 'image/png' });
      const fileInput = screen.getByLabelText(/Click to upload/i).querySelector('input[type="file"]');

      if (fileInput) {
        await user.upload(fileInput as HTMLInputElement, file);
      }

      // Try to submit immediately
      const submitButton = screen.getByRole('button', { name: /Create Product/i });
      await user.click(submitButton);

      // Should show error
      await waitFor(() => {
        const toast = require('react-hot-toast').toast;
        expect(toast.error).toHaveBeenCalledWith('Please wait for images to finish uploading');
      });
    });
  });
});

describe('5.4 Product Appears in List', () => {
  it('should display newly created product in product list', async () => {
    const user = userEvent.setup();
    
    const mockProduct = {
      id: 'prod-123',
      name: 'New Test Product',
      description: 'Test description',
      category: { id: 'cat-1', name: 'Electronics' },
      variants: [
        {
          id: 'var-1',
          name: 'Default',
          base_price: 29.99,
          sku: 'NEW-12345678-0',
          stock: 100,
          images: [
            {
              id: 'img-1',
              url: 'https://cdn.jsdelivr.net/gh/owner/repo@main/products/test.png',
              is_primary: true
            }
          ]
        }
      ]
    };

    // Mock product creation
    vi.mocked(ProductsAPI.createProduct).mockResolvedValue({
      success: true,
      data: mockProduct
    });

    renderComponent();

    // Fill and submit form
    const nameInput = screen.getByLabelText(/Product Name/i);
    await user.type(nameInput, 'New Test Product');

    const basePriceInput = screen.getByLabelText(/Base Price/i);
    await user.clear(basePriceInput);
    await user.type(basePriceInput, '29.99');

    const submitButton = screen.getByRole('button', { name: /Create Product/i });
    await user.click(submitButton);

    // Wait for navigation
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/admin/products');
    });

    // Verify product was created with correct data
    expect(ProductsAPI.createProduct).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'New Test Product'
      })
    );
  });

  it('should display product with images from CDN', async () => {
    const user = userEvent.setup();
    
    const mockCdnUrl = 'https://cdn.jsdelivr.net/gh/owner/repo@main/products/product-image.png';
    
    vi.mocked(githubLib.uploadMultipleFiles).mockResolvedValue([
      { name: 'product-image.png', url: mockCdnUrl, githubPath: 'products/product-image.png' }
    ]);

    const mockProduct = {
      id: 'prod-456',
      name: 'Product with Image',
      variants: [
        {
          id: 'var-1',
          sku: 'PRO-12345678-0',
          base_price: 39.99,
          images: [
            {
              id: 'img-1',
              url: mockCdnUrl,
              is_primary: true
            }
          ]
        }
      ]
    };

    vi.mocked(ProductsAPI.createProduct).mockResolvedValue({
      success: true,
      data: mockProduct
    });

    renderComponent();

    // Fill form
    const nameInput = screen.getByLabelText(/Product Name/i);
    await user.type(nameInput, 'Product with Image');

    const basePriceInput = screen.getByLabelText(/Base Price/i);
    await user.clear(basePriceInput);
    await user.type(basePriceInput, '39.99');

    // Upload image
    const file = new File(['test'], 'product-image.png', { type: 'image/png' });
    const fileInput = screen.getByLabelText(/Click to upload/i).querySelector('input[type="file"]');

    if (fileInput) {
      await user.upload(fileInput as HTMLInputElement, file);

      await waitFor(() => {
        expect(githubLib.uploadMultipleFiles).toHaveBeenCalled();
      });
    }

    // Submit
    const submitButton = screen.getByRole('button', { name: /Create Product/i });
    await user.click(submitButton);

    // Verify product includes CDN URL
    await waitFor(() => {
      expect(ProductsAPI.createProduct).toHaveBeenCalledWith(
        expect.objectContaining({
          variants: expect.arrayContaining([
            expect.objectContaining({
              image_urls: expect.arrayContaining([mockCdnUrl])
            })
          ])
        })
      );
    });
  });

  it('should verify images load from jsDelivr CDN', async () => {
    const user = userEvent.setup();
    
    const cdnUrl = 'https://cdn.jsdelivr.net/gh/Oahse/media@main/products/test-product.png';
    
    vi.mocked(githubLib.uploadMultipleFiles).mockResolvedValue([
      { name: 'test-product.png', url: cdnUrl, githubPath: 'products/test-product.png' }
    ]);

    vi.mocked(ProductsAPI.createProduct).mockResolvedValue({
      success: true,
      data: {
        id: 'prod-789',
        name: 'CDN Test Product',
        variants: [
          {
            id: 'var-1',
            sku: 'CDN-12345678-0',
            base_price: 49.99,
            images: [{ id: 'img-1', url: cdnUrl, is_primary: true }]
          }
        ]
      }
    });

    renderComponent();

    const nameInput = screen.getByLabelText(/Product Name/i);
    await user.type(nameInput, 'CDN Test Product');

    const basePriceInput = screen.getByLabelText(/Base Price/i);
    await user.clear(basePriceInput);
    await user.type(basePriceInput, '49.99');

    // Upload image
    const file = new File(['test'], 'test-product.png', { type: 'image/png' });
    const fileInput = screen.getByLabelText(/Click to upload/i).querySelector('input[type="file"]');

    if (fileInput) {
      await user.upload(fileInput as HTMLInputElement, file);

      await waitFor(() => {
        expect(githubLib.uploadMultipleFiles).toHaveBeenCalled();
      });
    }

    const submitButton = screen.getByRole('button', { name: /Create Product/i });
    await user.click(submitButton);

    // Verify CDN URL format
    await waitFor(() => {
      expect(ProductsAPI.createProduct).toHaveBeenCalledWith(
        expect.objectContaining({
          variants: expect.arrayContaining([
            expect.objectContaining({
              image_urls: expect.arrayContaining([
                expect.stringMatching(/^https:\/\/cdn\.jsdelivr\.net\/gh\/.+/)
              ])
            })
          ])
        })
      );
    });
  });

  it('should handle multiple variants with different images', async () => {
    const user = userEvent.setup();
    
    renderComponent();

    // Fill product info
    const nameInput = screen.getByLabelText(/Product Name/i);
    await user.type(nameInput, 'Multi-Variant Product');

    // Fill first variant
    const basePriceInput = screen.getByLabelText(/Base Price/i);
    await user.clear(basePriceInput);
    await user.type(basePriceInput, '19.99');

    // Add second variant
    const addVariantButton = screen.getByRole('button', { name: /Add Variant/i });
    await user.click(addVariantButton);

    // Verify second variant appears
    await waitFor(() => {
      const variantHeaders = screen.getAllByText(/Variant \d+/);
      expect(variantHeaders).toHaveLength(2);
    });

    // Fill second variant
    const allBasePriceInputs = screen.getAllByLabelText(/Base Price/i);
    await user.clear(allBasePriceInputs[1]);
    await user.type(allBasePriceInputs[1], '24.99');

    // Submit
    const submitButton = screen.getByRole('button', { name: /Create Product/i });
    
    vi.mocked(ProductsAPI.createProduct).mockResolvedValue({
      success: true,
      data: {
        id: 'prod-multi',
        name: 'Multi-Variant Product',
        variants: [
          { id: 'var-1', sku: 'MUL-12345678-0', base_price: 19.99, images: [] },
          { id: 'var-2', sku: 'MUL-12345678-1', base_price: 24.99, images: [] }
        ]
      }
    });

    await user.click(submitButton);

    // Verify both variants are included
    await waitFor(() => {
      expect(ProductsAPI.createProduct).toHaveBeenCalledWith(
        expect.objectContaining({
          variants: expect.arrayContaining([
            expect.objectContaining({ base_price: 19.99 }),
            expect.objectContaining({ base_price: 24.99 })
          ])
        })
      );
    });
  });
});
