/**
 * Tests for Header.tsx
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Header from '../../../components/layout/Header';
import { mockUser } from '../../setup';

// Mock auth context
const mockLogout = vi.fn();
vi.mock('../../../store/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    isAuthenticated: true,
    logout: mockLogout
  })
}));

// Mock cart context
vi.mock('../../../hooks/useCart', () => ({
  useCart: () => ({
    itemCount: 3,
    total: 99.99
  })
}));

// Mock router
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    Link: ({ children, to, className }: { children: React.ReactNode; to: string; className?: string }) => (
      <a href={to} className={className}>{children}</a>
    )
  };
});

// Mock components
vi.mock('../../../components/layout/MobileNav', () => ({
  MobileNav: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => (
    isOpen ? <div data-testid="mobile-nav">Mobile Nav</div> : null
  )
}));

vi.mock('../../../components/layout/MobileSearch', () => ({
  MobileSearch: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => (
    isOpen ? <div data-testid="mobile-search">Mobile Search</div> : null
  )
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render header with logo and navigation', () => {
    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    expect(screen.getByAltText(/logo/i)).toBeInTheDocument();
    expect(screen.getByText('Products')).toBeInTheDocument();
    expect(screen.getByText('Categories')).toBeInTheDocument();
  });

  it('should render search bar', () => {
    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    expect(screen.getByPlaceholderText(/search products/i)).toBeInTheDocument();
  });

  it('should render cart icon with item count', () => {
    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    expect(screen.getByTestId('cart-icon')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument(); // Cart item count
  });

  it('should render user menu when authenticated', () => {
    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    expect(screen.getByText(mockUser.first_name)).toBeInTheDocument();
    expect(screen.getByTestId('user-menu')).toBeInTheDocument();
  });

  it('should render login/register links when not authenticated', () => {
    // Mock unauthenticated state
    vi.mocked(require('../../../store/AuthContext').useAuth).mockReturnValue({
      user: null,
      isAuthenticated: false,
      logout: mockLogout
    });

    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    expect(screen.getByText('Sign In')).toBeInTheDocument();
    expect(screen.getByText('Register')).toBeInTheDocument();
  });

  it('should handle search functionality', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText(/search products/i);
    await user.type(searchInput, 'test product');
    await user.keyboard('{Enter}');

    expect(mockNavigate).toHaveBeenCalledWith('/products?search=test product');
  });

  it('should handle mobile menu toggle', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    const menuButton = screen.getByTestId('mobile-menu-button');
    await user.click(menuButton);

    expect(screen.getByTestId('mobile-nav')).toBeInTheDocument();
  });

  it('should handle mobile search toggle', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    const searchButton = screen.getByTestId('mobile-search-button');
    await user.click(searchButton);

    expect(screen.getByTestId('mobile-search')).toBeInTheDocument();
  });

  it('should handle user menu dropdown', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    const userMenuButton = screen.getByTestId('user-menu-button');
    await user.click(userMenuButton);

    expect(screen.getByText('My Account')).toBeInTheDocument();
    expect(screen.getByText('Orders')).toBeInTheDocument();
    expect(screen.getByText('Wishlist')).toBeInTheDocument();
    expect(screen.getByText('Sign Out')).toBeInTheDocument();
  });

  it('should handle logout', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    const userMenuButton = screen.getByTestId('user-menu-button');
    await user.click(userMenuButton);

    const logoutButton = screen.getByText('Sign Out');
    await user.click(logoutButton);

    expect(mockLogout).toHaveBeenCalled();
  });

  it('should navigate to cart when cart icon is clicked', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    const cartIcon = screen.getByTestId('cart-icon');
    await user.click(cartIcon);

    expect(mockNavigate).toHaveBeenCalledWith('/cart');
  });

  it('should show categories dropdown on hover', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    const categoriesLink = screen.getByText('Categories');
    await user.hover(categoriesLink);

    await waitFor(() => {
      expect(screen.getByTestId('categories-dropdown')).toBeInTheDocument();
    });
  });

  it('should be responsive', () => {
    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    // Check for responsive classes
    const header = screen.getByRole('banner');
    expect(header).toHaveClass('sticky', 'top-0', 'z-50');

    // Mobile menu button should be visible on mobile
    expect(screen.getByTestId('mobile-menu-button')).toHaveClass('md:hidden');

    // Desktop navigation should be hidden on mobile
    expect(screen.getByTestId('desktop-nav')).toHaveClass('hidden', 'md:flex');
  });

  it('should handle keyboard navigation', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    // Tab through navigation elements
    await user.tab();
    expect(screen.getByText('Products')).toHaveFocus();

    await user.tab();
    expect(screen.getByText('Categories')).toHaveFocus();

    await user.tab();
    expect(screen.getByPlaceholderText(/search products/i)).toHaveFocus();
  });

  it('should show notifications icon when user has notifications', () => {
    // Mock user with notifications
    vi.mocked(require('../../../store/AuthContext').useAuth).mockReturnValue({
      user: { ...mockUser, unread_notifications: 2 },
      isAuthenticated: true,
      logout: mockLogout
    });

    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    expect(screen.getByTestId('notifications-icon')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // Notification count
  });

  it('should handle theme toggle', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    const themeToggle = screen.getByTestId('theme-toggle');
    await user.click(themeToggle);

    // Should toggle between light and dark themes
    expect(themeToggle).toHaveAttribute('aria-pressed');
  });

  it('should show wishlist icon with count', () => {
    // Mock wishlist context
    vi.doMock('../../../store/WishlistContext', () => ({
      useWishlist: () => ({
        items: [{ id: '1' }, { id: '2' }],
        itemCount: 2
      })
    }));

    render(
      <TestWrapper>
        <Header />
      </TestWrapper>
    );

    expect(screen.getByTestId('wishlist-icon')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // Wishlist item count
  });
});