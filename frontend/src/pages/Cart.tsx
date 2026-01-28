import React, { useState, useEffect, useCallback} from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { ChevronRightIcon, TrashIcon, MinusIcon, PlusIcon, ShoppingCartIcon, AlertCircle, CheckCircle, Loader2} from 'lucide-react';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'react-hot-toast';
import { useLocale } from '../contexts/LocaleContext';
import { motion, AnimatePresence } from 'framer-motion';
import { CartSkeleton } from '../components/ui/CartSkeleton';
import { validation } from '../lib/validation';
import { ConfirmationModal } from '../components/ui/ConfirmationModal';

export const Cart = () => {
  const { 
    cart, 
    removeItem, 
    updateQuantity, 
    clearCart, 
    loading,
  } = useCart();
  const { isAuthenticated, isLoading: authLoading, setIntendedDestination } = useAuth();
  const { formatCurrency } = useLocale();
  const navigate = useNavigate();
  const location = useLocation();
  const [couponCode, setCouponCode] = useState('');
  const [taxLocation, setTaxLocation] = useState<{ country: string; province?: string }>({ country: 'US' });
  const [clearingCart, setClearingCart] = useState(false);
  const [showRemoveItemModal, setShowRemoveItemModal] = useState(false);
  const [showClearCartModal, setShowClearCartModal] = useState(false);
  const [itemToRemove, setItemToRemove] = useState<{ id: string; name: string; message: string } | null>(null);
  
  // Use cart items directly from context - this ensures the component re-renders when cart object changes
  var cartItems = cart?.items || [];
  
  
  const validateForCheckout = () => {
    if (!cart?.items.length) {
      toast.error('Your cart is empty');
      return false;
    }
    
    // Check for out of stock cartItems
    const outOfStockItems = cartItems.filter(item => 
      item.variant?.stock !== undefined && item.variant.stock < item.quantity
    );
    
    if (outOfStockItems.length > 0) {
      toast.error('Some items in your cart are out of stock');
      return false;
    }
    
    return true;
  };

  
  // Calculate cart summary locally
  const getCartSummary = () => {
    // Always prefer backend-calculated values when available
    const subtotal = cart?.subtotal || cartItems.reduce((sum, item) => sum + item.total_price, 0);
    const tax = cart?.tax_amount || 0;
    
    // Use shipping exactly as provided by backend, no fallback calculations
    const shipping = cart?.shipping_amount || 0;
    
    // Always prefer backend total when available
    const total = cart?.total_amount || (subtotal + tax + shipping);
    
    return { subtotal, tax, shipping, total };
  };
  
  const { subtotal, tax, shipping, total } = getCartSummary();

  
  // Get tax location info
  useEffect(() => {
    const country = localStorage.getItem('detected_country') || 'US';
    const province = localStorage.getItem('detected_province') || undefined;
    setTaxLocation({ country, province });
    
  }, [cart]); // Update when cart changes (which includes tax recalculation)
  
  // Enhanced remove item handler
  const handleRemoveItem = useCallback(async (id: string) => {
    if (!id) {
      toast.error('Invalid item ID');
      return;
    }
    
    // Find item for confirmation
    const item = cartItems.find(item => item.id === id);
    const itemName = item?.variant?.product_name || item?.variant?.name || 'this item';
    
    // Confirm removal for expensive items or multiple quantities
    if (item && (item.total_price > 100 || item.quantity > 1)) {
      const confirmMessage = item.quantity > 1 
        ? `Remove all ${item.quantity} units of "${itemName}" from your cart?`
        : `Remove "${itemName}" from your cart?`;
        
      setItemToRemove({
        id,
        name: itemName,
        message: confirmMessage
      });
      setShowRemoveItemModal(true);
      return;
    }

    // For inexpensive single items, remove directly
    try {
      await removeItem(String(id));
    } catch (error: any) {
      console.error('Failed to remove item:', error);
      const errorMessage = error?.message || 'Failed to remove item. Please try again.';
      toast.error(errorMessage);
    } 
  }, [cartItems, isAuthenticated, setIntendedDestination, location.pathname, removeItem]);

  const confirmRemoveItem = async () => {
    if (!itemToRemove) return;

    try {
      await removeItem(String(itemToRemove.id));
    } catch (error: any) {
      console.error('Failed to remove item:', error);
      const errorMessage = error?.message || 'Failed to remove item. Please try again.';
      toast.error(errorMessage);
    } finally {
      setShowRemoveItemModal(false);
      setItemToRemove(null);
    }
  };

  // Enhanced quantity change handler with optimistic updates
  const handleQuantityChange = useCallback(async (id: string, quantity: number) => {
    // Check authentication for cart operations
    // console.log(id,'item_id-----')
    if (!isAuthenticated) {
      setIntendedDestination({ 
        path: location.pathname,
        action: 'cart'
      });
      navigate('/login');
      return;
    }

    // If quantity is 0 or less, remove the item instead
    if (quantity <= 0) {
      await handleRemoveItem(id);
      return;
    }

    try {
      await updateQuantity(String(id), quantity);
    } catch (error: any) {
      console.error('Failed to update quantity:', error);
      const errorMessage = error?.message || 'Failed to update cart. Please try again.';
      toast.error(errorMessage);
      
    } 
  }, [isAuthenticated, setIntendedDestination, location.pathname, updateQuantity, handleRemoveItem]);

  // Enhanced clear cart handler
  const handleClearCart = useCallback(async () => {
    if (!isAuthenticated) {
      setIntendedDestination({ 
        path: location.pathname,
        action: 'cart'
      });
      navigate('/login');
      return;
    }

    // Show confirmation modal
    setShowClearCartModal(true);
  }, [isAuthenticated, setIntendedDestination, location.pathname, navigate]);

  const confirmClearCart = async () => {
    setClearingCart(true);
    
    try {
      await clearCart();
    } catch (error: any) {
      console.error('Failed to clear cart:', error);
      const errorMessage = error?.message || 'Failed to clear cart. Please try again.';
      toast.error(errorMessage);
    } finally {
      setClearingCart(false);
      setShowClearCartModal(false);
    }
  };

  // Enhanced coupon application
  const handleApplyCoupon = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isAuthenticated) {
      setIntendedDestination({ 
        path: location.pathname,
        action: 'cart'
      });
      navigate('/login');
      return;
    }
    
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
    } catch (error: any) {
      const errorMessage = error?.response?.data?.message || error?.message || 'Failed to apply coupon. Please try again.';
      toast.error(errorMessage);
    }
  };

  // Enhanced checkout handler with validation
  const handleCheckout = useCallback(async () => {
    if (!isAuthenticated) {
      setIntendedDestination({ 
        path: '/checkout',
        action: 'checkout'
      });
      navigate('/login');
      return;
    }

    // Use the built-in validation
    if (!validateForCheckout()) {
      return;
    }

    // Navigate to checkout
    navigate('/checkout');
  }, [isAuthenticated, setIntendedDestination, validateForCheckout, navigate]);

  // Show loading state while cart or auth is loading
  if (loading || authLoading) {
    return <CartSkeleton />;
  }

  // Enhanced cart item component with loading states
  const CartItemRow = React.forwardRef<HTMLDivElement, { item: typeof cartItems[0] }>(({ item }, ref) => {
    
    return (
      <motion.div 
        ref={ref}
        key={item.id} 
        className="p-4"
        initial={{ opacity: 1 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2 }}
      >
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
          <div className="col-span-6 flex items-center">
            <div className="w-20 h-20 rounded-md overflow-hidden flex-shrink-0 bg-gray-100 relative">
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
                    alt={item.variant?.product_name || (item.variant as any)?.product?.name || item.variant?.name || 'Product'} 
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      const target = e.currentTarget;
                      target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80"%3E%3Crect width="80" height="80" fill="%23f3f4f6"/%3E%3Cpath d="M40 25c-5.5 0-10 4.5-10 10s4.5 10 10 10 10-4.5 10-10-4.5-10-10-10zm0 15c-2.8 0-5-2.2-5-5s2.2-5 5-5 5 2.2 5 5-2.2 5-5 5z" fill="%239ca3af"/%3E%3Cpath d="M55 20H25c-2.8 0-5 2.2-5 5v30c0 2.8 2.2 5 5 5h30c2.8 0 5-2.2 5-5V25c0-2.8-2.2-5-5-5zm0 35H25V25h30v30z" fill="%239ca3af"/%3E%3C/svg%3E';
                      target.onerror = null;
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
              
              {/* Processing overlay - removed since not using processing state */}
            </div>
            <div className="ml-4">
              <Link
                to={`/products/${item.variant?.product_id}`}
                className="font-medium text-copy hover:text-primary">
                <div>
                  {(item.variant?.product_name || (item.variant as any)?.product?.name) && (
                    <div className="font-medium">{item.variant?.product_name || (item.variant as any)?.product?.name}</div>
                  )}
                  <div className="text-sm text-copy-light">{item.variant?.name || 'Product'}</div>
                  
                  {/* Show variant attributes if available */}
                  {item.variant?.attributes && Object.keys(item.variant.attributes).length > 0 && (
                    <div className="mt-1">
                      {Object.entries(item.variant.attributes).slice(0, 2).map(([key, value]) => (
                        <span 
                          key={key}
                          className="inline-block bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded mr-1 mb-1"
                        >
                          {key}: {value}
                        </span>
                      ))}
                    </div>
                  )}
                  
                  {/* Stock status indicator */}
                  {item.variant?.stock !== undefined && (
                    <div className="mt-1">
                      {item.variant.stock > 10 ? (
                        <span className="text-green-600 text-xs flex items-center">
                          <CheckCircle size={12} className="mr-1" />
                          In Stock
                        </span>
                      ) : item.variant.stock > 0 ? (
                        <span className="text-orange-600 text-xs flex items-center">
                          <AlertCircle size={12} className="mr-1" />
                          Only {item.variant.stock} left
                        </span>
                      ) : (
                        <span className="text-red-600 text-xs flex items-center">
                          <AlertCircle size={12} className="mr-1" />
                          Out of Stock
                        </span>
                      )}
                    </div>
                  )}
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
            <div>
              <span className="font-medium text-primary">{formatCurrency(item.price_per_unit)}</span>
              {/* Show discount if applicable */}
              {item.variant?.discount_percentage && item.variant.discount_percentage > 0 && (
                <div className="text-xs text-gray-500 line-through">
                  {formatCurrency(item.variant.base_price)}
                </div>
              )}
            </div>
          </div>
          <div className="col-span-2 flex justify-center">
            <div className="flex items-center border border-border rounded-md">
              <button
                onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                className="px-2 py-1 text-copy-light hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Decrease quantity">
                <MinusIcon size={14} />
              </button>
              <input
                type="number"
                min="1"
                max={item.variant?.stock || 999}
                value={item.quantity}
                onChange={(e) =>
                  handleQuantityChange(item.id, parseInt(e.target.value) || 1)
                }
                className="w-10 text-center border-none focus:outline-none bg-transparent"
              />
              <button
                onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                disabled={item.variant?.stock !== undefined && item.quantity >= item.variant.stock}
                className="px-2 py-1 text-copy-light hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Increase quantity">
                <PlusIcon size={14} />
              </button>
            </div>
          </div>
          <div className="col-span-2 text-center">
            <span className="md:hidden font-medium text-copy">Subtotal: </span>
            <span className="font-medium text-copy">{formatCurrency(item.total_price)}</span>
          </div>
        </div>
      </motion.div>
    );
  });
  
  return (
    <div className="container mx-auto px-4 py-8 text-copy" key={`cart-${cart?.id || 'empty'}-${cartItems.length}`}>
      {/* Breadcrumb */}
      <nav className="flex mb-6 text-sm">
        <Link to="/" className="text-copy-lighter hover:text-primary">
          Home
        </Link>
        <ChevronRightIcon size={16} className="mx-2" />
        <span className="text-copy">Shopping Cart</span>
      </nav>

      <h1 className="text-2xl md:text-3xl font-bold text-copy mb-6 flex items-center justify-between">
        <span>Your Shopping Cart</span>
      </h1>

      {cartItems.length === 0 ? (
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
                <AnimatePresence mode="popLayout">
                  {cartItems.map((item) => (
                    <CartItemRow key={item.id} item={item} />
                  ))}
                </AnimatePresence>
              </div>
              <div className="p-4 bg-background flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
                <div className="flex items-center">
                  <button
                    onClick={handleClearCart}
                    disabled={clearingCart || cartItems.length === 0}
                    className="text-sm text-error hover:text-error-dark flex items-center disabled:opacity-50 disabled:cursor-not-allowed">
                    {clearingCart ? (
                      <Loader2 size={14} className="mr-1 animate-spin" />
                    ) : (
                      <TrashIcon size={14} className="mr-1" />
                    )}
                    Clear Cart ({cartItems.length})
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
                    {formatCurrency(shipping)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-copy-light">
                    Tax {taxLocation.province ? `(${taxLocation.province}, ${taxLocation.country})` : `(${taxLocation.country})`}
                  </span>
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
                <button
                  onClick={handleCheckout}
                  className="block w-full bg-primary hover:bg-primary-dark text-white py-3 rounded-md transition-colors text-center font-medium">
                  {isAuthenticated ? 'Proceed to Checkout' : 'Login to Checkout'}
                </button>
              </motion.div>
            </div>
          </div>
        </div>
      )}

      {/* Remove Item Confirmation Modal */}
      <ConfirmationModal
        isOpen={showRemoveItemModal}
        onClose={() => {
          setShowRemoveItemModal(false);
          setItemToRemove(null);
        }}
        onConfirm={confirmRemoveItem}
        title="Remove Item"
        message={itemToRemove?.message || 'Are you sure you want to remove this item from your cart?'}
        confirmText="Remove Item"
        cancelText="Keep Item"
        variant="warning"
      />

      {/* Clear Cart Confirmation Modal */}
      <ConfirmationModal
        isOpen={showClearCartModal}
        onClose={() => setShowClearCartModal(false)}
        onConfirm={confirmClearCart}
        title="Clear Cart"
        message={`Are you sure you want to remove all ${cartItems.length} items from your cart? This action cannot be undone.`}
        confirmText="Clear Cart"
        cancelText="Keep Items"
        variant="danger"
        loading={clearingCart}
      />
    </div>
  );
};

export default Cart;