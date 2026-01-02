/**
 * Checkout Component - One-click checkout for returning customers
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
    <div className="bg-gradient-to-r from-success/10 to-primary/10 border border-success/30 rounded-lg p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-success/20 rounded-full flex items-center justify-center">
            <span className="text-success font-bold text-sm">⚡</span>
          </div>
          <h3 className="text-lg font-semibold text-copy">Checkout</h3>
          <span className="bg-success/20 text-success text-xs font-medium px-2 py-1 rounded-full">
            One-Click
          </span>
          {expressData.stockValidated && (
            <span className="bg-primary/20 text-primary text-xs font-medium px-2 py-1 rounded-full">
              ✓ Stock Verified
            </span>
          )}
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-copy">
            ${expressData.total.toFixed(2)}
          </div>
          <div className="text-sm text-copy-light">Total</div>
        </div>
      </div>

      {/* Checkout preview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Shipping Address */}
        <div className="flex items-start space-x-3">
          <MapPin className="w-5 h-5 text-copy-lighter mt-1" />
          <div>
            <div className="text-sm font-medium text-copy">Ship to</div>
            <div className="text-sm text-copy-light">
              {expressData.address.street}<br />
              {expressData.address.city}, {expressData.address.state} {expressData.address.post_code}
            </div>
          </div>
        </div>

        {/* Shipping Method */}
        <div className="flex items-start space-x-3">
          <Truck className="w-5 h-5 text-copy-lighter mt-1" />
          <div>
            <div className="text-sm font-medium text-copy">Shipping</div>
            <div className="text-sm text-copy-light">
              {expressData.shipping.name}<br />
              ${expressData.shipping.price.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Payment Method */}
        <div className="flex items-start space-x-3">
          <CreditCard className="w-5 h-5 text-copy-lighter mt-1" />
          <div>
            <div className="text-sm font-medium text-copy">Payment</div>
            <div className="text-sm text-copy-light">
              {expressData.payment.brand?.toUpperCase()} •••• {expressData.payment.last_four}
            </div>
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center justify-end">
        <Button
          onClick={handleExpressCheckout}
          isLoading={loading}
          className="bg-success hover:bg-success-dark text-copy-inverse px-8 py-3 text-lg font-semibold"
          size="lg"
        >
          {loading ? 'Processing...' : `Complete Order - $${expressData.total.toFixed(2)}`}
        </Button>
      </div>

      <div className="mt-4 text-xs text-copy-muted text-center">
        By clicking "Complete Order", you agree to our terms and authorize payment using your saved payment method.
      </div>
    </div>
  );
};

export default ExpressCheckout;