import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom';
import {
  ChevronRightIcon,
  HeartIcon,
  ShareIcon,
  ShoppingCartIcon,
  StarIcon,
  TruckIcon,
  ShieldCheckIcon,
  RefreshCwIcon,
  MinusIcon,
  PlusIcon,
  QrCodeIcon,
  ScanLineIcon,
  CalendarIcon,
} from 'lucide-react';

import { ProductImageGallery } from '../components/product/ProductImageGallery';
import { VariantSelector } from '../components/product/VariantSelector';
import { QRCodeModal } from '../components/product/QRCodeModal';
import { BarcodeModal } from '../components/product/BarcodeModal';
import { ProductCard } from '../components/product/ProductCard';
import { SubscriptionSelector } from '../components/subscription/SubscriptionSelector';
import { useCart } from '../store/CartContext';
import { useWishlist } from '../store/WishlistContext';
import { useLocale } from '../store/LocaleContext';
import { useApi } from '../hooks/useAsync';
import { useSubscriptionAction } from '../hooks/useSubscription';
import { ProductsAPI, ReviewsAPI } from '../api';
import { unwrapResponse, extractErrorMessage } from '../utils/api-response';

import ErrorMessage from '../components/Error';
import { toast } from 'react-hot-toast';
import { useAuth } from '../hooks/useAuth';

// Transform API product data with null checks
const transformProduct = (product, averageRating, reviewCount) => {
  if (!product) return null;
  
  return {
    id: product.id,
    name: product.name,
    price: product.variants?.[0]?.base_price || 0,
    discountPrice: product.variants?.[0]?.sale_price || null,
    rating: averageRating || 0, 
    reviewCount: reviewCount || 0, 
    description: product.description,
    longDescription: product.description, 
    category: product.category?.name,
    brand: product.supplier ? `${product.supplier.firstname || ''} ${product.supplier.lastname || ''}`.trim() : null,
    sku: product.variants?.[0]?.sku,
    stock: product.variants?.[0]?.stock || 0,
    images: product.variants?.[0]?.images?.map(img => img?.url).filter(Boolean) || [],
    variants: product.variants?.map(variant => ({
      id: variant.id,
      name: variant.name || '',
      base_price: variant.base_price || 0,
      sale_price: variant.sale_price || null,
      stock: variant.stock || 0,
      sku: variant.sku || '',
      attributes: variant.attributes || {}
    })) || [],
    features: [
      'High Quality Product',
      'Fast Shipping',
      'Customer Satisfaction Guaranteed',
      'Secure Payment',
    ],
    specifications: {
      'Product Name': product.name,
      'Category': product.category?.name,
      'Supplier': product.supplier ? `${product.supplier.firstname || ''} ${product.supplier.lastname || ''}`.trim() : null,
      'SKU': product.variants?.[0]?.sku,
    },
    reviews: [], 
  };
};

