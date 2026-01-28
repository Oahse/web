import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronRightIcon, PlusIcon, MinusIcon, ShoppingBagIcon, CalendarIcon, CreditCardIcon, TrashIcon, AlertTriangleIcon } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useSubscription } from '../contexts/SubscriptionContext';
import { useLocale } from '../contexts/LocaleContext';
import SubscriptionAPI from '../apis/subscription';
import { ProductsAPI } from '../apis/products';
import { SubscriptionProductCard } from '../components/subscription/SubscriptionProductCard';
import { AutoRenewToggle } from '../components/subscription/AutoRenewToggle';
import { Button } from '../components/ui/Button';
import { toast } from 'react-hot-toast';
import { themeClasses, combineThemeClasses, getButtonClasses } from '../lib/themeClasses';

export const SubscriptionManagement = () => {
  const { subscriptionId } = useParams();
  const { user } = useAuth();
  const { updateSubscription, cancelSubscription, addProductsToSubscription, removeProductsFromSubscription } = useSubscription();
  const { currency, formatCurrency } = useLocale();
  const [subscription, setSubscription] = useState(null);
  const [availableProducts, setAvailableProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [subscriptionLoading, setSubscriptionLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProducts, setSelectedProducts] = useState(new Set());
  const [isAddingProducts, setIsAddingProducts] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  useEffect(() => {
    if (subscriptionId) {
      loadSubscriptionData();
    }
  }, [subscriptionId]);

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
      const response = await SubscriptionAPI.getSubscription(subscriptionId);
      setSubscription(response.data);
    } catch (error) {
      console.error('Failed to load subscription:', error);
      toast.error('Failed to load subscription details');
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
      const variantIds = Array.from(selectedProducts);
      const success = await addProductsToSubscription(subscriptionId, variantIds);
      
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

  const handleRemoveProduct = async (variantId) => {
    if (!window.confirm('Are you sure you want to remove this product from your subscription?')) {
      return;
    }

    try {
      const success = await removeProductsFromSubscription(subscriptionId, [variantId]);
      if (success) {
        await loadSubscriptionData(); // Refresh subscription data
        toast.success('Product removed from subscription successfully');
      }
    } catch (error) {
      console.error('Failed to remove product:', error);
      toast.error('Failed to remove product from subscription');
    }
  };

  const handleCancelSubscription = async () => {
    if (subscription.status === 'cancelled') {
      toast.error('This subscription is already cancelled');
      setShowCancelDialog(false);
      return;
    }

    try {
      setIsCancelling(true);
      const success = await cancelSubscription(subscriptionId);
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

  const toggleProductSelection = (variantId) => {
    const newSelection = new Set(selectedProducts);
    if (newSelection.has(variantId)) {
      newSelection.delete(variantId);
    } else {
      newSelection.add(variantId);
    }
    setSelectedProducts(newSelection);
  };

  const isProductInSubscription = (productId) => {
    return subscription?.products?.some(p => p.product_id === productId);
  };

  const getAvailableVariants = (product) => {
    if (!subscription?.products) return product.variants || [];
    
    const subscriptionVariantIds = subscription.products.map(p => p.id);
    return (product.variants || []).filter(v => !subscriptionVariantIds.includes(v.id));
  };

  if (loading || subscriptionLoading || !subscription) {
    return (
      <div className="container mx-auto px-4 py-8">
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
                  <span>{formatCurrency(subscription.price, subscription.currency)}/{subscription.billing_cycle}</span>
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
                  const success = await updateSubscription(subscriptionId, { auto_renew: enabled });
                  if (success) {
                    setSubscription(prev => ({ ...prev, auto_renew: enabled }));
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

          {/* Cancel Subscription Button */}
          {subscription.status !== 'cancelled' && (
            <div className="flex justify-end">
              <Button
                onClick={() => setShowCancelDialog(true)}
                variant="outline"
                className="text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
              >
                <TrashIcon size={16} className="mr-2" />
                Cancel Subscription
              </Button>
            </div>
          )}
        </div>

        {/* Current Products */}
        <div className="mb-8">
          <h2 className={combineThemeClasses(themeClasses.text.heading, 'text-xl font-bold mb-4')}>
            Current Products in Your Subscription
          </h2>
          {subscription.products && subscription.products.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {subscription.products.map((variantInSubscription) => (
                <SubscriptionProductCard
                  key={variantInSubscription.id}
                  product={{
                    id: variantInSubscription.id,
                    product_id: variantInSubscription.product_id,
                    product_name: variantInSubscription.product_name || variantInSubscription.name,
                    name: variantInSubscription.product_name || variantInSubscription.name,
                    price: variantInSubscription.price || 0,
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
              {availableProducts.map((product) => {
                const availableVariants = getAvailableVariants(product);
                
                if (availableVariants.length === 0) {
                  return null; // Skip products with no available variants
                }

                return availableVariants.map((variant) => (
                  <div key={variant.id} className="relative">
                    <SubscriptionProductCard
                      product={{
                        id: variant.id,
                        product_id: product.id,
                        product_name: product.name,
                        name: product.name,
                        price: variant.current_price || variant.base_price || 0,
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
                    {formatCurrency(subscription.price, subscription.currency)}/{subscription.billing_cycle}
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
    </div>
  );
};

export default SubscriptionManagement;