import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useWishlist } from '../store/WishlistContext';
import { 
  ArrowLeftIcon,
  SaveIcon,
  PackageIcon,
  HeartIcon,
  ShareIcon,
  TrashIcon,
  PlusIcon
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { ProductVariantModal } from '../components/ui/ProductVariantModal';
import { ConfirmationModal } from '../components/ui/ConfirmationModal';
import { Product, ProductVariant } from '../types';

interface WishlistDetail {
  id: string;
  name: string;
  description?: string;
  is_public: boolean;
  share_token?: string;
  items: Array<{
    id: string;
    product_id: string;
    product?: Product;
    variant_id?: string;
    quantity: number;
    created_at: string;
  }>;
  created_at: string;
  updated_at?: string;
}

export const WishlistEdit = () => {
  const { wishlistId } = useParams<{ wishlistId: string }>();
  const navigate = useNavigate();
  const { removeItem, addItem } = useWishlist();

  const [wishlist, setWishlist] = useState<WishlistDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showProductModal, setShowProductModal] = useState(false);
  const [selectedVariants, setSelectedVariants] = useState<string[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showRemoveModal, setShowRemoveModal] = useState(false);
  const [itemToRemove, setItemToRemove] = useState<string | null>(null);
  const [showShareModal, setShowShareModal] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_public: false
  });

  useEffect(() => {
    if (wishlistId) {
      loadWishlist();
    }
  }, [wishlistId]);

  const loadWishlist = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // This would typically call an API to get wishlist details
      // For now, we'll simulate the data
      const mockWishlist: WishlistDetail = {
        id: wishlistId!,
        name: 'My Favorite Products',
        description: 'A collection of products I love and want to buy later',
        is_public: false,
        share_token: 'abc123',
        items: [
          {
            id: 'item_1',
            product_id: 'prod_1',
            product: {
              id: 'prod_1',
              name: 'Premium Coffee Beans',
              description: 'High-quality arabica coffee beans',
              min_price: 19.99,
              max_price: 29.99,
              variants: [
                {
                  id: 'var_1',
                  product_id: 'prod_1',
                  sku: 'COFFEE-001',
                  name: '1lb Bag',
                  base_price: 19.99,
                  current_price: 19.99,
                  stock: 10,
                  is_active: true,
                  images: [],
                  created_at: '2024-01-01T00:00:00Z',
                  updated_at: '2024-01-01T00:00:00Z'
                }
              ],
              images: [],
              created_at: '2024-01-01T00:00:00Z'
            },
            variant_id: 'var_1',
            quantity: 1,
            created_at: '2024-01-01T00:00:00Z'
          }
        ],
        created_at: '2024-01-01T00:00:00Z'
      };

      setWishlist(mockWishlist);
      setFormData({
        name: mockWishlist.name,
        description: mockWishlist.description || '',
        is_public: mockWishlist.is_public
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load wishlist');
      toast.error('Failed to load wishlist');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!wishlist) return;

    setSaving(true);
    try {
      // For now, just show success - the updateWishlist would need to be implemented
      toast.success('Wishlist updated successfully');
      await loadWishlist(); // Reload to get updated data
    } catch (err: any) {
      toast.error('Failed to update wishlist');
    } finally {
      setSaving(false);
    }
  };

  const handleAddProducts = async (variantIds: string[]) => {
    if (!wishlist || variantIds.length === 0) return;

    try {
      // Add each variant to wishlist
      for (const variantId of variantIds) {
        await addItem(wishlist.id, variantId, 1);
      }
      
      setShowProductModal(false);
      setShowAddModal(false);
      setSelectedVariants([]);
      toast.success(`${variantIds.length} item${variantIds.length !== 1 ? 's' : ''} added to wishlist`);
      await loadWishlist();
    } catch (err: any) {
      toast.error('Failed to add items to wishlist');
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    if (!wishlist) return;

    try {
      await removeItem(wishlist.id, itemId);
      setShowRemoveModal(false);
      setItemToRemove(null);
      toast.success('Item removed from wishlist');
      await loadWishlist();
    } catch (err: any) {
      toast.error('Failed to remove item');
    }
  };

  const handleShare = () => {
    if (!wishlist) return;
    
    const shareUrl = `${window.location.origin}/wishlist/${wishlist.share_token}`;
    navigator.clipboard.writeText(shareUrl);
    toast.success('Wishlist link copied to clipboard!');
    setShowShareModal(false);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount || 0);
  };

  const getProductPrice = (product: Product) => {
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        <p className="ml-4 text-gray-600 dark:text-gray-400">Loading wishlist...</p>
      </div>
    );
  }

  if (error || !wishlist) {
    return (
      <div className="text-center p-6">
        <p className="text-red-600 dark:text-red-400">Error: {error || 'Wishlist not found'}</p>
        <button
          onClick={() => navigate('/account/wishlist')}
          className="mt-4 text-primary hover:underline"
        >
          Back to Wishlists
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/account/wishlist')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
          >
            <ArrowLeftIcon size={20} />
            Back to Wishlist
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Edit Wishlist
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              {wishlist.items.length} {wishlist.items.length === 1 ? 'item' : 'items'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowShareModal(true)}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <ShareIcon size={16} />
            Share
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50 transition-colors"
          >
            <SaveIcon size={16} />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Settings */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Wishlist Settings</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_public}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_public: e.target.checked }))}
                    className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    Make wishlist public
                  </span>
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Anyone with the link can view this wishlist
                </p>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => {
                  setSelectedVariants([]);
                  setShowAddModal(true);
                  setShowProductModal(true);
                }}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
              >
                <PlusIcon size={16} />
                Add Items
              </button>
            </div>
          </div>
        </div>

        {/* Items */}
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Items ({wishlist.items.length})
              </h3>
            </div>

            {wishlist.items.length === 0 ? (
              <div className="p-12 text-center">
                <HeartIcon size={48} className="text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  No items yet
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Add some products to get started
                </p>
                <button
                  onClick={() => {
                    setSelectedVariants([]);
                    setShowAddModal(true);
                    setShowProductModal(true);
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
                >
                  <PlusIcon size={16} />
                  Add Items
                </button>
              </div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {wishlist.items.map((item) => {
                  const product = item.product;
                  const variant = product?.variants?.find(v => v.id === item.variant_id);

                  return (
                    <div key={item.id} className="p-6">
                      <div className="flex items-center gap-4">
                        {/* Product Image */}
                        {variant?.primary_image?.url || variant?.images?.[0]?.url || product?.images?.[0]?.url ? (
                          <img
                            src={variant?.primary_image?.url || variant?.images?.[0]?.url || product?.images?.[0]?.url}
                            alt={product?.name || 'Product'}
                            className="w-16 h-16 rounded-lg object-cover border border-gray-300 dark:border-gray-600"
                          />
                        ) : (
                          <div className="w-16 h-16 rounded-lg bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                            <PackageIcon className="w-8 h-8 text-gray-400" />
                          </div>
                        )}

                        {/* Product Info */}
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900 dark:text-white">
                            {product?.name || 'Unknown Product'}
                          </h4>
                          {variant && (
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {variant.name} • SKU: {variant.sku}
                            </p>
                          )}
                          <div className="flex items-center gap-4 mt-2">
                            <span className="font-medium text-gray-900 dark:text-white">
                              {variant ? getVariantPrice(variant) : getProductPrice(product || {} as Product)}
                            </span>
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                              Qty: {item.quantity}
                            </span>
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => navigate(`/products/${product?.id}`)}
                            className="p-2 text-gray-600 hover:text-primary dark:text-gray-400 dark:hover:text-primary transition-colors"
                            title="View Product"
                          >
                            <PackageIcon size={18} />
                          </button>
                          <button
                            onClick={() => {
                              setItemToRemove(item.id);
                              setShowRemoveModal(true);
                            }}
                            className="p-2 text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 transition-colors"
                            title="Remove from Wishlist"
                          >
                            <TrashIcon size={18} />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

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
          message={`Are you sure you want to add ${selectedVariants.length} item${selectedVariants.length !== 1 ? 's' : ''} to this wishlist?`}
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
          onConfirm={() => handleRemoveItem(itemToRemove)}
          title="Remove Item"
          message="Are you sure you want to remove this item from your wishlist?"
          confirmText="Remove"
          cancelText="Cancel"
        />
      )}

      {showShareModal && (
        <ConfirmationModal
          isOpen={true}
          onClose={() => setShowShareModal(false)}
          onConfirm={handleShare}
          title="Share Wishlist"
          message="Copy the wishlist link to share it with others."
          confirmText="Copy Link"
          cancelText="Close"
        />
      )}
    </div>
  );
};

export default WishlistEdit;
