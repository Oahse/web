/**
 * CORRECTED: Checkout Page - Simplified one-click checkout with proper validation
 * Fixes: Issue 1.4 - Orders checkout response handling, Issue 4.2 - Validation
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../store/CartContext';
import { useAuth } from '../store/AuthContext';
import { AuthAPI } from '../api/auth';
import { CartAPI } from '../api/cart';
import { OrdersAPI } from '../api/orders';
import { toast } from 'react-hot-toast';
import SmartCheckoutForm from '../components/checkout/SmartCheckoutForm';

export const Checkout = () => {
  const navigate = useNavigate();
  const { cart, loading: cartLoading, clearCart, refreshCart } = useCart();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  // UI state
  const [loading, setLoading] = useState(false);
  const [stockValidation, setStockValidation] = useState({ valid: true, issues: [] });
  const [selectedAddress, setSelectedAddress] = useState<any>(null);
  const [selectedShipping, setSelectedShipping] = useState<any>(null);
  const [selectedPayment, setSelectedPayment] = useState<any>(null);
  const [orderNotes, setOrderNotes] = useState('');

  // Handle authentication check
  useEffect(() => {
    // If not authenticated, redirect to login
    if (!authLoading && !isAuthenticated) {
      toast.error('Please login to checkout');
      navigate('/login', {
        state: { from: { pathname: '/checkout' } }
      });
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
  // FIXED: Properly handle response structure
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

        // FIXED: Handle response structure properly
        // Response might be wrapped: { success: true, data: { ... } }
        const stockCheckData = stockCheckRes.data || stockCheckRes;
        const stockCheck = stockCheckData?.data || stockCheckData;
        
        const stockIssues = stockCheck?.items?.filter((item: any) => !item.available) || [];

        setStockValidation({
          valid: stockCheck?.all_available || (stockIssues.length === 0),
          issues: stockIssues.map((issue: any) => ({
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

  /**
   * FIXED: Comprehensive checkout validation
   * Ensures all required fields are filled and valid before submission
   */
  const validateCheckout = (): boolean => {
    // Validate stock first
    if (!stockValidation.valid && stockValidation.issues.length > 0) {
      toast.error('Please resolve stock issues. Check items in your cart.');
      return false;
    }

    // Validate shipping address
    if (!selectedAddress) {
      toast.error('Please select a shipping address');
      return false;
    }

    // Validate shipping method
    if (!selectedShipping) {
      toast.error('Please select a shipping method');
      return false;
    }

    // Validate payment method
    if (!selectedPayment) {
      toast.error('Please select a payment method');
      return false;
    }

    // Validate cart is not empty
    if (!cart?.items || cart.items.length === 0) {
      toast.error('Your cart is empty');
      return false;
    }

    return true;
  };

  /**
   * FIXED: Handle checkout submission with proper error handling
   * Issue 1.4: Handle response structure properly
   */
  const handleCheckoutSubmit = async () => {
    // Validate all requirements
    if (!validateCheckout()) {
      return;
    }

    setLoading(true);
    try {
      // FIXED: Place order with corrected request structure
      const result = await OrdersAPI.placeOrder({
        shipping_address_id: selectedAddress.id,
        shipping_method_id: selectedShipping.id,
        payment_method_id: selectedPayment.id,
        notes: orderNotes || undefined
      });

      // FIXED: Handle response structure properly
      // Backend returns: { success: true, data: { id, order_number, ... }, message: "..." }
      const orderId = result.data?.id || result.data?.order_id;
      
      if (!orderId) {
        throw new Error('Order ID not found in response');
      }

      // Clear cart after successful order
      await clearCart();
      
      toast.success('Order placed successfully!');
      
      // Redirect to order confirmation
      navigate(`/account/orders/${orderId}`, {
        replace: true,
        state: { fromCheckout: true }
      });
      
    } catch (error: any) {
      console.error('Checkout error:', error);
      const errorMessage = error?.response?.data?.message || 
                          error?.message || 
                          'Failed to place order. Please try again.';
      toast.error(errorMessage);
      setLoading(false);
    }
  };

  /**
   * FIXED: SmartCheckoutForm success handler
   * Issue 1.4: Properly handle order creation response
   */
  const handleSmartCheckoutSuccess = (orderId: string) => {
    navigate(`/account/orders/${orderId}`, {
      replace: true,
      state: { fromCheckout: true }
    });
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
                    {stockValidation.issues.map((issue: any, index: number) => (
                      <li key={index}>
                        {issue.message} (Current stock: {issue.current_stock}, Requested: {issue.requested_quantity})
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => navigate('/cart')}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-error bg-white hover:bg-gray-50"
                  >
                    Return to Cart
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Checkout Form */}
        <SmartCheckoutForm 
          onSuccess={handleSmartCheckoutSuccess}
          onValidationChange={(isValid) => {
            // Handle validation state if needed
          }}
        />
      </div>
    </div>
  );
};

export default Checkout;
