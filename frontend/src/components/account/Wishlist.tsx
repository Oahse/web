import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWishlist } from '../../store/WishlistContext';
import { useCart } from '../../store/CartContext';
import { useAuth } from '../../store/AuthContext';
import { 
  HeartIcon, 
  ShoppingCartIcon, 
  TrashIcon, 
  PlusIcon,
  PackageIcon,
  EditIcon,
  EyeIcon,
  ShareIcon
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { ConfirmationModal } from '../ui/ConfirmationModal';
import { ProductCard } from '../../components/product/ProductCard';
import { Product, ProductVariant } from '../../types';

interface WishlistItem {
  id: string;
  product_id: string;
  product?: Product;
  variant?: ProductVariant;
  variant_id?: string;
  quantity?: number;
  created_at: string;
}

interface WishlistProps {
  mode?: 'list' | 'manage';
  wishlistId?: string;
}

export const WishlistConsolidated: React.FC<WishlistProps> = ({ mode = 'list', wishlistId }) => {
  const navigate = useNavigate();
  const { defaultWishlist, removeItem, clearWishlist, addItem } = useWishlist();
  const { addItem: addToCart } = useCart();
  const { isAuthenticated } = useAuth();

  const [loading, setLoading] = useState(true);
  const [showRemoveModal, setShowRemoveModal] = useState(false);
  const [itemToRemove, setItemToRemove] = useState<string | null>(null);
  const [showClearModal, setShowClearModal] = useState(false);

  // Use items directly from defaultWishlist for real-time updates
  const items = defaultWishlist?.items || [];

  // Debug: Log items data to see what we're working with
  console.log('Wishlist items debug:', {
    itemsCount: items.length,
    items: items,
    defaultWishlist: defaultWishlist,
    hasDefaultWishlist: !!defaultWishlist,
    itemsKeys: items.map(item => ({
      id: item.id,
      hasProduct: !!item.product,
      hasVariant: !!item.variant,
      productId: item.product_id,
      variantId: item.variant_id,
      productKeys: item.product ? Object.keys(item.product) : [],
      variantKeys: item.variant ? Object.keys(item.variant) : []
    }))
  });

  useEffect(() => {
    // Set loading to false once we have defaultWishlist (even if empty)
    if (defaultWishlist !== undefined) {
      setLoading(false);
    }
  }, [defaultWishlist]);

  const handleAddToCart = async (item: WishlistItem) => {
    if (!isAuthenticated) {
      toast.error('Please log in to add items to cart');
      navigate('/login');
      return;
    }

    try {
      let variantId = item.variant_id;
      
      if (!variantId && item.product?.variants?.length) {
        variantId = item.product.variants[0].id;
      }

      if (!variantId) {
        toast.error('Product variant not found');
        return;
      }

      await addToCart({
        variant_id: String(variantId),
        quantity: item.quantity || 1,
      });
      
      toast.success(`${item.product?.name || 'Item'} added to cart`);
    } catch (error) {
      console.error('Failed to add to cart:', error);
      toast.error('Failed to add item to cart');
    }
  };

  const handleRemoveFromWishlist = async (itemId: string) => {
    if (!defaultWishlist) return;

    try {
      await removeItem(defaultWishlist.id, itemId);
      toast.success('Item removed from wishlist');
    } catch (error) {
      console.error('Failed to remove from wishlist:', error);
      toast.error('Failed to remove item');
    }
  };

  const handleClearWishlist = async () => {
    if (!defaultWishlist) return;

    try {
      await clearWishlist();
      setShowClearModal(false);
      toast.success('Wishlist cleared');
    } catch (error) {
      console.error('Failed to clear wishlist:', error);
      toast.error('Failed to clear wishlist');
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount || 0);
  };

  const getProductPrice = (product: Product) => {
    if (product.price) return formatCurrency(product.price);
    if (product.min_price !== undefined && product.max_price !== undefined) {
      if (product.min_price === product.max_price) {
        return formatCurrency(product.min_price);
      }
      return `${formatCurrency(product.min_price)} - ${formatCurrency(product.max_price)}`;
    }
    return 'Price not available';
  };

  const getVariantPrice = (variant: ProductVariant) => {
    const price = variant.current_price || variant.base_price || 0;
    return formatCurrency(price);
  };

  const getStockStatus = (variant: ProductVariant) => {
    const quantity = variant.inventory_quantity_available || variant.stock || 0;
    if (quantity === 0) return { text: 'Out of Stock', color: 'text-red-600' };
    if (quantity < 5) return { text: `Only ${quantity} left`, color: 'text-yellow-600' };
    return { text: 'In Stock', color: 'text-green-600' };
  };

  // Handle errors gracefully - show empty UI instead of error message
  if (!defaultWishlist && !loading) {
    return (
      <div className="text-center py-8 border border-dashed border-gray-300 dark:border-gray-700 rounded-lg">
        <HeartIcon size={48} className="mx-auto text-gray-400 mb-4" />
        <p className="text-gray-500 dark:text-gray-400 mb-3">
          Unable to load wishlist
        </p>
        <button 
          onClick={() => window.location.reload()} 
          className="text-primary hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        <p className="ml-4 text-gray-600 dark:text-gray-400">Loading wishlist...</p>
      </div>
    );
  }

  // List mode - show all wishlist items
  if (mode === 'list') {
    return (
      <div>
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-3 gap-3">
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-300 mt-1">
              {items.length} {items.length === 1 ? 'item' : 'items'} saved
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => navigate('/products')}
              className="flex items-center gap-2 px-3 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors text-xs"
            >
              <PlusIcon size={16} />
              Browse Products
            </button>
            {items.length > 0 && (
              <button
                onClick={() => setShowClearModal(true)}
                className="flex items-center gap-2 px-3 py-2 border border-red-600 text-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-xs"
              >
                <TrashIcon size={16} />
                Clear All
              </button>
            )}
          </div>
        </div>

        {/* Wishlist Items Grid */}
        {items.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
              <HeartIcon size={20} className="text-gray-500 dark:text-gray-400" />
            </div>
            <h2 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
              Your wishlist is empty
            </h2>
            <p className="text-xs text-gray-600 dark:text-gray-300 mb-3">
              Save items you like to your wishlist and they'll appear here.
            </p>
            <div className="flex gap-2 justify-center">
              <button
                onClick={() => navigate('/products')}
                className="inline-flex items-center gap-2 px-3 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors text-xs"
              >
                <PlusIcon size={16} />
                Browse Products
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-3 sm:gap-4 lg:gap-6">
            {items.map((item) => {
              const product = item.product;
              const selectedVariant = item.variant || product?.variants?.find(v => v.id === item.variant_id) || product?.variants?.[0];

              // If no product data, show a simple placeholder
              if (!product) {
                return (
                  <div key={item.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 border border-gray-200 dark:border-gray-700">
                    <div className="aspect-square bg-gray-100 dark:bg-gray-700 rounded-lg mb-3 flex items-center justify-center">
                      <PackageIcon size={24} className="text-gray-400" />
                    </div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-1 line-clamp-2">
                      Loading product...
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Product ID: {item.product_id}
                    </p>
                    <div className="mt-3">
                      <button
                        onClick={() => handleRemoveFromWishlist(item.id)}
                        className="w-full flex items-center justify-center gap-1 px-2 py-1 text-xs text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                      >
                        <TrashIcon size={12} />
                        Remove
                      </button>
                    </div>
                  </div>
                );
              }

              return (
                <ProductCard
                  key={item.id}
                  product={product}
                  selectedVariant={selectedVariant}
                  className=""
                  showSubscriptionButton={false}
                  subscriptionId={null}
                  wishlistMode={true}
                />
              );
            })}
          </div>
        )}

        {/* Clear Wishlist Modal */}
        {showClearModal && (
          <ConfirmationModal
            isOpen={true}
            onClose={() => setShowClearModal(false)}
            onConfirm={handleClearWishlist}
            title="Clear Wishlist"
            message="Are you sure you want to remove all items from your wishlist?"
            confirmText="Clear All"
            cancelText="Cancel"
          />
        )}
      </div>
    );
  }

  // Manage mode - show detailed wishlist management
  return (
    <div className="p-4 sm:p-6">
      <div className="text-center">
        <p>Wishlist management view would be implemented here</p>
        <button 
          onClick={() => navigate('/account/wishlist')}
          className="mt-4 text-primary hover:underline"
        >
          Back to Wishlist
        </button>
      </div>
    </div>
  );
};

export default WishlistConsolidated;

// Simple wrapper for Account page sidebar layout
export const Wishlist = () => {
  return <WishlistConsolidated mode="list" />;
};
