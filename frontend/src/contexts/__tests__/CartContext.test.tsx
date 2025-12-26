import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { CartProvider, useCart } from '../CartContext';
import { AuthContext } from '../AuthContext';

// Mock the APIs
vi.mock('../../apis/cart', () => ({
  default: {
    getCart: vi.fn(),
    addToCart: vi.fn(),
    updateCartItem: vi.fn(),
    removeFromCart: vi.fn(),
    clearCart: vi.fn(),
  },
}));

// Test component that uses the cart context
const TestComponent = () => {
  const { cart, isLoading, addItem, updateQuantity, removeItem, clearCart, refreshCart } = useCart();

  return (
    <div>
      <div data-testid="cart-status">
        {isLoading ? 'Loading' : cart ? 'Cart Loaded' : 'No Cart'}
      </div>
      {cart && (
        <div>
          <div data-testid="cart-items-count">{cart.items?.length || 0}</div>
          <div data-testid="cart-total">${cart.total_amount || 0}</div>
        </div>
      )}
      <button onClick={() => addItem({ variant_id: '1', quantity: 1 })}>Add Item</button>
      <button onClick={() => updateQuantity('item-1', 2)}>Update Quantity</button>
      <button onClick={() => removeItem('item-1')}>Remove Item</button>
      <button onClick={clearCart}>Clear Cart</button>
      <button onClick={refreshCart}>Refresh Cart</button>
    </div>
  );
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

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <AuthContext.Provider value={mockAuthContext}>
      <CartProvider>
        {component}
      </CartProvider>
    </AuthContext.Provider>
  );
};

