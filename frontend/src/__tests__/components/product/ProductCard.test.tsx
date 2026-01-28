/**
 * Tests for ProductCard.tsx
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ProductCard } from '../../../components/product/ProductCard';
import { mockProduct } from '../../setup';

// Mock cart context
const mockAddToCart = vi.fn();
vi.mock('../../../hooks/useCart', () => ({
  useCart: () => ({
    addToCart: mockAddToCart,
    isLoading: false
  })
}));

// Mock wishlist context
const mockAddToWishlist = vi.fn();
const mockRemoveFromWishlist = vi.fn();
vi.mock('../../../store/WishlistContext', () => ({
  useWishlist: () => ({
    addToWishlist: mockAddToWishlist,
    removeFromWishlist: mockRemoveFromWishlist,
    isInWishlist: vi.fn(() => false)
  })
}));

// Mock auth context
vi.mock('../../../store/AuthContext', () => ({
  useAuth: () => ({
    isAuthenticated: true
  })
}));

// Mock router
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
      <a href={to}>{children}</a>
    )
  };
});

// Mock components
vi.mock('../../../components/ui/LazyImage', () => ({
  LazyImage: ({ src, alt, className }: { src: string; alt: string; className?: string }) => (
    <img src={src} alt={alt} className={className} data-testid="product-image" />
  )
}));

vi.mock('../../../components/ui/Button', () => ({
  Button: ({ children, onClick, disabled, variant, size, ...props }: any) => (
    <button 
      onClick={onClick} 
      disabled={disabled} 
      className={`btn-${variant} btn-${size}`}
      {...props}
    >
      {children}
    </button>
  )
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('ProductCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render product information', () => {
    render(
      <TestWrapper>
        <ProductCard product={mockProduct} />
      </TestWrapper>
    );

    expect(screen.getByText(mockProduct.name)).toBeInTheDocument();
    expect(screen.getByText(mockProduct.description)).toBeInTheDocument();
    expect(screen.getByText(`$${mockProduct.variants[0].price}`)).toBeInTheDocument();
    expect(screen.getByTestId('product-image')).toHaveAttribute('alt', mockProduct.name);
  });

  it('should render product brand', () => {
    render(
      <TestWrapper>
        <ProductCard product={mockProduct} />
      </TestWrapper>
    );

    expect(screen.getByText(mockProduct.brand)).toBeInTheDocument();
  });

  it('should render product category', () => {
    render(
      <TestWrapper>
        <ProductCard product={mockProduct} />
      </TestWrapper>
    );

    expect(screen.getByText(mockProduct.category)).toBeInTheDocument();
  });

  it('should handle add to cart', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ProductCard product={mockProduct} />
      </TestWrapper>
    );

    const addToCartButton = screen.getByText('Add to Cart');
    await user.click(addToCartButton);

    expect(mockAddToCart).toHaveBeenCalledWith(
      mockProduct.variants[0].id,
      1
    );
  });

  it('should handle add to wishlist', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ProductCard product={mockProduct} />
      </TestWrapper>
    );

    const wishlistButton = screen.getByTestId('wishlist-button');
    await user.click(wishlistButton);

    expect(mockAddToWishlist).toHaveBeenCalledWith(mockProduct.id);
  });

  it('should handle remove from wishlist when already in wishlist', async () => {
    const user = userEvent.setup();
    
    // Mock product already in wishlist
    vi.mocked(require('../../../store/WishlistContext').useWishlist).mockReturnValue({
      addToWishlist: mockAddToWishlist,
      removeFromWishlist: mockRemoveFromWishlist,
      isInWishlist: vi.fn(() => true)
    });

    render(
      <TestWrapper>
        <ProductCard product={mockProduct} />
      </TestWrapper>
    );

    const wishlistButton = screen.getByTestId('wishlist-button');
    expect(wishlistButton).toHaveClass('text-red-500'); // Should show as active

    await user.click(wishlistButton);

    expect(mockRemoveFromWishlist).toHaveBeenCalledWith(mockProduct.id);
  });

  it('should navigate to product details on click', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ProductCard product={mockProduct} />
      </TestWrapper>
    );

    const productCard = screen.getByTestId('product-card');
    await user.click(productCard);

    expect(mockNavigate).toHaveBeenCalledWith(`/products/${mockProduct.id}`);
  });

  it('should show discount badge when product is on sale', () => {
    const discountedProduct = {
      ...mockProduct,
      variants: [{
        ...mockProduct.variants[0],
        original_price: 149.99,
        price: 99.99
      }]
    };

    render(
      <TestWrapper>
        <ProductCard product={discountedProduct} />
      </TestWrapper>
    );

    expect(screen.getByText('33% OFF')).toBeInTheDocument();
    expect(screen.getByText('$149.99')).toHaveClass('line-through');
  });

  it('should show out of stock state', () => {
    const outOfStockProduct = {
      ...mockProduct,
      variants: [{
        ...mockProduct.variants[0],
        stock_quantity: 0
      }]
    };

    render(
      <TestWrapper>
        <ProductCard product={outOfStockProduct} />
      </TestWrapper>
    );

    expect(screen.getByText('Out of Stock')).toBeInTheDocument();
    expect(screen.getByText('Add to Cart')).toBeDisabled();
  });

  it('should show low stock warning', () => {
    const lowStockProduct = {
      ...mockProduct,
      variants: [{
        ...mockProduct.variants[0],
        stock_quantity: 3
      }]
    };

    render(
      <TestWrapper>
        <ProductCard product={lowStockProduct} />
      </TestWrapper>
    );

    expect(screen.getByText('Only 3 left!')).toBeInTheDocument();
  });

  it('should show product rating', () => {
    const ratedProduct = {
      ...mockProduct,
      average_rating: 4.5,
      review_count: 23
    };

    render(
      <TestWrapper>
        <ProductCard product={ratedProduct} />
      </TestWrapper>
    );

    expect(screen.getByTestId('product-rating')).toBeInTheDocument();
    expect(screen.getByText('4.5')).toBeInTheDocument();
    expect(screen.getByText('(23 reviews)')).toBeInTheDocument();
  });

  it('should handle quick view', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ProductCard product={mockProduct} showQuickView />
      </TestWrapper>
    );

    const quickViewButton = screen.getByText('Quick View');
    await user.click(quickViewButton);

    expect(screen.getByTestId('quick-view-modal')).toBeInTheDocument();
  });

  it('should show new badge for new products', () => {
    const newProduct = {
      ...mockProduct,
      created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString() // 5 days ago
    };

    render(
      <TestWrapper>
        <ProductCard product={newProduct} />
      </TestWrapper>
    );

    expect(screen.getByText('New')).toBeInTheDocument();
  });

  it('should handle loading state for add to cart', async () => {
    const user = userEvent.setup();
    
    // Mock loading state
    vi.mocked(require('../../../hooks/useCart').useCart).mockReturnValue({
      addToCart: mockAddToCart,
      isLoading: true
    });

    render(
      <TestWrapper>
        <ProductCard product={mockProduct} />
      </TestWrapper>
    );

    const addToCartButton = screen.getByText('Adding...');
    expect(addToCartButton).toBeDisabled();
  });

  it('should show variant selector for products with multiple variants', () => {
    const multiVariantProduct = {
      ...mockProduct,
      variants: [
        { ...mockProduct.variants[0], name: 'Small', price: 89.99 },
        { ...mockProduct.variants[0], name: 'Medium', price: 99.99 },
        { ...mockProduct.variants[0], name: 'Large', price: 109.99 }
      ]
    };

    render(
      <TestWrapper>
        <ProductCard product={multiVariantProduct} />
      </TestWrapper>
    );

    expect(screen.getByTestId('variant-selector')).toBeInTheDocument();
    expect(screen.getByText('Small')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Large')).toBeInTheDocument();
  });

  it('should be accessible', () => {
    render(
      <TestWrapper>
        <ProductCard product={mockProduct} />
      </TestWrapper>
    );

    // Check for proper ARIA labels
    expect(screen.getByRole('button', { name: /add to cart/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /add to wishlist/i })).toBeInTheDocument();

    // Check for proper heading structure
    expect(screen.getByRole('heading', { name: mockProduct.name })).toBeInTheDocument();

    // Check for proper image alt text
    expect(screen.getByTestId('product-image')).toHaveAttribute('alt', mockProduct.name);
  });

  it('should handle keyboard navigation', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ProductCard product={mockProduct} />
      </TestWrapper>
    );

    // Tab through interactive elements
    await user.tab();
    expect(screen.getByTestId('product-card')).toHaveFocus();

    await user.tab();
    expect(screen.getByTestId('wishlist-button')).toHaveFocus();

    await user.tab();
    expect(screen.getByText('Add to Cart')).toHaveFocus();
  });

  it('should handle hover effects', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ProductCard product={mockProduct} />
      </TestWrapper>
    );

    const productCard = screen.getByTestId('product-card');
    await user.hover(productCard);

    // Should show additional actions on hover
    expect(screen.getByText('Quick View')).toBeVisible();
  });
});