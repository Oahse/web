import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ProductDetails } from '../ProductDetails';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { AuthContext } from '../../store/AuthContext';
import { CartContext } from '../../store/CartContext';
import { WishlistContext } from '../../store/WishlistContext';

// Mock the APIs
vi.mock('../../apis/products', () => ({
  ProductsAPI: {
    getProduct: vi.fn(),
    getRecommendedProducts: vi.fn(),
    generateVariantCodes: vi.fn(),
  },
}));

vi.mock('../../apis/reviews', () => ({
  ReviewsAPI: {
    getProductReviews: vi.fn(),
  },
}));

// Mock components
vi.mock('../../components/product/ProductImageGallery', () => ({
  ProductImageGallery: ({ images, onImageSelect }: any) => (
    <div data-testid="image-gallery">
      {images.map((img: any, index: number) => (
        <img
          key={index}
          src={img.url}
          alt={img.alt_text}
          onClick={() => onImageSelect(index)}
          data-testid={`gallery-image-${index}`}
        />
      ))}
    </div>
  ),
}));

vi.mock('../../components/product/VariantSelector', () => ({
  VariantSelector: ({ variants, selectedVariant, onVariantChange }: any) => (
    <div data-testid="variant-selector">
      {variants.map((variant: any) => (
        <button
          key={variant.id}
          onClick={() => onVariantChange(variant)}
          data-testid={`variant-${variant.id}`}
          className={selectedVariant?.id === variant.id ? 'selected' : ''}
        >
          {variant.name} - ${variant.base_price}
        </button>
      ))}
    </div>
  ),
}));

vi.mock('../../components/product/QRCodeModal', () => ({
  QRCodeModal: ({ isOpen, onClose, data }: any) =>
    isOpen ? (
      <div data-testid="qr-modal">
        <button onClick={onClose}>Close</button>
        <div>QR Code for: {data}</div>
      </div>
    ) : null,
}));

vi.mock('../../components/product/BarcodeModal', () => ({
  BarcodeModal: ({ isOpen, onClose, code }: any) =>
    isOpen ? (
      <div data-testid="barcode-modal">
        <button onClick={onClose}>Close</button>
        <div>Barcode for: {code}</div>
      </div>
    ) : null,
}));

