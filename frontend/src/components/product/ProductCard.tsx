import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { ShoppingCartIcon, HeartIcon, EyeIcon, CheckIcon, PlusIcon, CalendarIcon } from 'lucide-react';
import { motion } from 'framer-motion';
import { useCart } from '../../contexts/CartContext';
import { useWishlist } from '../../contexts/WishlistContext';
import { useAuthenticatedAction } from '../../hooks/useAuthenticatedAction';
import { useSubscriptionAction } from '../../hooks/useSubscriptionAction';
import { useLocale } from '../../contexts/LocaleContext';
import { SkeletonCard } from '../ui/SkeletonCard';
import { QRCodeDisplay } from './QRCodeDisplay';
import { BarcodeDisplay } from './BarcodeDisplay';
import { SubscriptionSelector } from '../subscription/SubscriptionSelector';
import SubscriptionAPI from '../../apis/subscription';
import { toast } from 'react-hot-toast';
import { cn } from '../../lib/utils';

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
 * @property {Product} [product]
 * @property {ProductVariant} [selectedVariant]
 * @property {boolean} [showQRCode=false]
 * @property {boolean} [showBarcode=false]
 * @property {'grid' | 'list'} [viewMode='grid']
 * @property {string} [className]
 * @property {boolean} [isLoading=false]
 * @property {'shimmer' | 'pulse' | 'wave'} [animation='shimmer']
 * @property {boolean} [showSubscriptionButton=false]
 * @property {string} [subscriptionId]
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
}) => {
  const { addItem: addToCart, cart } = useCart();
  const { addItem: addToWishlist, isInWishlist } = useWishlist();
  const { executeWithAuth } = useAuthenticatedAction();
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

  const isInCart = cart?.items?.some(item => item.variant.id === displayVariant?.id) || false;

  // Get the primary image from variant or fallback to product image
  const getPrimaryImage = () => {
    if (displayVariant && displayVariant.images && Array.isArray(displayVariant.images) && displayVariant.images.length > 0) {
      const primaryImage = displayVariant.images.find(img => img.is_primary);
      return primaryImage?.url || displayVariant.images[0]?.url;
    }
    return product.image;
  };

  // Get the display price (variant price or product price)
  const getDisplayPrice = () => {
    if (displayVariant) {
      return {
        basePrice: displayVariant.base_price,
        salePrice: displayVariant.sale_price || null,
        currentPrice: displayVariant.sale_price || displayVariant.base_price,
        discountPercentage: displayVariant.sale_price 
          ? Math.round(((displayVariant.base_price - displayVariant.sale_price) / displayVariant.base_price) * 100)
          : 0
      };
    }
    return {
      basePrice: product.price,
      salePrice: product.discountPrice,
      currentPrice: product.discountPrice || product.price,
      discountPercentage: product.discountPrice 
        ? Math.round(((product.price - product.discountPrice) / product.price) * 100)
        : 0
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
          toast.success('This item is already in your cart.');
        } else {
          try {
            await executeWithAuth(async () => {
              console.log('Adding to cart:', {
                variant_id: String(displayVariant.id),
                quantity: 1,
                product_name: product.name
              });
              
              const success = await addToCart({
                variant_id: String(displayVariant.id),
                quantity: 1,
              });
              
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
          toast.success('This item is already in your wishlist.');
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
        'bg-surface rounded-lg overflow-hidden shadow-sm border border-border-light transition-shadow hover:shadow-md group text-copy',
        viewMode === 'list' && 'flex flex-col md:flex-row items-center p-4',
        className
      )}
      whileHover={{ y: -5 }}
      transition={{ duration: 0.2 }}>
      <div className={cn('relative', viewMode === 'list' && 'w-full md:w-1/3 flex-shrink-0 mb-4 md:mb-0 md:mr-4')}>
        <Link to={`/product/${product.id}`}>
          <img
            src={displayImage}
            alt={displayVariant ? `${product.name} - ${displayVariant.name}` : product.name}
            className={cn(
              'w-full object-cover group-hover:scale-105 transition-transform duration-300',
              viewMode === 'grid' && 'h-40 sm:h-48', // Adjusted height
              viewMode === 'list' && 'h-40 md:h-32 rounded-md'
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
              to={`/product/${product.id}`}
              className="w-9 h-9 rounded-full bg-surface text-copy flex items-center justify-center hover:bg-primary hover:text-white transition-colors"
              aria-label="View product">
              <EyeIcon size={16} />
            </Link>
          </div>
        </div>
      </div>
      <div className={cn('p-3 sm:p-4', viewMode === 'list' && 'flex-grow')}>
        <span className="text-xs text-copy-lighter">{product.category}</span>
        <Link to={`/product/${product.id}`}>
          <h3 className="font-medium text-sm sm:text-base text-copy hover:text-primary transition-colors mb-1 line-clamp-2 h-10 sm:h-12">
            {product.name}
          </h3>
        </Link>
        <div className="flex items-center mb-2">
          <div className="flex text-yellow-400 text-xs">
            {'★'.repeat(Math.floor(product.rating))}
            {'☆'.repeat(5 - Math.floor(product.rating))}
          </div>
          <span className="text-xs text-copy-lighter ml-1">({product.reviewCount})</span>
        </div>
        <div className={cn('flex items-center justify-between', viewMode === 'list' && 'flex-grow md:flex-row-reverse md:justify-start md:space-x-4 md:space-x-reverse')}>
          <div>
            {salePrice && discountPercentage > 0 ? (
              <div className="flex items-center">
                <span className="font-bold text-primary mr-2 text-sm sm:text-base">
                  {formatCurrency(currentPrice)}
                </span>
                <span className="text-xs text-copy-lighter line-through">
                  {formatCurrency(basePrice)}
                </span>
                <span className="bg-error text-white text-xs font-medium px-2 py-1 rounded-full ml-2">
                  -{discountPercentage}%
                </span>
              </div>
            ) : (
              <span className="font-bold text-primary text-sm sm:text-base">
                {formatCurrency(currentPrice)}
              </span>
            )}
            {displayVariant && (
              <div className="text-xs text-copy-lighter mt-1">
                {displayVariant.name}
              </div>
            )}
          </div>
          {/* Show simple add to cart button on mobile for grid view */}
          <div className={cn(
            'flex items-center gap-2',
            viewMode === 'grid' && 'sm:hidden',
            viewMode === 'list' && 'hidden'
          )}>
            <button
              onClick={handleAddToCart}
              className="text-copy-lighter hover:text-white transition-colors bg-primary text-white px-3 py-1.5 rounded-md flex items-center"
              aria-label={isInCart ? "Remove from cart" : "Add to cart"}>
              {isInCart ? <CheckIcon size={16} /> : <ShoppingCartIcon size={16} />}
            </button>
            {/* Mobile subscription button */}
            {isAuthenticated && hasActiveSubscriptions && (
              <button
                onClick={handleAddToSubscription}
                className="text-white bg-green-600 hover:bg-green-700 px-2 sm:px-3 py-1.5 rounded-md flex items-center transition-colors flex-shrink-0"
                aria-label="Add to subscription">
                <CalendarIcon size={16} />
              </button>
            )}
          </div>
          <div className={cn(
            'hidden sm:flex items-center gap-2',
            viewMode === 'list' && 'md:order-1'
          )}>
            <button
              onClick={handleAddToCart}
              className="text-copy-lighter hover:text-white transition-colors bg-primary text-white px-4 py-2 rounded-md flex items-center"
              aria-label={isInCart ? "Remove from cart" : "Add to cart"}>
              {isInCart ? <CheckIcon size={18} /> : <ShoppingCartIcon size={18} />}
              {viewMode === 'list' && <span className="hidden md:inline ml-2">{isInCart ? "In Cart" : "Add to Cart"}</span>}
            </button>
            
            {/* Desktop subscription button */}
            {isAuthenticated && hasActiveSubscriptions && (
              <button
                onClick={handleAddToSubscription}
                className="flex items-center text-white bg-green-600 hover:bg-green-700 px-3 sm:px-4 py-2 rounded-md transition-colors flex-shrink-0"
                aria-label="Add to subscription">
                <CalendarIcon size={18} className="flex-shrink-0" />
                {viewMode === 'list' && <span className="hidden md:inline ml-2 whitespace-nowrap">Subscribe</span>}
              </button>
            )}
          </div>
          
          {/* Subscription Button */}
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