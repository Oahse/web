/**
 * Express Checkout Page - Simplified one-click checkout
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { AuthAPI } from '../apis/auth';
import { CartAPI } from '../apis/cart';
import { toast } from 'react-hot-toast';
import ExpressCheckout from '../components/checkout/ExpressCheckout';
import SmartCheckoutForm from '../components/checkout/SmartCheckoutForm';

export const Checkout = () => {
  const navigate = useNavigate();
  const { cart, loading: cartLoading, clearCart, refreshCart } = useCart();
  const { isAuthenticated } = useAuth();
  const { isConnected } = useWebSocket();

  // UI state
  const [loading, setLoading] = useState(false);
  const [priceUpdateReceived, setPriceUpdateReceived] = useState(false);
  const [stockValidation, setStockValidation] = useState({ valid: true, issues: [] });

  // Listen for price updates via WebSocket
  useEffect(() => {
    const handlePriceUpdate = (event) => {
      const { items, summary, message } = event.detail;
      
      // Show detailed toast with price changes
      if (summary.total_price_change !== 0) {
        const changeText = summary.total_price_change > 0 
          ? `increased by ${summary.total_price_change.toFixed(2)}`
          : `reduced by ${Math.abs(summary.total_price_change).toFixed(2)}`;
          
        toast.success(
          `Cart prices ${changeText}. ${summary.total_items_updated} item(s) updated.`,
          {
            duration: 6000,
            icon: summary.total_price_change > 0 ? '⚠️' : '🎉'
          }
        );
      }
      
      // Refresh cart to show updated prices
      if (refreshCart) {
        refreshCart();
      }
      
      setPriceUpdateReceived(true);
      
      // Reset the flag after a short delay
      setTimeout(() => setPriceUpdateReceived(false), 3000);
    };

    window.addEventListener('priceUpdate', handlePriceUpdate);
    
    return () => {
      window.removeEventListener('priceUpdate', handlePriceUpdate);
    };
  }, [refreshCart]);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      toast.error('Please login to checkout');
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  // Redirect if cart is empty
  useEffect(() => {
    if (!cartLoading && (!cart || !cart.items || cart.items.length === 0)) {
      toast.error('Your cart is empty');
      navigate('/cart');
    }
  }, [cart, cartLoading, navigate]);

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

    // Validate stock when cart changes or every 30 seconds
    validateStock();
    const interval = setInterval(validateStock, 30000);

    return () => clearInterval(interval);
  }, [cart?.items]);

  // Fetch checkout data for express mode
  useEffect(() => {
    const fetchCheckoutData = async () => {
      if (!isAuthenticated) return;

      try {
        setLoading(true);
        // Pre-load data needed for express checkout
        await Promise.all([
          AuthAPI.getAddresses(),
          AuthAPI.getPaymentMethods(),
          CartAPI.getShippingOptions({})
        ]);
      } catch (error) {
        const errorMessage = error?.response?.data?.message || error?.message || 'Failed to load checkout information';
        toast.error(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchCheckoutData();
  }, [isAuthenticated]);

  // Express checkout handlers
  const handleExpressSuccess = (orderId: string) => {
    navigate(`/account/orders/${orderId}`);
  };

  const handleExpressFallback = () => {
    toast.error('Express checkout failed. Please try again or contact support.');
  };

  const handleSmartCheckoutSuccess = (orderId: string) => {
    navigate(`/account/orders/${orderId}`);
  };

  if (loading || cartLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading checkout...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Express Checkout</h1>
          <p className="mt-2 text-gray-600">
            Complete your purchase quickly and securely with one-click checkout
          </p>
        </div>

        {/* Stock Validation Warning */}
        {!stockValidation.valid && stockValidation.issues.length > 0 && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Stock Issues Detected
                </h3>
                <div className="mt-2 text-sm text-red-700">
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
                    className="bg-red-600 text-white px-4 py-2 rounded-md text-sm hover:bg-red-700"
                  >
                    Review Cart
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Express Checkout */}
        {stockValidation.valid && (
          <>
            <ExpressCheckout
              onSuccess={handleExpressSuccess}
              onFallback={handleExpressFallback}
            />
            
            {/* Smart Checkout Form as fallback */}
            <SmartCheckoutForm
              onSuccess={handleSmartCheckoutSuccess}
            />
          </>
        )}

        {/* Price update indicator */}
        {priceUpdateReceived && (
          <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg">
            <div className="flex items-center space-x-2">
              <div className="animate-pulse w-2 h-2 bg-white rounded-full"></div>
              <span className="text-sm">Prices updated</span>
            </div>
          </div>
        )}

        {/* Connection status indicator */}
        {!isConnected && (
          <div className="fixed bottom-4 left-4 bg-yellow-600 text-white px-4 py-2 rounded-lg shadow-lg">
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