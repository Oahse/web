import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useWishlist } from '../store/WishlistContext';
import { useCart } from '../store/CartContext';
import { useAuth } from '../hooks/useAuth';
import { HeartIcon, ShoppingCartIcon, XCircleIcon, RefreshCwIcon, AlertCircleIcon } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { PLACEHOLDER_IMAGES } from '../utils/placeholderImage';

export const Wishlist = () => {
  const { defaultWishlist, removeItem, fetchWishlists, loading, error } = useWishlist();
  const { addItem: addToCart } = useCart();
  const { executeWithAuth } = useAuth();

  useEffect(() => {
    fetchWishlists();
  }, [fetchWishlists]);

  const handleRemoveItem = async (wishlistId: string, itemId: string) => {
    await removeItem(wishlistId, itemId);
  };

  const handleAddToCart = async (item: any) => {
    await executeWithAuth(async () => {
      // Ensure a variant is available - check variant_id first, then variant object, then product variants
      const targetVariantId = item.variant_id || item.variant?.id || item.product?.variants?.[0]?.id;
      if (!targetVariantId) {
        toast.error("Cannot add to cart: variant information missing. Please try refreshing the page.");
        return false;
      }

      await addToCart({
        variant_id: targetVariantId,
        quantity: item.quantity,
      });
      toast.success("Item added to cart!");
      // Optionally remove from wishlist after adding to cart
      if (defaultWishlist) {
        await handleRemoveItem(defaultWishlist.id, item.id);
      }
      return true;
    }, 'cart');
  };

  const handleRetry = () => {
    fetchWishlists();
  };

  // Loading state - show skeleton
  if (loading && !defaultWishlist) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-main mb-6">My Wishlist</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-surface rounded-lg shadow-sm overflow-hidden animate-pulse">
              <div className="h-48 bg-gray-300"></div>
              <div className="p-4">
                <div className="h-4 bg-gray-300 rounded mb-2"></div>
                <div className="h-4 bg-gray-300 rounded w-2/3 mb-4"></div>
                <div className="flex items-center justify-between">
                  <div className="h-6 bg-gray-300 rounded w-20"></div>
                  <div className="h-10 bg-gray-300 rounded w-32"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error state - show error message with retry button
  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <AlertCircleIcon size={48} className="mx-auto text-error mb-4" />
        <h1 className="text-2xl font-bold text-main mb-2">Failed to Load Wishlist</h1>
        <p className="text-copy-light mb-6">{error}</p>
        <button
          onClick={handleRetry}
          className="bg-primary hover:bg-primary-dark text-white py-2 px-4 rounded-md transition-colors inline-flex items-center"
        >
          <RefreshCwIcon size={18} className="mr-2" />
          Retry
        </button>
      </div>
    );
  }

  // Empty state
  if (!defaultWishlist || !defaultWishlist.items || defaultWishlist.items.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <HeartIcon size={48} className="mx-auto text-gray-400 mb-4" />
        <h1 className="text-2xl font-bold text-main mb-2">Your Wishlist is Empty</h1>
        <p className="text-copy-light mb-6">Add items you love to your wishlist to easily find them later.</p>
        <Link to="/products" className="bg-primary hover:bg-primary-dark text-white py-2 px-4 rounded-md transition-colors">
          Start Shopping
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-main mb-6">My Wishlist</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {defaultWishlist.items.map((item) => (
          <div key={item.id} className="bg-surface rounded-lg shadow-sm overflow-hidden flex flex-col">
            <Link to={`/products/${item.product_id}`} className="block relative h-48 overflow-hidden">
              <img
                src={item.variant?.primary_image?.url || item.variant?.images?.[0]?.url || PLACEHOLDER_IMAGES.medium}
                alt={item.product?.name || item.variant?.name || "Product Image"}
                className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
              />
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  if (defaultWishlist) {
                    handleRemoveItem(defaultWishlist.id, item.id);
                  }
                }}
                className="absolute top-2 right-2 bg-white rounded-full p-1 shadow-md text-error hover:text-error-dark"
                title="Remove from Wishlist"
              >
                <XCircleIcon size={20} />
              </button>
            </Link>
            <div className="p-4 flex-grow flex flex-col">
              <Link to={`/products/${item.product_id}`}>
                <h2 className="text-lg font-semibold text-main hover:text-primary line-clamp-2 mb-1">
                  {item.product?.name}
                </h2>
              </Link>
              {item.variant && (
                <p className="text-sm text-copy-light mb-2">Variant: {item.variant.name}</p>
              )}
              <div className="flex items-center justify-between mt-auto">
                <span className="text-xl font-bold text-primary">
                  ${(item.variant?.sale_price || item.variant?.base_price || 0).toFixed(2)}
                </span>
                <button
                  onClick={() => handleAddToCart(item)}
                  className="bg-primary hover:bg-primary-dark text-white py-2 px-4 rounded-md transition-colors flex items-center"
                >
                  <ShoppingCartIcon size={18} className="mr-2" />
                  Add to Cart
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Wishlist;