describe('CartContext', () => {
  const mockCart = {
    id: 'cart-1',
    user_id: '1',
    items: [
      {
        id: 'item-1',
        variant: {
          id: '1',
          product_id: 'product-1',
          sku: 'SKU-001',
          name: 'Test Product',
          base_price: 29.99,
          stock: 10,
          images: [],
        },
        quantity: 1,
        price_per_unit: 29.99,
        total_price: 29.99,
      },
    ],
    total_items: 1,
    total_amount: 29.99,
    created_at: '2023-01-01T00:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('provides initial empty cart state', () => {
    const { CartAPI } = require('../../apis/cart');
    (CartAPI.getCart as any).mockResolvedValue({
      success: true,
      data: null,
    });

    renderWithProviders(<TestComponent />);

    expect(screen.getByTestId('cart-status')).toHaveTextContent('Loading');
  });

  it('loads cart data on initialization', async () => {
    const { CartAPI } = require('../../apis/cart');
    (CartAPI.getCart as any).mockResolvedValue({
      success: true,
      data: mockCart,
    });

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('cart-status')).toHaveTextContent('Cart Loaded');
      expect(screen.getByTestId('cart-items-count')).toHaveTextContent('1');
      expect(screen.getByTestId('cart-total')).toHaveTextContent('$29.99');
    });
  });

  it('adds item to cart successfully', async () => {
    const { CartAPI } = require('../../apis/cart');
    (CartAPI.getCart as any).mockResolvedValue({
      success: true,
      data: mockCart,
    });
    (CartAPI.addToCart as any).mockResolvedValue({
      success: true,
      data: {
        ...mockCart,
        items: [
          ...mockCart.items,
          {
            id: 'item-2',
            variant: {
              id: '2',
              product_id: 'product-2',
              sku: 'SKU-002',
              name: 'Another Product',
              base_price: 19.99,
              stock: 5,
              images: [],
            },
            quantity: 1,
            price_per_unit: 19.99,
            total_price: 19.99,
          },
        ],
        total_items: 2,
        total_amount: 49.98,
      },
    });

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('cart-status')).toHaveTextContent('Cart Loaded');
    });

    const addButton = screen.getByText('Add Item');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(CartAPI.addToCart).toHaveBeenCalledWith('1', 1);
    });
  });

  it('handles add item failure', async () => {
    const { CartAPI } = require('../../apis/cart');
    (CartAPI.getCart as any).mockResolvedValue({
      success: true,
      data: mockCart,
    });
    (CartAPI.addToCart as any).mockRejectedValue({
      message: 'Product out of stock',
    });

    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('cart-status')).toHaveTextContent('Cart Loaded');
    });

    const addButton = screen.getByText('Add Item');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to add item to cart:', expect.any(Object));
    });

    consoleErrorSpy.mockRestore();
  });

  it('updates item quantity successfully', async () => {
    const { CartAPI } = require('../../apis/cart');
    (CartAPI.getCart as any).mockResolvedValue({
      success: true,
      data: mockCart,
    });
    (CartAPI.updateCartItem as any).mockResolvedValue({
      success: true,
      data: {
        ...mockCart,
        items: [
          {
            ...mockCart.items[0],
            quantity: 2,
            total_price: 59.98,
          },
        ],
        total_items: 2,
        total_amount: 59.98,
      },
    });

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('cart-status')).toHaveTextContent('Cart Loaded');
    });

    const updateButton = screen.getByText('Update Quantity');
    fireEvent.click(updateButton);

    await waitFor(() => {
      expect(CartAPI.updateCartItem).toHaveBeenCalledWith('item-1', 2);
    });
  });

  it('removes item from cart successfully', async () => {
    const { CartAPI } = require('../../apis/cart');
    (CartAPI.getCart as any).mockResolvedValue({
      success: true,
      data: mockCart,
    });
    (CartAPI.removeFromCart as any).mockResolvedValue({
      success: true,
      data: {
        ...mockCart,
        items: [],
        total_items: 0,
        total_amount: 0,
      },
    });

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('cart-status')).toHaveTextContent('Cart Loaded');
    });

    const removeButton = screen.getByText('Remove Item');
    fireEvent.click(removeButton);

    await waitFor(() => {
      expect(CartAPI.removeFromCart).toHaveBeenCalledWith('item-1');
    });
  });

  it('clears cart successfully', async () => {
    const { CartAPI } = require('../../apis/cart');
    (CartAPI.getCart as any).mockResolvedValue({
      success: true,
      data: mockCart,
    });
    (CartAPI.clearCart as any).mockResolvedValue({
      success: true,
      data: {
        ...mockCart,
        items: [],
        total_items: 0,
        total_amount: 0,
      },
    });

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('cart-status')).toHaveTextContent('Cart Loaded');
    });

    const clearButton = screen.getByText('Clear Cart');
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(CartAPI.clearCart).toHaveBeenCalled();
    });
  });

  it('refreshes cart data', async () => {
    const { CartAPI } = require('../../apis/cart');
    (CartAPI.getCart as any).mockResolvedValue({
      success: true,
      data: mockCart,
    });

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('cart-status')).toHaveTextContent('Cart Loaded');
      expect(CartAPI.getCart).toHaveBeenCalledTimes(1);
    });

    const refreshButton = screen.getByText('Refresh Cart');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(CartAPI.getCart).toHaveBeenCalledTimes(2);
    });
  });

  it('handles cart loading errors', async () => {
    const { CartAPI } = require('../../apis/cart');
    (CartAPI.getCart as any).mockRejectedValue({
      message: 'Failed to load cart',
    });

    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to load cart:', expect.any(Object));
      expect(screen.getByTestId('cart-status')).toHaveTextContent('No Cart');
    });

    consoleErrorSpy.mockRestore();
  });

  it('does not load cart when user is not authenticated', () => {
    const unauthenticatedContext = {
      ...mockAuthContext,
      isAuthenticated: false,
      user: null,
    };

    render(
      <AuthContext.Provider value={unauthenticatedContext}>
        <CartProvider>
          <TestComponent />
        </CartProvider>
      </AuthContext.Provider>
    );

    expect(screen.getByTestId('cart-status')).toHaveTextContent('No Cart');
  });

  it('shows loading state during cart operations', async () => {
    const { CartAPI } = require('../../apis/cart');
    (CartAPI.getCart as any).mockResolvedValue({
      success: true,
      data: mockCart,
    });
    (CartAPI.addToCart as any).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('cart-status')).toHaveTextContent('Cart Loaded');
    });

    const addButton = screen.getByText('Add Item');
    fireEvent.click(addButton);

    expect(screen.getByTestId('cart-status')).toHaveTextContent('Loading');
  });
});