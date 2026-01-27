import React, { useState, useEffect } from 'react';
import { HeartIcon, ShoppingCartIcon, EyeIcon } from 'lucide-react';
import { useCart } from '../contexts/CartContext';
import { useWishlist } from '../contexts/WishlistContext';
import { stockMonitor } from '../services/stockMonitoring';
import { toast } from 'react-hot-toast';
import { Link } from 'react-router-dom';

export const ProductCard = ({ product }: { product: any }) => {
  // ✅ Using useState for local state management
  const [isAddingToCart, setIsAddingToCart] = useState<boolean>(false);
  const [isAddingToWishlist, setIsAddingToWishlist] = useState<boolean>(false);
  const [imageError, setImageError] = useState<boolean>(false);
  const [imageLoaded, setImageLoaded] = useState<boolean>(false);
  const [stockStatus, setStockStatus] = useState<any>(null);

  const { addItem: addToCart } = useCart();
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
      toast.error(error.message || 'Failed to add item to cart');
    } finally {
      setIsAddingToCart(false);
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
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    if (!imageError) {
      setImageError(true);
    }
  };

  // Handle image load
  const handleImageLoad = () => {
    setImageLoaded(true);
  };

  // Handle quantity change - removed since we don't need quantity selector

  // Get stock status styling
  const getStockStatusStyle = () => {
    if (!stockStatus) return '';
    
    const styles: Record<string, string> = {
      in_stock: 'text-green-600',
      low_stock: 'text-yellow-600',
      critical: 'text-orange-600',
      out_of_stock: 'text-red-600'
    };
    
    return styles[stockStatus.status] || 'text-gray-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-all duration-300 group overflow-hidden h-full flex flex-col">
      {/* Image Container - Smaller aspect ratio */}
      <div className="relative aspect-[4/3] overflow-hidden bg-gray-100">
        <Link to={`/product/${product.id}`} className="block w-full h-full">
          {/* Image Loading Skeleton */}
          {!imageLoaded && (
            <div className="absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-gray-300 border-t-transparent rounded-full animate-spin"></div>
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
        
        {/* Sale Badge */}
        {isOnSale && (
          <div className="absolute top-1.5 left-1.5 bg-red-500 text-white px-1.5 py-0.5 rounded text-xs font-semibold shadow-sm">
            -{discount}%
          </div>
        )}

        {/* Stock Status Badge */}
        {stockStatus && stockStatus.status !== 'in_stock' && (
          <div className={`absolute top-1.5 ${isOnSale ? 'left-12' : 'left-1.5'} px-1.5 py-0.5 rounded text-xs font-semibold text-white shadow-sm ${
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

        {/* Quick Actions - Smaller and positioned better */}
        <div className="absolute top-1.5 right-1.5 flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-all duration-300">
          {(isInStock && stockStatus?.status !== 'out_of_stock') && (
            <button
              onClick={handleAddToWishlist}
              disabled={isAddingToWishlist}
              className={`p-1.5 rounded-full shadow-md transition-all duration-200 transform hover:scale-110 ${
                isWishlisted 
                  ? 'bg-red-500 text-white' 
                  : 'bg-white/90 hover:bg-white text-gray-600 hover:text-red-500'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              title={isWishlisted ? 'In wishlist' : 'Add to wishlist'}
            >
              {isAddingToWishlist ? (
                <div className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <HeartIcon size={12} className={isWishlisted ? 'fill-current' : ''} />
              )}
            </button>
          )}

          <Link
            to={`/product/${product.id}`}
            className="p-1.5 bg-white/90 hover:bg-white text-gray-600 hover:text-primary rounded-full shadow-md transition-all duration-200 transform hover:scale-110"
            title="View details"
          >
            <EyeIcon size={12} />
          </Link>
        </div>
      </div>

      {/* Content - More compact */}
      <div className="p-2 sm:p-3 space-y-2 flex-1 flex flex-col">
        <Link to={`/product/${product.id}`} className="flex-1">
          <h3 className="text-xs sm:text-sm font-medium line-clamp-2 hover:text-primary transition-colors duration-200 leading-tight">
            {product.name}
          </h3>
        </Link>
        
        {/* Variant name if different from product name */}
        {variant.name && variant.name !== product.name && (
          <p className="text-xs text-gray-500 truncate">
            {variant.name}
          </p>
        )}
        
        {/* Price */}
        <div className="flex items-center gap-1.5">
          <span className="text-sm sm:text-base font-semibold text-gray-900">
            ${(isOnSale ? salePrice : price).toFixed(2)}
          </span>
          {isOnSale && (
            <span className="text-xs text-gray-500 line-through">
              ${price.toFixed(2)}
            </span>
          )}
        </div>

        {/* Rating - More compact */}
        {product.rating > 0 && (
          <div className="flex items-center gap-1">
            <div className="flex items-center">
              {[...Array(5)].map((_, i) => (
                <span
                  key={i}
                  className={`text-xs ${
                    i < Math.floor(product.rating)
                      ? 'text-yellow-400'
                      : 'text-gray-300'
                  }`}
                >
                  ★
                </span>
              ))}
            </div>
            <span className="text-xs text-gray-600">
              {product.rating.toFixed(1)} ({product.review_count})
            </span>
          </div>
        )}

        {/* Stock Status */}
        {stockStatus && (
          <div className={`text-xs font-medium ${getStockStatusStyle()}`}>
            {stockStatus.message}
          </div>
        )}

        {/* Add to Cart Button - Compact */}
        <button
          onClick={handleAddToCart}
          disabled={!isInStock || isAddingToCart || stockStatus?.status === 'out_of_stock'}
          className={`w-full flex items-center justify-center gap-1.5 px-2 py-1.5 sm:py-2 rounded-md font-medium text-xs sm:text-sm transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] ${
            isInStock && stockStatus?.status !== 'out_of_stock'
              ? 'bg-primary text-white hover:bg-primary-dark shadow-sm hover:shadow-md'
              : 'bg-gray-100 text-gray-500 cursor-not-allowed'
          } disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none`}
        >
          {isAddingToCart ? (
            <>
              <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Adding...</span>
            </>
          ) : (
            <>
              <ShoppingCartIcon size={14} />
              <span>
                {!isInStock || stockStatus?.status === 'out_of_stock' ? 'Out of Stock' : 'Add to Cart'}
              </span>
            </>
          )}
        </button>

        {/* Additional stock info */}
        {isInStock && stockStatus?.status === 'critical' && (
          <p className="text-xs text-orange-600 text-center font-medium">
            Only {variant.stock} left!
          </p>
        )}
      </div>
    </div>
  );
};

export default ProductCard;