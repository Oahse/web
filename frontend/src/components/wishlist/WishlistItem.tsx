import React, { useState } from 'react';
import { HeartIcon, ShoppingCartIcon, TrashIcon } from 'lucide-react';
import { useWishlist } from '../../contexts/WishlistContext';
import { useCart } from '../../contexts/CartContext';
import { toast } from 'react-hot-toast';

interface WishlistItemProps {
  item: {
    id: string;
    product_id: string;
    variant_id?: string;
    quantity: number;
    wishlist_id: string;
    added_at: string;
    product?: {
      id: string;
      name: string;
      description?: string;
      category?: {
        name: string;
      };
    };
    variant?: {
      id: string;
      name: string;
      sku: string;
      base_price: number;
      sale_price?: number;
      stock: number;
      images?: Array<{
        url: string;
        alt_text?: string;
        is_primary?: boolean;
      }>;
      attributes?: Array<{
        name: string;
        value: string;
      }>;
    };
  };
  onRemove?: (itemId: string) => void;
  onAddToCart?: (itemId: string) => void;
}

export const WishlistItem: React.FC<WishlistItemProps> = ({ 
  item, 
  onRemove, 
  onAddToCart 
}) => {
  // ✅ Using useState for local state management
  const [isRemoving, setIsRemoving] = useState<boolean>(false);
  const [isAddingToCart, setIsAddingToCart] = useState<boolean>(false);
  const [quantity, setQuantity] = useState<number>(item.quantity || 1);

  const { removeItem } = useWishlist();
  const { addItem: addToCart } = useCart();

  // Get primary image or first available image
  const getItemImage = () => {
    if (!item.variant?.images || item.variant.images.length === 0) {
      return '/placeholder-product.jpg';
    }
    
    const primaryImage = item.variant.images.find(img => img.is_primary);
    return primaryImage?.url || item.variant.images[0]?.url || '/placeholder-product.jpg';
  };

  // Get current price (sale price if available, otherwise base price)
  const getCurrentPrice = () => {
    if (!item.variant) return 0;
    return item.variant.sale_price || item.variant.base_price;
  };

  // Check if item is on sale
  const isOnSale = () => {
    return item.variant?.sale_price && item.variant.sale_price < item.variant.base_price;
  };

  // Calculate discount percentage
  const getDiscountPercentage = () => {
    if (!isOnSale() || !item.variant) return 0;
    const discount = item.variant.base_price - (item.variant.sale_price || 0);
    return Math.round((discount / item.variant.base_price) * 100);
  };

  // Format variant attributes for display
  const getVariantDescription = () => {
    if (!item.variant?.attributes || item.variant.attributes.length === 0) {
      return item.variant?.name || '';
    }
    
    const attributes = item.variant.attributes
      .map(attr => `${attr.name}: ${attr.value}`)
      .join(', ');
    
    return `${item.variant.name} (${attributes})`;
  };

  // Check if item is in stock
  const isInStock = () => {
    return item.variant ? item.variant.stock > 0 : false;
  };

  // Handle removing item from wishlist
  const handleRemove = async () => {
    setIsRemoving(true);

    try {
      await removeItem(item.wishlist_id, item.id);
      
      // Notify parent component
      if (onRemove) {
        onRemove(item.id);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to remove item from wishlist');
      setIsRemoving(false);
    }
  };

  // Handle adding item to cart
  const handleAddToCart = async () => {
    if (!item.variant) {
      toast.error('Product variant not available');
      return;
    }

    if (!isInStock()) {
      toast.error('This item is currently out of stock');
      return;
    }

    setIsAddingToCart(true);

    try {
      const cartItem = {
        variant_id: item.variant.id,
        quantity: quantity,
        price_per_unit: getCurrentPrice(),
        variant: item.variant
      };

      await addToCart(cartItem);
      
      // Notify parent component
      if (onAddToCart) {
        onAddToCart(item.id);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to add item to cart');
    } finally {
      setIsAddingToCart(false);
    }
  };

  // Handle quantity change
  const handleQuantityChange = (newQuantity: number) => {
    if (newQuantity < 1) return;
    if (item.variant && newQuantity > item.variant.stock) {
      toast.error(`Only ${item.variant.stock} items available in stock`);
      return;
    }
    setQuantity(newQuantity);
  };

  return (
    <div className={`bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow ${isRemoving ? 'opacity-50' : ''}`}>
      {/* Product Image */}
      <div className="relative aspect-square">
        <img
          src={getItemImage()}
          alt={item.product?.name || item.variant?.name || 'Product'}
          className="w-full h-full object-cover"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = '/placeholder-product.jpg';
          }}
        />
        
        {/* Sale badge */}
        {isOnSale() && (
          <div className="absolute top-2 left-2 bg-red-500 text-white px-2 py-1 rounded text-xs font-medium">
            -{getDiscountPercentage()}%
          </div>
        )}

        {/* Stock status */}
        {!isInStock() && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <span className="text-white font-medium">Out of Stock</span>
          </div>
        )}

        {/* Remove button */}
        <button
          onClick={handleRemove}
          disabled={isRemoving}
          className="absolute top-2 right-2 p-2 bg-white/90 hover:bg-white rounded-full shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          title="Remove from wishlist"
        >
          <HeartIcon size={16} className="text-red-500 fill-current" />
        </button>
      </div>

      {/* Product Details */}
      <div className="p-4">
        <div className="mb-2">
          <h3 className="product-title text-sm font-medium text-gray-900 line-clamp-2">
            {item.product?.name || 'Unknown Product'}
          </h3>
          
          {item.variant && (
            <p className="body-text text-xs text-gray-500 mt-1">
              {getVariantDescription()}
            </p>
          )}
          
          {item.product?.category && (
            <p className="body-text text-xs text-gray-400 mt-1">
              {item.product.category.name}
            </p>
          )}
        </div>

        {/* Price */}
        {item.variant && (
          <div className="mb-3">
            <div className="flex items-center gap-2">
              <span className="price text-lg font-semibold text-gray-900">
                ${getCurrentPrice().toFixed(2)}
              </span>
              {isOnSale() && (
                <span className="price text-sm text-gray-500 line-through">
                  ${item.variant.base_price.toFixed(2)}
                </span>
              )}
            </div>
            
            {/* Stock info */}
            <div className="mt-1">
              {isInStock() ? (
                <span className="body-text text-xs text-green-600">
                  {item.variant.stock} in stock
                </span>
              ) : (
                <span className="body-text text-xs text-red-600">
                  Out of stock
                </span>
              )}
            </div>
          </div>
        )}

        {/* Quantity selector (only if in stock) */}
        {isInStock() && item.variant && (
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Quantity
            </label>
            <select
              value={quantity}
              onChange={(e) => handleQuantityChange(parseInt(e.target.value))}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              {Array.from({ length: Math.min(item.variant.stock, 10) }, (_, i) => i + 1).map(num => (
                <option key={num} value={num}>{num}</option>
              ))}
            </select>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleAddToCart}
            disabled={!isInStock() || isAddingToCart || isRemoving}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isAddingToCart ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <ShoppingCartIcon size={16} />
            )}
            <span className="button-text text-sm">
              {isAddingToCart ? 'Adding...' : 'Add to Cart'}
            </span>
          </button>

          <button
            onClick={handleRemove}
            disabled={isRemoving}
            className="p-2 text-red-500 hover:bg-red-50 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Remove from wishlist"
          >
            {isRemoving ? (
              <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <TrashIcon size={16} />
            )}
          </button>
        </div>

        {/* Added date */}
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="body-text text-xs text-gray-400">
            Added {new Date(item.added_at).toLocaleDateString()}
          </p>
        </div>
      </div>
    </div>
  );
};