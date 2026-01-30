import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { ShoppingCartIcon, HeartIcon, EyeIcon, CheckIcon, PlusIcon, CalendarIcon } from 'lucide-react';
import { motion } from 'framer-motion';
import { useCart } from '../../store/CartContext';
import { useWishlist } from '../../store/WishlistContext';
import { useAuth } from '../../hooks/useAuth';
import { useSubscriptionAction } from '../../hooks/useSubscription';
import { useLocale } from '../../store/LocaleContext';
import { SkeletonCard } from '../ui/SkeletonCard';
import { QRCodeDisplay } from './QRCodeDisplay';
import { BarcodeDisplay } from './BarcodeDisplay';
import { SubscriptionSelector } from '../subscription/SubscriptionSelector';
import SubscriptionAPI from '../../api/subscription';
import { toast } from 'react-hot-toast';
import { cn } from '../../utils/utils';

/**
 * @typedef {object} ProductVariantImage
 * @property {string} id
 * @property {string} variant_id
 * @property {string} url
 * @property {string} [alt_text]
 * @property {number} sort_order
 * @property {boolean} is_primary
 */

/**
 * @typedef {object} ProductVariant
 * @property {string} id
 * @property {string} product_id
 * @property {string} sku
 * @property {string} name
 * @property {number} base_price
 * @property {number} [sale_price]
 * @property {number} current_price
 * @property {number} discount_percentage
 * @property {number} stock
 * @property {string} [barcode]
 * @property {string} [qr_code]
 * @property {ProductVariantImage[]} images
 */

/**
 * @typedef {object} Product
 * @property {string} id
 * @property {string} name
 * @property {number} price
 * @property {number | null} discountPrice
 * @property {number} rating
 * @property {number} reviewCount
 * @property {string} image
 * @property {string} category
 * @property {boolean} [isNew]
 * @property {boolean} [isFeatured]
 * @property {ProductVariant[]} variants
 */

/**
 * @typedef {object} ProductCardProps
 * @property {Product} product
 * @property {ProductVariant} [selectedVariant]
 * @property {boolean} [showQRCode=false]
 * @property {boolean} [showBarcode=false]
 * @property {string} [viewMode='grid']
 * @property {string} [className]
 * @property {boolean} [isLoading=false]
 * @property {string} [animation='shimmer']
 * @property {boolean} [showSubscriptionButton=false]
 * @property {string} [subscriptionId]
 * @property {boolean} [wishlistMode=false]
 */

