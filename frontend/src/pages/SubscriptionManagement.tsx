import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronRightIcon, PlusIcon, MinusIcon, ShoppingBagIcon, CalendarIcon, CreditCardIcon, TrashIcon, AlertTriangleIcon } from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { useSubscription } from '../store/SubscriptionContext';
import { useLocale } from '../store/LocaleContext';
import { getBestPrice, formatPriceWithFallback } from '../utils/price-utils';
import * as SubscriptionAPI from '../api/subscription';
import { ProductsAPI } from '../api/products';
import { SubscriptionProductCard } from '../components/subscription/SubscriptionProductCard';
import { AutoRenewToggle } from '../components/subscription/AutoRenewToggle';
import { Button } from '../components/ui/Button';
import { toast } from 'react-hot-toast';
import { themeClasses, combineThemeClasses, getButtonClasses } from '../utils/themeClasses';
import { ConfirmationModal } from '../components/ui/ConfirmationModal';

export const SubscriptionManagement = () => {
  const { subscriptionId } = useParams();
  const { user } = useAuth();
  const { updateSubscription, cancelSubscription, activateSubscription, pauseSubscription, resumeSubscription, addProductsToSubscription, removeProductsFromSubscription } = useSubscription();
  const { currency, formatCurrency } = useLocale();
  const [subscription, setSubscription] = useState<any>(null);
  const [availableProducts, setAvailableProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [subscriptionLoading, setSubscriptionLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProducts, setSelectedProducts] = useState(new Set());
  const [isAddingProducts, setIsAddingProducts] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [showActivateDialog, setShowActivateDialog] = useState(false);
  const [isActivating, setIsActivating] = useState(false);
  const [showPauseDialog, setShowPauseDialog] = useState(false);
  const [isPausing, setIsPausing] = useState(false);
  const [pauseReason, setPauseReason] = useState('');
  const [subscriptionError, setSubscriptionError] = useState<string | null>(null);
  const [showRemoveProductModal, setShowRemoveProductModal] = useState(false);
  const [productToRemove, setProductToRemove] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      console.error('User not authenticated');
      toast.error('Please log in to view your subscriptions');
      return;
    }
    
    if (!subscriptionId) {
      console.error('No subscription ID provided in URL');
      toast.error('Invalid subscription URL');
      return;
    }
    
    // Validate UUID format (more permissive for different UUID versions)
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(subscriptionId)) {
      console.error('Invalid subscription ID format:', subscriptionId);
      toast.error('Invalid subscription ID format');
      return;
    }
    
    console.log('Loading subscription for user:', user.id, 'subscription:', subscriptionId);
    loadSubscriptionData();
  }, [subscriptionId, user]);

  // Add error state for when subscription fails to load

  // Show error state if subscription failed to load
  if (subscriptionError && !subscriptionLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto text-center">
          <div className={combineThemeClasses(themeClasses.card.base, 'p-8')}>
            <div className="mb-6">
              <AlertTriangleIcon className="w-16 h-16 text-error mx-auto mb-4" />
              <h1 className={combineThemeClasses(themeClasses.text.heading, 'text-2xl font-bold mb-2')}>
                Unable to Load Subscription
              </h1>
              <p className={combineThemeClasses(themeClasses.text.secondary, 'mb-6')}>
                {subscriptionError}
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button
                onClick={() => {
                  setSubscriptionError(null);
                  loadSubscriptionData();
                }}
                variant="primary"
                className="flex items-center justify-center"
              >
                Try Again
              </Button>
              <Link
                to="/account/subscriptions"
                className={combineThemeClasses(getButtonClasses('outline'), 'flex items-center justify-center')}
              >
                Back to Subscriptions
              </Link>
            </div>
            
            {/* Debug Info in Development */}
            {import.meta.env.DEV && (
              <div className="mt-6 p-4 bg-gray-100 rounded-lg text-left">
                <h3 className="font-medium text-sm mb-2">Debug Information</h3>
                <div className="text-xs text-gray-600 space-y-1">
                  <p>Subscription ID: {subscriptionId}</p>
                  <p>User ID: {user?.id}</p>
                  <p>API Base URL: {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  useEffect(() => {
    if (searchQuery) {
      searchProducts();
    } else {
      loadAvailableProducts();
    }
  }, [searchQuery]);

  const loadSubscriptionData = async () => {
    try {
      setSubscriptionLoading(true);
      setSubscriptionError(null);
      console.log('Loading subscription data for ID:', subscriptionId);
      
      if (!subscriptionId) {
        throw new Error('No subscription ID provided');
      }
      
      const response = await SubscriptionAPI.getSubscription(subscriptionId);
      console.log('Subscription API response:', response);
      
      if (response) {
        setSubscription(response);
        console.log('Subscription data loaded successfully:', response);
      } else {
        throw new Error('Invalid response format from API');
      }
    } catch (error: any) {
      console.error('Failed to load subscription:', error);
      
      // More detailed error logging
      if (error.response) {
        console.error('Error response:', error.response);
        console.error('Error status:', error.response.status);
        console.error('Error data:', error.response.data);
      } else if (error.request) {
        console.error('Error request:', error.request);
      } else {
        console.error('Error message:', error.message);
      }
      
      // Show more specific error messages
      let errorMessage = 'Failed to load subscription details';
      if (error.statusCode === 404) {
        errorMessage = 'Subscription not found. It may have been deleted or you may not have access to it.';
      } else if (error.statusCode === 401) {
        errorMessage = 'You are not authorized to view this subscription. Please log in again.';
      } else if (error.statusCode === 403) {
        errorMessage = 'You do not have permission to view this subscription.';
      } else if (error.code === 'CONNECTION_ERROR') {
        errorMessage = 'Unable to connect to the server. Please check your internet connection and try again.';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setSubscriptionError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setSubscriptionLoading(false);
    }
  };

  const loadAvailableProducts = async () => {
    try {
      setLoading(true);
      const response = await ProductsAPI.getProducts({ 
        limit: 20,
        availability: true 
      });
      setAvailableProducts(response.data.data || []);
    } catch (error) {
      console.error('Failed to load products:', error);
      toast.error('Failed to load available products');
    } finally {
      setLoading(false);
    }
  };

  const searchProducts = async () => {
    try {
      setLoading(true);
      const response = await ProductsAPI.searchProducts(searchQuery, { limit: 20 });
      setAvailableProducts(response.data.products || []);
    } catch (error) {
      console.error('Failed to search products:', error);
      toast.error('Failed to search products');
    } finally {
      setLoading(false);
    }
  };

  const handleAddProducts = async () => {
    if (selectedProducts.size === 0) {
      toast.error('Please select at least one product to add');
      return;
    }

    try {
      setIsAddingProducts(true);
      const variantIds = Array.from(selectedProducts) as string[];
      const success = await addProductsToSubscription(subscriptionId!, variantIds);
      
      if (success) {
        setSelectedProducts(new Set());
        await loadSubscriptionData(); // Refresh subscription data
        toast.success(`Successfully added ${variantIds.length} product${variantIds.length !== 1 ? 's' : ''} to your subscription`);
      }
    } catch (error) {
      console.error('Failed to add products:', error);
      toast.error('Failed to add products to subscription');
    } finally {
      setIsAddingProducts(false);
    }
  };

  const handleRemoveProduct = async (variantId: string) => {
    setProductToRemove(variantId);
    setShowRemoveProductModal(true);
  };

  const confirmRemoveProduct = async () => {
    if (!productToRemove) return;

    try {
      const success = await removeProductsFromSubscription(subscriptionId!, [productToRemove]);
      if (success) {
        await loadSubscriptionData(); // Refresh subscription data
        toast.success('Product removed from subscription successfully');
      }
    } catch (error) {
      console.error('Failed to remove product:', error);
      toast.error('Failed to remove product from subscription');
    } finally {
      setShowRemoveProductModal(false);
      setProductToRemove(null);
    }
  };

  const handleCancelSubscription = async () => {
    if (!subscription || subscription.status === 'cancelled') {
      toast.error('This subscription is already cancelled');
      setShowCancelDialog(false);
      return;
    }

    try {
      setIsCancelling(true);
      const success = await cancelSubscription(subscriptionId!);
      if (success) {
        setShowCancelDialog(false);
        toast.success('Subscription cancelled successfully');
        // Redirect to subscriptions list after successful cancellation
        setTimeout(() => {
          window.location.href = '/account/subscriptions';
        }, 1500);
      }
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
      toast.error('Failed to cancel subscription');
    } finally {
      setIsCancelling(false);
    }
  };

  const handleActivateSubscription = async () => {
    try {
      setIsActivating(true);
      const success = await activateSubscription(subscriptionId!);
      if (success) {
        setShowActivateDialog(false);
        await loadSubscriptionData(); // Refresh subscription data
        toast.success('Subscription activated successfully');
      }
    } catch (error) {
      console.error('Failed to activate subscription:', error);
      toast.error('Failed to activate subscription');
    } finally {
      setIsActivating(false);
    }
  };

  const handlePauseSubscription = async () => {
    try {
      setIsPausing(true);
      const success = await pauseSubscription(subscriptionId!, pauseReason);
      if (success) {
        setShowPauseDialog(false);
        setPauseReason('');
        await loadSubscriptionData(); // Refresh subscription data
        toast.success('Subscription paused successfully');
      }
    } catch (error) {
      console.error('Failed to pause subscription:', error);
      toast.error('Failed to pause subscription');
    } finally {
      setIsPausing(false);
    }
  };

  const handleResumeSubscription = async () => {
    try {
      const success = await resumeSubscription(subscriptionId!);
      if (success) {
        await loadSubscriptionData(); // Refresh subscription data
        toast.success('Subscription resumed successfully');
      }
    } catch (error) {
      console.error('Failed to resume subscription:', error);
      toast.error('Failed to resume subscription');
    }
  };

  const toggleProductSelection = (variantId: string) => {
    const newSelection = new Set(selectedProducts);
    if (newSelection.has(variantId)) {
      newSelection.delete(variantId);
    } else {
      newSelection.add(variantId);
    }
    setSelectedProducts(newSelection);
  };

  const isProductInSubscription = (productId: string) => {
    return subscription?.products?.some((p: any) => p.product_id === productId);
  };

  const getAvailableVariants = (product: any) => {
    if (!subscription?.products) return product.variants || [];
    
    const subscriptionVariantIds = subscription.products.map((p: any) => p.id);
    return (product.variants || []).filter((v: any) => !subscriptionVariantIds.includes(v.id));
  };

  if (loading || subscriptionLoading || !subscription) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Loading Header */}
          <div className="text-center mb-8">
            <h1 className={combineThemeClasses(themeClasses.text.heading, 'text-2xl font-bold mb-2')}>
              Loading Subscription Details...
            </h1>
            <p className={themeClasses.text.secondary}>
              {subscriptionLoading ? 'Fetching your subscription information' : 'Loading available products'}
            </p>
          </div>

          {/* Debug Info in Development */}
          {import.meta.env.DEV && (
            <div className={combineThemeClasses(themeClasses.card.base, 'p-4 mb-6')}>
              <h3 className={combineThemeClasses(themeClasses.text.heading, 'text-sm font-medium mb-2')}>
                Debug Information
              </h3>
              <div className={combineThemeClasses(themeClasses.text.muted, 'text-xs space-y-1')}>
                <p>Subscription ID: {subscriptionId || 'Not provided'}</p>
                <p>User ID: {user?.id || 'Not authenticated'}</p>
                <p>Subscription Loading: {subscriptionLoading ? 'Yes' : 'No'}</p>
                <p>Products Loading: {loading ? 'Yes' : 'No'}</p>
                <p>Subscription Data: {subscription ? 'Loaded' : 'Not loaded'}</p>
              </div>
            </div>
          )}

          {/* Skeleton for Subscription Header */}
          <div className="bg-surface rounded-lg shadow-md p-6 mb-8 animate-pulse">
            <div className="h-6 bg-gray-300 rounded w-3/4 mb-4"></div>
            <div className="flex items-center space-x-4">
              <div className="h-4 bg-gray-300 rounded w-1/4"></div>
              <div className="h-4 bg-gray-300 rounded w-1/4"></div>
              <div className="h-4 bg-gray-300 rounded w-1/4"></div>
            </div>
          </div>

          {/* Skeleton for Current Products */}
          <div className="mb-8">
            <div className="h-6 bg-gray-300 rounded w-1/2 mb-6 animate-pulse"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(3)].map((_, i) => ( // Show 3 skeleton cards
                <div key={i} className="bg-surface rounded-lg shadow-md p-4 animate-pulse">
                  <div className="h-48 bg-gray-300 rounded mb-4"></div>
                  <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
                  <div className="h-4 bg-gray-300 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          </div>

          {/* Skeleton for Add Products Section */}
          <div className="bg-surface rounded-lg shadow-md p-6 animate-pulse">
            <div className="h-6 bg-gray-300 rounded w-2/3 mb-6"></div>
            <div className="h-10 bg-gray-300 rounded mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(3)].map((_, i) => ( // Show 3 skeleton cards
                <div key={i} className="bg-surface rounded-lg shadow-md p-4 animate-pulse">
                  <div className="h-48 bg-gray-300 rounded mb-4"></div>
                  <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
                  <div className="h-4 bg-gray-300 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }


  return (
    <div className="container mx-auto px-4 py-8 text-copy">
      {/* Breadcrumb */}
      <nav className="flex mb-6 text-sm">
        <Link to="/" className="text-copy-lighter hover:text-primary">Home</Link>
        <ChevronRightIcon size={16} className="mx-2" />
        <Link to="/account/subscriptions" className="text-copy-lighter hover:text-primary">Subscriptions</Link>
        <ChevronRightIcon size={16} className="mx-2" />
        <span className="text-copy">Manage Subscription</span>
      </nav>

      <div className="max-w-6xl mx-auto">
        {/* Subscription Header */}
        <div className={combineThemeClasses(themeClasses.card.base, 'p-6 mb-8')}>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
            <div>
              <h1 className={combineThemeClasses(themeClasses.text.heading, 'text-2xl font-bold mb-2')}>
                {subscription.plan_id.charAt(0).toUpperCase() + subscription.plan_id.slice(1)} Subscription
              </h1>
              <div className={combineThemeClasses(themeClasses.text.secondary, 'flex items-center space-x-4 text-sm')}>
                <div className="flex items-center">
                  <CalendarIcon size={16} className="mr-1" />
                  <span>Next billing: {new Date(subscription.next_billing_date).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center">
                  <CreditCardIcon size={16} className="mr-1" />
                  <span>{formatPriceWithFallback(subscription, subscription.currency, formatCurrency, 'Price not set')}/{subscription.billing_cycle}</span>
                </div>
                <div className="flex items-center">
                  <ShoppingBagIcon size={16} className="mr-1" />
                  <span>{subscription.products?.length || 0} products</span>
                </div>
              </div>
            </div>
            <div className="mt-4 md:mt-0">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                subscription.status === 'active' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}
              </span>
            </div>
          </div>

          {/* Auto-Renew Toggle */}
          <div className="mb-6">
            <AutoRenewToggle
              isEnabled={subscription.auto_renew || false}
              onToggle={async (enabled) => {
                try {
                  const success = await updateSubscription(subscriptionId!, { auto_renew: enabled });
                  if (success) {
                    setSubscription((prev: any) => ({ ...prev, auto_renew: enabled }));
                  }
                } catch (error) {
                  console.error('Failed to update auto-renew:', error);
                  toast.error('Failed to update auto-renew setting');
                }
              }}
              nextBillingDate={subscription.next_billing_date}
              billingCycle={subscription.billing_cycle}
              showDetails={true}
              size="md"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3 justify-end">
            {subscription.status === 'cancelled' && (
              <Button
                onClick={() => setShowActivateDialog(true)}
                variant="primary"
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                <PlusIcon size={16} className="mr-2" />
                Activate Subscription
              </Button>
            )}
            
            {subscription.status === 'active' && (
              <Button
                onClick={() => setShowPauseDialog(true)}
                variant="outline"
                className="text-yellow-600 border-yellow-200 hover:bg-yellow-50 hover:border-yellow-300"
              >
                Pause Subscription
              </Button>
            )}
            
            {subscription.status === 'paused' && (
              <Button
                onClick={handleResumeSubscription}
                variant="primary"
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Resume Subscription
              </Button>
            )}
            
            {(subscription.status === 'active' || subscription.status === 'paused') && (
              <Button
                onClick={() => setShowCancelDialog(true)}
                variant="outline"
                className="text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
              >
                <TrashIcon size={16} className="mr-2" />
                Cancel Subscription
              </Button>
            )}
          </div>
        </div>

        {/* Current Products */}
        <div className="mb-8">
          <h2 className={combineThemeClasses(themeClasses.text.heading, 'text-xl font-bold mb-4')}>
            Current Products in Your Subscription
          </h2>
          {subscription.products && subscription.products.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {subscription.products.map((variantInSubscription: any) => (
                <SubscriptionProductCard
                  key={variantInSubscription.id}
                  product={{
                    id: variantInSubscription.id,
                    product_id: variantInSubscription.product_id,
                    product_name: variantInSubscription.product_name || variantInSubscription.name,
                    name: variantInSubscription.product_name || variantInSubscription.name,
                    price: getBestPrice(variantInSubscription),
                    currency: subscription.currency,
                    quantity: variantInSubscription.quantity || 1,
                    primary_image: variantInSubscription.primary_image,
                    images: variantInSubscription.images,
                    variant_name: variantInSubscription.name,
                    variant_id: variantInSubscription.id,
                    stock: variantInSubscription.stock,
                    sku: variantInSubscription.sku
                  }}
                  onRemove={handleRemoveProduct}
                  showActions={true}
                  viewMode="grid"
                />
              ))}
            </div>
          ) : (
            <div className={combineThemeClasses(themeClasses.card.base, 'text-center py-8')}>
              <ShoppingBagIcon size={48} className={combineThemeClasses(themeClasses.text.muted, 'mx-auto mb-4')} />
              <p className={themeClasses.text.secondary}>No products in your subscription yet.</p>
            </div>
          )}
        </div>

        {/* Add Products Section */}
        <div className={combineThemeClasses(themeClasses.card.base, 'p-6')}>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
            <h2 className={combineThemeClasses(themeClasses.text.heading, 'text-xl font-bold mb-4 md:mb-0')}>
              Add Products to Your Subscription
            </h2>
            {selectedProducts.size > 0 && (
              <Button
                onClick={handleAddProducts}
                disabled={isAddingProducts}
                className={combineThemeClasses(getButtonClasses('primary'), 'flex items-center')}
              >
                <PlusIcon size={16} className="mr-2" />
                Add {selectedProducts.size} Product{selectedProducts.size !== 1 ? 's' : ''}
                {isAddingProducts && <div className="ml-2 animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>}
              </Button>
            )}
          </div>

          {/* Search */}
          <div className="mb-6">
            <input
              type="text"
              placeholder="Search for products to add..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={combineThemeClasses(
                themeClasses.input.base,
                themeClasses.input.default,
                'w-full px-4 py-2'
              )}
            />
          </div>

          {/* Available Products */}
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className={combineThemeClasses(themeClasses.loading.spinner, 'h-8 w-8')}></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {availableProducts.map((product: any) => {
                const availableVariants = getAvailableVariants(product);
                
                if (availableVariants.length === 0) {
                  return null; // Skip products with no available variants
                }

                return availableVariants.map((variant: any) => (
                  <div key={variant.id} className="relative">
                    <SubscriptionProductCard
                      product={{
                        id: variant.id,
                        product_id: product.id,
                        product_name: product.name,
                        name: product.name,
                        price: getBestPrice(variant),
                        currency: subscription.currency,
                        primary_image: variant.primary_image,
                        images: variant.images,
                        variant_name: variant.name,
                        variant_id: variant.id,
                        stock: variant.stock,
                        sku: variant.sku
                      }}
                      showActions={false}
                      viewMode="grid"
                    />
                    <Button
                      onClick={() => toggleProductSelection(variant.id)}
                      variant={selectedProducts.has(variant.id) ? "primary" : "outline"}
                      size="sm"
                      className="absolute top-2 right-2 bg-white/90"
                    >
                      {selectedProducts.has(variant.id) ? (
                        <MinusIcon size={16} />
                      ) : (
                        <PlusIcon size={16} />
                      )}
                    </Button>
                  </div>
                ));
              })}
            </div>
          )}

          {!loading && availableProducts.length === 0 && (
            <div className={combineThemeClasses(themeClasses.card.base, 'text-center py-8')}>
              <p className={themeClasses.text.secondary}>No products found. Try a different search term.</p>
            </div>
          )}
        </div>
      </div>

      {/* Cancel Subscription Confirmation Dialog */}
      {showCancelDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className={combineThemeClasses(themeClasses.card.base, 'w-full max-w-md')}>
            <div className="p-6">
              <div className="flex items-center mb-4">
                <AlertTriangleIcon className="w-6 h-6 text-red-600 mr-3" />
                <h3 className={combineThemeClasses(themeClasses.text.heading, 'text-lg font-bold')}>
                  Cancel Subscription
                </h3>
              </div>
              
              <div className="mb-6">
                <p className={combineThemeClasses(themeClasses.text.secondary, 'mb-3')}>
                  Are you sure you want to cancel your subscription? This action cannot be undone.
                </p>
                <div className={combineThemeClasses(themeClasses.background.elevated, 'p-3 rounded-lg')}>
                  <p className={combineThemeClasses(themeClasses.text.primary, 'text-sm font-medium mb-1')}>
                    {subscription.plan_id.charAt(0).toUpperCase() + subscription.plan_id.slice(1)} Plan
                  </p>
                  <p className={combineThemeClasses(themeClasses.text.muted, 'text-sm')}>
                    {formatPriceWithFallback(subscription, subscription.currency, formatCurrency, 'Price not set')}/{subscription.billing_cycle}
                  </p>
                  <p className={combineThemeClasses(themeClasses.text.muted, 'text-sm')}>
                    {subscription.products?.length || 0} products included
                  </p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <Button
                  onClick={() => setShowCancelDialog(false)}
                  variant="outline"
                  className="flex-1"
                  disabled={isCancelling}
                >
                  Keep Subscription
                </Button>
                <Button
                  onClick={handleCancelSubscription}
                  variant="primary"
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                  disabled={isCancelling}
                >
                  {isCancelling ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Cancelling...
                    </>
                  ) : (
                    'Yes, Cancel Subscription'
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Activate Subscription Confirmation Dialog */}
      {showActivateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className={combineThemeClasses(themeClasses.card.base, 'w-full max-w-md')}>
            <div className="p-6">
              <div className="flex items-center mb-4">
                <PlusIcon className="w-6 h-6 text-green-600 mr-3" />
                <h3 className={combineThemeClasses(themeClasses.text.heading, 'text-lg font-bold')}>
                  Activate Subscription
                </h3>
              </div>
              
              <div className="mb-6">
                <p className={combineThemeClasses(themeClasses.text.secondary, 'mb-3')}>
                  Are you sure you want to activate this subscription? Billing will resume according to your plan.
                </p>
                <div className={combineThemeClasses(themeClasses.background.elevated, 'p-3 rounded-lg')}>
                  <p className={combineThemeClasses(themeClasses.text.primary, 'text-sm font-medium mb-1')}>
                    {subscription.plan_id.charAt(0).toUpperCase() + subscription.plan_id.slice(1)} Plan
                  </p>
                  <p className={combineThemeClasses(themeClasses.text.muted, 'text-sm')}>
                    {formatPriceWithFallback(subscription, subscription.currency, formatCurrency, 'Price not set')}/{subscription.billing_cycle}
                  </p>
                  <p className={combineThemeClasses(themeClasses.text.muted, 'text-sm')}>
                    {subscription.products?.length || 0} products included
                  </p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <Button
                  onClick={() => setShowActivateDialog(false)}
                  variant="outline"
                  className="flex-1"
                  disabled={isActivating}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleActivateSubscription}
                  variant="primary"
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                  disabled={isActivating}
                >
                  {isActivating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Activating...
                    </>
                  ) : (
                    'Yes, Activate Subscription'
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pause Subscription Dialog */}
      {showPauseDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className={combineThemeClasses(themeClasses.card.base, 'w-full max-w-md')}>
            <div className="p-6">
              <div className="flex items-center mb-4">
                <AlertTriangleIcon className="w-6 h-6 text-yellow-600 mr-3" />
                <h3 className={combineThemeClasses(themeClasses.text.heading, 'text-lg font-bold')}>
                  Pause Subscription
                </h3>
              </div>
              
              <div className="mb-6">
                <p className={combineThemeClasses(themeClasses.text.secondary, 'mb-3')}>
                  Your subscription will be paused and billing will stop. You can resume it anytime.
                </p>
                
                <div className="mb-4">
                  <label className={combineThemeClasses(themeClasses.text.primary, 'block text-sm font-medium mb-2')}>
                    Reason for pausing (optional)
                  </label>
                  <textarea
                    value={pauseReason}
                    onChange={(e) => setPauseReason(e.target.value)}
                    placeholder="Let us know why you're pausing your subscription..."
                    className={combineThemeClasses(
                      themeClasses.input.base,
                      themeClasses.input.default,
                      'w-full px-3 py-2 h-20 resize-none'
                    )}
                  />
                </div>
                
                <div className={combineThemeClasses(themeClasses.background.elevated, 'p-3 rounded-lg')}>
                  <p className={combineThemeClasses(themeClasses.text.primary, 'text-sm font-medium mb-1')}>
                    {subscription.plan_id.charAt(0).toUpperCase() + subscription.plan_id.slice(1)} Plan
                  </p>
                  <p className={combineThemeClasses(themeClasses.text.muted, 'text-sm')}>
                    {formatPriceWithFallback(subscription, subscription.currency, formatCurrency, 'Price not set')}/{subscription.billing_cycle}
                  </p>
                  <p className={combineThemeClasses(themeClasses.text.muted, 'text-sm')}>
                    {subscription.products?.length || 0} products included
                  </p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <Button
                  onClick={() => {
                    setShowPauseDialog(false);
                    setPauseReason('');
                  }}
                  variant="outline"
                  className="flex-1"
                  disabled={isPausing}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handlePauseSubscription}
                  variant="primary"
                  className="flex-1 bg-yellow-600 hover:bg-yellow-700 text-white"
                  disabled={isPausing}
                >
                  {isPausing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Pausing...
                    </>
                  ) : (
                    'Pause Subscription'
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Remove Product Confirmation Modal */}
      <ConfirmationModal
        isOpen={showRemoveProductModal}
        onClose={() => {
          setShowRemoveProductModal(false);
          setProductToRemove(null);
        }}
        onConfirm={confirmRemoveProduct}
        title="Remove Product"
        message="Are you sure you want to remove this product from your subscription? This action cannot be undone."
        confirmText="Remove Product"
        cancelText="Keep Product"
        variant="danger"
      />
    </div>
  );
};

export default SubscriptionManagement;