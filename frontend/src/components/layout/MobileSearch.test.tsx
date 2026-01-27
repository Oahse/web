// frontend/src/components/layout/MobileSearch.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vitest, beforeEach, afterEach } from 'vitest';
import { useNavigate } from 'react-router-dom';
import { MobileSearch } from './MobileSearch';
import { useCategories } from '../../contexts/CategoryContext';
import { SearchIcon, XIcon } from 'lucide-react'; // Mocked icons

// Mock external dependencies
vitest.mock('react-router-dom', () => ({
  useNavigate: vitest.fn(),
}));

vitest.mock('../../contexts/CategoryContext', () => ({
  useCategories: vitest.fn(),
}));

// Mock lucide-react icons
vitest.mock('lucide-react', () => ({
  SearchIcon: vitest.fn(() => <svg data-testid="search-icon" />),
  XIcon: vitest.fn(() => <svg data-testid="x-icon" />),
}));

describe('MobileSearch Component', () => {
  const mockUseNavigate = useNavigate as vitest.Mock;
  const mockUseCategories = useCategories as vitest.Mock;
  const mockOnClose = vitest.fn();

  const mockCategories = [
    { name: 'Cereal Crops', slug: 'cereal-crops' },
    { name: 'Legumes', slug: 'legumes' },
  ];

  let inputFocusSpy: vitest.SpyInstance;

  beforeEach(() => {
    vitest.clearAllMocks();
    mockUseNavigate.mockReturnValue(vitest.fn()); // Ensure useNavigate returns a function
    mockUseCategories.mockReturnValue({
      categories: mockCategories,
      loading: false,
      error: null,
    });
    // Ensure body overflow is reset before each test
    document.body.style.overflow = 'unset';

    // Mock inputRef.current.focus()
    const mockInputRef = { current: { focus: vitest.fn() } };
    vitest.spyOn(React, 'useRef').mockReturnValue(mockInputRef);
    inputFocusSpy = mockInputRef.current.focus;
  });

  afterEach(() => {
    document.body.style.overflow = 'unset';
    vitest.restoreAllMocks(); // Restore all mocks after each test
  });

  it('renders nothing when isOpen is false', () => {
    const { container } = render(<MobileSearch isOpen={false} onClose={mockOnClose} />);
    expect(container).toBeEmptyDOMElement();
    expect(document.body.style.overflow).toBe('unset');
  });

  it('renders search overlay when isOpen is true and sets body overflow to hidden', () => {
    render(<MobileSearch isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByText('Search Products')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search for products...')).toBeInTheDocument();
    expect(screen.getByTestId('search-icon')).toBeInTheDocument();
    expect(document.body.style.overflow).toBe('hidden');
    expect(inputFocusSpy).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when "X" button is clicked', () => {
    render(<MobileSearch isOpen={true} onClose={mockOnClose} />);
    fireEvent.click(screen.getByTestId('x-icon').closest('button')!);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when backdrop is clicked', () => {
    render(<MobileSearch isOpen={true} onClose={mockOnClose} />);
    // Click on the backdrop div (flex-grow div)
    const backdrop = screen.getByText('Search Products').closest('div')?.parentElement?.lastElementChild;
    if (backdrop) {
      fireEvent.click(backdrop);
    } else {
      // Fallback if direct selection fails
      fireEvent.click(document.body);
    }
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('handles product search submission', async () => {
    const navigate = vitest.fn();
    (useNavigate as vitest.Mock).mockReturnValue(navigate);

    render(<MobileSearch isOpen={true} onClose={mockOnClose} />);
    const searchInput = screen.getByPlaceholderText('Search for products...') as HTMLInputElement;
    fireEvent.change(searchInput, { target: { value: 'organic coffee' } });
    fireEvent.submit(searchInput);

    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith('/products/search?q=organic%20coffee');
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  it('displays popular search terms and handles clicks', async () => {
    const navigate = vitest.fn();
    (useNavigate as vitest.Mock).mockReturnValue(navigate);

    render(<MobileSearch isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByText('Popular Searches')).toBeInTheDocument();
    
    const moringaButton = screen.getByRole('button', { name: 'Moringa powder' });
    fireEvent.click(moringaButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search for products...')).toHaveValue('Moringa powder');
      expect(navigate).toHaveBeenCalledWith('/products/search?q=Moringa%20powder');
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  it('displays popular categories and handles clicks', async () => {
    const navigate = vitest.fn();
    (useNavigate as vitest.Mock).mockReturnValue(navigate);

    render(<MobileSearch isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByText('Popular Categories')).toBeInTheDocument();

    const cerealCropsButton = screen.getByRole('button', { name: 'Cereal Crops' });
    fireEvent.click(cerealCropsButton);

    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith('/products?category=Cereal%20Crops');
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  it('shows loading message for popular categories', () => {
    mockUseCategories.mockReturnValue({ categories: [], loading: true, error: null });
    render(<MobileSearch isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByText('Loading categories...')).toBeInTheDocument();
  });

  it('shows error message for popular categories', () => {
    mockUseCategories.mockReturnValue({ categories: [], loading: false, error: 'Failed to fetch' });
    render(<MobileSearch isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByText('Error loading categories: Failed to fetch')).toBeInTheDocument();
  });
});
