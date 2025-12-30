/**
 * Express Checkout Component - One-click checkout for returning customers
 * Optimized for performance and responsiveness
 */
import React from 'react';
import { Button } from '../ui/Button';
import { CreditCard, Truck, MapPin } from 'lucide-react';
import { useExpressCheckout } from '../../hooks/useExpressCheckout';

interface ExpressCheckoutProps {
  onSuccess: (orderId: string) => void;
  onFallback: () => void;
}

export const ExpressCheckout: React.FC<ExpressCheckoutProps> = ({
  onSuccess,
  onFallback
}) => {
  const {
    canUseExpress,
    expressData,
    loading,
    handleExpressCheckout
  } = useExpressCheckout(onSuccess, onFallback);

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
          {expressData.stockValidated && (
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded-full">
              ✓ Stock Verified
            </span>
          )}
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
          <MapPin className="w-5 h-5 text-gray-400 mt-1" />
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
          <Truck className="w-5 h-5 text-gray-400 mt-1" />
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
          <CreditCard className="w-5 h-5 text-gray-400 mt-1" />
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
          isLoading={loading}
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