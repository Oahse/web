// frontend/src/components/payment/StripePaymentForm.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vitest, beforeEach } from 'vitest';
import StripePaymentForm from './StripePaymentForm';
import { useStripe, useElements, CardElement } from '@stripe/react-stripe-js';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';

// --- Mock external dependencies ---
vitest.mock('@stripe/react-stripe-js', () => ({
  useStripe: vitest.fn(),
  useElements: vitest.fn(),
  CardElement: vitest.fn(() => <div data-testid="mock-card-element">Card Element</div>),
}));

vitest.mock('axios', () => ({
  default: {
    post: vitest.fn(),
  },
}));

vitest.mock('../../contexts/AuthContext', () => ({
  useAuth: vitest.fn(),
}));

vitest.mock('react-router-dom', () => ({
  useNavigate: vitest.fn(),
}));

vitest.mock('react-hot-toast', () => ({
  toast: {
    success: vitest.fn(),
    error: vitest.fn(),
  },
}));

describe('StripePaymentForm Component', () => {
  const mockUseStripe = useStripe as vitest.Mock;
  const mockUseElements = useElements as vitest.Mock;
  const mockCardElement = CardElement as vitest.Mock;
  const mockAxiosPost = axios.post as vitest.Mock;
  const mockUseAuth = useAuth as vitest.Mock;
  const mockUseNavigate = useNavigate as vitest.Mock;

  const mockStripe = {
    confirmCardPayment: vitest.fn(),
  };
  const mockElements = {
    getElement: vitest.fn(() => ({ type: 'mock-card-element' })), // Simulate CardElement instance
  };
  const mockNavigate = vitest.fn();
  const mockLocalStorageGetItem = vitest.spyOn(Storage.prototype, 'getItem');

  const defaultProps = {
    orderId: 'order-123',
    amount: 1000,
    currency: 'usd',
    onPaymentSuccess: vitest.fn(),
    onPaymentError: vitest.fn(),
  };

  beforeEach(() => {
    vitest.clearAllMocks();
    mockUseStripe.mockReturnValue(mockStripe);
    mockUseElements.mockReturnValue(mockElements);
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user: { name: 'Test User', email: 'test@example.com' } });
    mockUseNavigate.mockReturnValue(mockNavigate);
    mockLocalStorageGetItem.mockReturnValue('mock-access-token');

    mockAxiosPost.mockResolvedValue({
      data: { client_secret: 'mock_client_secret' },
    });

    mockStripe.confirmCardPayment.mockResolvedValue({
      paymentIntent: { id: 'pi_123', status: 'succeeded' },
    });
  });

  it('redirects to login if user is not authenticated', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, user: null });
    render(<StripePaymentForm {...defaultProps} />);
    
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Please log in to make a payment.');
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
    expect(mockAxiosPost).not.toHaveBeenCalled(); // Payment intent should not be created
  });

  it('calls createPaymentIntent on mount for authenticated users', async () => {
    render(<StripePaymentForm {...defaultProps} />);
    
    await waitFor(() => {
      expect(mockAxiosPost).toHaveBeenCalledWith(
        '/v1/payments/create-payment-intent',
        { order_id: defaultProps.orderId, amount: defaultProps.amount, currency: defaultProps.currency },
        { headers: { Authorization: 'Bearer mock-access-token' } }
      );
      expect(screen.getByTestId('mock-card-element')).toBeInTheDocument(); // CardElement should be visible
      expect(screen.getByRole('button', { name: 'Pay Now' })).not.toBeDisabled();
    });
  });

  it('shows loading message during payment intent creation', async () => {
    mockAxiosPost.mockImplementationOnce(() => new Promise(() => {})); // Never resolve
    render(<StripePaymentForm {...defaultProps} />);
    
    expect(screen.getByText('Loading payment options...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Pay Now' })).toBeDisabled();
  });

  it('handles payment intent creation failure', async () => {
    mockAxiosPost.mockRejectedValueOnce(new Error('API Error'));
    render(<StripePaymentForm {...defaultProps} />);
    
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to initialize payment. Please try again.');
      expect(defaultProps.onPaymentError).toHaveBeenCalledWith('Failed to initialize payment.');
      expect(screen.queryByTestId('mock-card-element')).not.toBeInTheDocument(); // CardElement shouldn't render
    });
  });

  it('submits payment and handles success', async () => {
    render(<StripePaymentForm {...defaultProps} />);
    await waitFor(() => expect(screen.getByTestId('mock-card-element')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Pay Now' }));

    await waitFor(() => {
      expect(mockStripe.confirmCardPayment).toHaveBeenCalledWith(
        'mock_client_secret',
        {
          payment_method: {
            card: { type: 'mock-card-element' },
            billing_details: { name: 'Test User', email: 'test@example.com' },
          },
        }
      );
      expect(toast.success).toHaveBeenCalledWith('Payment successful!');
      expect(defaultProps.onPaymentSuccess).toHaveBeenCalledWith('pi_123');
    });
  });

  it('handles payment failure (Stripe error)', async () => {
    mockStripe.confirmCardPayment.mockResolvedValueOnce({
      error: { message: 'Card declined' },
    });
    render(<StripePaymentForm {...defaultProps} />);
    await waitFor(() => expect(screen.getByTestId('mock-card-element')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Pay Now' }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Card declined');
      expect(defaultProps.onPaymentError).toHaveBeenCalledWith('Card declined');
    });
  });

  it('handles payment failure (non-succeeded status)', async () => {
    mockStripe.confirmCardPayment.mockResolvedValueOnce({
      paymentIntent: { id: 'pi_123', status: 'requires_action' },
    });
    render(<StripePaymentForm {...defaultProps} />);
    await waitFor(() => expect(screen.getByTestId('mock-card-element')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Pay Now' }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Payment not successful. Status: requires_action');
      expect(defaultProps.onPaymentError).toHaveBeenCalledWith('Payment not successful. Status: requires_action');
    });
  });

  it('shows "Processing..." and disables button during submission', async () => {
    mockStripe.confirmCardPayment.mockImplementationOnce(() => new Promise(() => {})); // Never resolve
    render(<StripePaymentForm {...defaultProps} />);
    await waitFor(() => expect(screen.getByTestId('mock-card-element')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Pay Now' }));

    expect(screen.getByRole('button', { name: 'Processing...' })).toBeDisabled();
  });
});
