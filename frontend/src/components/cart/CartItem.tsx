import React, { useState } from 'react';
import { MinusIcon, PlusIcon, TrashIcon } from 'lucide-react';
import { useCart } from '../../contexts/CartContext';
import { toast } from 'react-hot-toast';

interface CartItemProps {
  item: {
    id: string;
    variant_id: string;
    quantity: number;
    price_per_unit: number;
    total_price: number;
    variant: {
      id: string;
      name: string;
      product_name?: string;
      sku: string;
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
  onQuantityChange?: (itemId: string, newQuantity: number) => void;
  onRemove?: (itemId: string) => void;
}

export const CartItem: React.FC<CartItemProps> = ({ 
  item, 
  onQuantityChange, 
  onRemove 
}) => {
  // ✅ Using useState for local state management
  const [quantity, setQuantity] = useState<number>(item.quantity);
  const [isUpdating, setIsUpdating] = useState<boolean>(false);
  const [isRemoving, setIsRemoving] = useState<boolean>(false);

  const { updateQuantity, removeItem } = useCart();

  // Get primary image or first available image
  const getItemImage = () => {
    if (!item.variant.images || item.variant.images.length === 0) {
      return '/placeholder-product.jpg';
    }
    
    const primaryImage = item.variant.images.find(img => img.is_primary);
    return primaryImage?.url || item.variant.images[0]?.url || '/placeholder-product.jpg';
  };

  // Format variant attributes for display
  const getVariantDescription = () => {
    if (!item.variant.attributes || item.variant.attributes.length === 0) {
      return item.variant.name;
    }
    
    const attributes = item.variant.attributes
      .map(attr => `${attr.name}: ${attr.value}`)
      .join(', ');
    
    return `${item.variant.name} (${attributes})`;
  };

  // Handle quantity increase
  const handleIncrease = async () => {
    const newQuantity = quantity + 1;
    
    // Check stock availability
    if (newQuantity > item.variant.stock) {
      toast.error(`Only ${item.variant.stock} items available in stock`);
      return;
    }

    // Optimistic update
    setQuantity(newQuantity);
    setIsUpdating(true);

    try {
      await updateQuantity(item.id, newQuantity);
      
      // Notify parent component
      if (onQuantityChange) {
        onQuantityChange(item.id, newQuantity);
      }
    } catch (error: any) {
      // Revert optimistic update on error
      setQuantity(quantity);
      toast.error(error.message || 'Failed to update quantity');
    } finally {
      setIsUpdating(false);
    }
  };

  // Handle quantity decrease
  const handleDecrease = async () => {
    if (quantity <= 1) {
      // If quantity would become 0, remove the item instead
      handleRemove();
      return;
    }

    const newQuantity = quantity - 1;
    
    // Optimistic update
    setQuantity(newQuantity);
    setIsUpdating(true);

    try {
      await updateQuantity(item.id, newQuantity);
      
      // Notify parent component
      if (onQuantityChange) {
        onQuantityChange(item.id, newQuantity);
      }
    } catch (error: any) {
      // Revert optimistic update on error
      setQuantity(quantity);
      toast.error(error.message || 'Failed to update quantity');
    } finally {
      setIsUpdating(false);
    }
  };

  // Handle direct quantity input
  const handleQuantityInput = async (newQuantity: number) => {
    if (newQuantity < 1) {
      handleRemove();
      return;
    }

    if (newQuantity > item.variant.stock) {
      toast.error(`Only ${item.variant.stock} items available in stock`);
      return;
    }

    // Optimistic update
    const previousQuantity = quantity;
    setQuantity(newQuantity);
    setIsUpdating(true);

    try {
      await updateQuantity(item.id, newQuantity);
      
      // Notify parent component
      if (onQuantityChange) {
        onQuantityChange(item.id, newQuantity);
      }
    } catch (error: any) {
      // Revert optimistic update on error
      setQuantity(previousQuantity);
      toast.error(error.message || 'Failed to update quantity');
    } finally {
      setIsUpdating(false);
    }
  };

  // Handle item removal
  const handleRemove = async () => {
    setIsRemoving(true);

    try {
      await removeItem(item.id);
      
      // Notify parent component
      if (onRemove) {
        onRemove(item.id);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to remove item');
      setIsRemoving(false);
    }
  };

  // Calculate total price based on current quantity
  const totalPrice = quantity * item.price_per_unit;

  return (
    <div className={`flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-lg ${isRemoving ? 'opacity-50' : ''}`}>
      {/* Product Image */}
      <div className="flex-shrink-0">
        <img
          src={getItemImage()}
          alt={item.variant.product_name || item.variant.name}
          className="w-16 h-16 object-cover rounded-lg border border-gray-200"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = '/placeholder-product.jpg';
          }}
        />
      </div>

      {/* Product Details */}
      <div className="flex-grow min-w-0">
        <h3 className="product-title text-sm font-medium text-gray-900 truncate">
          {item.variant.product_name || item.variant.name}
        </h3>
        <p className="body-text text-xs text-gray-500 mt-1">
          {getVariantDescription()}
        </p>
        <p className="body-text text-xs text-gray-500">
          SKU: {item.variant.sku}
        </p>
        
        {/* Stock warning */}
        {item.variant.stock <= 5 && (
          <p className="body-text text-xs text-orange-600 mt-1">
            Only {item.variant.stock} left in stock
          </p>
        )}
      </div>

      {/* Quantity Controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleDecrease}
          disabled={isUpdating || isRemoving}
          className="p-1 rounded-md border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          title={quantity <= 1 ? 'Remove item' : 'Decrease quantity'}
        >
          <MinusIcon size={14} />
        </button>
        
        <input
          type="number"
          min="1"
          max={item.variant.stock}
          value={quantity}
          onChange={(e) => {
            const newQuantity = parseInt(e.target.value) || 1;
            handleQuantityInput(newQuantity);
          }}
          disabled={isUpdating || isRemoving}
          className="w-16 px-2 py-1 text-center border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50"
        />
        
        <button
          onClick={handleIncrease}
          disabled={isUpdating || isRemoving || quantity >= item.variant.stock}
          className="p-1 rounded-md border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Increase quantity"
        >
          <PlusIcon size={14} />
        </button>
      </div>

      {/* Price */}
      <div className="text-right min-w-0">
        <div className="price text-sm font-medium text-gray-900">
          ${totalPrice.toFixed(2)}
        </div>
        <div className="body-text text-xs text-gray-500">
          ${item.price_per_unit.toFixed(2)} each
        </div>
      </div>

      {/* Remove Button */}
      <button
        onClick={handleRemove}
        disabled={isRemoving}
        className="p-2 text-red-500 hover:bg-red-50 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
        title="Remove item"
      >
        <TrashIcon size={16} />
      </button>

      {/* Loading overlay */}
      {(isUpdating || isRemoving) && (
        <div className="absolute inset-0 bg-white/50 flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}
    </div>
  );
};