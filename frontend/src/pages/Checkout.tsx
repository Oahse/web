/**
 * Checkout Page - Simplified one-click checkout
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { AuthAPI } from '../apis/auth';
import { CartAPI } from '../apis/cart';
import { toast } from 'react-hot-toast';
import SmartCheckoutForm from '../components/checkout/SmartCheckoutForm';

export const Checkout = () => {
  const navigate = useNavigate();
  const { cart, loading: cartLoading, clearCart, refreshCart } = useCart();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  // UI state
  const [loading, setLoading] = useState(false);
  const [stockValidation, setStockValidation] = useState({ valid: true, issues: [] });

  // Handle authentication check
  useEffect(() => {
    // If not authenticated, redirect to login
    if (!authLoading && !isAuthenticated) {
      toast.error('Please login to checkout');
      navigate('/login');
      return;
    }
      return;
    }
  }, [authLoading, isAuthenticated, navigate]);

  // Redirect if cart is empty (only after auth is confirmed)
  useEffect(() => {
    if (!authLoading && isAuthenticated && !cartLoading && (!cart || !cart.items || cart.items.length === 0)) {
      toast.error('Your cart is empty');
      navigate('/cart');
    }
  }, [cart, cartLoading, navigate, authLoading, isAuthenticated]);

  // Real-time stock validation using bulk check
  useEffect(() => {
    const validateStock = async () => {
      if (!cart?.items || cart.items.length === 0) {
        setStockValidation({ valid: true, issues: [] });
        return;
      }

      try {
        // Use bulk stock check for better performance
        const stockCheckRes = await CartAPI.checkBulkStock(cart.items.map(item => ({
          variant_id: item.variant_id || item.variant?.id,
          quantity: item.quantity
        })));

        const stockCheck = stockCheckRes.data;
        const stockIssues = stockCheck?.items?.filter(item => !item.available) || [];

        setStockValidation({
          valid: stockCheck?.all_available || false,
          issues: stockIssues.map(issue => ({
            variant_id: issue.variant_id,
            message: issue.message || 'Out of stock',
            current_stock: issue.current_stock || 0,
            requested_quantity: issue.quantity_requested || 0
          }))
        });

        // Show toast for stock issues
        if (stockIssues.length > 0) {
          const itemCount = stockIssues.length;
          toast.error(`${itemCount} item${itemCount > 1 ? 's' : ''} in your cart ${itemCount > 1 ? 'are' : 'is'} no longer available`);
        }
      } catch (error) {
        console.error('Stock validation failed:', error);
        setStockValidation({ valid: false, issues: [] });
      }
    };

    // Only validate stock if authenticated and cart is loaded
    if (!authLoading && isAuthenticated && cart?.items) {
      validateStock();
      const interval = setInterval(validateStock, 300000); // 5 minutes
      return () => clearInterval(interval);
    }
  }, [cart?.items, authLoading, isAuthenticated]);

  // Checkout handler
  const handleSmartCheckoutSuccess = (orderId: string) => {
    navigate(`/account/orders/${orderId}`);
  };

  // Show loading state while checking authentication or loading cart
  if (authLoading || (isAuthenticated && cartLoading)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-copy-light">
            {authLoading ? 'Checking authentication...' : 'Loading checkout...'}
          </p>
        </div>
      </div>
    );
  }

  // Don't render anything if not authenticated (will redirect)
  if (!isAuthenticated && !authLoading) {
    return null;
  }

  // Don't render if cart is empty (redirect will happen)
  if (!cart || !cart.items || cart.items.length === 0) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-copy">Checkout</h1>
          <p className="mt-2 text-copy-light">
            Complete your purchase quickly and securely
          </p>
        </div>

        {/* Stock Validation Warning */}
        {!stockValidation.valid && stockValidation.issues.length > 0 && (
          <div className="mb-6 bg-error/10 border border-error/30 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-error" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-error-dark">
                  Stock Issues Detected
                </h3>
                <div className="mt-2 text-sm text-error">
                  <ul className="list-disc pl-5 space-y-1">
                    {stockValidation.issues.map((issue, index) => (
                      <li key={index}>
                        {issue.message}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => navigate('/cart')}
                    className="bg-error text-copy-inverse px-4 py-2 rounded-md text-sm hover:bg-error-dark"
                  >
                    Review Cart
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Checkout */}
        {stockValidation.valid && (
          <SmartCheckoutForm
            onSuccess={handleSmartCheckoutSuccess}
          />
        )}

        {/* Price update indicator */}
        {priceUpdateReceived && (
          <div className="fixed bottom-4 right-4 bg-primary text-copy-inverse px-4 py-2 rounded-lg shadow-lg">
            <div className="flex items-center space-x-2">
              <div className="animate-pulse w-2 h-2 bg-copy-inverse rounded-full"></div>
              <span className="text-sm">Prices updated</span>
            </div>
          </div>
        )}

        {/* Connection status indicator */}
        {!isConnected && (
          <div className="fixed bottom-4 left-4 bg-warning text-copy-inverse px-4 py-2 rounded-lg shadow-lg">
            <div className="flex items-center space-x-2">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="text-sm">Offline Mode</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Checkout;