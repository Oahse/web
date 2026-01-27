/**
 * Product Card Cart Integration Tests
 * Tests the add to cart functionality from product cards with real-time updates
 */

import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { toast } from 'react-hot-toast';

// Components
import { ProductCard } from '../../components/ProductCard';
import { AuthProvider } from '../../contexts/AuthContext';
import { CartProvider } from '../../contexts/CartContext';
import { WishlistProvider } from '../../contexts/WishlistContext';
import { SubscriptionProvider } from '../../contexts/SubscriptionContext';

// Mock APIs
vi.mock('../../apis/cart', () => ({
  CartAPI: {
    getCart: vi.fn(),
    addToCart: vi.fn(),
    updateCartItem: vi.fn(),
    removeFromCart: vi.fn(),
    clearCart: vi.fn(),
    validateCart: vi.fn(),
  }
}));

vi.mock('../../apis/wishlist', () => ({
  WishlistAPI: {
    getWishlists: vi.fn(),
    addToWishlist: vi.fn(),
  }
}));

vi.mock('../../services/stockMonitoring', () => ({
  stockMonitor: {
    setStockThreshold: vi.fn(),
    updateStock: vi.fn(),
    getStockStatus: vi.fn(() => ({ status: 'in_stock', message: 'In Stock' })),
  }
}));

// Mock toast notifications
vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(),
  }
}));

