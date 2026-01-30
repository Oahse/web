import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AccountLayout from '../components/account/AccountLayout';
import { useWishlist } from '../store/WishlistContext';
import { useCart } from '../store/CartContext';
import { useAuth } from '../hooks/useAuth';
import { 
  HeartIcon, 
  ShoppingCartIcon, 
  XCircleIcon, 
  RefreshCwIcon, 
  AlertCircleIcon,
  UserIcon,
  ShoppingBagIcon,
  MapPinIcon,
  CreditCardIcon,
  LogOutIcon,
  ChevronRightIcon,
  PackageIcon,
  ShieldIcon,
  ChevronLeftIcon
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { PLACEHOLDER_IMAGES } from '../utils/placeholderImage';
import { unwrapResponse, extractErrorMessage } from '../utils/api-response';

export const Wishlist = () => {
  const { defaultWishlist, removeItem, fetchWishlists, loading, error } = useWishlist();
  const { addItem: addToCart } = useCart();
  const { executeWithAuth, user, logout, isAdmin, isSupplier } = useAuth();
  const navigate = useNavigate();
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12; // Show 12 items per page for wishlist
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  // Calculate pagination
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentItems = defaultWishlist?.items?.slice(startIndex, endIndex) || [];

  // Update pagination when wishlist changes
  useEffect(() => {
    if (defaultWishlist?.items) {
      const total = defaultWishlist.items.length;
      setTotalItems(total);
      setTotalPages(Math.ceil(total / itemsPerPage));
      
      // Reset to page 1 if current page is beyond bounds
      if (currentPage > Math.ceil(total / itemsPerPage)) {
        setCurrentPage(1);
      }
    }
  }, [defaultWishlist, currentPage, itemsPerPage]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

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
        return;
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

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  // Navigation items for sidebar
  const navItems = [
    { path: '/account', label: 'Dashboard', icon: <UserIcon size={20} /> },
    { path: '/account/profile', label: 'Profile', icon: <UserIcon size={20} /> },
    { path: '/account/orders', label: 'Orders', icon: <ShoppingBagIcon size={20} /> },
    { path: '/account/wishlist', label: 'Wishlist', icon: <HeartIcon size={20} /> },
    { path: '/account/addresses', label: 'Addresses', icon: <MapPinIcon size={20} /> },
    { path: '/account/payment-methods', label: 'Payment Methods', icon: <CreditCardIcon size={20} /> },
    { path: '/account/subscriptions', label: 'My Subscriptions', icon: <PackageIcon size={20} /> },
  ];

  if (isSupplier) {
    navItems.splice(2, 0, {
      path: '/account/products',
      label: 'My Products',
      icon: <PackageIcon size={20} />
    });
  }

  if (isAdmin) {
    navItems.push({ path: '/admin', label: 'Admin Dashboard', icon: <ShieldIcon size={20} /> });
  }

  const isActive = (path: string) => {
    return location.pathname.startsWith(path);
  };

  // Loading state - show skeleton
  if (loading && !defaultWishlist) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
              <div className="h-48 bg-gray-200 dark:bg-gray-700"></div>
              <div className="p-4">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3 mb-4"></div>
                <div className="flex items-center justify-between">
                  <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                  <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
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
      <div className="text-center py-8 border border-dashed border-gray-300 dark:border-gray-700 rounded-lg">
        <AlertCircleIcon size={48} className="mx-auto text-red-500 dark:text-red-400 mb-4" />
        <h2 className="text-xl font-medium text-gray-900 dark:text-white mb-2">Unable to Load Wishlist</h2>
        <p className="text-gray-500 dark:text-gray-400 mb-4">{error}</p>
        <button
          onClick={handleRetry}
          className="bg-primary hover:bg-primary-dark text-white py-2 px-4 rounded-md transition-colors inline-flex items-center"
        >
          <RefreshCwIcon size={18} className="mr-2" />
          Try Again
        </button>
      </div>
    );
  }

  // Empty state
  if (!defaultWishlist || !defaultWishlist.items || defaultWishlist.items.length === 0) {
    return (
      <div className="text-center py-8 border border-dashed border-gray-300 dark:border-gray-700 rounded-lg">
        <HeartIcon size={48} className="mx-auto text-gray-400 dark:text-gray-500 mb-4" />
        <h2 className="text-xl font-medium text-gray-900 dark:text-white mb-2">Your Wishlist is Empty</h2>
        <p className="text-gray-500 dark:text-gray-400 mb-4">Add items you love to your wishlist to easily find them later.</p>
        <Link to="/products" className="bg-primary hover:bg-primary-dark text-white py-2 px-4 rounded-md transition-colors">
          Start Shopping
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">My Wishlist</h1>
        {defaultWishlist && defaultWishlist.items && (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {totalItems} item{totalItems !== 1 ? 's' : ''} • Page {currentPage} of {totalPages}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {currentItems.map((item) => (
          <div key={item.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden flex flex-col">
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
                className="absolute top-2 right-2 bg-white dark:bg-gray-800 rounded-full p-1 shadow-md text-red-500 dark:text-red-400 hover:text-red-600 dark:hover:text-red-300"
                title="Remove from Wishlist"
              >
                <XCircleIcon size={20} />
              </button>
            </Link>
            <div className="p-4 flex-grow flex flex-col">
              <Link to={`/products/${item.product_id}`}>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white hover:text-primary line-clamp-2 mb-1">
                  {item.product?.name}
                </h2>
              </Link>
              {item.variant && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Variant: {item.variant.name}</p>
              )}
              <div className="flex items-center justify-between mt-auto">
                <span className="text-xl font-bold text-gray-900 dark:text-white">
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

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2 pt-6">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="flex items-center px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeftIcon size={16} className="mr-1" />
            Previous
          </button>
          
          <div className="flex items-center space-x-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }
              
              return (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={`px-3 py-2 text-sm rounded transition-colors ${
                    currentPage === pageNum
                      ? 'bg-primary text-white'
                      : 'border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>
          
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="flex items-center px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Next
            <ChevronRightIcon size={16} className="ml-1" />
          </button>
        </div>
      )}
    </div>
  );
};

export default Wishlist;
