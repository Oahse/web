/**
 * Express Checkout Component - One-click checkout for returning customers
 * Reduces friction by auto-selecting saved preferences and enabling quick purchase
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useCart } from '../../contexts/CartContext';
import { OrdersAPI } from '../../apis/orders';
import { AuthAPI } from '../../apis/auth';
import { toast } from 'react-hot-toast';
import { Button } from '../ui/Button';
import { CreditCardIcon, TruckIcon, MapPinIcon } from '@heroicons/react/24/outline';

interface ExpressCheckoutProps {
  onSuccess: (orderId: string) => void;
  onFallback: () => void;
}

export const ExpressCheckout: React.FC<ExpressCheckoutProps> = ({
  onSuccess,
  onFallback
}) => {
  const { user } = useAuth();
  const { cart, clearCart } = useCart();
  const [loading, setLoading] = useState(false);
  const [canUseExpress, setCanUseExpress] = useState(false);
  const [expressData, setExpressData] = useState(null);

  useEffect(() => {
    checkExpressEligibility();
  }, [user, cart]);

  const checkExpressEligibility = async () => {
    if (!user || !cart?.items?.length) {
      setCanUseExpress(false);
      return;
    }

    try {
      // Check if user has saved preferences for express checkout
      const [addresses, paymentMethods, shippingMethods] = await Promise.all([
        AuthAPI.getAddresses(),
        AuthAPI.getPaymentMethods(),
        AuthAPI.getShippingMethods()
      ]);

      // Find default/last used options
      const defaultAddress = addresses.data?.find(addr => addr.is_default) || addresses.data?.[0];
      const defaultPayment = paymentMethods.data?.find(pm => pm.is_default) || paymentMethods.data?.[0];
      const standardShipping = shippingMethods.data?.find(sm => sm.name.toLowerCase().includes('standard'));

      if (defaultAddress && defaultPayment && standardShipping) {
        setExpressData({
          address: defaultAddress,
          payment: defaultPayment,
          shipping: standardShipping,
          total: calculateTotal(cart, standardShipping)
        });
        setCanUseExpress(true);
      } else {
        setCanUseExpress(false);
      }
    } catch (error) {
      console.error('Failed to check express eligibility:', error);
      setCanUseExpress(false);
    }
  };

  const calculateTotal = (cart, shippingMethod) => {
    const subtotal = cart.subtotal || 0;
    const shipping = shippingMethod?.price || 0;
    const tax = cart.tax_amount || 0;
    return subtotal + shipping + tax;
  };

  const handleExpressCheckout = async () => {
    if (!expressData) return;

    setLoading(true);
    try {
      const checkoutRequest = {
        shipping_address_id: expressData.address.id,
        shipping_method_id: expressData.shipping.id,
        payment_method_id: expressData.payment.id,
        notes: 'Express checkout order',
        express_checkout: true
      };

      const response = await OrdersAPI.checkout(checkoutRequest);

      if (response?.success && response?.data) {
        toast.success('Order placed successfully! 🎉');
        await clearCart();
        onSuccess(response.data.id);
      } else {
        throw new Error('Failed to place order');
      }
    } catch (error) {
      console.error('Express checkout failed:', error);
      toast.error('Express checkout failed. Please try regular checkout.');
      onFallback();
    } finally {
      setLoading(false);
    }
  };

  if (!canUseExpress || !expressData) {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
            <span className="text-green-600 font-bold text-sm">⚡</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Express Checkout</h3>
          <span className="bg-green-100 text-green-800 text-xs font-medium px-2 py-1 rounded-full">
            One-Click
          </span>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">
            ${expressData.total.toFixed(2)}
          </div>
          <div className="text-sm text-gray-600">Total</div>
        </div>
      </div>

      {/* Express checkout preview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Shipping Address */}
        <div className="flex items-start space-x-3">
          <MapPinIcon className="w-5 h-5 text-gray-400 mt-1" />
          <div>
            <div className="text-sm font-medium text-gray-900">Ship to</div>
            <div className="text-sm text-gray-600">
              {expressData.address.street}<br />
              {expressData.address.city}, {expressData.address.state} {expressData.address.post_code}
            </div>
          </div>
        </div>

        {/* Shipping Method */}
        <div className="flex items-start space-x-3">
          <TruckIcon className="w-5 h-5 text-gray-400 mt-1" />
          <div>
            <div className="text-sm font-medium text-gray-900">Shipping</div>
            <div className="text-sm text-gray-600">
              {expressData.shipping.name}<br />
              ${expressData.shipping.price.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Payment Method */}
        <div className="flex items-start space-x-3">
          <CreditCardIcon className="w-5 h-5 text-gray-400 mt-1" />
          <div>
            <div className="text-sm font-medium text-gray-900">Payment</div>
            <div className="text-sm text-gray-600">
              {expressData.payment.brand?.toUpperCase()} •••• {expressData.payment.last_four}
            </div>
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center justify-between">
        <button
          onClick={onFallback}
          className="text-sm text-gray-600 hover:text-gray-800 underline"
        >
          Use regular checkout instead
        </button>
        
        <Button
          onClick={handleExpressCheckout}
          loading={loading}
          className="bg-green-600 hover:bg-green-700 text-white px-8 py-3 text-lg font-semibold"
          size="lg"
        >
          {loading ? 'Processing...' : `Complete Order - $${expressData.total.toFixed(2)}`}
        </Button>
      </div>

      <div className="mt-4 text-xs text-gray-500 text-center">
        By clicking "Complete Order", you agree to our terms and authorize payment using your saved payment method.
      </div>
    </div>
  );
};

export default ExpressCheckout;