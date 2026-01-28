/**
 * Tests for Cart.tsx
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Cart from '../../pages/Cart';
import { mockCart, mockUser } from '../setup';

// Mock cart context
const mockUpdateQuantity = vi.fn();
const mockRemoveItem = vi.fn();
const mockClearCart = vi.fn();

vi.mock('../../hooks/useCart', () => ({
  useCart: () => ({
    items: mockCart.items,
    total: mockCart.total,
    itemCount: 2,
    isLoading: false,
    error: null,
    updateQuantity: mockUpdateQuantity,
    removeItem: mockRemoveItem,
    clearCart: mockClearCart
  })
}));

// Mock auth context
vi.mock('../../store/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
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
vi.mock('../../components/cart/CartItem', () => ({
  CartItem: ({ item, onUpdateQuantity, onRemove }: any) => (
    <div data-testid={`cart-item-${item.id}`}>
      <h3>{item.variant.name}</h3>
      <p>${item.price}</p>
      <p>Quantity: {item.quantity}</p>
      <button onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}>
        Increase
      </button>
      <button onClick={() => onUpdateQuantity(item.id, item.quantity - 1)}>
        Decrease
      </button>
      <button onClick={() => onRemove(item.id)}>Remove</button>
    </div>
  )
}));

vi.mock('../../components/ui/Button', () => ({
  Button: ({ children, onClick, disabled, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} {...props}>
      {children}
    </button>
  )
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('Cart', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render cart page with items', () => {
    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    expect(screen.getByText('Shopping Cart')).toBeInTheDocument();
    expect(screen.getByText('2 items')).toBeInTheDocument();
    expect(screen.getByTestId(`cart-item-${mockCart.items[0].id}`)).toBeInTheDocument();
  });

  it('should display cart total', () => {
    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    expect(screen.getByText(`$${mockCart.total.toFixed(2)}`)).toBeInTheDocument();
  });

  it('should handle quantity updates', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    const increaseButton = screen.getByText('Increase');
    await user.click(increaseButton);

    expect(mockUpdateQuantity).toHaveBeenCalledWith(
      mockCart.items[0].id,
      mockCart.items[0].quantity + 1
    );
  });

  it('should handle item removal', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    const removeButton = screen.getByText('Remove');
    await user.click(removeButton);

    expect(mockRemoveItem).toHaveBeenCalledWith(mockCart.items[0].id);
  });

  it('should handle clear cart', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    const clearButton = screen.getByText('Clear Cart');
    await user.click(clearButton);

    // Should show confirmation dialog
    expect(screen.getByText(/are you sure/i)).toBeInTheDocument();

    const confirmButton = screen.getByText('Yes, Clear Cart');
    await user.click(confirmButton);

    expect(mockClearCart).toHaveBeenCalled();
  });

  it('should navigate to checkout', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    const checkoutButton = screen.getByText('Proceed to Checkout');
    await user.click(checkoutButton);

    expect(mockNavigate).toHaveBeenCalledWith('/checkout');
  });

  it('should show empty cart message when no items', () => {
    // Mock empty cart
    vi.mocked(require('../../hooks/useCart').useCart).mockReturnValue({
      items: [],
      total: 0,
      itemCount: 0,
      isLoading: false,
      error: null,
      updateQuantity: mockUpdateQuantity,
      removeItem: mockRemoveItem,
      clearCart: mockClearCart
    });

    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    expect(screen.getByText(/your cart is empty/i)).toBeInTheDocument();
    expect(screen.getByText('Continue Shopping')).toBeInTheDocument();
  });

  it('should show loading state', () => {
    // Mock loading state
    vi.mocked(require('../../hooks/useCart').useCart).mockReturnValue({
      items: [],
      total: 0,
      itemCount: 0,
      isLoading: true,
      error: null,
      updateQuantity: mockUpdateQuantity,
      removeItem: mockRemoveItem,
      clearCart: mockClearCart
    });

    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('should show error state', () => {
    // Mock error state
    vi.mocked(require('../../hooks/useCart').useCart).mockReturnValue({
      items: [],
      total: 0,
      itemCount: 0,
      isLoading: false,
      error: 'Failed to load cart',
      updateQuantity: mockUpdateQuantity,
      removeItem: mockRemoveItem,
      clearCart: mockClearCart
    });

    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    expect(screen.getByText('Failed to load cart')).toBeInTheDocument();
  });

  it('should calculate and display subtotal', () => {
    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    const subtotal = mockCart.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    expect(screen.getByText(`Subtotal: $${subtotal.toFixed(2)}`)).toBeInTheDocument();
  });

  it('should show estimated tax and shipping', () => {
    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    expect(screen.getByText(/estimated tax/i)).toBeInTheDocument();
    expect(screen.getByText(/shipping/i)).toBeInTheDocument();
  });

  it('should handle continue shopping', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    const continueButton = screen.getByText('Continue Shopping');
    await user.click(continueButton);

    expect(mockNavigate).toHaveBeenCalledWith('/products');
  });

  it('should show save for later option', () => {
    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    expect(screen.getByText(/save for later/i)).toBeInTheDocument();
  });

  it('should handle promo code application', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    const promoInput = screen.getByPlaceholderText(/enter promo code/i);
    const applyButton = screen.getByText('Apply');

    await user.type(promoInput, 'SAVE10');
    await user.click(applyButton);

    // Should call API to validate promo code
    expect(promoInput).toHaveValue('SAVE10');
  });

  it('should be responsive', () => {
    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    const cartContainer = screen.getByTestId('cart-container');
    expect(cartContainer).toHaveClass('container', 'mx-auto', 'px-4');
  });

  it('should handle guest user cart', () => {
    // Mock unauthenticated user
    vi.mocked(require('../../store/AuthContext').useAuth).mockReturnValue({
      user: null,
      isAuthenticated: false
    });

    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    // Should still show cart items for guest users
    expect(screen.getByText('Shopping Cart')).toBeInTheDocument();
    expect(screen.getByText(/sign in for faster checkout/i)).toBeInTheDocument();
  });

  it('should show recently viewed items when cart is empty', () => {
    // Mock empty cart
    vi.mocked(require('../../hooks/useCart').useCart).mockReturnValue({
      items: [],
      total: 0,
      itemCount: 0,
      isLoading: false,
      error: null,
      updateQuantity: mockUpdateQuantity,
      removeItem: mockRemoveItem,
      clearCart: mockClearCart
    });

    render(
      <TestWrapper>
        <Cart />
      </TestWrapper>
    );

    expect(screen.getByText(/recently viewed/i)).toBeInTheDocument();
  });
});