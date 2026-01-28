/**
 * Tests for Home.tsx
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Home from '../../pages/Home';
import { mockApiResponses } from '../setup';

// Mock API client
vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    getFeaturedProducts: vi.fn(),
    getProducts: vi.fn()
  }
}));

// Mock components
vi.mock('../../components/product/ProductCard', () => ({
  ProductCard: ({ product }: { product: any }) => (
    <div data-testid={`product-card-${product.id}`}>
      <h3>{product.name}</h3>
      <p>${product.variants[0]?.price}</p>
    </div>
  )
}));

vi.mock('../../components/ui/SkeletonProductCard', () => ({
  SkeletonProductCard: () => <div data-testid="skeleton-product-card" />
}));

vi.mock('../../components/ui/Button', () => ({
  Button: ({ children, onClick, ...props }: any) => (
    <button onClick={onClick} {...props}>
      {children}
    </button>
  )
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('Home', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render home page with hero section', async () => {
    const { apiClient } = await import('../../api/client');
    vi.mocked(apiClient.getFeaturedProducts).mockResolvedValue([]);
    vi.mocked(apiClient.getProducts).mockResolvedValue({ products: [] });

    render(
      <TestWrapper>
        <Home />
      </TestWrapper>
    );

    // Check for hero section elements
    expect(screen.getByText(/welcome/i)).toBeInTheDocument();
    expect(screen.getByText(/discover/i)).toBeInTheDocument();
  });

  it('should load and display featured products', async () => {
    const { apiClient } = await import('../../api/client');
    const featuredProducts = [mockApiResponses.products.list[0]];
    
    vi.mocked(apiClient.getFeaturedProducts).mockResolvedValue(featuredProducts);
    vi.mocked(apiClient.getProducts).mockResolvedValue({ products: [] });

    render(
      <TestWrapper>
        <Home />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Featured Products')).toBeInTheDocument();
      expect(screen.getByTestId(`product-card-${featuredProducts[0].id}`)).toBeInTheDocument();
    });

    expect(apiClient.getFeaturedProducts).toHaveBeenCalledWith(8);
  });

  it('should load and display popular products', async () => {
    const { apiClient } = await import('../../api/client');
    const popularProducts = [mockApiResponses.products.list[0]];
    
    vi.mocked(apiClient.getFeaturedProducts).mockResolvedValue([]);
    vi.mocked(apiClient.getProducts).mockResolvedValue({ 
      products: popularProducts 
    });

    render(
      <TestWrapper>
        <Home />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Popular Products')).toBeInTheDocument();
      expect(screen.getByTestId(`product-card-${popularProducts[0].id}`)).toBeInTheDocument();
    });

    expect(apiClient.getProducts).toHaveBeenCalledWith({
      sort: 'popular',
      limit: 8
    });
  });

  it('should show loading skeletons while fetching data', () => {
    const { apiClient } = await import('../../api/client');
    vi.mocked(apiClient.getFeaturedProducts).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );
    vi.mocked(apiClient.getProducts).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <TestWrapper>
        <Home />
      </TestWrapper>
    );

    // Should show skeleton loaders
    expect(screen.getAllByTestId('skeleton-product-card')).toHaveLength(16); // 8 featured + 8 popular
  });

  it('should handle API errors gracefully', async () => {
    const { apiClient } = await import('../../api/client');
    vi.mocked(apiClient.getFeaturedProducts).mockRejectedValue(new Error('API Error'));
    vi.mocked(apiClient.getProducts).mockRejectedValue(new Error('API Error'));

    render(
      <TestWrapper>
        <Home />
      </TestWrapper>
    );

    await waitFor(() => {
      // Should not crash and should show some fallback content
      expect(screen.getByText(/welcome/i)).toBeInTheDocument();
    });
  });

  it('should render call-to-action buttons', async () => {
    const { apiClient } = await import('../../api/client');
    vi.mocked(apiClient.getFeaturedProducts).mockResolvedValue([]);
    vi.mocked(apiClient.getProducts).mockResolvedValue({ products: [] });

    render(
      <TestWrapper>
        <Home />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Shop Now')).toBeInTheDocument();
      expect(screen.getByText('View All Products')).toBeInTheDocument();
    });
  });

  it('should display categories section', async () => {
    const { apiClient } = await import('../../api/client');
    vi.mocked(apiClient.getFeaturedProducts).mockResolvedValue([]);
    vi.mocked(apiClient.getProducts).mockResolvedValue({ products: [] });

    render(
      <TestWrapper>
        <Home />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Shop by Category')).toBeInTheDocument();
    });
  });

  it('should be responsive', async () => {
    const { apiClient } = await import('../../api/client');
    vi.mocked(apiClient.getFeaturedProducts).mockResolvedValue([]);
    vi.mocked(apiClient.getProducts).mockResolvedValue({ products: [] });

    render(
      <TestWrapper>
        <Home />
      </TestWrapper>
    );

    // Check for responsive classes
    const container = screen.getByRole('main');
    expect(container).toHaveClass('container', 'mx-auto', 'px-4');
  });
});