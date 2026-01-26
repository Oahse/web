import React, { useState } from 'react';
import { HeartIcon, ShoppingCartIcon, EyeIcon } from 'lucide-react';
import { useCart } from '../contexts/CartContext';
import { useWishlist } from '../contexts/WishlistContext';
import { toast } from 'react-hot-toast';
import { Link } from 'react-router-dom';

export const ProductCard = ({ product }: { product: any }) => {
  // ✅ Using useState for local state management
  const [isAddingToCart, setIsAddingToCart] = useState<boolean>(false);
  const [isAddingToWishlist, setIsAddingToWishlist] = useState<boolean>(false);
  const [selectedQuantity, setSelectedQuantity] = useState<number>(1);
  const [imageError, setImageError] = useState<boolean>(false);

  const { addItem: addToCart } = useCart();
  const { addItem: addToWishlist, isInWishlist } = useWishlist();

  const variant = product.variants?.[0] || product;
  const image = variant.primary_image?.url || variant.images?.[0]?.url || '/placeholder.jpg';
  const price = variant.current_price || variant.base_price;
  const salePrice = variant.sale_price;
  const isOnSale = salePrice && salePrice < price;
  const discount = isOnSale ? Math.round(((price - salePrice) / price) * 100) : 0;
  const isInStock = variant.stock > 0;
  const isWishlisted = isInWishlist(product.id, variant.id);

  // Handle adding to cart
  const handleAddToCart = async (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent navigation if this is inside a Link
    
    if (!isInStock) {
      toast.error('This item is currently out of stock');
      return;
    }

    setIsAddingToCart(true);

    try {
      const cartItem = {
        variant_id: variant.id,
        quantity: selectedQuantity,
        price_per_unit: isOnSale ? salePrice : price,
        variant: variant
      };

      await addToCart(cartItem);
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
        // Remove from wishlist logic would go here
        toast.info('Item is already in your wishlist');
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
      const target = e.target as HTMLImageElement;
      target.src = '/placeholder.jpg';
    }
  };

  // Handle quantity change
  const handleQuantityChange = (newQuantity: number) => {
    if (newQuantity < 1) return;
    if (newQuantity > variant.stock) {
      toast.error(`Only ${variant.stock} items available`);
      return;
    }
    setSelectedQuantity(newQuantity);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow group">
      {/* Image Container */}
      <div className="relative aspect-square overflow-hidden rounded-t-lg">
        <Link to={`/product/${product.id}`}>
          <img
            src={image}
            alt={product.name}
            className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
            onError={handleImageError}
          />
        </Link>
        
        {/* Sale Badge */}
        {isOnSale && (
          <div className="absolute top-2 left-2 bg-red-500 text-white px-2 py-1 rounded text-xs font-medium">
            -{discount}%
          </div>
        )}

        {/* Stock Status */}
        {!isInStock && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <span className="text-white font-medium">Out of Stock</span>
          </div>
        )}

        {/* Quick Actions */}
        <div className="absolute top-2 right-2 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleAddToWishlist}
            disabled={isAddingToWishlist}
            className={`p-2 rounded-full shadow-sm transition-colors ${
              isWishlisted 
                ? 'bg-red-500 text-white' 
                : 'bg-white/90 hover:bg-white text-gray-600 hover:text-red-500'
            } disabled:opacity-50`}
            title={isWishlisted ? 'In wishlist' : 'Add to wishlist'}
          >
            {isAddingToWishlist ? (
              <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <HeartIcon size={16} className={isWishlisted ? 'fill-current' : ''} />
            )}
          </button>

          <Link
            to={`/product/${product.id}`}
            className="p-2 bg-white/90 hover:bg-white text-gray-600 hover:text-primary rounded-full shadow-sm transition-colors"
            title="View details"
          >
            <EyeIcon size={16} />
          </Link>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <Link to={`/product/${product.id}`}>
          <h3 className="product-title text-base truncate mb-2 hover:text-primary transition-colors">
            {product.name}
          </h3>
        </Link>
        
        {/* Price */}
        <div className="flex items-center gap-2 mb-3">
          <span className="price text-lg">
            ${(isOnSale ? salePrice : price).toFixed(2)}
          </span>
          {isOnSale && (
            <span className="price text-sm text-gray-500 line-through">
              ${price.toFixed(2)}
            </span>
          )}
        </div>

        {/* Rating */}
        {product.rating_average > 0 && (
          <div className="flex items-center gap-1 mb-3 text-sm text-gray-600">
            <span>⭐</span>
            <span className="body-text">{product.rating_average.toFixed(1)}</span>
            <span className="body-text">({product.rating_count})</span>
          </div>
        )}

        {/* Quantity Selector (only if in stock) */}
        {isInStock && (
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Quantity
            </label>
            <select
              value={selectedQuantity}
              onChange={(e) => handleQuantityChange(parseInt(e.target.value))}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              {Array.from({ length: Math.min(variant.stock, 10) }, (_, i) => i + 1).map(num => (
                <option key={num} value={num}>{num}</option>
              ))}
            </select>
          </div>
        )}

        {/* Add to Cart Button */}
        <button
          onClick={handleAddToCart}
          disabled={!isInStock || isAddingToCart}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isAddingToCart ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <ShoppingCartIcon size={16} />
          )}
          <span className="button-text text-sm">
            {isAddingToCart ? 'Adding...' : isInStock ? 'Add to Cart' : 'Out of Stock'}
          </span>
        </button>

        {/* Stock info */}
        {isInStock && variant.stock <= 5 && (
          <p className="body-text text-xs text-orange-600 mt-2 text-center">
            Only {variant.stock} left!
          </p>
        )}
      </div>
    </div>
  );
};

export default ProductCard;