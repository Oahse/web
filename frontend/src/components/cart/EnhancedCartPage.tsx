import React, { useState } from 'react';
import { useCart } from '../../hooks/useCart';
import { useAuth } from '../../hooks/useAuth';
import { toast } from 'react-hot-toast';
import { Trash2, Plus, Minus, ShoppingBag, AlertCircle } from 'lucide-react';

interface CartItemProps {
  item: any;
  isOptimistic: boolean;
  isProcessing: boolean;
  onUpdateQuantity: (itemId: string, quantity: number) => void;
  onRemoveItem: (itemId: string) => void;
}

const CartItem: React.FC<CartItemProps> = ({ 
  item, 
  isOptimistic, 
  isProcessing, 
  onUpdateQuantity, 
  onRemoveItem 
}) => {
  const [localQuantity, setLocalQuantity] = useState(item.quantity);

  const handleQuantityChange = (newQuantity: number) => {
    if (newQuantity < 1) return;
    setLocalQuantity(newQuantity);
    onUpdateQuantity(item.id, newQuantity);
  };

  const variant = item.variant;
  const productName = variant?.product_name || variant?.name || 'Unknown Product';
  const imageUrl = variant?.primary_image?.url || '/placeholder-product.jpg';
  const currentPrice = variant?.current_price || item.price_per_unit;
  const isOnSale = variant?.sale_price && variant.sale_price < variant.base_price;

  return (
    <div className={`
      bg-white rounded-lg shadow-sm border p-4 transition-all duration-200
      ${isOptimistic ? 'opacity-70 ring-2 ring-blue-200' : ''}
      ${isProcessing ? 'pointer-events-none' : ''}
    `}>
      {/* Optimistic indicator */}
      {isOptimistic && (
        <div className="flex items-center gap-2 mb-2 text-sm text-blue-600">
          <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <span>Updating...</span>
        </div>
      )}

      <div className="flex gap-4">
        {/* Product Image */}
        <div className="flex-shrink-0">
          <img
            src={imageUrl}
            alt={productName}
            className="w-20 h-20 object-cover rounded-md"
            onError={(e) => {
              e.currentTarget.src = '/placeholder-product.jpg';
            }}
          />
        </div>

        {/* Product Details */}
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 truncate">{productName}</h3>
          
          {/* Variant attributes */}
          {variant?.attributes && Object.keys(variant.attributes).length > 0 && (
            <div className="mt-1 text-sm text-gray-500">
              {Object.entries(variant.attributes).map(([key, value]) => (
                <span key={key} className="mr-3">
                  {key}: {String(value)}
                </span>
              ))}
            </div>
          )}

          {/* Price */}
          <div className="mt-2 flex items-center gap-2">
            <span className="text-lg font-semibold text-gray-900">
              ${currentPrice?.toFixed(2)}
            </span>
            {isOnSale && variant?.base_price && (
              <span className="text-sm text-gray-500 line-through">
                ${variant.base_price.toFixed(2)}
              </span>
            )}
          </div>

          {/* Stock warning */}
          {variant?.stock !== undefined && variant.stock < item.quantity && (
            <div className="mt-1 flex items-center gap-1 text-sm text-red-600">
              <AlertCircle className="w-4 h-4" />
              <span>Only {variant.stock} in stock</span>
            </div>
          )}
        </div>

        {/* Quantity Controls */}
        <div className="flex flex-col items-end gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleQuantityChange(localQuantity - 1)}
              disabled={localQuantity <= 1 || isProcessing}
              className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Minus className="w-4 h-4" />
            </button>
            
            <span className="w-12 text-center font-medium">
              {localQuantity}
            </span>
            
            <button
              onClick={() => handleQuantityChange(localQuantity + 1)}
              disabled={isProcessing || (variant?.stock && localQuantity >= variant.stock)}
              className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>

          {/* Remove button */}
          <button
            onClick={() => onRemoveItem(item.id)}
            disabled={isProcessing}
            className="text-red-600 hover:text-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Item total */}
      <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between items-center">
        <span className="text-sm text-gray-600">Item total:</span>
        <span className="font-semibold text-gray-900">
          ${(currentPrice * localQuantity).toFixed(2)}
        </span>
      </div>
    </div>
  );
};

