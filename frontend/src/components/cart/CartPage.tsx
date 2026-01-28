import React, { useState } from 'react';
import { useCart } from '../../hooks/useCart';
import { useAuth } from '../../hooks/useAuth';
import { useLocale } from '../../store/LocaleContext';
import { ConfirmationModal } from '../ui/ConfirmationModal';
import { toast } from 'react-hot-toast';
import { Trash2, Plus, Minus, ShoppingBag } from 'lucide-react';

const CartItem = ({ item, onUpdate, onRemove }) => {
  const [qty, setQty] = useState(item.quantity);
  
  const handleQtyChange = (newQty) => {
    if (newQty < 1) return;
    setQty(newQty);
    onUpdate(item.id, newQty);
  };

  const variant = item.variant;
  const name = variant?.product_name || variant?.name || 'Product';
  const image = variant?.primary_image?.url || '/placeholder.jpg';
  const price = variant?.current_price || item.price_per_unit;

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border">
      <div className="flex gap-4">
        {/* Image */}
        <img
          src={image}
          alt={name}
          className="w-16 h-16 sm:w-20 sm:h-20 object-cover rounded"
          onError={(e) => e.target.src = '/placeholder.jpg'}
        />

        {/* Details */}
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 truncate">{name}</h3>
          <p className="text-lg font-semibold text-gray-900 mt-1">
            ${price?.toFixed(2)}
          </p>
          
          {/* Mobile quantity controls */}
          <div className="flex items-center gap-2 mt-2 sm:hidden">
            <button
              onClick={() => handleQtyChange(qty - 1)}
              disabled={qty <= 1}
              className="w-8 h-8 rounded-full border flex items-center justify-center disabled:opacity-50"
            >
              <Minus className="w-4 h-4" />
            </button>
            <span className="w-8 text-center">{qty}</span>
            <button
              onClick={() => handleQtyChange(qty + 1)}
              className="w-8 h-8 rounded-full border flex items-center justify-center"
            >
              <Plus className="w-4 h-4" />
            </button>
            <button
              onClick={() => onRemove(item.id)}
              className="ml-2 text-red-600"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Desktop controls */}
        <div className="hidden sm:flex flex-col items-end gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleQtyChange(qty - 1)}
              disabled={qty <= 1}
              className="w-8 h-8 rounded-full border flex items-center justify-center disabled:opacity-50"
            >
              <Minus className="w-4 h-4" />
            </button>
            <span className="w-12 text-center">{qty}</span>
            <button
              onClick={() => handleQtyChange(qty + 1)}
              className="w-8 h-8 rounded-full border flex items-center justify-center"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          <button
            onClick={() => onRemove(item.id)}
            className="text-red-600"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Item total */}
      <div className="mt-3 pt-3 border-t flex justify-between">
        <span className="text-sm text-gray-600">Total:</span>
        <span className="font-semibold">${(price * qty).toFixed(2)}</span>
      </div>
    </div>
  );
};

const CartPage = () => {
  const { formatCurrency } = useLocale();
  const { user } = useAuth();
  const { cart, loading, items, totalItems, addItem, removeItem, updateQuantity, clearCart } = useCart();
  const [showClearModal, setShowClearModal] = useState(false);

  const handleUpdate = async (itemId, quantity) => {
    try {
      await updateQuantity(itemId, quantity);
    } catch (error) {
      toast.error(error.message || 'Failed to update');
    }
  };

  const handleRemove = async (itemId) => {
    try {
      await removeItem(itemId);
    } catch (error) {
      toast.error(error.message || 'Failed to remove');
    }
  };

  const handleClear = async () => {
    setShowClearModal(true);
  };

  const confirmClearCart = async () => {
    try {
      await clearCart();
      setShowClearModal(false);
    } catch (error) {
      toast.error(error.message || 'Failed to clear');
    }
  };

  // Early returns after all hooks
  if (!user) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <ShoppingBag className="w-16 h-16 mx-auto text-gray-400 mb-4" />
        <h2 className="text-xl sm:text-2xl font-semibold mb-2">Please log in</h2>
        <p className="text-gray-600 mb-6">You need to log in to view your cart</p>
        <button
          onClick={() => window.location.href = '/login'}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
        >
          Log In
        </button>
      </div>
    );
  }

  if (loading && !cart) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          {[1, 2, 3].map(i => (
            <div key={i} className="h-32 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <ShoppingBag className="w-16 h-16 mx-auto text-gray-400 mb-4" />
        <h2 className="text-xl sm:text-2xl font-semibold mb-2">Cart is empty</h2>
        <p className="text-gray-600 mb-6">Add some items to get started</p>
        <button
          onClick={() => window.location.href = '/products'}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
        >
          Shop Now
        </button>
      </div>
    );
  }

  const subtotal = cart?.subtotal || 0;
  const tax = cart?.tax_amount || 0;
  const shipping = cart?.shipping_cost || cart?.shipping_amount || 0;
  const total = cart?.total_amount || 0;

  return (
    <div className="max-w-6xl mx-auto px-4 py-4 sm:py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <h1 className="text-xl sm:text-2xl font-bold mb-2 sm:mb-0">
          Cart ({totalItems} items)
        </h1>
        <button
          onClick={handleClear}
          className="text-red-600 hover:text-red-700 text-sm sm:text-base"
        >
          Clear Cart
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
        {/* Items */}
        <div className="lg:col-span-2 space-y-4">
          {items.map(item => (
            <CartItem
              key={item.id}
              item={item}
              onUpdate={handleUpdate}
              onRemove={handleRemove}
            />
          ))}
        </div>

        {/* Summary */}
        <div className="lg:col-span-1">
          <div className="bg-gray-50 p-4 sm:p-6 rounded-lg sticky top-4">
            <h2 className="text-lg font-semibold mb-4">Summary</h2>
            
            <div className="space-y-2 text-sm sm:text-base">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Tax</span>
                <span>${tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Shipping</span>
                <span>{formatCurrency(shipping)}</span>
              </div>
              <div className="border-t pt-2 flex justify-between font-semibold text-base sm:text-lg">
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>
            </div>

            <button
              onClick={() => window.location.href = '/checkout'}
              disabled={loading}
              className="w-full mt-6 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Checkout'}
            </button>

            <button
              onClick={() => window.location.href = '/products'}
              className="w-full mt-3 border border-gray-300 py-3 rounded-lg hover:bg-gray-50"
            >
              Continue Shopping
            </button>
          </div>
        </div>
      </div>

      {/* Clear Cart Confirmation Modal */}
      <ConfirmationModal
        isOpen={showClearModal}
        onClose={() => setShowClearModal(false)}
        onConfirm={confirmClearCart}
        title="Clear Cart"
        message="Are you sure you want to clear your cart? This will remove all items."
        confirmText="Clear Cart"
        cancelText="Cancel"
        variant="warning"
        loading={loading}
      />
    </div>
  );
};

export default CartPage;