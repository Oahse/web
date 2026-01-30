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
import { ProductVariantModal } from '../ui/ProductVariantModal';
import { ConfirmationModal } from '../ui/ConfirmationModal';
import { ProductCard } from '../product/ProductCard';
import { Product, ProductVariant } from '../../types';

interface WishlistItem {
  id: string;
  product_id: string;
  product?: Product;
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

  const [items, setItems] = useState<WishlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showProductModal, setShowProductModal] = useState(false);
  const [selectedVariants, setSelectedVariants] = useState<string[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showRemoveModal, setShowRemoveModal] = useState(false);
  const [itemToRemove, setItemToRemove] = useState<string | null>(null);
  const [showClearModal, setShowClearModal] = useState(false);

  useEffect(() => {
    if (defaultWishlist) {
      setItems(defaultWishlist.items || []);
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
      setItems(prev => prev.filter(item => item.id !== itemId));
      toast.success('Item removed from wishlist');
    } catch (error) {
      console.error('Failed to remove from wishlist:', error);
      toast.error('Failed to remove item');
    }
  };

  const handleAddProducts = async (variantIds: string[]) => {
    if (!defaultWishlist || variantIds.length === 0) return;

    try {
      for (const variantId of variantIds) {
        await addItem(defaultWishlist.id, variantId, 1);
      }
      
      setShowProductModal(false);
      setShowAddModal(false);
      setSelectedVariants([]);
      toast.success(`${variantIds.length} item${variantIds.length !== 1 ? 's' : ''} added to wishlist`);
      
      if (defaultWishlist) {
        setItems(defaultWishlist.items || []);
      }
    } catch (error) {
      console.error('Failed to add to wishlist:', error);
      toast.error('Failed to add items to wishlist');
    }
  };

  const handleClearWishlist = async () => {
    if (!defaultWishlist) return;

    try {
      await clearWishlist();
      setItems([]);
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
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">My Wishlist</h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {items.length} {items.length === 1 ? 'item' : 'items'} saved
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => {
                setSelectedVariants([]);
                setShowAddModal(true);
                setShowProductModal(true);
              }}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
            >
              <PlusIcon size={20} />
              Browse Products
            </button>
            {items.length > 0 && (
              <button
                onClick={() => setShowClearModal(true)}
                className="flex items-center gap-2 px-4 py-2 border border-red-600 text-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              >
                <TrashIcon size={20} />
                Clear All
              </button>
            )}
          </div>
        </div>

        {/* Wishlist Items Grid */}
        {items.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
              <HeartIcon size={24} className="text-gray-500 dark:text-gray-400" />
            </div>
            <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Your wishlist is empty
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Save items you like to your wishlist and they'll appear here.
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => {
                  setSelectedVariants([]);
                  setShowAddModal(true);
                  setShowProductModal(true);
                }}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
              >
                <PlusIcon size={20} />
                Browse Products
              </button>
              <button
                onClick={() => navigate('/products')}
                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <PackageIcon size={20} />
                Browse Products
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-3 sm:gap-4 lg:gap-6">
            {items.map((item) => {
              const product = item.product;
              const selectedVariant = product?.variants?.find(v => v.id === item.variant_id) || product?.variants?.[0];

              return (
                <ProductCard
                  key={item.id}
                  product={product}
                  selectedVariant={selectedVariant}
                  className="w-full"
                  showSubscriptionButton={false}
                  subscriptionId={null}
                />
              );
            })}
          </div>
        )}

        {/* Product Variant Modal */}
        <ProductVariantModal
          isOpen={showProductModal}
          onClose={() => {
            setShowProductModal(false);
            setSelectedVariants([]);
          }}
          onSelectionChange={(variants) => {
            setSelectedVariants(variants);
          }}
          selectedVariants={selectedVariants}
          multiSelect={true}
          title="Add Items to Wishlist"
        />

        {/* Confirmation Modals */}
        {showAddModal && (
          <ConfirmationModal
            isOpen={true}
            onClose={() => {
              setShowAddModal(false);
              setShowProductModal(false);
              setSelectedVariants([]);
            }}
            onConfirm={() => handleAddProducts(selectedVariants)}
            title="Add to Wishlist"
            message={`Are you sure you want to add ${selectedVariants.length} item${selectedVariants.length !== 1 ? 's' : ''} to your wishlist?`}
            confirmText="Add Items"
            cancelText="Cancel"
          />
        )}

        {showRemoveModal && itemToRemove && (
          <ConfirmationModal
            isOpen={true}
            onClose={() => {
              setShowRemoveModal(false);
              setItemToRemove(null);
            }}
            onConfirm={async () => {
              if (itemToRemove) {
                await handleRemoveFromWishlist(itemToRemove);
              }
            }}
            title="Remove from Wishlist"
            message="Are you sure you want to remove this item from your wishlist?"
            confirmText="Remove"
            cancelText="Cancel"
          />
        )}

        {showClearModal && (
          <ConfirmationModal
            isOpen={true}
            onClose={() => setShowClearModal(false)}
            onConfirm={async () => {
              if (defaultWishlist) {
                try {
                  await clearWishlist(defaultWishlist.id);
                  setItems([]);
                  toast.success('Wishlist cleared');
                } catch (error) {
                  console.error('Failed to clear wishlist:', error);
                  toast.error('Failed to clear wishlist');
                }
              }
            }}
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