const EnhancedCartPage: React.FC = () => {
  const { user } = useAuth();
  const { 
    cart, 
    loading, 
    isOptimistic,
    items, 
    totalItems, 
    processingItems,
    clearingCart,
    updateQuantity, 
    removeItem, 
    clearCart,
    validateForCheckout,
    getCartSummary 
  } = useCart();

  const handleUpdateQuantity = async (itemId: string, quantity: number) => {
    try {
      await updateQuantity(itemId, quantity);
    } catch (error: any) {
      toast.error(error.message || 'Failed to update quantity');
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    try {
      await removeItem(itemId);
    } catch (error: any) {
      toast.error(error.message || 'Failed to remove item');
    }
  };

  const handleClearCart = async () => {
    if (!window.confirm('Are you sure you want to clear your cart?')) {
      return;
    }

    try {
      await clearCart();
    } catch (error: any) {
      toast.error(error.message || 'Failed to clear cart');
    }
  };

  const handleCheckout = () => {
    if (validateForCheckout()) {
      // Navigate to checkout
      window.location.href = '/checkout';
    }
  };

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center">
          <ShoppingBag className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Please log in to view your cart
          </h2>
          <p className="text-gray-600 mb-6">
            You need to be logged in to add items to your cart and make purchases.
          </p>
          <button
            onClick={() => window.location.href = '/login'}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Log In
          </button>
        </div>
      </div>
    );
  }

  if (loading && !cart) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-gray-200 h-32 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center">
          <ShoppingBag className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Your cart is empty
          </h2>
          <p className="text-gray-600 mb-6">
            Looks like you haven't added any items to your cart yet.
          </p>
          <button
            onClick={() => window.location.href = '/products'}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Continue Shopping
          </button>
        </div>
      </div>
    );
  }

  const summary = getCartSummary();

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Shopping Cart ({totalItems} items)
        </h1>
        
        {/* Global optimistic indicator */}
        {isOptimistic && (
          <div className="flex items-center gap-2 text-sm text-blue-600">
            <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span>Updating cart...</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Cart Items */}
        <div className="lg:col-span-2">
          <div className="space-y-4">
            {items.map((item) => (
              <CartItem
                key={item.id}
                item={item}
                isOptimistic={isOptimistic}
                isProcessing={processingItems.has(item.id)}
                onUpdateQuantity={handleUpdateQuantity}
                onRemoveItem={handleRemoveItem}
              />
            ))}
          </div>

          {/* Clear Cart Button */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <button
              onClick={handleClearCart}
              disabled={clearingCart || isOptimistic}
              className="text-red-600 hover:text-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {clearingCart ? 'Clearing...' : 'Clear Cart'}
            </button>
          </div>
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <div className={`
            bg-gray-50 rounded-lg p-6 sticky top-4 transition-all duration-200
            ${isOptimistic ? 'opacity-70' : ''}
          `}>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Order Summary
            </h2>

            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span className="font-medium">${summary.subtotal.toFixed(2)}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Tax</span>
                <span className="font-medium">${summary.tax.toFixed(2)}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Shipping</span>
                <span className="font-medium">
                  {summary.shipping > 0 ? `$${summary.shipping.toFixed(2)}` : 'Free'}
                </span>
              </div>
              
              <div className="border-t border-gray-200 pt-3">
                <div className="flex justify-between">
                  <span className="text-lg font-semibold text-gray-900">Total</span>
                  <span className="text-lg font-semibold text-gray-900">
                    ${summary.total.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={handleCheckout}
              disabled={loading || isOptimistic || clearingCart}
              className="w-full mt-6 bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading || isOptimistic ? 'Updating...' : 'Proceed to Checkout'}
            </button>

            <button
              onClick={() => window.location.href = '/products'}
              className="w-full mt-3 border border-gray-300 text-gray-700 py-3 px-4 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Continue Shopping
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedCartPage;