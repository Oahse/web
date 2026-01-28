/**
 * Tests for Products.tsx
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Products from '../../pages/Products';
import { mockApiResponses } from '../setup';

// Mock API client
vi.mock('../../api/client', () => ({
  apiClient: {
    getProducts: vi.fn(),
    get: vi.fn()
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

vi.mock('../../components/ui/Pagination', () => ({
  Pagination: ({ currentPage, totalPages, onPageChange }: any) => (
    <div data-testid="pagination">
      <button onClick={() => onPageChange(currentPage - 1)} disabled={currentPage === 1}>
        Previous
      </button>
      <span>Page {currentPage} of {totalPages}</span>
      <button onClick={() => onPageChange(currentPage + 1)} disabled={currentPage === totalPages}>
        Next
      </button>
    </div>
  )
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('Products', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render products page with search and filters', async () => {
    const { apiClient } = await import('../../api/client');
    vi.mocked(apiClient.getProducts).mockResolvedValue({
      products: [],
      total: 0,
      page: 1,
      totalPages: 1
    });

    render(
      <TestWrapper>
        <Products />
      </TestWrapper>
    );

    expect(screen.getByPlaceholderText(/search products/i)).toBeInTheDocument();
    expect(screen.getByText(/filters/i)).toBeInTheDocument();
  });

  it('should load and display products', async () => {
    const { apiClient } = await import('../../api/client');
    const products = [mockApiResponses.products.list[0]];
    
    vi.mocked(apiClient.getProducts).mockResolvedValue({
      products,
      total: 1,
      page: 1,
      totalPages: 1
    });

    render(
      <TestWrapper>
        <Products />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId(`product-card-${products[0].id}`)).toBeInTheDocument();
      expect(screen.getByText('1 products found')).toBeInTheDocument();
    });
  });

  it('should handle search functionality', async () => {
    const user = userEvent.setup();
    const { apiClient } = await import('../../api/client');
    
    vi.mocked(apiClient.getProducts).mockResolvedValue({
      products: [],
      total: 0,
      page: 1,
      totalPages: 1
    });

    render(
      <TestWrapper>
        <Products />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText(/search products/i);
    await user.type(searchInput, 'test product');

    await waitFor(() => {
      expect(apiClient.getProducts).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'test product'
        })
      );
    });
  });

  it('should handle category filtering', async () => {
    const user = userEvent.setup();
    const { apiClient } = await import('../../api/client');
    
    vi.mocked(apiClient.getProducts).mockResolvedValue({
      products: [],
      total: 0,
      page: 1,
      totalPages: 1
    });

    render(
      <TestWrapper>
        <Products />
      </TestWrapper>
    );

    // Mock category filter interaction
    const categoryFilter = screen.getByText(/category/i);
    await user.click(categoryFilter);

    // Select electronics category
    const electronicsOption = screen.getByText('Electronics');
    await user.click(electronicsOption);

    await waitFor(() => {
      expect(apiClient.getProducts).toHaveBeenCalledWith(
        expect.objectContaining({
          category: 'electronics'
        })
      );
    });
  });

  it('should handle price range filtering', async () => {
    const user = userEvent.setup();
    const { apiClient } = await import('../../api/client');
    
    vi.mocked(apiClient.getProducts).mockResolvedValue({
      products: [],
      total: 0,
      page: 1,
      totalPages: 1
    });

    render(
      <TestWrapper>
        <Products />
      </TestWrapper>
    );

    // Mock price range filter
    const minPriceInput = screen.getByLabelText(/min price/i);
    const maxPriceInput = screen.getByLabelText(/max price/i);

    await user.type(minPriceInput, '10');
    await user.type(maxPriceInput, '100');

    await waitFor(() => {
      expect(apiClient.getProducts).toHaveBeenCalledWith(
        expect.objectContaining({
          min_price: 10,
          max_price: 100
        })
      );
    });
  });

  it('should handle sorting', async () => {
    const user = userEvent.setup();
    const { apiClient } = await import('../../api/client');
    
    vi.mocked(apiClient.getProducts).mockResolvedValue({
      products: [],
      total: 0,
      page: 1,
      totalPages: 1
    });

    render(
      <TestWrapper>
        <Products />
      </TestWrapper>
    );

    const sortSelect = screen.getByLabelText(/sort by/i);
    await user.selectOptions(sortSelect, 'price_asc');

    await waitFor(() => {
      expect(apiClient.getProducts).toHaveBeenCalledWith(
        expect.objectContaining({
          sort: 'price_asc'
        })
      );
    });
  });

  it('should handle pagination', async () => {
    const user = userEvent.setup();
    const { apiClient } = await import('../../api/client');
    
    vi.mocked(apiClient.getProducts).mockResolvedValue({
      products: [],
      total: 50,
      page: 1,
      totalPages: 5
    });

    render(
      <TestWrapper>
        <Products />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('pagination')).toBeInTheDocument();
    });

    const nextButton = screen.getByText('Next');
    await user.click(nextButton);

    await waitFor(() => {
      expect(apiClient.getProducts).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2
        })
      );
    });
  });

  it('should show loading state', () => {
    const { apiClient } = await import('../../api/client');
    vi.mocked(apiClient.getProducts).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <TestWrapper>
        <Products />
      </TestWrapper>
    );

    expect(screen.getAllByTestId('skeleton-product-card')).toHaveLength(12);
  });

  it('should handle empty results', async () => {
    const { apiClient } = await import('../../api/client');
    vi.mocked(apiClient.getProducts).mockResolvedValue({
      products: [],
      total: 0,
      page: 1,
      totalPages: 1
    });

    render(
      <TestWrapper>
        <Products />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/no products found/i)).toBeInTheDocument();
    });
  });

  it('should handle API errors', async () => {
    const { apiClient } = await import('../../api/client');
    vi.mocked(apiClient.getProducts).mockRejectedValue(new Error('API Error'));

    render(
      <TestWrapper>
        <Products />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/error loading products/i)).toBeInTheDocument();
    });
  });

  it('should clear filters', async () => {
    const user = userEvent.setup();
    const { apiClient } = await import('../../api/client');
    
    vi.mocked(apiClient.getProducts).mockResolvedValue({
      products: [],
      total: 0,
      page: 1,
      totalPages: 1
    });

    render(
      <TestWrapper>
        <Products />
      </TestWrapper>
    );

    // Apply some filters first
    const searchInput = screen.getByPlaceholderText(/search products/i);
    await user.type(searchInput, 'test');

    // Clear filters
    const clearButton = screen.getByText(/clear filters/i);
    await user.click(clearButton);

    await waitFor(() => {
      expect(searchInput).toHaveValue('');
      expect(apiClient.getProducts).toHaveBeenCalledWith({
        page: 1,
        limit: 12
      });
    });
  });

  it('should be responsive', async () => {
    const { apiClient } = await import('../../api/client');
    vi.mocked(apiClient.getProducts).mockResolvedValue({
      products: [],
      total: 0,
      page: 1,
      totalPages: 1
    });

    render(
      <TestWrapper>
        <Products />
      </TestWrapper>
    );

    // Check for responsive grid classes
    const productsGrid = screen.getByTestId('products-grid');
    expect(productsGrid).toHaveClass('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3', 'xl:grid-cols-4');
  });
});