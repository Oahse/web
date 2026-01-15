import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronRightIcon, TrashIcon, MinusIcon, PlusIcon, ShoppingCartIcon } from 'lucide-react';
import { useCart } from '../contexts/CartContext';
import { useLocale } from '../contexts/LocaleContext';
import { motion } from 'framer-motion';
import { CartSkeleton } from '../components/ui/CartSkeleton';
import { toast } from 'react-hot-toast';
import { validation } from '../lib/validation';

export const Cart = () => {
  const { cart, removeItem, updateQuantity, clearCart, loading } = useCart();
  const { formatCurrency } = useLocale();
  const [couponCode, setCouponCode] = useState('');

  const handleQuantityChange = (id: string, quantity: number) => {
    // Enhanced validation using validation utility
    const quantityValidation = validation.quantity(quantity);
    if (!quantityValidation.valid) {
      toast.error(quantityValidation.message);
      return;
    }

    // Find the item to check stock limits
    const item = items.find(item => item.id === id);
    if (!item) {
      toast.error('Item not found in cart');
      return;
    }

    // Check stock availability if variant data is available
    const maxStock = item.variant?.stock || 999; // Default to 999 if stock not available
    const stockValidation = validation.quantity(quantity, maxStock);
    if (!stockValidation.valid) {
      toast.error(stockValidation.message);
      return;
    }

    updateQuantity(String(id), quantity);
  };

  const handleRemoveItem = (id: string) => {
    if (!id) {
      toast.error('Invalid item ID');
      return;
    }
    
    // Confirm removal for expensive items
    const item = items.find(item => item.id === id);
    if (item && item.total_price > 100) {
      if (!window.confirm(`Are you sure you want to remove "${item.variant?.product_name || 'this item'}" from your cart?`)) {
        return;
      }
    }
    
    removeItem(String(id));
  };

  const handleApplyCoupon = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const couponValidation = validation.couponCode(couponCode);
    if (!couponValidation.valid) {
      toast.error(couponValidation.message);
      return;
    }

    try {
      // TODO: Replace with actual API call
      // await CartAPI.applyPromocode(couponCode.trim().toUpperCase(), access_token);
      
      // Mock coupon application logic for now
      const validCoupons = ['SAVE10', 'WELCOME5', 'FREESHIP'];
      const normalizedCode = couponCode.trim().toUpperCase();
      
      if (validCoupons.includes(normalizedCode)) {
        toast.success(`Coupon ${normalizedCode} applied successfully!`);
        setCouponCode('');
      } else {
        toast.error('Invalid coupon code. Please check and try again.');
      }
    } catch (error) {
      const errorMessage = error?.response?.data?.message || error?.message || 'Failed to apply coupon. Please try again.';
      toast.error(errorMessage);
    }
  };

  const items = cart?.items || [];
  const subtotal = cart?.subtotal || 0;
  const shipping = cart?.shipping_amount || 0;
  const tax = cart?.tax_amount || 0;
  const total = cart?.total_amount || 0;

  if (loading) {
    return <CartSkeleton />;
  }

  return (
    <div className="container mx-auto px-4 py-8 text-copy">
      {/* Breadcrumb */}
      <nav className="flex mb-6 text-sm">
        <Link to="/" className="text-copy-lighter hover:text-primary">
          Home
        </Link>
        <ChevronRightIcon size={16} className="mx-2" />
        <span className="text-copy">Shopping Cart</span>
      </nav>

      <h1 className="text-2xl md:text-3xl font-bold text-copy mb-6">Your Shopping Cart</h1>

      {items.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-background flex items-center justify-center">
            <ShoppingCartIcon size={32} className="text-copy-lighter" />
          </div>
          <h2 className="text-xl font-medium text-copy mb-2">Your cart is empty</h2>
          <p className="text-copy-light mb-6">Looks like you haven't added any products to your cart yet.</p>
          <Link
            to="/products"
            className="inline-flex items-center bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-md transition-colors">
            Continue Shopping
          </Link>
        </div>
      ) : (
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Cart Items */}
          <div className="lg:w-2/3">
            <div className="bg-surface rounded-lg shadow-sm overflow-hidden">
              <div className="hidden md:grid grid-cols-12 gap-4 p-4 bg-background text-copy font-medium">
                <div className="col-span-6">Product</div>
                <div className="col-span-2 text-center">Price</div>
                <div className="col-span-2 text-center">Quantity</div>
                <div className="col-span-2 text-center">Subtotal</div>
              </div>
              <div className="divide-y divide-border-light">
                {items.map((item) => (
                  <div key={item.id} className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                      <div className="col-span-6 flex items-center">
                        <div className="w-20 h-20 rounded-md overflow-hidden flex-shrink-0 bg-gray-100">
                          {(() => {
                            // Get image URL from cart item data
                            let imageUrl = null;
                            
                            // First try to get from variant images array (if available)
                            if (item.variant?.images && item.variant.images.length > 0) {
                              const primaryImage = item.variant.images.find(img => img.is_primary);
                              imageUrl = primaryImage?.url || item.variant.images[0]?.url;
                            }
                            
                            // Fallback to direct image_url from cart item (if available)
                            if (!imageUrl && (item as any).image_url) {
                              imageUrl = (item as any).image_url;
                            }
                            
                            // Fallback to variant primary_image if available
                            if (!imageUrl && item.variant?.primary_image?.url) {
                              imageUrl = item.variant.primary_image.url;
                            }
                            
                            return imageUrl ? (
                              <img 
                                src={imageUrl} 
                                alt={item.variant.product_name || (item.variant as any).product?.name || item.variant.name} 
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                  e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80"%3E%3Crect width="80" height="80" fill="%23f3f4f6"/%3E%3Cpath d="M40 25c-5.5 0-10 4.5-10 10s4.5 10 10 10 10-4.5 10-10-4.5-10-10-10zm0 15c-2.8 0-5-2.2-5-5s2.2-5 5-5 5 2.2 5 5-2.2 5-5 5z" fill="%239ca3af"/%3E%3Cpath d="M55 20H25c-2.8 0-5 2.2-5 5v30c0 2.8 2.2 5 5 5h30c2.8 0 5-2.2 5-5V25c0-2.8-2.2-5-5-5zm0 35H25V25h30v30z" fill="%239ca3af"/%3E%3C/svg%3E';
                                  e.currentTarget.onerror = null;
                                }}
                                loading="lazy"
                              />
                            ) : (
                              <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                                <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                              </div>
                            );
                          })()}
                        </div>
                        <div className="ml-4">
                          <Link
                            to={`/products/${item.variant.product_id}`}
                            className="font-medium text-copy hover:text-primary">
                            <div>
                              {(item.variant.product_name || (item.variant as any).product?.name) && (
                                <div className="font-medium">{item.variant.product_name || (item.variant as any).product?.name}</div>
                              )}
                              <div className="text-sm text-copy-light">{item.variant.name}</div>
                            </div>
                          </Link>
                          <button
                            onClick={() => handleRemoveItem(item.id)}
                            className="text-sm text-error hover:text-error-dark flex items-center mt-1">
                            <TrashIcon size={14} className="mr-1" />
                            Remove
                          </button>
                        </div>
                      </div>
                      <div className="col-span-2 text-center">
                        <span className="md:hidden font-medium text-copy">Price: </span>
                        <span className="font-medium text-primary">{formatCurrency(item.price_per_unit)}</span>
                      </div>
                      <div className="col-span-2 flex justify-center">
                        <div className="flex items-center border border-border rounded-md">
                          <button
                            onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                            className="px-2 py-1 text-copy-light hover:text-primary"
                            disabled={item.quantity <= 1}>
                            <MinusIcon size={14} />
                          </button>
                          <input
                            type="number"
                            min="1"
                            value={item.quantity}
                            onChange={(e) =>
                              handleQuantityChange(item.id, parseInt(e.target.value) || 1)
                            }
                            className="w-10 text-center border-none focus:outline-none bg-transparent"
                          />
                          <button
                            onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                            className="px-2 py-1 text-copy-light hover:text-primary">
                            <PlusIcon size={14} />
                          </button>
                        </div>
                      </div>
                      <div className="col-span-2 text-center">
                        <span className="md:hidden font-medium text-copy">Subtotal: </span>
                        <span className="font-medium text-copy">{formatCurrency(item.total_price)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-4 bg-background flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
                <div className="flex items-center">
                  <button
                    onClick={() => clearCart()}
                    className="text-sm text-error hover:text-error-dark flex items-center">
                    <TrashIcon size={14} className="mr-1" />
                    Clear Cart
                  </button>
                </div>
                <Link to="/products" className="text-sm text-primary hover:underline flex items-center">
                  Continue Shopping
                  <ChevronRightIcon size={16} className="ml-1" />
                </Link>
              </div>
            </div>
          </div>

          {/* Order Summary */}
          <div className="lg:w-1/3">
            <div className="bg-surface rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-copy mb-4">Order Summary</h2>
              <div className="space-y-3 mb-6">
                <div className="flex justify-between">
                  <span className="text-copy-light">Subtotal</span>
                  <span className="font-medium text-copy">{formatCurrency(subtotal)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-copy-light">Shipping</span>
                  <span className="font-medium text-copy">
                    {shipping === 0 ? 'Free' : formatCurrency(shipping)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-copy-light">Tax</span>
                  <span className="font-medium text-copy">{formatCurrency(tax)}</span>
                </div>
                <div className="border-t border-border-light pt-3 flex justify-between">
                  <span className="text-lg font-semibold text-copy">Total</span>
                  <span className="text-lg font-bold text-primary">{formatCurrency(total)}</span>
                </div>
              </div>
              <form onSubmit={handleApplyCoupon} className="mb-6">
                <div className="flex">
                  <input
                    type="text"
                    placeholder="Coupon code"
                    className="flex-grow px-4 py-2 border border-border rounded-l-md focus:outline-none focus:ring-1 focus:ring-primary bg-transparent"
                    value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value)}
                  />
                  <button
                    type="submit"
                    className="bg-primary text-white px-4 py-2 rounded-r-md hover:bg-primary-dark transition-colors">
                    Apply
                  </button>
                </div>
              </form>
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Link
                  to="/checkout"
                  className="block w-full bg-primary hover:bg-primary-dark text-white py-3 rounded-md transition-colors text-center font-medium">
                  Proceed to Checkout
                </Link>
              </motion.div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};