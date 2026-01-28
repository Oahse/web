import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { Home } from '../Home';
import { BrowserRouter } from 'react-router-dom';
import { AuthContext } from '../../store/AuthContext';
import { CartContext } from '../../store/CartContext';
import { WishlistContext } from '../../store/WishlistContext';

// Mock the APIs
vi.mock('../../apis/products', () => ({
  default: {
    getHomeData: vi.fn(),
    getFeaturedProducts: vi.fn(),
    getProducts: vi.fn(),
  },
}));

vi.mock('../../apis/categories', () => ({
  default: {
    getCategories: vi.fn(),
  },
}));

// Mock components that might not be available
vi.mock('../../components/product/ProductCard', () => ({
  ProductCard: ({ product }: any) => (
    <div data-testid={`product-${product.id}`}>
      <h3>{product.name}</h3>
      <p>${product.price}</p>
    </div>
  ),
}));

vi.mock('../../components/category/CategoryCard', () => ({
  CategoryCard: ({ category }: any) => (
    <div data-testid={`category-${category.id}`}>
      <h3>{category.name}</h3>
    </div>
  ),
}));

describe('Home Page', () => {
  const mockAuthContext = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    updateUser: vi.fn(),
  };

  const mockCartContext = {
    cart: null,
    isLoading: false,
    addItem: vi.fn(),
    updateQuantity: vi.fn(),
    removeItem: vi.fn(),
    clearCart: vi.fn(),
    refreshCart: vi.fn(),
  };

  const mockWishlistContext = {
    wishlists: [],
    isLoading: false,
    addItem: vi.fn(),
    removeItem: vi.fn(),
    refreshWishlists: vi.fn(),
  };

  const mockHomeData = {
    categories: [
      {
        id: '1',
        name: 'Electronics',
        description: 'Electronic devices',
        image_url: 'https://example.com/electronics.jpg',
        is_active: true,
        created_at: '2023-01-01T00:00:00Z',
      },
      {
        id: '2',
        name: 'Clothing',
        description: 'Fashion items',
        image_url: 'https://example.com/clothing.jpg',
        is_active: true,
        created_at: '2023-01-01T00:00:00Z',
      },
    ],
    featured: [
      {
        id: '1',
        name: 'Featured Product 1',
        price: 99.99,
        image: 'https://example.com/product1.jpg',
        rating: 4.5,
        reviewCount: 10,
      },
      {
        id: '2',
        name: 'Featured Product 2',
        price: 149.99,
        image: 'https://example.com/product2.jpg',
        rating: 4.8,
        reviewCount: 25,
      },
    ],
    popular: [
      {
        id: '3',
        name: 'Popular Product 1',
        price: 79.99,
        image: 'https://example.com/product3.jpg',
        rating: 4.2,
        reviewCount: 15,
      },
    ],
    deals: [
      {
        id: '4',
        name: 'Deal Product 1',
        price: 59.99,
        discountPrice: 39.99,
        image: 'https://example.com/product4.jpg',
        rating: 4.0,
        reviewCount: 8,
      },
    ],
  };

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <BrowserRouter>
        <AuthContext.Provider value={mockAuthContext}>
          <CartContext.Provider value={mockCartContext}>
            <WishlistContext.Provider value={mockWishlistContext}>
              {component}
            </WishlistContext.Provider>
          </CartContext.Provider>
        </AuthContext.Provider>
      </BrowserRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    renderWithProviders(<Home />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('displays home data after loading', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getHomeData as any).mockResolvedValue({
      success: true,
      data: mockHomeData,
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText('Featured Products')).toBeInTheDocument();
      expect(screen.getByText('Popular Products')).toBeInTheDocument();
      expect(screen.getByText('Special Deals')).toBeInTheDocument();
    });
  });

  it('displays categories', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getHomeData as any).mockResolvedValue({
      success: true,
      data: mockHomeData,
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByTestId('category-1')).toBeInTheDocument();
      expect(screen.getByTestId('category-2')).toBeInTheDocument();
      expect(screen.getByText('Electronics')).toBeInTheDocument();
      expect(screen.getByText('Clothing')).toBeInTheDocument();
    });
  });

  it('displays featured products', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getHomeData as any).mockResolvedValue({
      success: true,
      data: mockHomeData,
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByTestId('product-1')).toBeInTheDocument();
      expect(screen.getByTestId('product-2')).toBeInTheDocument();
      expect(screen.getByText('Featured Product 1')).toBeInTheDocument();
      expect(screen.getByText('$99.99')).toBeInTheDocument();
    });
  });

  it('displays popular products', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getHomeData as any).mockResolvedValue({
      success: true,
      data: mockHomeData,
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByTestId('product-3')).toBeInTheDocument();
      expect(screen.getByText('Popular Product 1')).toBeInTheDocument();
      expect(screen.getByText('$79.99')).toBeInTheDocument();
    });
  });

  it('displays deal products', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getHomeData as any).mockResolvedValue({
      success: true,
      data: mockHomeData,
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByTestId('product-4')).toBeInTheDocument();
      expect(screen.getByText('Deal Product 1')).toBeInTheDocument();
      expect(screen.getByText('$59.99')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getHomeData as any).mockRejectedValue({
      message: 'Failed to load home data',
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load home data')).toBeInTheDocument();
    });
  });

  it('shows empty state when no data is available', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getHomeData as any).mockResolvedValue({
      success: true,
      data: {
        categories: [],
        featured: [],
        popular: [],
        deals: [],
      },
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText('No featured products available')).toBeInTheDocument();
      expect(screen.getByText('No popular products available')).toBeInTheDocument();
      expect(screen.getByText('No deals available')).toBeInTheDocument();
    });
  });

  it('displays hero section', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getHomeData as any).mockResolvedValue({
      success: true,
      data: mockHomeData,
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText('Welcome to Banwee')).toBeInTheDocument();
      expect(screen.getByText('Discover amazing products')).toBeInTheDocument();
    });
  });

  it('has working navigation links', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getHomeData as any).mockResolvedValue({
      success: true,
      data: mockHomeData,
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      const shopNowButton = screen.getByText('Shop Now');
      expect(shopNowButton).toBeInTheDocument();
      expect(shopNowButton.closest('a')).toHaveAttribute('href', '/products');
    });
  });

  it('displays newsletter signup', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getHomeData as any).mockResolvedValue({
      success: true,
      data: mockHomeData,
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText('Subscribe to our newsletter')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument();
    });
  });

  it('handles newsletter signup', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getHomeData as any).mockResolvedValue({
      success: true,
      data: mockHomeData,
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      const emailInput = screen.getByPlaceholderText('Enter your email');
      const subscribeButton = screen.getByText('Subscribe');
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(subscribeButton);
      
      // Should show success message or handle subscription
      expect(emailInput).toHaveValue('test@example.com');
    });
  });

  it('is responsive and mobile-friendly', async () => {
    const { ProductsAPI } = await import('../../apis/products');
    (ProductsAPI.getHomeData as any).mockResolvedValue({
      success: true,
      data: mockHomeData,
    });

    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      // Check that mobile-specific classes or layouts are applied
      const container = screen.getByTestId('home-container');
      expect(container).toHaveClass('mobile-responsive');
    });
  });
});