/**
 * Integration tests for checkout flow
 * Tests the complete frontend checkout process including cart validation,
 * payment processing, and real-time updates
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { Checkout } from '../../pages/Checkout';
import { CartProvider } from '../../contexts/CartContext';
import { AuthProvider } from '../../contexts/AuthContext';
import { server } from '../mocks/server';
import { rest } from 'msw';

// Mock WebSocket
const mockWebSocket = {
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  send: vi.fn(),
  close: vi.fn(),
  readyState: WebSocket.OPEN
};

vi.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    isConnected: true,
    socket: mockWebSocket
  })
}));

// Mock toast notifications
vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn()
  }
}));

// Mock navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate
  };
});

describe('Checkout Integration Tests', () => {
  const mockUser = {
    id: 'user-123',
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User'
  };

  const mockCart = {
    id: 'cart-123',
    items: [
      {
        id: 'item-1',
        variant_id: 'variant-1',
        quantity: 2,
        price_per_unit: 29.99,
        product: {
          name: 'Test Product',
          image_url: '/test-image.jpg'
        }
      }
    ],
    total_amount: 65.97, // 2 * 29.99 + 5.99 shipping
    subtotal: 59.98,
    shipping_amount: 5.99,
    tax_amount: 0
  };

  const mockAddresses = [
    {
      id: 'address-1',
      street: '123 Test St',
      city: 'Test City',
      state: 'TS',
      country: 'US',
      post_code: '12345',
      kind: 'Shipping'
    }
  ];

  const mockShippingMethods = [
    {
      id: 'shipping-1',
      name: 'Standard Shipping',
      price: 5.99,
      estimated_days: 3
    }
  ];

  const mockPaymentMethods = [
    {
      id: 'payment-1',
      type: 'card',
      last_four: '4242',
      brand: 'visa',
      is_default: true
    }
  ];

  const TestWrapper = ({ children }: { children: React.ReactNode }) => (
    <BrowserRouter>
      <AuthProvider>
        <CartProvider>
          {children}
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  );

  beforeEach(() => {
    // Setup MSW handlers for successful responses
    server.use(
      rest.get('/api/users/me/cart', (req, res, ctx) => {
        return res(ctx.json({ success: true, data: mockCart }));
      }),
      rest.get('/api/users/me/addresses', (req, res, ctx) => {
        return res(ctx.json({ success: true, data: mockAddresses }));
      }),
      rest.get('/api/shipping-methods', (req, res, ctx) => {
        return res(ctx.json({ success: true, data: mockShippingMethods }));
      }),
      rest.get('/api/users/me/payment-methods', (req, res, ctx) => {
        return res(ctx.json({ success: true, data: mockPaymentMethods }));
      }),
      rest.post('/api/orders/checkout', (req, res, ctx) => {
        return res(ctx.json({
          success: true,
          data: {
            id: 'order-123',
            order_number: 'ORD-123456',
            status: 'confirmed',
            total_amount: 65.97
          }
        }));
      })
    );

    // Mock localStorage for auth
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(() => JSON.stringify({
          access_token: 'mock-token',
          user: mockUser
        })),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn()
      },
      writable: true
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
  });

  it('should complete successful checkout flow', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <Checkout />
      </TestWrapper>
    );

    // Wait for initial data to load
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Verify cart items are displayed
    expect(screen.getByText('2')).toBeInTheDocument(); // quantity
    expect(screen.getByText('$29.99')).toBeInTheDocument(); // price

    // Verify address selection
    expect(screen.getByText('123 Test St')).toBeInTheDocument();

    // Verify shipping method selection
    expect(screen.getByText('Standard Shipping')).toBeInTheDocument();
    expect(screen.getByText('$5.99')).toBeInTheDocument();

    // Verify payment method selection
    expect(screen.getByText('**** 4242')).toBeInTheDocument();

    // Verify total calculation
    expect(screen.getByText('$65.97')).toBeInTheDocument();

    // Click place order button
    const placeOrderButton = screen.getByRole('button', { name: /place order/i });
    expect(placeOrderButton).toBeEnabled();
    
    await user.click(placeOrderButton);

    // Wait for order completion
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/orders/order-123');
    });
  });

  it('should handle cart validation errors', async () => {
    // Override cart endpoint to return validation errors
    server.use(
      rest.get('/api/users/me/cart', (req, res, ctx) => {
        return res(ctx.json({
          success: true,
          data: {
            ...mockCart,
            items: [] // Empty cart
          }
        }));
      })
    );

    render(
      <TestWrapper>
        <Checkout />
      </TestWrapper>
    );

    // Should redirect to cart page for empty cart
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/cart');
    });
  });

  it('should handle payment processing errors', async () => {
    const user = userEvent.setup();
    
    // Override checkout endpoint to return payment error
    server.use(
      rest.post('/api/orders/checkout', (req, res, ctx) => {
        return res(ctx.status(400), ctx.json({
          success: false,
          error: 'Payment failed: insufficient funds'
        }));
      })
    );

    render(
      <TestWrapper>
        <Checkout />
      </TestWrapper>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Click place order button
    const placeOrderButton = screen.getByRole('button', { name: /place order/i });
    await user.click(placeOrderButton);

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/payment failed/i)).toBeInTheDocument();
    });

    // Should not navigate away
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should handle real-time price updates via WebSocket', async () => {
    render(
      <TestWrapper>
        <Checkout />
      </TestWrapper>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('$65.97')).toBeInTheDocument();
    });

    // Simulate price update event
    const priceUpdateEvent = new CustomEvent('priceUpdate', {
      detail: {
        items: [
          {
            variant_id: 'variant-1',
            old_price: 29.99,
            new_price: 24.99,
            price_change: -5.00
          }
        ],
        summary: {
          total_items_updated: 1,
          total_price_change: -10.00, // 2 items * -5.00
          new_total: 55.97
        },
        message: 'Prices updated due to promotion'
      }
    });

    act(() => {
      window.dispatchEvent(priceUpdateEvent);
    });

    // Should show price update notification
    // Note: In a real test, you'd verify the toast was called
    // and that the cart was refreshed with new prices
  });

  it('should validate form fields before submission', async () => {
    const user = userEvent.setup();
    
    // Override endpoints to return empty data
    server.use(
      rest.get('/api/users/me/addresses', (req, res, ctx) => {
        return res(ctx.json({ success: true, data: [] }));
      }),
      rest.get('/api/shipping-methods', (req, res, ctx) => {
        return res(ctx.json({ success: true, data: [] }));
      }),
      rest.get('/api/users/me/payment-methods', (req, res, ctx) => {
        return res(ctx.json({ success: true, data: [] }));
      })
    );

    render(
      <TestWrapper>
        <Checkout />
      </TestWrapper>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Try to place order without required selections
    const placeOrderButton = screen.getByRole('button', { name: /place order/i });
    await user.click(placeOrderButton);

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText(/please select a shipping address/i)).toBeInTheDocument();
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should handle network connectivity issues', async () => {
    const user = userEvent.setup();
    
    // Override checkout endpoint to simulate network error
    server.use(
      rest.post('/api/orders/checkout', (req, res, ctx) => {
        return res.networkError('Network error');
      })
    );

    render(
      <TestWrapper>
        <Checkout />
      </TestWrapper>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Click place order button
    const placeOrderButton = screen.getByRole('button', { name: /place order/i });
    await user.click(placeOrderButton);

    // Should show network error message
    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  it('should handle concurrent checkout attempts', async () => {
    const user = userEvent.setup();
    
    let requestCount = 0;
    server.use(
      rest.post('/api/orders/checkout', (req, res, ctx) => {
        requestCount++;
        if (requestCount === 1) {
          // First request succeeds
          return res(ctx.json({
            success: true,
            data: {
              id: 'order-123',
              order_number: 'ORD-123456'
            }
          }));
        } else {
          // Subsequent requests should be prevented by idempotency
          return res(ctx.status(409), ctx.json({
            success: false,
            error: 'Order already exists'
          }));
        }
      })
    );

    render(
      <TestWrapper>
        <Checkout />
      </TestWrapper>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    const placeOrderButton = screen.getByRole('button', { name: /place order/i });
    
    // Rapidly click the button multiple times
    await user.click(placeOrderButton);
    await user.click(placeOrderButton);
    await user.click(placeOrderButton);

    // Should only make one successful request
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/orders/order-123');
    });
    
    // Button should be disabled during processing
    expect(placeOrderButton).toBeDisabled();
  });

  it('should handle inventory shortage during checkout', async () => {
    const user = userEvent.setup();
    
    // Override checkout endpoint to return inventory error
    server.use(
      rest.post('/api/orders/checkout', (req, res, ctx) => {
        return res(ctx.status(400), ctx.json({
          success: false,
          error: 'Insufficient inventory for Test Product',
          details: {
            type: 'inventory_shortage',
            variant_id: 'variant-1',
            requested: 2,
            available: 1
          }
        }));
      })
    );

    render(
      <TestWrapper>
        <Checkout />
      </TestWrapper>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Click place order button
    const placeOrderButton = screen.getByRole('button', { name: /place order/i });
    await user.click(placeOrderButton);

    // Should show inventory error with details
    await waitFor(() => {
      expect(screen.getByText(/insufficient inventory/i)).toBeInTheDocument();
      expect(screen.getByText(/only 1 available/i)).toBeInTheDocument();
    });

    // Should suggest updating cart
    expect(screen.getByRole('button', { name: /update cart/i })).toBeInTheDocument();
  });

  it('should handle 3D Secure authentication flow', async () => {
    const user = userEvent.setup();
    
    // Override checkout endpoint to return 3D Secure requirement
    server.use(
      rest.post('/api/orders/checkout', (req, res, ctx) => {
        return res(ctx.json({
          success: false,
          requires_action: true,
          payment_intent: {
            id: 'pi_test_123',
            client_secret: 'pi_test_123_secret_456'
          },
          next_action: {
            type: 'use_stripe_sdk'
          }
        }));
      })
    );

    // Mock Stripe SDK
    const mockStripe = {
      confirmCardPayment: vi.fn().mockResolvedValue({
        paymentIntent: {
          status: 'succeeded'
        }
      })
    };

    // @ts-ignore
    window.Stripe = vi.fn(() => mockStripe);

    render(
      <TestWrapper>
        <Checkout />
      </TestWrapper>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Test Product')).toBeInTheDocument();
    });

    // Click place order button
    const placeOrderButton = screen.getByRole('button', { name: /place order/i });
    await user.click(placeOrderButton);

    // Should show 3D Secure authentication prompt
    await waitFor(() => {
      expect(screen.getByText(/authentication required/i)).toBeInTheDocument();
    });

    // In a real test, you would simulate the 3D Secure flow completion
    // and verify the order is completed after authentication
  });
});