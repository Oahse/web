/**
 * New Frictionless Checkout Page
 * Combines express checkout and smart checkout form for optimal UX
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { toast } from 'react-hot-toast';
import ExpressCheckout from '../components/checkout/ExpressCheckout';
import SmartCheckoutForm from '../components/checkout/SmartCheckoutForm';

export const CheckoutNew = () => {
  const navigate = useNavigate();
  const { cart, loading: cartLoading, clearCart, refreshCart } = useCart();
  const { isAuthenticated } = useAuth();
  const { isConnected } = useWebSocket();

  // UI state
  const [showExpressCheckout, setShowExpressCheckout] = useState(true);
  const [priceUpdateReceived, setPriceUpdateReceived] = useState(false);

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

  const handleExpressSuccess = (orderId: string) => {
    navigate(`/orders/${orderId}`);
  };

  const handleExpressFallback = () => {
    setShowExpressCheckout(false);
  };

  const handleSmartCheckoutSuccess = (orderId: string) => {
    navigate(`/orders/${orderId}`);
  };

  if (cartLoading) {
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
          <h1 className="text-3xl font-bold text-gray-900">Checkout</h1>
          <p className="mt-2 text-gray-600">
            Complete your purchase quickly and securely
          </p>
        </div>

        {/* Express Checkout Option */}
        {showExpressCheckout && (
          <ExpressCheckout
            onSuccess={handleExpressSuccess}
            onFallback={handleExpressFallback}
          />
        )}

        {/* Smart Checkout Form */}
        {!showExpressCheckout && (
          <SmartCheckoutForm
            onSuccess={handleSmartCheckoutSuccess}
          />
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
      </div>
    </div>
  );
};

export default CheckoutNew;