describe('ProductDetails Page', () => {
  const mockProduct = {
    id: 'product-1',
    name: 'Test Product',
    description: 'A great test product',
    category: { id: 'cat-1', name: 'Electronics' },
    supplier: { firstname: 'John', lastname: 'Doe', email: 'john@example.com' },
    rating: 4.5,
    review_count: 10,
    variants: [
      {
        id: 'variant-1',
        product_id: 'product-1',
        sku: 'SKU-001',
        name: 'Standard',
        base_price: 99.99,
        sale_price: 79.99,
        stock: 10,
        barcode: 'data:image/png;base64,barcode_data',
        qr_code: 'data:image/png;base64,qr_code_data',
        attributes: { color: 'blue', size: 'medium' },
        images: [
          {
            id: 'img-1',
            url: 'https://example.com/image1.jpg',
            alt_text: 'Product image 1',
            is_primary: true,
          },
        ],
      },
      {
        id: 'variant-2',
        product_id: 'product-1',
        sku: 'SKU-002',
        name: 'Premium',
        base_price: 149.99,
        stock: 5,
        barcode: null,
        qr_code: null,
        attributes: { color: 'red', size: 'large' },
        images: [
          {
            id: 'img-2',
            url: 'https://example.com/image2.jpg',
            alt_text: 'Product image 2',
            is_primary: true,
          },
        ],
      },
    ],
  };

  const mockAuthContext = {
    user: {
      id: '1',
      email: 'test@example.com',
      firstname: 'Test',
      lastname: 'User',
      role: 'customer' as const,
      is_active: true,
      is_verified: true,
      created_at: '2023-01-01T00:00:00Z',
    },
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    updateUser: vi.fn(),
  };

  const mockCartContext = {
    cart: { items: [] },
    isLoading: false,
    addItem: vi.fn(),
    updateQuantity: vi.fn(),
    removeItem: vi.fn(),
    clearCart: vi.fn(),
    refreshCart: vi.fn(),
  };

  const mockWishlistContext = {
    wishlists: [{ id: 'wishlist-1', items: [] }],
    isLoading: false,
    addItem: vi.fn(),
    removeItem: vi.fn(),
    refreshWishlists: vi.fn(),
  };

  const renderWithProviders = (component: React.ReactElement, route = '/product/product-1') => {
    return render(
      <MemoryRouter initialEntries={[route]}>
        <AuthContext.Provider value={mockAuthContext}>
          <CartContext.Provider value={mockCartContext}>
            <WishlistContext.Provider value={mockWishlistContext}>
              {component}
            </WishlistContext.Provider>
          </CartContext.Provider>
        </AuthContext.Provider>
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    renderWithProviders(<ProductDetails />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('displays product information after loading', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getProduct as any).mockResolvedValue({
      success: true,
      data: mockProduct,
    });
    (ProductsAPI.getRecommendedProducts as any).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
      expect(screen.getByText('A great test product')).toBeInTheDocument();
      expect(screen.getByText('$79.99')).toBeInTheDocument();
      expect(screen.getByText('$99.99')).toBeInTheDocument(); // Original price
    });
  });

  it('displays product variants', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getProduct as any).mockResolvedValue({
      success: true,
      data: mockProduct,
    });
    (ProductsAPI.getRecommendedProducts as any).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      expect(screen.getByTestId('variant-selector')).toBeInTheDocument();
      expect(screen.getByTestId('variant-variant-1')).toBeInTheDocument();
      expect(screen.getByTestId('variant-variant-2')).toBeInTheDocument();
    });
  });

  it('shows barcode and QR code buttons when available', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getProduct as any).mockResolvedValue({
      success: true,
      data: mockProduct,
    });
    (ProductsAPI.getRecommendedProducts as any).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      expect(screen.getByText('View QR Code')).toBeInTheDocument();
      expect(screen.getByText('View Barcode')).toBeInTheDocument();
    });
  });

  it('opens QR code modal when button is clicked', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getProduct as any).mockResolvedValue({
      success: true,
      data: mockProduct,
    });
    (ProductsAPI.getRecommendedProducts as any).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      const qrButton = screen.getByText('View QR Code');
      fireEvent.click(qrButton);
      expect(screen.getByTestId('qr-modal')).toBeInTheDocument();
    });
  });

  it('opens barcode modal when button is clicked', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getProduct as any).mockResolvedValue({
      success: true,
      data: mockProduct,
    });
    (ProductsAPI.getRecommendedProducts as any).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      const barcodeButton = screen.getByText('View Barcode');
      fireEvent.click(barcodeButton);
      expect(screen.getByTestId('barcode-modal')).toBeInTheDocument();
    });
  });

  it('hides barcode/QR buttons when codes are not available', async () => {
    const productWithoutCodes = {
      ...mockProduct,
      variants: [
        {
          ...mockProduct.variants[1], // This variant has no barcode/QR code
        },
      ],
    };

    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getProduct as any).mockResolvedValue({
      success: true,
      data: productWithoutCodes,
    });
    (ProductsAPI.getRecommendedProducts as any).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      expect(screen.queryByText('View QR Code')).not.toBeInTheDocument();
      expect(screen.queryByText('View Barcode')).not.toBeInTheDocument();
    });
  });

  it('updates codes when variant is changed', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getProduct as any).mockResolvedValue({
      success: true,
      data: mockProduct,
    });
    (ProductsAPI.getRecommendedProducts as any).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      // Initially shows codes for first variant
      expect(screen.getByText('View QR Code')).toBeInTheDocument();
      expect(screen.getByText('View Barcode')).toBeInTheDocument();

      // Switch to second variant (no codes)
      const variant2Button = screen.getByTestId('variant-variant-2');
      fireEvent.click(variant2Button);

      // Codes should be hidden
      expect(screen.queryByText('View QR Code')).not.toBeInTheDocument();
      expect(screen.queryByText('View Barcode')).not.toBeInTheDocument();
    });
  });

  it('adds product to cart', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getProduct as any).mockResolvedValue({
      success: true,
      data: mockProduct,
    });
    (ProductsAPI.getRecommendedProducts as any).mockResolvedValue({
      success: true,
      data: [],
    });

    mockCartContext.addItem.mockResolvedValue(true);

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      const addToCartButton = screen.getByText('Add to Cart');
      fireEvent.click(addToCartButton);

      expect(mockCartContext.addItem).toHaveBeenCalledWith({
        variant_id: 'variant-1',
        quantity: 1,
      });
    });
  });

  it('adds product to wishlist', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getProduct as any).mockResolvedValue({
      success: true,
      data: mockProduct,
    });
    (ProductsAPI.getRecommendedProducts as any).mockResolvedValue({
      success: true,
      data: [],
    });

    mockWishlistContext.addItem.mockResolvedValue(true);

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      const wishlistButton = screen.getByLabelText('Add to Wishlist');
      fireEvent.click(wishlistButton);

      expect(mockWishlistContext.addItem).toHaveBeenCalledWith(
        'product-1',
        'variant-1',
        1
      );
    });
  });

  it('handles quantity changes', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getProduct as any).mockResolvedValue({
      success: true,
      data: mockProduct,
    });
    (ProductsAPI.getRecommendedProducts as any).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      const increaseButton = screen.getByLabelText('Increase quantity');
      fireEvent.click(increaseButton);

      expect(screen.getByDisplayValue('2')).toBeInTheDocument();

      const decreaseButton = screen.getByLabelText('Decrease quantity');
      fireEvent.click(decreaseButton);

      expect(screen.getByDisplayValue('1')).toBeInTheDocument();
    });
  });

  it('displays product reviews', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    const { ReviewsAPI } = await import('../../apis/reviews');

    (ProductsAPI.getProduct as any).mockResolvedValue({
      success: true,
      data: mockProduct,
    });
    (ProductsAPI.getRecommendedProducts as any).mockResolvedValue({
      success: true,
      data: [],
    });
    (ReviewsAPI.getProductReviews as any).mockResolvedValue({
      success: true,
      data: {
        data: [
          {
            id: 'review-1',
            user: { firstname: 'Jane', lastname: 'Smith' },
            rating: 5,
            comment: 'Great product!',
            created_at: '2023-01-01T00:00:00Z',
          },
        ],
        total: 1,
        limit: 10,
      },
    });

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      // Switch to reviews tab
      const reviewsTab = screen.getByText('Reviews (10)');
      fireEvent.click(reviewsTab);

      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      expect(screen.getByText('Great product!')).toBeInTheDocument();
    });
  });

  it('handles product not found error', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getProduct as any).mockRejectedValue({
      message: 'Product not found',
    });

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      expect(screen.getByText('Product not found')).toBeInTheDocument();
    });
  });

  it('displays breadcrumb navigation', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getProduct as any).mockResolvedValue({
      success: true,
      data: mockProduct,
    });
    (ProductsAPI.getRecommendedProducts as any).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Products')).toBeInTheDocument();
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });
  });

  it('shows out of stock message when variant has no stock', async () => {
    const outOfStockProduct = {
      ...mockProduct,
      variants: [
        {
          ...mockProduct.variants[0],
          stock: 0,
        },
      ],
    };

    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getProduct as any).mockResolvedValue({
      success: true,
      data: outOfStockProduct,
    });
    (ProductsAPI.getRecommendedProducts as any).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<ProductDetails />);

    await waitFor(() => {
      expect(screen.getByText('Out of Stock')).toBeInTheDocument();
      expect(screen.getByText('Out of Stock')).toBeDisabled();
    });
  });
});