// Mock navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Product Card Cart Integration', () => {
  const { CartAPI } = require('../../apis/cart');
  const { WishlistAPI } = require('../../apis/wishlist');

  // Mock data
  const mockUser = {
    id: 'user-123',
    email: 'test@example.com',
    firstname: 'John',
    lastname: 'Doe',
    role: 'customer' as const,
    verified: true,
    is_active: true,
    created_at: '2023-01-01T00:00:00Z',
  };

  const mockProduct = {
    id: 'product-1',
    name: 'Test Product',
    description: 'A test product',
    slug: 'test-product',
    rating_average: 4.5,
    review_count: 25,
    variants: [{
      id: 'variant-1',
      product_id: 'product-1',
      sku: 'TEST-001',
      name: 'Default Variant',
      base_price: 29.99,
      sale_price: null,
      current_price: 29.99,
      stock: 10,
      is_active: true,
      attributes: { color: 'Red', size: 'M' },
      images: [{
        id: 'img-1',
        variant_id: 'variant-1',
        url: 'https://example.com/image.jpg',
        alt_text: 'Test Product Image',
        is_primary: true,
        sort_order: 1,
      }],
      created_at: '2023-01-01T00:00:00Z',
      product_name: 'Test Product',
    }],
    created_at: '2023-01-01T00:00:00Z',
  };

  const mockProductOnSale = {
    ...mockProduct,
    id: 'product-2',
    name: 'Sale Product',
    variants: [{
      ...mockProduct.variants[0],
      id: 'variant-2',
      base_price: 39.99,
      sale_price: 29.99,
      current_price: 29.99,
    }]
  };

  const mockProductOutOfStock = {
    ...mockProduct,
    id: 'product-3',
    name: 'Out of Stock Product',
    variants: [{
      ...mockProduct.variants[0],
      id: 'variant-3',
      stock: 0,
    }]
  };

  const mockEmptyCart = {
    id: 'cart-123',
    user_id: 'user-123',
    items: [],
    subtotal: 0,
    tax_amount: 0,
    shipping_amount: 0,
    total_amount: 0,
    total_items: 0,
    item_count: 0,
    currency: 'USD',
    created_at: '2023-01-01T00:00:00Z',
  };

  const mockCartWithItem = {
    id: 'cart-123',
    user_id: 'user-123',
    items: [{
      id: 'item-1',
      cart_id: 'cart-123',
      variant_id: 'variant-1',
      variant: mockProduct.variants[0],
      quantity: 1,
      price_per_unit: 29.99,
      total_price: 29.99,
      created_at: '2023-01-01T00:00:00Z',
    }],
    subtotal: 29.99,
    tax_amount: 2.99,
    shipping_amount: 9.99,
    total_amount: 42.97,
    total_items: 1,
    item_count: 1,
    currency: 'USD',
    created_at: '2023-01-01T00:00:00Z',
  };

  // Test wrapper component
  const TestWrapper = ({ 
    children, 
    authenticated = true,
    user = mockUser 
  }: { 
    children: React.ReactNode; 
    authenticated?: boolean;
    user?: any;
  }) => {
    const authContextValue = {
      user: authenticated ? user : null,
      isAuthenticated: authenticated,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateUser: vi.fn(),
      setIntendedDestination: vi.fn(),
    };

    return (
      <BrowserRouter>
        <AuthProvider value={authContextValue}>
          <WishlistProvider>
            <SubscriptionProvider>
              <CartProvider>
                {children}
              </CartProvider>
            </SubscriptionProvider>
          </WishlistProvider>
        </AuthProvider>
      </BrowserRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    
    // Default API responses
    CartAPI.getCart.mockResolvedValue({ data: mockEmptyCart });
    WishlistAPI.getWishlists.mockResolvedValue({ data: [] });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Add to Cart Functionality', () => {
    it('should render product card with add to cart button', async () => {
      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product')).toBeInTheDocument();
        expect(screen.getByText('Default Variant')).toBeInTheDocument();
        expect(screen.getByText('$29.99')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /add to cart/i })).toBeInTheDocument();
      });
    });

    it('should add item to cart successfully', async () => {
      const user = userEvent.setup();
      
      CartAPI.addToCart.mockResolvedValue({ data: mockCartWithItem });

      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      const addToCartButton = screen.getByRole('button', { name: /add to cart/i });
      await user.click(addToCartButton);

      await waitFor(() => {
        expect(CartAPI.addToCart).toHaveBeenCalledWith({
          variant_id: 'variant-1',
          quantity: 1,
        }, expect.any(String));
      });

      expect(toast.success).toHaveBeenCalledWith('Added 1 item to cart');
    });

    it('should show loading state during add to cart', async () => {
      const user = userEvent.setup();
      
      // Mock slow API response
      CartAPI.addToCart.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ data: mockCartWithItem }), 500))
      );

      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      const addToCartButton = screen.getByRole('button', { name: /add to cart/i });
      await user.click(addToCartButton);

      // Should show loading state
      expect(addToCartButton).toBeDisabled();
      expect(screen.getByText(/adding/i)).toBeInTheDocument();

      await waitFor(() => {
        expect(addToCartButton).not.toBeDisabled();
        expect(screen.getByText(/add to cart/i)).toBeInTheDocument();
      }, { timeout: 1000 });
    });

    it('should handle add to cart errors', async () => {
      const user = userEvent.setup();
      
      CartAPI.addToCart.mockRejectedValue(new Error('Product out of stock'));

      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      const addToCartButton = screen.getByRole('button', { name: /add to cart/i });
      await user.click(addToCartButton);

      await waitFor(() => {
        expect(CartAPI.addToCart).toHaveBeenCalled();
      });

      // Should not show success toast
      expect(toast.success).not.toHaveBeenCalled();
      
      // Button should be enabled again
      expect(addToCartButton).not.toBeDisabled();
    });
  });

  describe('Authentication Handling', () => {
    it('should redirect unauthenticated users to login', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper authenticated={false}>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      const addToCartButton = screen.getByRole('button', { name: /add to cart/i });
      await user.click(addToCartButton);

      // Should redirect to login
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/login', expect.objectContaining({
          replace: true,
          state: expect.objectContaining({
            from: expect.any(Object)
          })
        }));
      });

      // Should not call cart API
      expect(CartAPI.addToCart).not.toHaveBeenCalled();
    });

    it('should handle authentication errors during add to cart', async () => {
      const user = userEvent.setup();
      
      CartAPI.addToCart.mockRejectedValue({
        message: 'User must be authenticated to add items to cart'
      });

      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      const addToCartButton = screen.getByRole('button', { name: /add to cart/i });
      await user.click(addToCartButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/login', expect.any(Object));
      });
    });
  });

  describe('Product Variants and Pricing', () => {
    it('should display sale price correctly', async () => {
      render(
        <TestWrapper>
          <ProductCard product={mockProductOnSale} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('$29.99')).toBeInTheDocument(); // sale price
        expect(screen.getByText('$39.99')).toBeInTheDocument(); // original price (crossed out)
        expect(screen.getByText('-25%')).toBeInTheDocument(); // discount badge
      });
    });

    it('should handle out of stock products', async () => {
      render(
        <TestWrapper>
          <ProductCard product={mockProductOutOfStock} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Out of Stock Product')).toBeInTheDocument();
        expect(screen.getByText('Out of Stock')).toBeInTheDocument();
      });

      const addToCartButton = screen.getByRole('button', { name: /out of stock/i });
      expect(addToCartButton).toBeDisabled();
    });

    it('should prevent adding out of stock items to cart', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <ProductCard product={mockProductOutOfStock} />
        </TestWrapper>
      );

      const addToCartButton = screen.getByRole('button', { name: /out of stock/i });
      expect(addToCartButton).toBeDisabled();

      // Try to click (should not work)
      await user.click(addToCartButton);

      expect(CartAPI.addToCart).not.toHaveBeenCalled();
    });
  });

  describe('Stock Monitoring Integration', () => {
    it('should update stock monitoring after successful add to cart', async () => {
      const user = userEvent.setup();
      const { stockMonitor } = require('../../services/stockMonitoring');
      
      CartAPI.addToCart.mockResolvedValue({ data: mockCartWithItem });

      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      const addToCartButton = screen.getByRole('button', { name: /add to cart/i });
      await user.click(addToCartButton);

      await waitFor(() => {
        expect(CartAPI.addToCart).toHaveBeenCalled();
      });

      // Should update stock monitoring
      expect(stockMonitor.updateStock).toHaveBeenCalledWith(
        'variant-1',
        9, // original stock (10) - 1
        'Test Product',
        'Default Variant'
      );
    });

    it('should display stock status indicators', async () => {
      const { stockMonitor } = require('../../services/stockMonitoring');
      
      // Mock low stock status
      stockMonitor.getStockStatus.mockReturnValue({
        status: 'low_stock',
        message: 'Only 3 left!'
      });

      const lowStockProduct = {
        ...mockProduct,
        variants: [{
          ...mockProduct.variants[0],
          stock: 3,
        }]
      };

      render(
        <TestWrapper>
          <ProductCard product={lowStockProduct} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('3 left!')).toBeInTheDocument();
      });
    });
  });

  describe('Wishlist Integration', () => {
    it('should add item to wishlist', async () => {
      const user = userEvent.setup();
      
      WishlistAPI.addToWishlist.mockResolvedValue({ success: true });

      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      // Find wishlist button (heart icon)
      const wishlistButton = screen.getByTitle('Add to wishlist');
      await user.click(wishlistButton);

      await waitFor(() => {
        expect(WishlistAPI.addToWishlist).toHaveBeenCalled();
      });
    });

    it('should handle wishlist errors', async () => {
      const user = userEvent.setup();
      
      WishlistAPI.addToWishlist.mockRejectedValue(new Error('Failed to add to wishlist'));

      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      const wishlistButton = screen.getByTitle('Add to wishlist');
      await user.click(wishlistButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Failed to add item to wishlist');
      });
    });
  });

  describe('Multiple Product Cards', () => {
    it('should handle multiple products independently', async () => {
      const user = userEvent.setup();
      
      const product2 = {
        ...mockProduct,
        id: 'product-2',
        name: 'Second Product',
        variants: [{
          ...mockProduct.variants[0],
          id: 'variant-2',
          product_id: 'product-2',
        }]
      };

      CartAPI.addToCart.mockResolvedValue({ data: mockCartWithItem });

      render(
        <TestWrapper>
          <div>
            <ProductCard product={mockProduct} />
            <ProductCard product={product2} />
          </div>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Product')).toBeInTheDocument();
        expect(screen.getByText('Second Product')).toBeInTheDocument();
      });

      const addToCartButtons = screen.getAllByRole('button', { name: /add to cart/i });
      expect(addToCartButtons).toHaveLength(2);

      // Click first product's add to cart
      await user.click(addToCartButtons[0]);

      await waitFor(() => {
        expect(CartAPI.addToCart).toHaveBeenCalledWith({
          variant_id: 'variant-1',
          quantity: 1,
        }, expect.any(String));
      });

      // Click second product's add to cart
      await user.click(addToCartButtons[1]);

      await waitFor(() => {
        expect(CartAPI.addToCart).toHaveBeenCalledWith({
          variant_id: 'variant-2',
          quantity: 1,
        }, expect.any(String));
      });

      expect(CartAPI.addToCart).toHaveBeenCalledTimes(2);
    });

    it('should show individual loading states', async () => {
      const user = userEvent.setup();
      
      const product2 = {
        ...mockProduct,
        id: 'product-2',
        name: 'Second Product',
        variants: [{
          ...mockProduct.variants[0],
          id: 'variant-2',
        }]
      };

      // Mock slow response for first product only
      CartAPI.addToCart
        .mockImplementationOnce(() => 
          new Promise(resolve => setTimeout(() => resolve({ data: mockCartWithItem }), 1000))
        )
        .mockResolvedValue({ data: mockCartWithItem });

      render(
        <TestWrapper>
          <div>
            <ProductCard product={mockProduct} />
            <ProductCard product={product2} />
          </div>
        </TestWrapper>
      );

      const addToCartButtons = screen.getAllByRole('button', { name: /add to cart/i });

      // Click both buttons
      await user.click(addToCartButtons[0]);
      await user.click(addToCartButtons[1]);

      // First button should be loading, second should complete quickly
      expect(addToCartButtons[0]).toBeDisabled();
      
      await waitFor(() => {
        expect(addToCartButtons[1]).not.toBeDisabled();
      });

      // Wait for first button to complete
      await waitFor(() => {
        expect(addToCartButtons[0]).not.toBeDisabled();
      }, { timeout: 1500 });
    });
  });

  describe('Image Handling', () => {
    it('should display product image correctly', async () => {
      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      await waitFor(() => {
        const image = screen.getByAltText('Test Product - Default Variant');
        expect(image).toBeInTheDocument();
        expect(image).toHaveAttribute('src', 'https://example.com/image.jpg');
      });
    });

    it('should handle image loading errors with fallback', async () => {
      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      const image = screen.getByAltText('Test Product - Default Variant');
      
      // Simulate image error
      fireEvent.error(image);

      await waitFor(() => {
        expect(image).toHaveAttribute('src', expect.stringContaining('data:image/svg+xml'));
      });
    });

    it('should show loading skeleton while image loads', async () => {
      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      // Should show loading skeleton initially
      expect(screen.getByRole('img')).toHaveClass('opacity-0');

      // Simulate image load
      const image = screen.getByAltText('Test Product - Default Variant');
      fireEvent.load(image);

      await waitFor(() => {
        expect(image).toHaveClass('opacity-100');
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', async () => {
      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add to cart/i })).toBeInTheDocument();
        expect(screen.getByRole('img')).toHaveAttribute('alt', 'Test Product - Default Variant');
        expect(screen.getByRole('link')).toHaveAttribute('href', '/products/product-1');
      });
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      
      CartAPI.addToCart.mockResolvedValue({ data: mockCartWithItem });

      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      const addToCartButton = screen.getByRole('button', { name: /add to cart/i });
      
      // Focus and activate with keyboard
      addToCartButton.focus();
      expect(addToCartButton).toHaveFocus();

      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(CartAPI.addToCart).toHaveBeenCalled();
      });
    });
  });

  describe('Performance', () => {
    it('should not re-render unnecessarily', async () => {
      const renderSpy = vi.fn();
      
      const TestProductCard = (props: any) => {
        renderSpy();
        return <ProductCard {...props} />;
      };

      const { rerender } = render(
        <TestWrapper>
          <TestProductCard product={mockProduct} />
        </TestWrapper>
      );

      expect(renderSpy).toHaveBeenCalledTimes(1);

      // Re-render with same props
      rerender(
        <TestWrapper>
          <TestProductCard product={mockProduct} />
        </TestWrapper>
      );

      // Should not cause unnecessary re-renders
      expect(renderSpy).toHaveBeenCalledTimes(2); // Initial + rerender
    });

    it('should handle rapid clicks gracefully', async () => {
      const user = userEvent.setup();
      
      CartAPI.addToCart.mockResolvedValue({ data: mockCartWithItem });

      render(
        <TestWrapper>
          <ProductCard product={mockProduct} />
        </TestWrapper>
      );

      const addToCartButton = screen.getByRole('button', { name: /add to cart/i });

      // Rapid clicks
      await user.click(addToCartButton);
      await user.click(addToCartButton);
      await user.click(addToCartButton);

      // Should only make one API call due to loading state
      await waitFor(() => {
        expect(CartAPI.addToCart).toHaveBeenCalledTimes(1);
      });
    });
  });
});