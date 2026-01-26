import React, { useState } from 'react';
import { useCart } from '../hooks/useCart';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'react-hot-toast';
import { ShoppingCart, Plus, Check } from 'lucide-react';

interface OptimisticCartButtonProps {
  variant: any;
  quantity?: number;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showQuantity?: boolean;
  disabled?: boolean;
}

const OptimisticCartButton: React.FC<OptimisticCartButtonProps> = ({
  variant,
  quantity = 1,
  className = '',
  size = 'md',
  showQuantity = false,
  disabled = false,
}) => {
  const { user } = useAuth();
  const { addItem, isOptimistic, getItemQuantity, isInCart } = useCart();
  const [isAdding, setIsAdding] = useState(false);
  const [justAdded, setJustAdded] = useState(false);

  const currentQuantity = getItemQuantity(variant.id);
  const inCart = isInCart(variant.id);

  const handleAddToCart = async () => {
    if (!user) {
      toast.error('Please log in to add items to cart');
      return;
    }

    if (!variant || disabled) return;

    setIsAdding(true);
    
    try {
      await addItem({
        variant_id: variant.id,
        quantity,
        price_per_unit: variant.current_price,
        variant,
      });
      
      setJustAdded(true);
      setTimeout(() => setJustAdded(false), 2000);
    } catch (error: any) {
      toast.error(error.message || 'Failed to add item to cart');
    } finally {
      setIsAdding(false);
    }
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  const baseClasses = `
    inline-flex items-center justify-center gap-2 font-medium rounded-lg
    transition-all duration-200 relative overflow-hidden
    ${sizeClasses[size]}
    ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-md'}
  `;

  // Show different states
  if (justAdded) {
    return (
      <button
        className={`${baseClasses} bg-green-600 text-white ${className}`}
        disabled
      >
        <Check className={iconSizes[size]} />
        Added!
      </button>
    );
  }

  if (isAdding || isOptimistic) {
    return (
      <button
        className={`${baseClasses} bg-blue-500 text-white ${className}`}
        disabled
      >
        <div className={`border-2 border-white border-t-transparent rounded-full animate-spin ${iconSizes[size]}`}></div>
        Adding...
      </button>
    );
  }

  if (inCart && showQuantity) {
    return (
      <button
        onClick={handleAddToCart}
        disabled={disabled}
        className={`${baseClasses} bg-blue-600 text-white hover:bg-blue-700 ${className}`}
      >
        <ShoppingCart className={iconSizes[size]} />
        In Cart ({currentQuantity}) - Add More
      </button>
    );
  }

  return (
    <button
      onClick={handleAddToCart}
      disabled={disabled}
      className={`${baseClasses} bg-blue-600 text-white hover:bg-blue-700 ${className}`}
    >
      <Plus className={iconSizes[size]} />
      {inCart ? 'Add More' : 'Add to Cart'}
    </button>
  );
};

export default OptimisticCartButton;