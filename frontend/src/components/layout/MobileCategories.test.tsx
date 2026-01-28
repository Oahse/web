// frontend/src/components/layout/MobileCategories.test.tsx
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vitest, beforeEach, afterEach } from 'vitest';
import { BrowserRouter, Link } from 'react-router-dom';
import { MobileCategories } from './MobileCategories';
import { useCategories } from '../../store/CategoryContext';
import { XIcon, ChevronRightIcon } from 'lucide-react'; // Mocked icons

// Mock external dependencies
vitest.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    Link: vitest.fn(({ to, children, ...props }) => (
      <a href={to} {...props}>
        {children}
      </a>
    )),
  };
});

vitest.mock('../../contexts/CategoryContext', () => ({
  useCategories: vitest.fn(),
}));

// Mock lucide-react icons
vitest.mock('lucide-react', () => ({
  XIcon: vitest.fn(() => <svg data-testid="x-icon" />),
  ChevronRightIcon: vitest.fn(() => <svg data-testid="chevron-right-icon" />),
}));

describe('MobileCategories Component', () => {
  const mockUseCategories = useCategories as vitest.Mock;
  const mockOnClose = vitest.fn();

  const mockCategories = [
    { name: 'Cereal Crops', slug: 'cereal-crops', image: '🌾' },
    { name: 'Legumes', slug: 'legumes', image: '🌱' },
  ];

  beforeEach(() => {
    vitest.clearAllMocks();
    mockUseCategories.mockReturnValue({
      categories: mockCategories,
      loading: false,
      error: null,
    });
    // Ensure body overflow is reset before each test
    document.body.style.overflow = 'unset';
  });

  afterEach(() => {
    // Clean up any lingering body overflow styles
    document.body.style.overflow = 'unset';
  });

  it('renders nothing when isOpen is false', () => {
    const { container } = render(<MobileCategories isOpen={false} onClose={mockOnClose} />);
    expect(container).toBeEmptyDOMElement();
    expect(document.body.style.overflow).toBe('unset');
  });

  it('renders sidebar when isOpen is true and sets body overflow to hidden', () => {
    render(<MobileCategories isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByText('Categories')).toBeInTheDocument();
    expect(screen.getByText('Shop By Category')).toBeInTheDocument();
    expect(screen.getByText('Cereal Crops')).toBeInTheDocument();
    expect(document.body.style.overflow).toBe('hidden');
  });

  it('calls onClose when "X" button is clicked', () => {
    render(<MobileCategories isOpen={true} onClose={mockOnClose} />);
    fireEvent.click(screen.getByTestId('x-icon').closest('button')!);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
    expect(document.body.style.overflow).toBe('unset'); // Should reset on close
  });

  it('calls onClose when backdrop is clicked', () => {
    render(<MobileCategories isOpen={true} onClose={mockOnClose} />);
    fireEvent.click(screen.getByText('Categories').closest('div')!.nextElementSibling!); // Click on the backdrop div
    expect(mockOnClose).toHaveBeenCalledTimes(1);
    expect(document.body.style.overflow).toBe('unset'); // Should reset on close
  });

  it('displays loading message when categories are loading', () => {
    mockUseCategories.mockReturnValue({ categories: [], loading: true, error: null });
    render(<MobileCategories isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByText('Loading categories...')).toBeInTheDocument();
  });

  it('displays error message when categories fail to load', () => {
    mockUseCategories.mockReturnValue({ categories: [], loading: false, error: 'Failed to fetch' });
    render(<MobileCategories isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByText('Error loading categories: Failed to fetch')).toBeInTheDocument();
  });

  it('renders category links', () => {
    render(<MobileCategories isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByRole('link', { name: /cereal crops/i })).toHaveAttribute('href', '/products?category=cereal-crops');
    expect(screen.getByText('🌾')).toBeInTheDocument(); // Emoji icon
    expect(screen.getByRole('link', { name: /legumes/i })).toHaveAttribute('href', '/products?category=legumes');
  });

  it('renders user action links', () => {
    render(<MobileCategories isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByRole('link', { name: 'Sign In / Register' })).toHaveAttribute('href', '/login');
    expect(screen.getByRole('link', { name: 'My Orders' })).toHaveAttribute('href', '/account/orders');
    expect(screen.getByRole('link', { name: 'Wishlist' })).toHaveAttribute('href', '/account/wishlist');
  });

  it('renders main navigation links', () => {
    render(<MobileCategories isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByRole('link', { name: 'Home' })).toHaveAttribute('href', '/');
    expect(screen.getByRole('link', { name: 'About' })).toHaveAttribute('href', '/about');
  });

  it('renders support center info', () => {
    render(<MobileCategories isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByText('1900100888')).toBeInTheDocument();
    expect(screen.getByText('Support Center')).toBeInTheDocument();
  });

  it('calls onClose when any navigation link is clicked', () => {
    render(<MobileCategories isOpen={true} onClose={mockOnClose} />);
    fireEvent.click(screen.getByRole('link', { name: 'Home' }));
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
});
