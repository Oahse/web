import React, { useState, useEffect } from 'react';
import { HeartIcon, ShoppingCartIcon, EyeIcon, CalendarIcon } from 'lucide-react';
import { useCart } from '../contexts/CartContext';
import { useWishlist } from '../contexts/WishlistContext';
import { useSubscription } from '../contexts/SubscriptionContext';
import { stockMonitor } from '../services/stockMonitoring';
import { toast } from 'react-hot-toast';
import { Link } from 'react-router-dom';
import { themeClasses, combineThemeClasses } from '../lib/themeClasses';

export const ProductCard = ({ product }: { product: any }) => {
  // ✅ Using useState for local state management
  const [isAddingToCart, setIsAddingToCart] = useState<boolean>(false);
  const [isAddingToSubscription, setIsAddingToSubscription] = useState<boolean>(false);
  const [isAddingToWishlist, setIsAddingToWishlist] = useState<boolean>(false);
  const [imageError, setImageError] = useState<boolean>(false);
  const [imageLoaded, setImageLoaded] = useState<boolean>(false);
  const [stockStatus, setStockStatus] = useState<any>(null);

  const { addItem: addToCart } = useCart();
  const { activeSubscription, addProductsToSubscription } = useSubscription();
  const { addItem: addToWishlist, isInWishlist } = useWishlist();

  const variant = product.variants?.[0] || product;
  const price = variant.current_price || variant.base_price;
  const salePrice = variant.sale_price;
  const isOnSale = salePrice && salePrice < price;
  const discount = isOnSale ? Math.round(((price - salePrice) / price) * 100) : 0;
  const isInStock = variant.stock > 0;
  const isWishlisted = isInWishlist(product.id, variant.id);

  // Initialize stock monitoring for this variant
  useEffect(() => {
    if (variant.id && variant.stock !== undefined) {
      // Set up stock thresholds
      stockMonitor.setStockThreshold(variant.id, {
        low_stock_threshold: 10,
        critical_threshold: 5,
        out_of_stock_threshold: 0,
        email_notifications_enabled: true
      });

      // Update current stock
      stockMonitor.updateStock(
        variant.id,
        variant.stock,
        product.name,
        variant.name
      );

      // Get stock status
      const status = stockMonitor.getStockStatus(variant.id);
      setStockStatus(status);
    }
  }, [variant.id, variant.stock, product.name, variant.name]);

  // Get primary image with proper fallback handling
  const getPrimaryImage = () => {
    if (imageError) {
      return '/placeholder-product.jpg';
    }

    // Check variant images first
    if (variant.images && variant.images.length > 0) {
      const primaryImage = variant.images.find((img: any) => img.is_primary);
      if (primaryImage?.url) {
        return primaryImage.url;
      }
      if (variant.images[0]?.url) {
        return variant.images[0].url;
      }
    }

    // Fallback to legacy image fields
    if (variant.primary_image?.url) {
      return variant.primary_image.url;
    }

    return '/placeholder-product.jpg';
  };

  // Handle adding to cart - automatically add 1 quantity
  const handleAddToCart = async (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent navigation if this is inside a Link
    
    if (!isInStock || stockStatus?.status === 'out_of_stock') {
      toast.error('This item is currently out of stock');
      return;
    }

    setIsAddingToCart(true);

    try {
      const cartItem = {
        variant_id: variant.id,
        quantity: 1, // Always add 1 item
      };

      await addToCart(cartItem);

      // Update stock monitoring after successful cart addition
      const newStock = variant.stock - 1;
      stockMonitor.updateStock(variant.id, newStock, product.name, variant.name);
      
      // Update local stock status
      const status = stockMonitor.getStockStatus(variant.id);
      setStockStatus(status);
      
    } catch (error: any) {
      // CartContext handles auth redirects and error messages
      console.error('Failed to add item to cart:', error);
    } finally {
      setIsAddingToCart(false);
    }
  };

  // Handle adding to Subscription - automatically add 1 quantity
  const handleAddToSubscription = async (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent navigation if this is inside a Link
    
    if (!isInStock || stockStatus?.status === 'out_of_stock') {
      toast.error('This item is currently out of stock');
      return;
    }

    if (!activeSubscription) {
      toast.error('You need an active subscription to add products');
      return;
    }

    setIsAddingToSubscription(true);

    try {
      await addProductsToSubscription(activeSubscription.id, [variant.id]);

      // Update stock monitoring after successful subscription addition
      const newStock = variant.stock - 1;
      stockMonitor.updateStock(variant.id, newStock, product.name, variant.name);
      
      // Update local stock status
      const status = stockMonitor.getStockStatus(variant.id);
      setStockStatus(status);
      
    } catch (error: any) {
      toast.error(error.message || 'Failed to add item to subscription');
    } finally {
      setIsAddingToSubscription(false);
    }
  };

  // Handle adding to wishlist
  const handleAddToWishlist = async (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent navigation if this is inside a Link
    
    setIsAddingToWishlist(true);

    try {
      if (isWishlisted) {
        toast('Item is already in your wishlist');
      } else {
        await addToWishlist(product.id, variant.id, 1);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to add item to wishlist');
    } finally {
      setIsAddingToWishlist(false);
    }
  };

  // Handle image error
  const handleImageError = () => {
    if (!imageError) {
      setImageError(true);
    }
  };

  // Handle image load
  const handleImageLoad = () => {
    setImageLoaded(true);
  };

  return (
    <div className={combineThemeClasses(
      themeClasses.card.base,
      themeClasses.border.default,
      themeClasses.shadow.sm,
      'hover:shadow-md transition-all duration-300 group overflow-hidden h-full flex flex-col'
    )}>
      {/* Image Container - Responsive aspect ratio */}
      <div className={combineThemeClasses(
        themeClasses.background.elevated,
        'relative aspect-[4/3] overflow-hidden'
      )}>
        <Link to={`/product/${product.id}`} className="block w-full h-full">
          {/* Image Loading Skeleton */}
          {!imageLoaded && (
            <div className={combineThemeClasses(
              themeClasses.background.surface,
              'absolute inset-0 animate-pulse flex items-center justify-center'
            )}>
              <div className={combineThemeClasses(
                themeClasses.loading.spinner,
                'w-4 h-4 sm:w-6 sm:h-6'
              )}></div>
            </div>
          )}
          
          <img
            src={getPrimaryImage()}
            alt={`${product.name} - ${variant.name}`}
            className={`w-full h-full object-cover transition-all duration-500 ${
              imageLoaded 
                ? 'opacity-100 group-hover:scale-105' 
                : 'opacity-0'
            }`}
            onError={handleImageError}
            onLoad={handleImageLoad}
            loading="lazy"
          />
        </Link>
        
        {/* Sale Badge - Responsive sizing */}
        {isOnSale && (
          <div className="absolute top-1 left-1 sm:top-1.5 sm:left-1.5 bg-red-500 text-white px-1 py-0.5 sm:px-1.5 sm:py-0.5 rounded text-xs font-semibold shadow-sm">
            -{discount}%
          </div>
        )}

        {/* Stock Status Badge - Responsive positioning */}
        {stockStatus && stockStatus.status !== 'in_stock' && (
          <div className={`absolute top-1 sm:top-1.5 ${isOnSale ? 'left-8 sm:left-12' : 'left-1 sm:left-1.5'} px-1 py-0.5 sm:px-1.5 sm:py-0.5 rounded text-xs font-semibold text-white shadow-sm ${
            stockStatus.status === 'out_of_stock' ? 'bg-red-500' :
            stockStatus.status === 'critical' ? 'bg-orange-500' : 'bg-yellow-500'
          }`}>
            {stockStatus.status === 'out_of_stock' ? 'Out' :
             stockStatus.status === 'critical' ? 'Low' : 'Limited'}
          </div>
        )}

        {/* Out of Stock Overlay */}
        {(!isInStock || stockStatus?.status === 'out_of_stock') && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <span className="text-white font-semibold text-xs px-2 py-1 bg-black/50 rounded">
              Out of Stock
            </span>
          </div>
        )}

        {/* Quick Actions - Responsive sizing and positioning */}
        <div className="absolute top-1 right-1 sm:top-1.5 sm:right-1.5 flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-all duration-300">
          {(isInStock && stockStatus?.status !== 'out_of_stock') && (
            <button
              onClick={handleAddToWishlist}
              disabled={isAddingToWishlist}
              className={combineThemeClasses(
                'p-1 sm:p-1.5 rounded-full shadow-md transition-all duration-200 transform hover:scale-110 disabled:opacity-50 disabled:cursor-not-allowed',
                isWishlisted 
                  ? 'bg-red-500 text-white' 
                  : combineThemeClasses(
                      themeClasses.background.surface,
                      themeClasses.text.secondary,
                      'hover:bg-white dark:hover:bg-gray-700 hover:text-red-500'
                    )
              )}
              title={isWishlisted ? 'In wishlist' : 'Add to wishlist'}
            >
              {isAddingToWishlist ? (
                <div className={combineThemeClasses(themeClasses.loading.spinner, 'w-2.5 h-2.5 sm:w-3 sm:h-3')}></div>
              ) : (
                <HeartIcon size={10} className={`sm:w-3 sm:h-3 ${isWishlisted ? 'fill-current' : ''}`} />
              )}
            </button>
          )}

          <Link
            to={`/product/${product.id}`}
            className={combineThemeClasses(
              themeClasses.background.surface,
              themeClasses.text.secondary,
              'hover:bg-white dark:hover:bg-gray-700 hover:text-primary',
              'p-1 sm:p-1.5 rounded-full shadow-md transition-all duration-200 transform hover:scale-110'
            )}
            title="View details"
          >
            <EyeIcon size={10} className="sm:w-3 sm:h-3" />
          </Link>
        </div>
      </div>

      {/* Content - Responsive padding and spacing */}
      <div className="p-2 sm:p-3 space-y-1.5 sm:space-y-2 flex-1 flex flex-col">
        <Link to={`/product/${product.id}`} className="flex-1">
          <h3 className={combineThemeClasses(
            themeClasses.text.heading,
            themeClasses.interactive.hover,
            'text-xs sm:text-sm font-medium line-clamp-2 transition-colors duration-200 leading-tight'
          )}>
            {product.name}
          </h3>
        </Link>
        
        {/* Variant name if different from product name */}
        {variant.name && variant.name !== product.name && (
          <p className={combineThemeClasses(themeClasses.text.muted, 'text-xs truncate')}>
            {variant.name}
          </p>
        )}
        
        {/* Price - Responsive sizing */}
        <div className="flex items-center gap-1 sm:gap-1.5">
          <span className={combineThemeClasses(
            themeClasses.text.heading,
            'text-sm sm:text-base font-semibold'
          )}>
            ${(isOnSale ? salePrice : price).toFixed(2)}
          </span>
          {isOnSale && (
            <span className={combineThemeClasses(themeClasses.text.muted, 'text-xs line-through')}>
              ${price.toFixed(2)}
            </span>
          )}
        </div>

        {/* Rating - Responsive and theme-aware */}
        {product.rating > 0 && (
          <div className="flex items-center gap-1">
            <div className="flex items-center">
              {[...Array(5)].map((_, i) => (
                <span
                  key={i}
                  className={`text-xs ${
                    i < Math.floor(product.rating)
                      ? 'text-yellow-400 dark:text-yellow-300'
                      : combineThemeClasses(themeClasses.text.muted)
                  }`}
                >
                  ★
                </span>
              ))}
            </div>
            <span className={combineThemeClasses(themeClasses.text.secondary, 'text-xs')}>
              {product.rating.toFixed(1)} ({product.review_count})
            </span>
          </div>
        )}

        {/* Stock Status - Theme-aware */}
        {/* {stockStatus && (
          <div className={`text-xs font-medium ${
            stockStatus.status === 'in_stock' ? 'text-green-600 dark:text-green-400' :
            stockStatus.status === 'low_stock' ? 'text-yellow-600 dark:text-yellow-400' :
            stockStatus.status === 'critical' ? 'text-orange-600 dark:text-orange-400' :
            stockStatus.status === 'out_of_stock' ? 'text-red-600 dark:text-red-400' :
            combineThemeClasses(themeClasses.text.muted)
          }`}>
            {stockStatus.message}
          </div>
        )} */}

        {/* Add to Cart Button - Fully responsive and theme-aware */}
        <button
          onClick={handleAddToCart}
          disabled={!isInStock || isAddingToCart || stockStatus?.status === 'out_of_stock'}
          className={combineThemeClasses(
            'w-full bg-primary-dark dark:bg-primary-light flex items-center justify-center gap-1 sm:gap-1.5 px-2 py-1.5 sm:py-2 rounded-md font-medium text-xs sm:text-sm transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]',
            themeClasses.interactive.disabled,
            isInStock && stockStatus?.status !== 'out_of_stock'
              ? combineThemeClasses(
                  themeClasses.background.primary,
                  themeClasses.text.inverse,
                  themeClasses.shadow.sm,
                  'hover:shadow-md hover:bg-primary-dark dark:hover:bg-primary-light'
                )
              : combineThemeClasses(
                  themeClasses.background.disabled,
                  themeClasses.text.muted,
                  'cursor-not-allowed'
                )
          )}
        >
          {isAddingToCart ? (
            <>
              <div className={combineThemeClasses(themeClasses.loading.spinner, 'w-3 h-3 border-current border-t-transparent')}></div>
              <span className="hidden sm:inline">Adding...</span>
              <span className="sm:hidden">...</span>
            </>
          ) : (
            <>
              <ShoppingCartIcon size={12} className="sm:w-3.5 sm:h-3.5" />
              <span className="hidden sm:inline">
                {!isInStock || stockStatus?.status === 'out_of_stock' ? 'Out of Stock' : 'Add to Cart'}
              </span>
              <span className="sm:hidden">
                {!isInStock || stockStatus?.status === 'out_of_stock' ? 'Out' : 'Add'}
              </span>
            </>
          )}
        </button>

        {/* Add to Subscription Button - Only show if user has active subscription */}
        {activeSubscription && (
          <button
            onClick={handleAddToSubscription}
            disabled={!isInStock || isAddingToSubscription || stockStatus?.status === 'out_of_stock'}
            className={combineThemeClasses(
              'w-full bg-primary-dark dark:bg-primary-light flex items-center justify-center gap-1 sm:gap-1.5 px-2 py-1.5 sm:py-2 rounded-md font-medium text-xs sm:text-sm transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]',
              themeClasses.interactive.disabled,
              isInStock && stockStatus?.status !== 'out_of_stock'
                ? combineThemeClasses(
                    'bg-secondary hover:bg-secondary-dark dark:bg-secondary-light dark:hover:bg-secondary',
                    themeClasses.text.inverse,
                    themeClasses.shadow.sm,
                    'hover:shadow-md'
                  )
                : combineThemeClasses(
                    themeClasses.background.disabled,
                    themeClasses.text.muted,
                    'cursor-not-allowed'
                  )
            )}
          >
            {isAddingToSubscription ? (
              <>
                <div className={combineThemeClasses(themeClasses.loading.spinner, 'w-3 h-3 border-current border-t-transparent')}></div>
                <span className="hidden sm:inline">Adding...</span>
                <span className="sm:hidden">...</span>
              </>
            ) : (
              <>
                <CalendarIcon size={12} className="sm:w-3.5 sm:h-3.5" />
                <span className="hidden sm:inline">
                  {!isInStock || stockStatus?.status === 'out_of_stock' ? 'Out of Stock' : 'Add to Subscription'}
                </span>
                <span className="sm:hidden">
                  {!isInStock || stockStatus?.status === 'out_of_stock' ? 'Out' : 'Subscribe'}
                </span>
              </>
            )}
          </button>
        )}

        {/* Additional stock info - Responsive */}
        {isInStock && stockStatus?.status === 'critical' && variant.stock && (
          <p className="text-xs text-orange-600 dark:text-orange-400 text-center font-medium">
            <span className="hidden sm:inline">Only {variant.stock} left!</span>
            <span className="sm:hidden">{variant.stock} left!</span>
          </p>
        )}
      </div>
    </div>
  );
};

export default ProductCard;