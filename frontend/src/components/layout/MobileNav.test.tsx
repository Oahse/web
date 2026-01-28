// frontend/src/components/layout/MobileNav.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vitest, beforeEach } from 'vitest';
import { BrowserRouter, Link, useLocation } from 'react-router-dom';
import { MobileNav } from './MobileNav';
import { useCart } from '../../store/CartContext';
import {
  HomeIcon, SearchIcon, ShoppingCartIcon, UserIcon, MenuIcon
} from 'lucide-react'; // Mocked icons

// --- Mock external dependencies ---
vitest.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    Link: vitest.fn(({ to, children, ...props }) => <a href={to} {...props}>{children}</a>),
    useLocation: vitest.fn(),
  };
});

vitest.mock('../../contexts/CartContext', () => ({
  useCart: vitest.fn(),
}));

// Mock lucide-react icons
vitest.mock('lucide-react', () => ({
  HomeIcon: vitest.fn(() => <svg data-testid="icon-home" />),
  SearchIcon: vitest.fn(() => <svg data-testid="icon-search" />),
  ShoppingCartIcon: vitest.fn(() => <svg data-testid="icon-shopping-cart" />),
  UserIcon: vitest.fn(() => <svg data-testid="icon-user" />),
  MenuIcon: vitest.fn(() => <svg data-testid="icon-menu" />),
}));

describe('MobileNav Component', () => {
  const mockUseLocation = useLocation as vitest.Mock;
  const mockUseCart = useCart as vitest.Mock;
  const mockOnSearchClick = vitest.fn();
  const mockOnCategoriesClick = vitest.fn();

  beforeEach(() => {
    vitest.clearAllMocks();
    mockUseLocation.mockReturnValue({ pathname: '/' }); // Default to home path
    mockUseCart.mockReturnValue({ totalItems: 0 }); // Default empty cart
    // Simulate mobile viewport
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 500 });
    window.dispatchEvent(new Event('resize'));
  });

  afterEach(() => {
    // Reset to desktop viewport for other tests if needed
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 1024 });
    window.dispatchEvent(new Event('resize'));
  });

  // Helper to render with BrowserRouter context
  const renderWithRouter = (ui) => render(<BrowserRouter>{ui}</BrowserRouter>);

  it('renders all navigation items', () => {
    renderWithRouter(
      <MobileNav onSearchClick={mockOnSearchClick} onCategoriesClick={mockOnCategoriesClick} />
    );
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Categories')).toBeInTheDocument();
    expect(screen.getByText('Search')).toBeInTheDocument();
    expect(screen.getByText('Cart')).toBeInTheDocument();
    expect(screen.getByText('Account')).toBeInTheDocument();

    expect(screen.getByTestId('icon-home')).toBeInTheDocument();
    expect(screen.getByTestId('icon-menu')).toBeInTheDocument();
    expect(screen.getByTestId('icon-search')).toBeInTheDocument();
    expect(screen.getByTestId('icon-shopping-cart')).toBeInTheDocument();
    expect(screen.getByTestId('icon-user')).toBeInTheDocument();
  });

  it('marks "Home" as active when on home path', () => {
    mockUseLocation.mockReturnValue({ pathname: '/' });
    renderWithRouter(
      <MobileNav onSearchClick={mockOnSearchClick} onCategoriesClick={mockOnCategoriesClick} />
    );
    expect(screen.getByText('Home')).toHaveClass('text-primary');
    expect(screen.getByTestId('icon-home')).toHaveClass('text-primary');
    expect(screen.getByText('Cart')).toHaveClass('text-copy-light'); // Other links not active
  });

  it('marks "Cart" as active when on cart path', () => {
    mockUseLocation.mockReturnValue({ pathname: '/cart' });
    renderWithRouter(
      <MobileNav onSearchClick={mockOnSearchClick} onCategoriesClick={mockOnCategoriesClick} />
    );
    expect(screen.getByText('Cart')).toHaveClass('text-primary');
    expect(screen.getByTestId('icon-shopping-cart')).toHaveClass('text-primary');
  });

  it('displays cart item count badge when totalItems > 0', () => {
    mockUseCart.mockReturnValue({ totalItems: 5 });
    renderWithRouter(
      <MobileNav onSearchClick={mockOnSearchClick} onCategoriesClick={mockOnCategoriesClick} />
    );
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('does not display cart item count badge when totalItems is 0', () => {
    mockUseCart.mockReturnValue({ totalItems: 0 });
    renderWithRouter(
      <MobileNav onSearchClick={mockOnSearchClick} onCategoriesClick={mockOnCategoriesClick} />
    );
    expect(screen.queryByText('0')).not.toBeInTheDocument();
  });

  it('calls onCategoriesClick when Categories button is clicked', () => {
    renderWithRouter(
      <MobileNav onSearchClick={mockOnSearchClick} onCategoriesClick={mockOnCategoriesClick} />
    );
    fireEvent.click(screen.getByText('Categories'));
    expect(mockOnCategoriesClick).toHaveBeenCalledTimes(1);
  });

  it('calls onSearchClick when Search button is clicked', () => {
    renderWithRouter(
      <MobileNav onSearchClick={mockOnSearchClick} onCategoriesClick={mockOnCategoriesClick} />
    );
    fireEvent.click(screen.getByText('Search'));
    expect(mockOnSearchClick).toHaveBeenCalledTimes(1);
  });
});