export const ProductDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [selectedImage, setSelectedImage] = useState(0);
  const [quantity, setQuantity] = useState(1);
  const [activeTab, setActiveTab] = useState('description');
  const [showQR, setShowQR] = useState(false);
  const [showBarcode, setShowBarcode] = useState(false);
  const [showSubscriptionSelector, setShowSubscriptionSelector] = useState(false);
  const [minRating, setMinRating] = useState(undefined);
  const [maxRating, setMaxRating] = useState(undefined);
  const [sortBy, setSortBy] = useState(undefined);
  const [reviewsPage, setReviewsPage] = useState(1);

  const { addItem: addToCart, removeItem: removeFromCart, updateQuantity, cart, refreshCart } = useCart();
  const { addItem: addToWishlist, removeItem: removeFromWishlist, isInWishlist, defaultWishlist } = useWishlist();
  const { executeWithAuth } = useAuth();
  const { isAuthenticated, hasActiveSubscriptions } = useSubscriptionAction();
  const { formatCurrency } = useLocale();

  // API calls
  const {
    data: productData,
    loading: productLoading,
    error: productError,
    execute: fetchProduct,
  } = useApi();

  const {
    data: relatedProductsData,
    loading: relatedLoading,
    error: relatedError,
    execute: fetchRelatedProducts,
  } = useApi();

  const {
    data: reviewsData,
    loading: reviewsLoading,
    error: reviewsError,
    execute: fetchReviews,
  } = useApi();

  // Fetch product data
  useEffect(() => {
    if (id && id !== 'search') {
      fetchProduct(() => ProductsAPI.getProduct(id));
      fetchRelatedProducts(() => ProductsAPI.getRecommendedProducts(id, 4));
    }
  }, [id, fetchProduct, fetchRelatedProducts]);

  // Extract actual data from API response
  const actualProductData = productData?.data || productData;
  const actualRelatedData = relatedProductsData?.data || relatedProductsData;
  const actualReviewsData = reviewsData?.data ? {
    data: reviewsData.data.data || reviewsData.data,
    total: reviewsData.data.total || reviewsData.total || 0,
    limit: reviewsData.data.limit || reviewsData.limit || 10
  } : { data: [], total: 0, limit: 10 };

  // Fetch reviews when product ID, filters, or page change
  useEffect(() => {
    if (id && id !== 'search') {
      const params = new URLSearchParams();
      params.append('page', reviewsPage.toString());
      params.append('limit', '10');
      if (minRating !== undefined) params.append('min_rating', minRating.toString());
      if (maxRating !== undefined) params.append('max_rating', maxRating.toString());
      if (sortBy) params.append('sort_by', sortBy);
      
      fetchReviews(() => ReviewsAPI.getProductReviews(id, reviewsPage, 10, minRating, maxRating, sortBy));
    }
  }, [id, reviewsPage, minRating, maxRating, sortBy, fetchReviews]);

  // Set initial variant when product loads
  useEffect(() => {
    if (actualProductData && actualProductData.variants && actualProductData.variants.length > 0) {
      const variant = actualProductData.variants[0];
      setSelectedVariant({
        id: variant.id,
        name: variant.name,
        base_price: variant.base_price,
        sale_price: variant.sale_price,
        current_price: variant.current_price,
        discount_percentage: variant.discount_percentage,
        stock: variant.stock,
        sku: variant.sku,
        attributes: variant.attributes,
        barcode: variant.barcode,
        qr_code: variant.qr_code,
      });
      // Reset image selection when product changes
      setSelectedImage(0);
    }
  }, [actualProductData]);

  // Update images when variant changes
  useEffect(() => {
    if (selectedVariant) {
      setSelectedImage(0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedVariant?.id]);

  const handleQuantityChange = (newQuantity) => {
    setQuantity(Math.max(1, newQuantity));
  };

  if (!id || id === 'search') {
    return <div>Product not found</div>;
  }

  if (productLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-gray-200 h-96 rounded-lg"></div>
            <div className="space-y-4">
              <div className="bg-gray-200 h-8 rounded"></div>
              <div className="bg-gray-200 h-6 rounded w-3/4"></div>
              <div className="bg-gray-200 h-4 rounded w-1/2"></div>
              <div className="bg-gray-200 h-20 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (productError || !actualProductData) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ErrorMessage
          error={productError || { error: true, message: 'Product not found' }}
          onRetry={() => fetchProduct(() => ProductsAPI.getProduct(id))}
        />
      </div>
    );
  }

  // Calculate average rating and total reviews with null checks
  const reviewsList = actualReviewsData.data || [];
  const averageRating = Array.isArray(reviewsList) && reviewsList.length > 0
    ? reviewsList.reduce((acc, review) => acc + (review?.rating || 0), 0) / reviewsList.length
    : 0;
  const totalReviews = actualReviewsData.total || 0;

  const product = transformProduct(actualProductData, averageRating, totalReviews);
  
  // If product transformation failed, show error
  if (!product) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ErrorMessage
          error={{ error: true, message: 'Failed to load product data' }}
          onRetry={() => fetchProduct(() => ProductsAPI.getProduct(id))}
        />
      </div>
    );
  }
  
  const isInWishlistState = isInWishlist(product.id, selectedVariant?.id);

  // Get cart item quantity with null checks and validation
  const cartItem = cart?.items?.find(item => 
    item?.variant?.id === selectedVariant?.id && 
    item?.id && 
    item?.quantity > 0
  );
  const cartQuantity = cartItem?.quantity || 0;

  // Helper function to handle cart operations with better error handling
  const handleCartOperation = async (operation: 'increment' | 'decrement') => {
    if (!selectedVariant) {
      toast.error('Please select a variant');
      return;
    }

    if (!cartItem) {
      toast.error('Item not found in cart. Refreshing...');
      await refreshCart();
      return;
    }

    try {
      console.log(`Cart ${operation}:`, { 
        cartItemId: cartItem.id, 
        currentQuantity: cartQuantity, 
        variantId: selectedVariant.id 
      });

      if (operation === 'decrement') {
        const newQuantity = Math.max(0, cartQuantity - 1);
        if (newQuantity === 0) {
          await removeFromCart(cartItem.id);
        } else {
          await updateQuantity(cartItem.id, newQuantity);
        }
      } else {
        await updateQuantity(cartItem.id, cartQuantity + 1);
      }
    } catch (error: any) {
      console.error(`Failed to ${operation} cart:`, error);
      
      // Handle 404 errors (item not found)
      if (error?.status === 404 || error?.statusCode === 404 || error?.message?.includes('not found')) {
        toast.error('Cart item not found. Refreshing cart...');
        await refreshCart();
        
        // For increment operations, try to add the item fresh
        if (operation === 'increment') {
          try {
            await addToCart({ variant_id: String(selectedVariant.id), quantity: 1 });
            toast.success('Item re-added to cart');
          } catch (addError) {
            console.error('Failed to re-add item:', addError);
            toast.error('Failed to add item to cart');
          }
        }
      } else {
        toast.error(error?.message || `Failed to ${operation} cart item`);
      }
    }
  };

  // Check if product is in wishlist


  return (
    <div className="pb-16 md:pb-0">
      {/* Breadcrumb */}
      <div className="bg-surface py-4">
        <div className="container mx-auto px-4">
          <nav className="flex items-center space-x-2 text-sm text-copy-light">
            <Link to="/" className="hover:text-primary">Home</Link>
            <ChevronRightIcon size={16} />
            <Link to="/products" className="hover:text-primary">Products</Link>
            <ChevronRightIcon size={16} />
            <span className="text-main">{product.name}</span>
          </nav>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* Product Images */}
          <div className="space-y-4">
            <ProductImageGallery
              images={selectedVariant 
                ? (actualProductData.variants?.find(v => v.id === selectedVariant.id)?.images || [])
                : (actualProductData.variants?.[0]?.images || [])
              }
              selectedImageIndex={selectedImage}
              onImageSelect={setSelectedImage}
              showThumbnails={true}
              zoomEnabled={true}
            />
            
            {/* QR Code and Barcode Section - Mobile Optimized */}
            {selectedVariant && (
              <div className="flex flex-col sm:flex-row sm:space-x-4 sm:space-y-0 space-y-2 justify-center mt-4">
                {selectedVariant.qr_code && (
                  <button
                    onClick={() => setShowQR(true)}
                    className="flex items-center justify-center space-x-2 text-sm text-primary hover:underline px-3 py-2 border border-primary/20 rounded-lg hover:bg-primary/5 transition-colors"
                  >
                    <QrCodeIcon size={16} />
                    <span className="sm:inline">View QR Code</span>
                  </button>
                )}
                
                {selectedVariant.barcode && (
                  <button
                    onClick={() => setShowBarcode(true)}
                    className="flex items-center justify-center space-x-2 text-sm text-primary hover:underline px-3 py-2 border border-primary/20 rounded-lg hover:bg-primary/5 transition-colors"
                  >
                    <ScanLineIcon size={16} />
                    <span className="sm:inline">View Barcode</span>
                  </button>
                )}
                
                {/* Show SKU on mobile */}
                <div className="flex items-center justify-center text-xs text-gray-500 dark:text-gray-400 px-3 py-2 sm:hidden">
                  SKU: {selectedVariant.sku || product.sku}
                </div>
              </div>
            )}

            {/* QR Code Modal */}
            <QRCodeModal
              data={selectedVariant?.qr_code || `${window.location.origin}/products/${id}`}
              title={`${product.name} - QR Code`}
              description={`QR Code for ${product.name} (${selectedVariant?.sku || product.sku})`}
              isOpen={showQR}
              onClose={() => setShowQR(false)}
            />

            {/* Barcode Modal */}
            {selectedVariant && (
              <BarcodeModal
                variant={{
                  id: selectedVariant.id,
                  product_id: actualProductData.id,
                  sku: selectedVariant.sku,
                  name: selectedVariant.name,
                  base_price: selectedVariant.base_price,
                  sale_price: selectedVariant.sale_price,
                  stock: selectedVariant.stock,
                  images: actualProductData.variants?.find(v => v.id === selectedVariant.id)?.images || [],
                  product_name: product.name,
                  barcode: selectedVariant.barcode,
                  qr_code: selectedVariant.qr_code
                }}
                title={`${product.name} - Product Codes`}
                isOpen={showBarcode}
                onClose={() => setShowBarcode(false)}
                canGenerate={false} // Set to true if user has admin permissions
              />
            )}
          </div>

          {/* Product Info */}
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold text-main mb-2">{product.name}</h1>
              <div className="flex items-center space-x-4 mb-4">
                <div className="flex items-center">
                  <div className="flex text-yellow-400">
                    {Array.from({ length: 5 }, (_, i) => (
                      <StarIcon
                        key={i}
                        size={16}
                        className={i < Math.floor(product.rating) ? 'fill-current' : ''}
                      />
                    ))}
                  </div>
                  <span className="text-sm text-copy-light ml-2">
                    ({product.reviewCount} reviews)
                  </span>
                </div>
                <span className="text-sm text-copy-light">SKU: {product.sku}</span>
              </div>

              <div className="flex items-center space-x-4 mb-4">
                {selectedVariant?.sale_price && selectedVariant.sale_price < selectedVariant.base_price ? (
                  <>
                    <span className="text-3xl font-bold text-primary">
                      {formatCurrency(selectedVariant.sale_price)}
                    </span>
                    <span className="text-xl text-copy-light line-through">
                      {formatCurrency(selectedVariant.base_price)}
                    </span>
                    <span className="bg-error-100 text-error-600 px-2 py-1 rounded text-sm font-medium">
                      {Math.round(((selectedVariant.base_price - selectedVariant.sale_price) / selectedVariant.base_price) * 100)}% OFF
                    </span>
                  </>
                ) : (
                  <span className="text-3xl font-bold text-primary">
                    {formatCurrency(selectedVariant?.sale_price || selectedVariant?.base_price || product.price)}
                  </span>
                )}
              </div>

              <p className="text-copy-light mb-6">{product.description}</p>
            </div>

            {/* Variant Selection */}
            {actualProductData?.variants && product.variants && product.variants.length > 1 && selectedVariant && (
              <VariantSelector
                variants={actualProductData.variants.map(variant => ({
                  id: variant.id,
                  product_id: variant.product_id || actualProductData.id,
                  sku: variant.sku || '',
                  name: variant.name || '',
                  base_price: variant.base_price || 0,
                  sale_price: variant.sale_price || null,
                  stock: variant.stock || 0,
                  barcode: variant.barcode || '',
                  qr_code: variant.qr_code || '',
                  attributes: variant.attributes ? Object.entries(variant.attributes).map(([name, value]) => ({
                    id: `${variant.id}-${name}`,
                    name,
                    value: String(value)
                  })) : [],
                  images: variant.images || []
                }))}
                selectedVariant={{
                  id: selectedVariant.id,
                  product_id: actualProductData.id,
                  sku: selectedVariant.sku || '',
                  name: selectedVariant.name || '',
                  base_price: selectedVariant.base_price || 0,
                  sale_price: selectedVariant.sale_price || null,
                  stock: selectedVariant.stock || 0,
                  barcode: selectedVariant.barcode || '',
                  qr_code: selectedVariant.qr_code || '',
                  attributes: selectedVariant.attributes ? Object.entries(selectedVariant.attributes).map(([name, value]) => ({
                    id: `${selectedVariant.id}-${name}`,
                    name,
                    value: String(value)
                  })) : [],
                  images: actualProductData.variants?.find(v => v.id === selectedVariant.id)?.images || []
                }}
                onVariantChange={(variant) => {
                  const originalVariant = actualProductData.variants?.find(v => v.id === variant.id);
                  if (originalVariant) {
                    setSelectedVariant({
                      id: originalVariant.id,
                      name: originalVariant.name,
                      base_price: originalVariant.base_price,
                      sale_price: originalVariant.sale_price,
                      current_price: originalVariant.current_price,
                      discount_percentage: originalVariant.discount_percentage,
                      stock: originalVariant.stock,
                      sku: originalVariant.sku,
                      attributes: originalVariant.attributes,
                      barcode: originalVariant.barcode,
                      qr_code: originalVariant.qr_code,
                    });
                  }
                }}
                showImages={false}
                showPrice={true}
                showStock={true}
                layout="grid"
              />
            )}

            {/* Stock Status */}
            {selectedVariant && (
              <div className="mb-4">
                {selectedVariant.stock > 0 ? (
                  <span className="text-sm text-success-600 font-medium">
                    ✓ In Stock ({selectedVariant.stock} available)
                  </span>
                ) : (
                  <span className="text-sm text-error-600 font-medium">
                    ✗ Out of Stock
                  </span>
                )}
              </div>
            )}

            {/* Quantity Selection */}
            {selectedVariant && selectedVariant.stock > 0 && (
              <div>
                <h3 className="font-medium text-main mb-3">Quantity:</h3>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => handleQuantityChange(quantity - 1)}
                    disabled={quantity <= 1}
                    className="w-10 h-10 rounded-md border border-border flex items-center justify-center hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <MinusIcon size={16} />
                  </button>
                  <span className="w-16 text-center font-medium">{quantity}</span>
                  <button
                    onClick={() => handleQuantityChange(quantity + 1)}
                    disabled={selectedVariant && quantity >= selectedVariant.stock}
                    className="w-10 h-10 rounded-md border border-border flex items-center justify-center hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <PlusIcon size={16} />
                  </button>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="space-y-4 mb-6">
              {/* Cart Button with Quantity */}
              <div className="flex space-x-4">
                <div className="flex-1">
                  {cartQuantity > 0 ? (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleCartOperation('decrement')}
                        className="bg-gray-200 hover:bg-gray-300 text-gray-700 p-2 rounded-md transition-colors"
                      >
                        <MinusIcon size={16} />
                      </button>
                      <span className="bg-primary text-white px-4 py-2 rounded-md font-medium min-w-[120px] text-center">
                        In Cart ({cartQuantity})
                      </span>
                      <button
                        onClick={() => handleCartOperation('increment')}
                        disabled={selectedVariant && cartQuantity >= selectedVariant.stock}
                        className="bg-primary hover:bg-primary-dark text-white p-2 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <PlusIcon size={16} />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={async () => {
                        if (!selectedVariant) return;
                        await executeWithAuth(async () => {
                          await addToCart({ variant_id: String(selectedVariant.id), quantity: quantity });
                          return true;
                        }, 'cart');
                      }}
                      disabled={!selectedVariant || selectedVariant.stock <= 0}
                      className="w-full bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-md font-medium transition-colors flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ShoppingCartIcon size={20} className="mr-2" />
                      {selectedVariant && selectedVariant.stock <= 0 ? 'Out of Stock' : 'Add to Cart'}
                    </button>
                  )}
                </div>

                {/* Wishlist Button */}
                <button
                  onClick={async () => {
                    await executeWithAuth(async () => {
                      if (!defaultWishlist) {
                        toast.error("No default wishlist found.");
                        return false;
                      }
                      if (isInWishlistState) {
                        const wishlistItem = defaultWishlist.items?.find(
                          item => item?.product_id === product.id && (selectedVariant ? item?.variant_id === selectedVariant.id : true)
                        );
                        if (wishlistItem) {
                          await removeFromWishlist(defaultWishlist.id, wishlistItem.id);
                        }
                      } else {
                        await addToWishlist(product.id, selectedVariant?.id, quantity);
                      }
                      return true;
                    }, 'wishlist');
                  }}
                  className={`px-6 py-3 rounded-md font-medium transition-colors flex items-center justify-center min-w-[60px] ${isInWishlistState
                    ? 'bg-error-100 text-error-600 hover:bg-error-200'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  title={isInWishlistState ? 'Remove from Wishlist' : 'Add to Wishlist'}
                >
                  <HeartIcon size={20} className={isInWishlistState ? 'fill-current' : ''} />
                </button>
              </div>

              {/* Subscription Button */}
              {isAuthenticated && hasActiveSubscriptions && selectedVariant && selectedVariant.stock > 0 && (
                <button
                  onClick={() => setShowSubscriptionSelector(true)}
                  className="w-full bg-green-600 hover:bg-green-700 text-white px-4 sm:px-6 py-2 sm:py-3 rounded-md font-medium transition-colors flex items-center justify-center text-sm sm:text-base"
                >
                  <CalendarIcon size={18} className="mr-1 sm:mr-2 flex-shrink-0" />
                  <span className="truncate">Add to Subscription</span>
                </button>
              )}
            </div>

            {/* Product Features */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                <TruckIcon size={20} className="text-primary" />
                <span className="text-sm">Standard Shipping Available</span>
              </div>
              <div className="flex items-center space-x-2">
                <ShieldCheckIcon size={20} className="text-primary" />
                <span className="text-sm">Secure Payment</span>
              </div>
              <div className="flex items-center space-x-2">
                <RefreshCwIcon size={20} className="text-primary" />
                <span className="text-sm">Easy Returns</span>
              </div>
              <div className="flex items-center space-x-2">
                <ShareIcon size={20} className="text-primary" />
                <span className="text-sm">Share Product</span>
              </div>
            </div>
          </div>
        </div>

        {/* Product Details Tabs */}
        <div className="mb-12">
          <div className="border-b border-gray-200 mb-6">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('description')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'description'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-copy-light hover:text-copy'
                  }`}
              >
                Description
              </button>
              <button
                onClick={() => setActiveTab('specifications')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'specifications'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-copy-light hover:text-copy'
                  }`}
              >
                Specifications
              </button>
              <button
                onClick={() => setActiveTab('reviews')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'reviews'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-copy-light hover:text-copy'
                  }`}
              >
                Reviews ({product.reviewCount})
              </button>
            </nav>
          </div>

          <div className="prose max-w-none">
            {activeTab === 'description' && (
              <div>
                <p className="text-copy-light mb-4">{product.longDescription}</p>
                <h4 className="font-medium text-main mb-2">Features:</h4>
                <ul className="list-disc list-inside space-y-1">
                  {product.features.map((feature, index) => (
                    <li key={index} className="text-copy-light">{feature}</li>
                  ))}
                </ul>
              </div>
            )}

            {activeTab === 'specifications' && (
              <div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(product.specifications).map(([key, value]) => (
                    <div key={key} className="flex justify-between py-2 border-b border-gray-100">
                      <span className="font-medium text-main">{key}:</span>
                      <span className="text-copy-light">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'reviews' && (
              <div>
                <div className="flex items-center space-x-4 mb-6">
                  {/* Min Rating Filter */}
                  <div>
                    <label htmlFor="minRating" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Min Rating</label>
                    <select
                      id="minRating"
                      value={minRating || ''}
                      onChange={(e) => setMinRating(e.target.value ? Number(e.target.value) : undefined)}
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    >
                      <option value="">Any</option>
                      {[1, 2, 3, 4, 5].map(r => <option key={r} value={r}>{r} Star{r > 1 ? 's' : ''}</option>)}
                    </select>
                  </div>

                  {/* Max Rating Filter */}
                  <div>
                    <label htmlFor="maxRating" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Max Rating</label>
                    <select
                      id="maxRating"
                      value={maxRating || ''}
                      onChange={(e) => setMaxRating(e.target.value ? Number(e.target.value) : undefined)}
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    >
                      <option value="">Any</option>
                      {[1, 2, 3, 4, 5].map(r => <option key={r} value={r}>{r} Star{r > 1 ? 's' : ''}</option>)}
                    </select>
                  </div>

                  {/* Sort By */}
                  <div>
                    <label htmlFor="sortBy" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Sort By</label>
                    <select
                      id="sortBy"
                      value={sortBy || ''}
                      onChange={(e) => setSortBy(e.target.value || undefined)}
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    >
                      <option value="">Newest</option>
                      <option value="rating_desc">Rating (High to Low)</option>
                      <option value="rating_asc">Rating (Low to High)</option>
                      <option value="created_at_asc">Oldest</option>
                    </select>
                  </div>
                </div>

                {reviewsLoading ? (
                  <div className="space-y-6">
                    {[...Array(3)].map((_, index) => (
                      <div key={index} className="animate-pulse border-b border-gray-100 pb-6">
                        <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
                        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
                        <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                      </div>
                    ))}
                  </div>
                ) : reviewsError ? (
                  <ErrorMessage
                    error={reviewsError}
                    onRetry={() => fetchReviews(() => ReviewsAPI.getProductReviews(id, reviewsPage, 10, minRating, maxRating, sortBy))}
                  />
                ) : reviewsList.length > 0 ? (
                  <div className="space-y-6">
                    {reviewsList.map((review) => (
                      <div key={review.id} className="border-b border-gray-100 pb-6">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium text-main">
                              {review.user?.firstname || 'Anonymous'} {review.user?.lastname || ''}
                            </span>
                            <div className="flex text-yellow-400">
                              {Array.from({ length: 5 }, (_, i) => (
                                <StarIcon
                                  key={i}
                                  size={14}
                                  className={i < (review.rating || 0) ? 'fill-current' : ''}
                                />
                              ))}
                            </div>
                          </div>
                          <span className="text-sm text-copy-light">
                            {review.created_at ? new Date(review.created_at).toLocaleDateString() : ''}
                          </span>
                        </div>
                        <p className="text-copy-light">{review.comment || ''}</p>
                      </div>
                    ))}

                    {/* Reviews Pagination */}
                    {actualReviewsData.total > actualReviewsData.limit && (
                      <div className="flex items-center justify-center space-x-2 mt-8">
                        <button
                          onClick={() => setReviewsPage(prev => Math.max(1, prev - 1))}
                          disabled={reviewsPage === 1}
                          className="px-3 py-2 rounded-md bg-surface border border-border text-copy hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Previous
                        </button>
                        
                        {Array.from({ length: Math.ceil(actualReviewsData.total / actualReviewsData.limit) }, (_, i) => {
                          const page = i + 1;
                          const totalPages = Math.ceil(actualReviewsData.total / actualReviewsData.limit);
                          
                          // Show first page, last page, current page, and pages around current
                          if (
                            page === 1 ||
                            page === totalPages ||
                            (page >= reviewsPage - 1 && page <= reviewsPage + 1)
                          ) {
                            return (
                              <button
                                key={page}
                                onClick={() => setReviewsPage(page)}
                                className={`px-3 py-2 rounded-md ${
                                  page === reviewsPage
                                    ? 'bg-primary text-white'
                                    : 'bg-surface border border-border text-copy hover:bg-surface-hover'
                                }`}
                              >
                                {page}
                              </button>
                            );
                          } else if (page === reviewsPage - 2 || page === reviewsPage + 2) {
                            return <span key={page} className="px-2">...</span>;
                          }
                          return null;
                        })}
                        
                        <button
                          onClick={() => setReviewsPage(prev => Math.min(Math.ceil(actualReviewsData.total / actualReviewsData.limit), prev + 1))}
                          disabled={reviewsPage === Math.ceil(actualReviewsData.total / actualReviewsData.limit)}
                          className="px-3 py-2 rounded-md bg-surface border border-border text-copy hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Next
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-copy-light">No reviews yet.</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Related Products */}
        <section className="py-12 bg-surface">
          <div className="container mx-auto px-4">
            <h2 className="text-2xl font-bold text-main mb-8">Related Products</h2>

            {relatedError && (
              <ErrorMessage
                error={relatedError}
                onRetry={() => fetchRelatedProducts(() => ProductsAPI.getRecommendedProducts(id && id !== 'search' ? id : '', 4))}
                className="mb-6"
              />
            )}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {relatedLoading ? (
                Array(4).fill(0).map((_, index) => (
                  <div key={index} className="animate-pulse">
                    <div className="bg-gray-200 rounded-lg h-48 mb-2"></div>
                    <div className="bg-gray-200 h-4 rounded mb-1"></div>
                    <div className="bg-gray-200 h-3 rounded w-16"></div>
                  </div>
                ))
              ) : actualRelatedData && Array.isArray(actualRelatedData) && actualRelatedData.length > 0 ? (
                actualRelatedData.map((relatedProduct) => {
                  if (!relatedProduct) return null;
                  
                  const transformedProduct = {
                    id: relatedProduct.id,
                    name: relatedProduct.name,
                    price: relatedProduct.variants?.[0]?.base_price || 0,
                    discountPrice: relatedProduct.variants?.[0]?.sale_price || null,
                    rating: relatedProduct.rating || 0,
                    reviewCount: relatedProduct.review_count || 0,
                    image: relatedProduct.variants?.[0]?.images?.[0]?.url,
                    category: relatedProduct.category?.name,
                    isNew: false,
                    isFeatured: false,
                    variants: relatedProduct.variants || [], // Add missing variants field
                  };

                  return (
                    <ProductCard
                      key={relatedProduct.id}
                      product={transformedProduct}
                      addToCart={addToCart}
                      removeFromCart={removeFromCart}
                      isInCart={cart?.items?.some(item => item?.variant?.product_id === relatedProduct.id)}
                      addToWishlist={addToWishlist}
                      removeFromWishlist={removeFromWishlist}
                      isInWishlist={isInWishlist(relatedProduct.id)}
                    />
                  );
                }).filter(Boolean)
              ) : (
                <div className="col-span-full text-center py-8 text-gray-500">
                  No related products found.
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Subscription Selector Modal */}
        {showSubscriptionSelector && selectedVariant && (
          <SubscriptionSelector
            isOpen={showSubscriptionSelector}
            onClose={() => setShowSubscriptionSelector(false)}
            productName={product.name}
            variantId={selectedVariant.id}
            quantity={quantity}
            onSuccess={() => {
              setShowSubscriptionSelector(false);
            }}
          />
        )}
      </div>
    </div>
  );
};

export default ProductDetails;