export const ProductCard = ({
  product,
  selectedVariant,
  showQRCode = false,
  showBarcode = false,
  viewMode = 'grid',
  className,
  isLoading = false,
  animation = 'shimmer',
  showSubscriptionButton = false,
  subscriptionId,
  wishlistMode = false,
}) => {
  const { addItem: addToCart, removeItem: removeFromCart, cart } = useCart();
  const { addItem: addToWishlist, removeItem: removeFromWishlist, isInWishlist, defaultWishlist, fetchWishlists } = useWishlist();
  const { executeWithAuth } = useAuth();
  const { isAuthenticated, hasActiveSubscriptions } = useSubscriptionAction();
  const { formatCurrency } = useLocale();
  const [isAddingToSubscription, setIsAddingToSubscription] = useState(false);
  const [showSubscriptionSelector, setShowSubscriptionSelector] = useState(false);

  if (isLoading) { // <--- Add this check
    return <SkeletonCard viewMode={viewMode} animation={animation} />;
  }

  // If not loading, ensure product is defined before proceeding
  if (!product) { // <--- Add this check
    return null; // Or throw an error, or render a placeholder
  }

  // Get the display variant (selected variant or first variant or fallback to product)
  const displayVariant = selectedVariant || (product.variants && Array.isArray(product.variants) && product.variants.length > 0 ? product.variants[0] : null);

  // Ensure we have valid product data
  const safeProduct = product || {};
  const safeVariant = displayVariant || {};

  const isInCart = cart?.items?.some(item => item.variant?.id === displayVariant?.id) || false;

  // Get the primary image from variant or fallback to product image
  const getPrimaryImage = () => {
    if (displayVariant && displayVariant.images && Array.isArray(displayVariant.images) && displayVariant.images.length > 0) {
      const primaryImage = displayVariant.images.find(img => img.is_primary);
      return primaryImage?.url || displayVariant.images[0]?.url;
    }
    if (safeProduct.images && Array.isArray(safeProduct.images) && safeProduct.images.length > 0) {
      const primaryImage = safeProduct.images.find(img => img.is_primary);
      return primaryImage?.url || safeProduct.images[0]?.url;
    }
    // Use a simple SVG placeholder instead of image file
    return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3QgeD0iNTAiIHk9IjUwIiB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgcng9IiM5ZjVmNjYiIGZpbGw9IiNmZjdmNjYiIHJ4PSI1IiByeT0iNSIvPjxwZyBmaWxsPSIjkwOTA5YSIgc3Ryb2tlLWRhc2hlcnJheSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBzdHJva2UtbWl0ZXJsaW1pdD0iMiIvPjxwZyBmaWxsPSIjZmZmIiBkPSJNNTAgMTAwaDh2bS0xMCAxMGgtMTAgMTAtMTB6Ii8+PC9zdmc+';
  };

  // Get the display price (variant price or product price)
  const getDisplayPrice = () => {
    if (displayVariant) {
      const basePrice = Number(displayVariant.base_price) || 0;
      const salePrice = displayVariant.sale_price ? Number(displayVariant.sale_price) : null;
      const currentPrice = salePrice || basePrice;
      return {
        basePrice,
        salePrice,
        currentPrice,
        discountPercentage: salePrice && basePrice > salePrice
          ? Math.round(((basePrice - salePrice) / basePrice) * 100)
          : 0
      };
    }
    // Use product price range when no variant
    const minPrice = Number(safeProduct.min_price) || Number(safeProduct.price) || 0;
    const maxPrice = Number(safeProduct.max_price) || minPrice;
    const currentPrice = minPrice; // Use min price as display price
    return {
      basePrice: maxPrice,
      salePrice: null,
      currentPrice,
      discountPercentage: 0
    };
  };

  const displayImage = getPrimaryImage();
  const { basePrice, salePrice, currentPrice, discountPercentage } = getDisplayPrice();

      const handleAddToCart = async (e) => {
        e.preventDefault();
        e.stopPropagation();
    
        if (!product) {
          toast.error("Product data is not available.");
          return;
        }

        // Check if we have a valid variant to add
        if (!displayVariant) {
          // More specific error message
          if (!product.variants || !Array.isArray(product.variants)) {
            toast.error("Product variants are not loaded yet. Please try again.");
          } else if (product.variants.length === 0) {
            toast.error("This product has no variants available.");
          } else {
            toast.error("Unable to select a variant for this product.");
          }
          return;
        }
    
        if (isInCart) {
          // Remove from cart
          try {
            await executeWithAuth(async () => {
              // Find the cart item with this variant
              const cartItem = cart?.items?.find(item => item.variant?.id === displayVariant?.id);
              if (cartItem) {
                await removeFromCart(cartItem.id);
                toast.success('Item removed from cart');
              }
              return true;
            }, 'cart');
          } catch (error) {
            console.error('Remove from cart error:', error);
            toast.error(error?.message || 'Failed to remove item from cart. Please try again.');
          }
        } else {
          try {
            await executeWithAuth(async () => {
              const payload = {
                variant_id: String(displayVariant.id),
                quantity: 1,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
              };
              
              console.log('Adding to cart:', payload);
              
              const success = await addToCart(payload);
              
              if (success) {
                toast.success('Item added to cart!');
              }
              return success;
            }, 'cart');
          } catch (error) {
            console.error('Add to cart error:', error);
            toast.error(error?.message || 'Failed to add item to cart. Please try again.');
          }
        }
      };

  const handleAddToSubscription = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!displayVariant) {
      toast.error("This product has no variants available.");
      return;
    }
    
    if (!isAuthenticated) {
      toast.error('Please log in to add products to subscriptions');
      return;
    }
    
    if (!hasActiveSubscriptions) {
      toast.error('You need an active subscription to add products');
      return;
    }
    
    setShowSubscriptionSelector(true);
  };

      const handleAddToWishlist = async (e) => {
        e.preventDefault();
        e.stopPropagation();
    
        if (!product) {
          toast.error("Product data is not available.");
          return;
        }

        // Check if we have a valid variant to add
        if (!displayVariant) {
          toast.error("This product has no variants available.");
          return;
        }
    
        const isProductInWishlist = isInWishlist(product.id, displayVariant?.id);
    
        if (isProductInWishlist) {
          // Remove from wishlist
          try {
            await executeWithAuth(async () => {
              // Debug: Log current state
              console.log('Removing from wishlist:', {
                productId: product.id,
                variantId: displayVariant?.id,
                defaultWishlistId: defaultWishlist?.id,
                wishlistItems: defaultWishlist?.items?.length
              });
              
              // Find the wishlist item
              const wishlistItem = defaultWishlist?.items?.find(
                item => item.product_id === product.id && 
                       (!displayVariant?.id || item.variant_id === displayVariant?.id)
              );
              
              console.log('Found wishlist item:', wishlistItem);
              
              if (wishlistItem && defaultWishlist) {
                // Check if this is a temporary item (optimistic update)
                if (wishlistItem.id.startsWith('temp-')) {
                  console.warn('Removing temporary item from optimistic update...');
                  // For temporary items, just remove them from the optimistic state
                  // The WishlistContext will handle the actual API call
                  const success = await removeFromWishlist(defaultWishlist.id, wishlistItem.id);
                  if (success) {
                    toast.success('Item removed from wishlist');
                  }
                  return true;
                }
                
                console.log('Calling removeFromWishlist with:', {
                  wishlistId: defaultWishlist.id,
                  itemId: wishlistItem.id
                });
                
                const success = await removeFromWishlist(defaultWishlist.id, wishlistItem.id);
                if (success) {
                  toast.success('Item removed from wishlist');
                }
              } else {
                console.warn('Wishlist item not found');
                toast.error('Item not found in wishlist. Please try again.');
              }
              return true;
            }, 'wishlist');
          } catch (error) {
            console.error('Remove from wishlist error:', error);
            toast.error(error?.message || 'Failed to remove item from wishlist. Please try again.');
          }
        } else {
          await executeWithAuth(async () => {
            await addToWishlist(product.id, displayVariant?.id);
            return true;
          }, 'wishlist');
        }
      };

  return (
    <motion.div
      className={cn(
        'bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 transition-all duration-200 hover:shadow-lg hover:-translate-y-1 group text-copy',
        'flex flex-col h-full',
        viewMode === 'list' && 'flex-row items-center p-4',
        'w-full'
      )}
      whileHover={{ y: -5 }}
      transition={{ duration: 0.2 }}>
      <div className={cn('relative flex-shrink-0', viewMode === 'list' && 'w-48 h-48 mr-4')}>
        <Link to={`/products/${product.id}`}>
          <img
            src={displayImage}
            alt={displayVariant ? `${product.name} - ${displayVariant.name}` : product.name}
            className={cn(
              'w-full object-cover group-hover:scale-105 transition-transform duration-300',
              viewMode === 'grid' && 'h-32 sm:h-36 md:h-40',
              viewMode === 'list' && 'h-32 w-32 rounded-lg'
            )}
          />
        </Link>
        {/* Product badges */}
        {product.isNew && (
          <span className="absolute top-2 left-2 bg-primary text-white text-xs font-medium px-2 py-1 rounded-full">
            New
          </span>
        )}
        {salePrice && (
          <span className="absolute top-2 right-2 bg-error text-white text-xs font-medium px-2 py-1 rounded-full">
            Sale
          </span>
        )}
        {displayVariant && displayVariant.stock <= 5 && displayVariant.stock > 0 && (
          <span className="absolute bottom-2 left-2 bg-warning text-white text-xs font-medium px-2 py-1 rounded-full">
            Only {displayVariant.stock} left
          </span>
        )}
        {displayVariant && displayVariant.stock === 0 && (
          <span className="absolute bottom-2 left-2 bg-error text-white text-xs font-medium px-2 py-1 rounded-full">
            Out of Stock
          </span>
        )}
        {/* Quick action buttons - hidden on mobile for grid view */}
        <div
          className={cn(
            'absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black bg-opacity-20',
            viewMode === 'grid' && 'hidden sm:flex', // Hide on mobile
            viewMode === 'list' && 'hidden md:flex'
          )}>
          <div className="flex space-x-2">
            <button
              onClick={handleAddToCart}
              className={`w-9 h-9 rounded-full flex items-center justify-center transition-colors ${isInCart
                ? 'bg-primary text-white'
                : 'bg-surface text-copy hover:bg-primary hover:text-white'
                }`}
              aria-label={isInCart ? "Remove from cart" : "Add to cart"}>
              {isInCart ? <CheckIcon size={16} /> : <ShoppingCartIcon size={16} />}
            </button>
            <button
              onClick={handleAddToWishlist}
              className={`w-9 h-9 rounded-full flex items-center justify-center transition-colors ${isInWishlist(product.id, displayVariant?.id)
                ? 'bg-error text-white'
                : 'bg-surface text-copy hover:bg-primary hover:text-white'
                }`}
              aria-label={isInWishlist(product.id, displayVariant?.id) ? "Remove from wishlist" : "Add to wishlist"}>
              <HeartIcon size={16} />
            </button>
            {/* Add to Subscription button */}
            {isAuthenticated && hasActiveSubscriptions && (
              <button
                onClick={handleAddToSubscription}
                className="w-9 h-9 rounded-full bg-surface text-copy flex items-center justify-center hover:bg-green-600 hover:text-white transition-colors flex-shrink-0"
                aria-label="Add to subscription">
                <CalendarIcon size={16} />
              </button>
            )}
            <Link
              to={`/products/${product.id}`}
              className="w-9 h-9 rounded-full bg-surface text-copy flex items-center justify-center hover:bg-primary hover:text-white transition-colors"
              aria-label="View product">
              <EyeIcon size={16} />
            </Link>
          </div>
        </div>
      </div>
      <div className={cn('flex flex-col flex-grow p-2 sm:p-3', viewMode === 'list' && 'p-0')}>
        <div className="space-y-1">
          <span className="text-xs text-copy-light dark:text-gray-400 line-clamp-1 uppercase tracking-wide">
            {(safeProduct.category && safeProduct.category.name) ? safeProduct.category.name : 'Uncategorized'}
          </span>
          <Link to={`/products/${safeProduct.id || ''}`}>
            <h3 className="font-semibold text-xs sm:text-sm text-main dark:text-white hover:text-primary transition-colors line-clamp-2 min-h-[1.5rem] sm:min-h-[2rem]">
              {safeProduct.name || 'Unknown Product'}
            </h3>
          </Link>
          <div className="flex items-center space-x-1">
            <div className="flex text-yellow-400 text-xs">
              {'★'.repeat(Math.floor(Number(safeProduct.rating_average) || Number(safeProduct.average_rating) || Number(safeProduct.rating) || 0))}
              {'☆'.repeat(5 - Math.floor(Number(safeProduct.rating_average) || Number(safeProduct.average_rating) || Number(safeProduct.rating) || 0))}
            </div>
            <span className="text-xs text-copy-light dark:text-gray-400">({Number(safeProduct.rating_count) || Number(safeProduct.review_count) || 0})</span>
          </div>
        </div>
        
        {/* Subscription Icon - Show above buttons for users with active subscriptions */}
        {isAuthenticated && hasActiveSubscriptions && (
          <div className="flex justify-center pt-2 pb-1">
            <div className="inline-flex items-center justify-center w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full hover:bg-green-200 dark:hover:bg-green-800 transition-colors cursor-pointer group">
              <CalendarIcon size={16} className="text-green-600 dark:text-green-300 group-hover:scale-110 transition-transform" />
            </div>
          </div>
        )}
        
        <div className="mt-auto pt-1.5 sm:pt-2 space-y-1.5 sm:space-y-2">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
            <div className="space-y-0.5">
              {salePrice && discountPercentage > 0 ? (
                <div className="flex items-center flex-wrap gap-1">
                  <span className="font-bold text-sm sm:text-base text-primary">
                    {formatCurrency(currentPrice)}
                  </span>
                  <span className="text-xs text-copy-light dark:text-gray-400 line-through">
                    {formatCurrency(basePrice)}
                  </span>
                  <span className="bg-red-500 text-white text-xs font-bold px-1 py-0.5 rounded-full">
                    -{discountPercentage}%
                  </span>
                </div>
              ) : (
                <span className="font-bold text-sm sm:text-base text-primary">
                  {formatCurrency(currentPrice)}
                </span>
              )}
              {displayVariant && (
                <div className="text-xs text-copy-light dark:text-gray-400">
                  {displayVariant.name || 'Default Variant'}
                </div>
              )}
            </div>
          </div>
          
          {/* Mobile buttons - optimized for smaller cards */}
          <div className="flex flex-col gap-1 sm:hidden">
            <div className="grid grid-cols-2 gap-1">
              <button
                onClick={handleAddToCart}
                disabled={(displayVariant?.stock ?? displayVariant?.inventory_quantity_available ?? 0) === 0}
                className={cn(
                  'flex items-center justify-center px-1.5 py-1.5 rounded-md text-xs font-medium transition-colors',
                  (displayVariant?.stock ?? displayVariant?.inventory_quantity_available ?? 0) === 0 
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : isInCart
                      ? 'bg-green-600 text-white'
                      : 'bg-primary text-white hover:bg-primary-dark'
                )}
                aria-label={isInCart ? "In cart" : "Add to cart"}>
                {isInCart ? (
                  <>
                    <CheckIcon size={10} />
                  </>
                ) : (
                  <>
                    <ShoppingCartIcon size={10} />
                  </>
                )}
              </button>
              
              {/* Mobile wishlist button */}
              <button
                onClick={handleAddToWishlist}
                className={cn(
                  'flex items-center justify-center px-1.5 py-1.5 rounded-md text-xs font-medium transition-colors',
                  wishlistMode || isInWishlist(product.id, displayVariant?.id)
                    ? 'bg-red-100 text-red-700 dark:bg-red-800 dark:text-red-100'
                    : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                )}
                aria-label={wishlistMode || isInWishlist(product.id, displayVariant?.id) ? "Remove from wishlist" : "Add to wishlist"}>
                <HeartIcon size={10} fill={wishlistMode || isInWishlist(product.id, displayVariant?.id) ? 'currentColor' : 'none'} />
              </button>
            </div>
            
            {/* Mobile subscription button - full width */}
            {isAuthenticated && hasActiveSubscriptions && (
              <button
                onClick={handleAddToSubscription}
                className="flex items-center justify-center bg-green-600 hover:bg-green-700 text-white px-1.5 py-1.5 rounded-md text-xs font-medium transition-colors"
                aria-label="Subscribe">
                <CalendarIcon size={10} />
              </button>
            )}
          </div>

          {/* Desktop buttons (hidden on mobile) */}
          <div className={cn(
            'hidden items-center gap-2',
            'sm:flex',
            viewMode === 'list' && 'md:flex md:order-1'
          )}>
            <button
              onClick={handleAddToCart}
              disabled={(displayVariant?.stock ?? displayVariant?.inventory_quantity_available ?? 0) === 0}
              className={cn(
                'flex items-center justify-center px-2 py-1.5 rounded-md text-xs font-medium transition-colors min-w-[80px] sm:min-w-[100px] whitespace-nowrap',
                (displayVariant?.stock ?? displayVariant?.inventory_quantity_available ?? 0) === 0 
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : isInCart
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-primary text-white hover:bg-primary-dark'
              )}
              aria-label={isInCart ? "In cart" : "Add to cart"}>
              {isInCart ? (
                <>
                  <CheckIcon size={12} />
                  <span className="ml-1 text-xs">In Cart</span>
                </>
              ) : (
                <>
                  <ShoppingCartIcon size={12} />
                  <span className="ml-1 text-xs">Add</span>
                </>
              )}
            </button>
            
            {/* Desktop wishlist button */}
            <button
              onClick={handleAddToWishlist}
              className={cn(
                'flex items-center justify-center px-3 py-2 rounded-md text-sm font-medium transition-colors min-w-[40px]',
                wishlistMode || isInWishlist(product.id, displayVariant?.id)
                  ? 'bg-red-100 text-red-700 dark:bg-red-800 dark:text-red-100 hover:bg-red-200 dark:hover:bg-red-700'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              )}
              aria-label={wishlistMode || isInWishlist(product.id, displayVariant?.id) ? "Remove from wishlist" : "Add to wishlist"}>
              <HeartIcon size={12} fill={wishlistMode || isInWishlist(product.id, displayVariant?.id) ? 'currentColor' : 'none'} />
            </button>
            
            {/* Desktop subscription button */}
            {isAuthenticated && hasActiveSubscriptions && (
              <button
                onClick={handleAddToSubscription}
                className="flex items-center justify-center bg-green-600 hover:bg-green-700 text-white px-2 py-1.5 rounded-md text-xs font-medium transition-colors min-w-[70px] sm:min-w-[90px] whitespace-nowrap"
                aria-label="Add to subscription">
                <CalendarIcon size={12} />
                <span className="ml-1 text-xs">Sub</span>
              </button>
            )}
          </div>
          
          {/* Subscription Button (legacy - keeping for compatibility) */}
          {showSubscriptionButton && subscriptionId && (
            <button
              onClick={handleAddToSubscription}
              disabled={isAddingToSubscription}
              className={cn(
                'ml-2 flex items-center text-white bg-green-600 hover:bg-green-700 px-2 sm:px-3 py-2 rounded-md transition-colors flex-shrink-0',
                isAddingToSubscription && 'opacity-50 cursor-not-allowed'
              )}
              aria-label="Add to subscription">
              {isAddingToSubscription ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                <PlusIcon size={16} className="flex-shrink-0" />
              )}
              <span className="ml-1 text-xs sm:text-sm whitespace-nowrap">Subscribe</span>
            </button>
          )}
        </div>

        {/* Subscription Selector Modal */}
        {showSubscriptionSelector && displayVariant && (
          <SubscriptionSelector
            isOpen={showSubscriptionSelector}
            onClose={() => setShowSubscriptionSelector(false)}
            productName={product.name}
            variantId={displayVariant.id}
            quantity={1}
            onSuccess={() => {
              setShowSubscriptionSelector(false);
            }}
          />
        )}

        {/* QR Code and Barcode Display */}
        {(showQRCode || showBarcode) && displayVariant && (
          <div className="mt-4 pt-4 border-t border-border-light">
            <div className="flex items-center justify-center space-x-4">
              {showQRCode && displayVariant.qr_code && (
                <div className="text-center">
                  <QRCodeDisplay
                    qrCode={displayVariant.qr_code}
                    variant={{
                      id: displayVariant.id,
                      name: displayVariant.name,
                      sku: displayVariant.sku,
                      product_name: product.name
                    }}
                    size="sm"
                    showControls={false}
                  />
                </div>
              )}
              {showBarcode && displayVariant.barcode && (
                <div className="text-center">
                  <BarcodeDisplay
                    variant={{
                      id: displayVariant.id,
                      product_id: product.id,
                      sku: displayVariant.sku,
                      name: displayVariant.name,
                      base_price: displayVariant.base_price,
                      sale_price: displayVariant.sale_price,
                      stock: displayVariant.stock,
                      images: displayVariant.images || [],
                      product_name: product.name,
                      barcode: displayVariant.barcode,
                      qr_code: displayVariant.qr_code
                    }}
                    showBoth={false}
                    size="sm"
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};