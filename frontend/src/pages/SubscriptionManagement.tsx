import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronRightIcon, PlusIcon, MinusIcon, ShoppingBagIcon, CalendarIcon, CreditCardIcon } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import SubscriptionAPI from '../apis/subscription';
import { ProductsAPI } from '../apis/products';
import { ProductCard } from '../components/product/ProductCard';
import { Button } from '../components/ui/Button';
import { toast } from 'react-hot-toast';

export const SubscriptionManagement = () => {
  const { subscriptionId } = useParams();
  const { user } = useAuth();
  const [subscription, setSubscription] = useState(null);
  const [availableProducts, setAvailableProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [subscriptionLoading, setSubscriptionLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProducts, setSelectedProducts] = useState(new Set());
  const [isAddingProducts, setIsAddingProducts] = useState(false);

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
      setAvailableProducts(response.data?.products || []);
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
      setAvailableProducts(response.data?.products || []);
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
      await SubscriptionAPI.addProductsToSubscription(subscriptionId, variantIds);
      
      toast.success(`Added ${selectedProducts.size} product(s) to your subscription!`);
      setSelectedProducts(new Set());
      await loadSubscriptionData(); // Refresh subscription data
    } catch (error) {
      console.error('Failed to add products:', error);
      toast.error('Failed to add products to subscription');
    } finally {
      setIsAddingProducts(false);
    }
  };

  const handleRemoveProduct = async (variantId) => {
    try {
      await SubscriptionAPI.removeProductsFromSubscription(subscriptionId, [variantId]);
      toast.success('Product removed from subscription');
      await loadSubscriptionData(); // Refresh subscription data
    } catch (error) {
      console.error('Failed to remove product:', error);
      toast.error('Failed to remove product from subscription');
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
        <div className="bg-surface rounded-lg shadow-md p-6 mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-copy mb-2">
                {subscription.plan_id.charAt(0).toUpperCase() + subscription.plan_id.slice(1)} Subscription
              </h1>
              <div className="flex items-center space-x-4 text-sm text-copy-light">
                <div className="flex items-center">
                  <CalendarIcon size={16} className="mr-1" />
                  <span>Next billing: {new Date(subscription.next_billing_date).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center">
                  <CreditCardIcon size={16} className="mr-1" />
                  <span>${subscription.price}/{subscription.billing_cycle}</span>
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
        </div>

        {/* Current Products */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-copy mb-4">Current Products in Your Subscription</h2>
          {subscription.products && subscription.products.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {subscription.products.map((variantInSubscription) => (
                <div key={variantInSubscription.id} className="relative">
                  <ProductCard 
                    product={{
                      id: variantInSubscription.product_id, // Use the product_id from the variant
                      name: variantInSubscription.product_name || variantInSubscription.name, // Use product name or variant name
                      image: variantInSubscription.primary_image?.url || '/placeholder-product.jpg',
                      variants: [], // ProductCard will use selectedVariant for price, etc.
                    }}
                    selectedVariant={variantInSubscription}
                    viewMode="grid"
                  />
                  <Button
                    onClick={() => handleRemoveProduct(product.id)}
                    variant="outline"
                    size="sm"
                    className="absolute top-2 right-2 bg-white/90 hover:bg-red-50 text-red-600 border-red-200"
                  >
                    <MinusIcon size={16} />
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-copy-light">
              <ShoppingBagIcon size={48} className="mx-auto mb-4 text-copy-lighter" />
              <p>No products in your subscription yet.</p>
            </div>
          )}
        </div>

        {/* Add Products Section */}
        <div className="bg-surface rounded-lg shadow-md p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
            <h2 className="text-xl font-bold text-copy mb-4 md:mb-0">Add Products to Your Subscription</h2>
            {selectedProducts.size > 0 && (
              <Button
                onClick={handleAddProducts}
                disabled={isAddingProducts}
                className="flex items-center"
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
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          {/* Available Products */}
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
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
                    <ProductCard 
                      product={product} // Pass the full product object
                      selectedVariant={variant} // Pass the specific variant as selected
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
            <div className="text-center py-8 text-copy-light">
              <p>No products found. Try a different search term.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SubscriptionManagement;