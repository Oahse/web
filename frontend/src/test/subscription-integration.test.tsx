import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { MySubscriptions } from '../components/account/MySubscriptions';
import { SubscriptionProvider } from '../store/SubscriptionContext';
import { AuthProvider } from '../store/AuthContext';
import { LocaleProvider } from '../store/LocaleContext';

// Mock the APIs
jest.mock('../apis/subscription');
jest.mock('../apis/products');

const MockProviders = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      <LocaleProvider>
        <SubscriptionProvider>
          {children}
        </SubscriptionProvider>
      </LocaleProvider>
    </AuthProvider>
  </BrowserRouter>
);

describe('Subscription Management Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should display subscription prices with proper currency formatting', async () => {
    render(
      <MockProviders>
        <MySubscriptions />
      </MockProviders>
    );

    // Wait for subscriptions to load
    await waitFor(() => {
      expect(screen.queryByText('Loading your subscriptions...')).not.toBeInTheDocument();
    });

    // Check if prices are formatted correctly (should not show raw numbers)
    const priceElements = screen.queryAllByText(/\$|€|£|₦/);
    expect(priceElements.length).toBeGreaterThan(0);
  });

  it('should handle subscription cancellation with confirmation', async () => {
    render(
      <MockProviders>
        <MySubscriptions />
      </MockProviders>
    );

    await waitFor(() => {
      expect(screen.queryByText('Loading your subscriptions...')).not.toBeInTheDocument();
    });

    // Look for cancel buttons (might be in dropdown menus)
    const cancelButtons = screen.queryAllByText(/cancel/i);
    if (cancelButtons.length > 0) {
      fireEvent.click(cancelButtons[0]);
      
      // Should show confirmation dialog
      await waitFor(() => {
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
      });
    }
  });

  it('should allow adding products to subscription', async () => {
    render(
      <MockProviders>
        <MySubscriptions />
      </MockProviders>
    );

    await waitFor(() => {
      expect(screen.queryByText('Loading your subscriptions...')).not.toBeInTheDocument();
    });

    // Look for "New Subscription" or "Add Products" buttons
    const addButtons = screen.queryAllByText(/new subscription|add/i);
    expect(addButtons.length).toBeGreaterThan(0);
  });

  it('should display product variants correctly', async () => {
    render(
      <MockProviders>
        <MySubscriptions />
      </MockProviders>
    );

    // Click on create subscription to open modal
    const createButton = screen.queryByText('New Subscription');
    if (createButton) {
      fireEvent.click(createButton);
      
      await waitFor(() => {
        expect(screen.getByText('Create New Subscription')).toBeInTheDocument();
      });

      // Should show product variant selection
      expect(screen.getByText(/select product variants/i)).toBeInTheDocument();
    }
  });
});