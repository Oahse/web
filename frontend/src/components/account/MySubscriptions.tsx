import React, { useState, useEffect } from 'react';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { useLocale } from '../../contexts/LocaleContext';
import { 
  PlusIcon, 
  SearchIcon,
  PackageIcon,
  XIcon
} from 'lucide-react';
import { themeClasses, getButtonClasses } from '../../lib/themeClasses';
import ProductsAPI from '../../apis/products';
import { toast } from 'react-hot-toast';
import { Product } from '../../types';
import { AutoRenewToggle } from '../subscription/AutoRenewToggle';
import { SubscriptionCard } from '../subscription/SubscriptionCard';
import { ConfirmationModal } from '../ui/ConfirmationModal';

interface NewSubscriptionData {
  plan_id: string;
  billing_cycle: string;
  product_variant_ids: string[];
  delivery_type: string;
  currency: string;
  auto_renew: boolean;
}

export const MySubscriptions = () => {
  const { 
    subscriptions, 
    loading, 
    error, 
    refreshSubscriptions, 
    createSubscription, 
    updateSubscription, 
    cancelSubscription,
    activateSubscription,
    pauseSubscription,
    resumeSubscription,
    addProductsToSubscription,
    removeProductsFromSubscription 
  } = useSubscription();
  const { currency, formatCurrency: formatCurrencyLocale } = useLocale();
  const [activeTab, setActiveTab] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [showAddProductModal, setShowAddProductModal] = useState<boolean>(false);
  const [selectedSubscription, setSelectedSubscription] = useState<any>(null);
  const [availableProducts, setAvailableProducts] = useState<Product[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedProducts, setSelectedProducts] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showActivateModal, setShowActivateModal] = useState<boolean>(false);
  const [subscriptionToActivate, setSubscriptionToActivate] = useState<string | null>(null);

  // New subscription form state - use user's detected currency
  const [newSubscription, setNewSubscription] = useState<NewSubscriptionData>({
    plan_id: 'basic',
    billing_cycle: 'monthly',
    product_variant_ids: [],
    delivery_type: 'standard',
    currency: currency, // Use user's detected currency
    auto_renew: true
  });
  const [selectedProductsForNew, setSelectedProductsForNew] = useState<Set<string>>(new Set());

  // Update currency when user's locale changes
  useEffect(() => {
    setNewSubscription(prev => ({ ...prev, currency: currency }));
  }, [currency]);

  useEffect(() => {
    refreshSubscriptions();
  }, [refreshSubscriptions]);

  useEffect(() => {
    if (showCreateModal || showAddProductModal) {
      loadAvailableProducts();
    }
  }, [showCreateModal, showAddProductModal, searchQuery]);

  const loadAvailableProducts = async () => {
    try {
      console.log('Loading products with query:', searchQuery);
      const response = await ProductsAPI.getProducts({ 
        q: searchQuery,
        page: 1,
        limit: 20 
      });
      console.log('Products response:', response);
      
      // Handle different response structures
      const products = response.data?.data || response.data || [];
      setAvailableProducts(Array.isArray(products) ? products : []);
    } catch (error) {
      console.error('Failed to load products:', error);
      toast.error('Failed to load products');
      setAvailableProducts([]);
    }
  };

  const handleCreateSubscription = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      // Convert selected products to array
      const productVariantIds = Array.from(selectedProductsForNew);
      
      // Ensure we have at least one product selected
      if (productVariantIds.length === 0) {
        toast.error('Please select at least one product for the subscription');
        return;
      }

      const subscriptionData = {
        ...newSubscription,
        product_variant_ids: productVariantIds
      };

      const result = await createSubscription(subscriptionData);
      if (result) {
        setShowCreateModal(false);
        setNewSubscription({
          plan_id: 'basic',
          billing_cycle: 'monthly',
          product_variant_ids: [],
          delivery_type: 'standard',
          currency: currency,
          auto_renew: true
        });
        setSelectedProductsForNew(new Set());
      }
    } catch (error) {
      console.error('Failed to create subscription:', error);
      toast.error('Failed to create subscription');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddProducts = async () => {
    if (selectedProducts.size === 0) {
      toast.error('Please select at least one product');
      return;
    }

    if (!selectedSubscription) {
      toast.error('No subscription selected');
      return;
    }

    setIsLoading(true);
    try {
      const variantIds = Array.from(selectedProducts);
      const result = await addProductsToSubscription(selectedSubscription.id, variantIds);
      if (result) {
        setShowAddProductModal(false);
        setSelectedProducts(new Set());
      }
    } catch (error) {
      console.error('Failed to add products:', error);
      toast.error('Failed to add products to subscription');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveProduct = async (subscriptionId: string, variantId: string) => {
    try {
      await removeProductsFromSubscription(subscriptionId, [variantId]);
    } catch (error) {
      console.error('Failed to remove product:', error);
      toast.error('Failed to remove product');
    }
  };

  const handleUpdatePeriod = async (subscriptionId: string, newPeriod: string) => {
    try {
      await updateSubscription(subscriptionId, { billing_cycle: newPeriod });
    } catch (error) {
      console.error('Failed to update subscription:', error);
      toast.error('Failed to update subscription period');
    }
  };

  const handleDeleteSubscription = async (subscriptionId: string, reason?: string) => {
    try {
      await cancelSubscription(subscriptionId, reason);
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
      toast.error('Failed to cancel subscription');
    }
  };

  const handleActivateSubscription = async (subscriptionId: string) => {
    setSubscriptionToActivate(subscriptionId);
    setShowActivateModal(true);
  };

  const confirmActivateSubscription = async () => {
    if (!subscriptionToActivate) return;
    
    try {
      await activateSubscription(subscriptionToActivate);
    } catch (error) {
      console.error('Failed to activate subscription:', error);
      toast.error('Failed to activate subscription');
    } finally {
      setShowActivateModal(false);
      setSubscriptionToActivate(null);
    }
  };

  const handlePauseSubscription = async (subscriptionId: string, reason?: string) => {
    try {
      await pauseSubscription(subscriptionId, reason || undefined);
    } catch (error) {
      console.error('Failed to pause subscription:', error);
      toast.error('Failed to pause subscription');
    }
  };

  const handleResumeSubscription = async (subscriptionId: string) => {
    try {
      await resumeSubscription(subscriptionId);
    } catch (error) {
      console.error('Failed to resume subscription:', error);
      toast.error('Failed to resume subscription');
    }
  };

  const handleOpenAddProductModal = (subscription: any) => {
    setSelectedSubscription(subscription);
    setShowAddProductModal(true);
  };

  const filteredSubscriptions = subscriptions.filter((sub: any) => {
    if (activeTab === 'all') return true;
    if (activeTab === 'active') return sub.status === 'active';
    if (activeTab === 'paused') return sub.status === 'paused';
    if (activeTab === 'cancelled') return sub.status === 'cancelled';
    return true;
  });

  // Early returns after all hooks
  if (loading) {
    return (
      <div className="text-center p-6">
        <div className={`${themeClasses.loading.spinner} w-12 h-12 mx-auto`}></div>
        <p className={`${themeClasses.text.secondary} mt-4`}>Loading your subscriptions...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-6">
        <p className={themeClasses.text.error}>Error loading subscriptions: {error}</p>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <h1 className={`${themeClasses.text.heading} text-2xl`}>My Subscriptions</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className={`${getButtonClasses('primary')} flex items-center w-full sm:w-auto justify-center`}
        >
          <PlusIcon size={20} className="mr-2" />
          New Subscription
        </button>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 mb-6 bg-surface-elevated rounded-lg p-1 overflow-x-auto">
        {[
          { key: 'all', label: 'All', count: subscriptions.length },
          { key: 'active', label: 'Active', count: subscriptions.filter((s: any) => s.status === 'active').length },
          { key: 'paused', label: 'Paused', count: subscriptions.filter((s: any) => s.status === 'paused').length },
          { key: 'cancelled', label: 'Cancelled', count: subscriptions.filter((s: any) => s.status === 'cancelled').length }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-3 sm:px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === tab.key
                ? `${themeClasses.background.surface} ${themeClasses.text.primary} shadow-sm`
                : `${themeClasses.text.secondary} hover:${themeClasses.text.primary}`
            }`}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      {/* Subscriptions List */}
      {filteredSubscriptions.length === 0 ? (
        <div className={`${themeClasses.card.base} text-center py-12`}>
          <PackageIcon size={48} className={`${themeClasses.text.muted} mx-auto mb-4`} />
          <p className={`${themeClasses.text.secondary} mb-3`}>
            {activeTab === 'all' 
              ? "You don't have any subscriptions yet." 
              : `No ${activeTab} subscriptions found.`
            }
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className={getButtonClasses('primary')}
          >
            Create Your First Subscription
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          {filteredSubscriptions.map((subscription: any) => (
            <SubscriptionCard
              key={subscription.id}
              subscription={subscription}
              onUpdate={async (subscriptionId, data) => {
                await updateSubscription(subscriptionId, data);
              }}
              onCancel={handleDeleteSubscription}
              onActivate={handleActivateSubscription}
              onPause={handlePauseSubscription}
              onResume={handleResumeSubscription}
              onProductsUpdated={refreshSubscriptions}
              onAddProducts={handleOpenAddProductModal}
              onRemoveProduct={handleRemoveProduct}
              showActions={true}
              compact={false}
            />
          ))}
        </div>
      )}

      {/* Create Subscription Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className={`${themeClasses.card.base} w-full max-w-2xl max-h-[90vh] overflow-y-auto`}>
            <div className="p-6">
              <h2 className={`${themeClasses.text.heading} text-xl mb-4`}>Create New Subscription</h2>
              <form onSubmit={handleCreateSubscription}>
                <div className="space-y-4">
                  <div>
                    <label className={`${themeClasses.text.primary} block text-sm font-medium mb-1`}>
                      Subscription Plan
                    </label>
                    <select
                      value={newSubscription.plan_id}
                      onChange={(e) => setNewSubscription({...newSubscription, plan_id: e.target.value})}
                      className={`${themeClasses.input.base} ${themeClasses.input.default}`}
                      required
                    >
                      <option value="basic">Basic Plan</option>
                      <option value="premium">Premium Plan</option>
                      <option value="enterprise">Enterprise Plan</option>
                    </select>
                  </div>
                  <div>
                    <label className={`${themeClasses.text.primary} block text-sm font-medium mb-1`}>
                      Billing Period
                    </label>
                    <select
                      value={newSubscription.billing_cycle}
                      onChange={(e) => setNewSubscription({...newSubscription, billing_cycle: e.target.value})}
                      className={`${themeClasses.input.base} ${themeClasses.input.default}`}
                    >
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                      <option value="yearly">Yearly</option>
                    </select>
                  </div>
                  <div>
                    <label className={`${themeClasses.text.primary} block text-sm font-medium mb-1`}>
                      Delivery Type
                    </label>
                    <select
                      value={newSubscription.delivery_type}
                      onChange={(e) => setNewSubscription({...newSubscription, delivery_type: e.target.value})}
                      className={`${themeClasses.input.base} ${themeClasses.input.default}`}
                    >
                      <option value="standard">Standard Delivery</option>
                      <option value="express">Express Delivery</option>
                      <option value="overnight">Overnight Delivery</option>
                    </select>
                  </div>
                  <div>
                    <label className={`${themeClasses.text.primary} block text-sm font-medium mb-1`}>
                      Currency
                    </label>
                    <select
                      value={newSubscription.currency}
                      onChange={(e) => setNewSubscription({...newSubscription, currency: e.target.value})}
                      className={`${themeClasses.input.base} ${themeClasses.input.default}`}
                    >
                      <option value="USD">USD</option>
                      <option value="EUR">EUR</option>
                      <option value="GBP">GBP</option>
                    </select>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="auto_renew"
                      checked={newSubscription.auto_renew}
                      onChange={(e) => setNewSubscription({...newSubscription, auto_renew: e.target.checked})}
                      className="sr-only"
                    />
                    <AutoRenewToggle
                      isEnabled={newSubscription.auto_renew}
                      onToggle={(enabled) => setNewSubscription({...newSubscription, auto_renew: enabled})}
                      showDetails={false}
                      size="sm"
                    />
                  </div>
                  
                  {/* Product Selection */}
                  <div>
                    <label className={`${themeClasses.text.primary} block text-sm font-medium mb-2`}>
                      Select Product Variants ({selectedProductsForNew.size} selected)
                    </label>
                    
                    {/* Selected Products Summary */}
                    {selectedProductsForNew.size > 0 && (
                      <div className={`${themeClasses.background.elevated} rounded-lg p-3 mb-3 border-l-4 border-blue-500`}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-5 h-5 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                              {selectedProductsForNew.size}
                            </div>
                            <span className={`${themeClasses.text.primary} text-sm font-medium`}>
                              {selectedProductsForNew.size} variant{selectedProductsForNew.size !== 1 ? 's' : ''} selected
                            </span>
                          </div>
                          <button
                            onClick={() => setSelectedProductsForNew(new Set())}
                            className={`${themeClasses.text.secondary} hover:${themeClasses.text.primary} text-xs`}
                          >
                            Clear all
                          </button>
                        </div>
                      </div>
                    )}

                    <div className="border border-border rounded-md bg-background shadow-sm">
                      <div className="max-h-64 overflow-y-auto">
                        {availableProducts.length === 0 ? (
                          <div className="text-center py-8">
                            <PackageIcon size={32} className={`${themeClasses.text.muted} mx-auto mb-2`} />
                            <p className={`${themeClasses.text.secondary} text-sm`}>
                              Loading products…
                            </p>
                          </div>
                        ) : (
                          <div className="divide-y divide-border">
                            {availableProducts.map((product: Product) => (
                              <div key={product.id} className="p-4">
                                {/* Product Header */}
                                <div className="flex items-center gap-3 mb-3">
                                  {product.images && product.images.length > 0 ? (
                                    <img
                                      src={product.images[0].url}
                                      alt={product.name}
                                      className="w-12 h-12 rounded-lg object-cover border border-border flex-shrink-0"
                                    />
                                  ) : (
                                    <div className="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                                      <PackageIcon className="w-6 h-6 text-gray-400" />
                                    </div>
                                  )}
                                  <div className="flex-1 min-w-0">
                                    <h4 className={`${themeClasses.text.primary} font-semibold text-sm truncate`}>
                                      {product.name}
                                    </h4>
                                    {product.description && (
                                      <p className={`${themeClasses.text.secondary} text-xs mt-1 truncate`}>
                                        {product.description}
                                      </p>
                                    )}
                                  </div>
                                </div>

                                {/* Variants */}
                                {product.variants?.length ? (
                                  <div className="space-y-2 ml-15">
                                    {product.variants.map((variant: any) => (
                                      <label
                                        key={variant.id}
                                        className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                                      >
                                        <input
                                          type="checkbox"
                                          checked={selectedProductsForNew.has(variant.id)}
                                          onChange={(e) => {
                                            const next = new Set(selectedProductsForNew);
                                            e.target.checked
                                              ? next.add(variant.id)
                                              : next.delete(variant.id);
                                            setSelectedProductsForNew(next);
                                          }}
                                          className={`${themeClasses.input.base} flex-shrink-0`}
                                        />

                                        {/* Variant Image */}
                                        {variant.images?.[0]?.url ? (
                                          <img
                                            src={variant.images[0].url}
                                            alt={variant.name}
                                            className="w-8 h-8 rounded object-cover border border-border flex-shrink-0"
                                          />
                                        ) : (
                                          <div className="w-8 h-8 rounded bg-gray-100 flex items-center justify-center flex-shrink-0">
                                            <PackageIcon className="w-4 h-4 text-gray-400" />
                                          </div>
                                        )}

                                        {/* Variant Info */}
                                        <div className="flex-1 min-w-0">
                                          <span className={`${themeClasses.text.primary} text-sm font-medium`}>
                                            {variant.name || "Default Variant"}
                                          </span>
                                        </div>

                                        {/* Price */}
                                        <span className={`${themeClasses.text.secondary} text-sm font-medium flex-shrink-0`}>
                                          {formatCurrencyLocale(
                                            variant.current_price || variant.base_price || 0,
                                            currency
                                          )}
                                        </span>
                                      </label>
                                    ))}
                                  </div>
                                ) : (
                                  <div className="ml-15">
                                    <label className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
                                      <input
                                        type="checkbox"
                                        checked={selectedProductsForNew.has(product.id)}
                                        onChange={(e) => {
                                          const next = new Set(selectedProductsForNew);
                                          e.target.checked
                                            ? next.add(product.id)
                                            : next.delete(product.id);
                                          setSelectedProductsForNew(next);
                                        }}
                                        className={`${themeClasses.input.base} flex-shrink-0`}
                                      />
                                      <span className={`${themeClasses.text.primary} text-sm`}>
                                        Default variant
                                      </span>
                                      <span className={`${themeClasses.text.secondary} text-sm font-medium ml-auto`}>
                                        {formatCurrencyLocale(product.price || 0, currency)}
                                      </span>
                                    </label>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className={`${themeClasses.background.elevated} rounded-md p-3`}>
                    <p className={`${themeClasses.text.secondary} text-sm`}>
                      You must select at least one product to create a subscription.
                    </p>
                  </div>
                </div>
                <div className="flex flex-col sm:flex-row justify-end space-y-3 sm:space-y-0 sm:space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateModal(false);
                      setSelectedProductsForNew(new Set());
                    }}
                    className={`${getButtonClasses('outline')} w-full sm:w-auto`}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isLoading || selectedProductsForNew.size === 0}
                    className={`${getButtonClasses('primary')} w-full sm:w-auto`}
                  >
                    {isLoading ? 'Creating...' : `Create Subscription (${selectedProductsForNew.size} variants)`}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Add Products Modal */}
      {showAddProductModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className={`${themeClasses.card.base} w-full max-w-6xl max-h-[90vh] overflow-hidden`}>
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className={`${themeClasses.text.heading} text-2xl font-bold`}>Add Products to Subscription</h2>
                  <p className={`${themeClasses.text.secondary} text-sm mt-1`}>
                    Select product variants to add to your subscription
                  </p>
                </div>
                <button
                  onClick={() => setShowAddProductModal(false)}
                  className={`${themeClasses.text.muted} hover:${themeClasses.text.primary} p-2 rounded-full hover:bg-gray-100 transition-colors`}
                >
                  <XIcon size={24} />
                </button>
              </div>
              
              {/* Search */}
              <div className="mb-6">
                <div className="relative">
                  <SearchIcon size={20} className={`${themeClasses.text.muted} absolute left-3 top-1/2 transform -translate-y-1/2`} />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search products by name..."
                    className={`${themeClasses.input.base} ${themeClasses.input.default} pl-10 text-base`}
                  />
                </div>
              </div>

              {/* Selected Products Summary */}
              {selectedProducts.size > 0 && (
                <div className={`${themeClasses.background.elevated} rounded-lg p-4 mb-6 border-l-4 border-blue-500`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                        {selectedProducts.size}
                      </div>
                      <span className={`${themeClasses.text.primary} font-medium`}>
                        {selectedProducts.size} variant{selectedProducts.size !== 1 ? 's' : ''} selected
                      </span>
                    </div>
                    <button
                      onClick={() => setSelectedProducts(new Set())}
                      className={`${themeClasses.text.secondary} hover:${themeClasses.text.primary} text-sm`}
                    >
                      Clear all
                    </button>
                  </div>
                </div>
              )}

              {/* Products List */}
              <div className="max-h-[400px] overflow-y-auto mb-6">
                {availableProducts.length === 0 ? (
                  <div className="text-center py-12">
                    <PackageIcon size={48} className={`${themeClasses.text.muted} mx-auto mb-4`} />
                    <p className={`${themeClasses.text.secondary} mb-2`}>
                      {searchQuery ? 'No products found matching your search.' : 'Loading products...'}
                    </p>
                    {searchQuery && (
                      <button
                        onClick={() => setSearchQuery('')}
                        className={`${themeClasses.text.primary} hover:underline text-sm`}
                      >
                        Clear search
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="border border-border rounded-md bg-background shadow-sm">
                    <div className="divide-y divide-border">
                      {availableProducts.map((product: Product) => (
                        <div key={product.id} className="p-4">
                          {/* Product Header */}
                          <div className="flex items-center gap-3 mb-3">
                            {product.images && product.images.length > 0 ? (
                              <img
                                src={product.images[0].url}
                                alt={product.name}
                                className="w-12 h-12 rounded-lg object-cover border border-border flex-shrink-0"
                              />
                            ) : (
                              <div className="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                                <PackageIcon className="w-6 h-6 text-gray-400" />
                              </div>
                            )}
                            <div className="flex-1 min-w-0">
                              <h4 className={`${themeClasses.text.primary} font-semibold text-base truncate`}>
                                {product.name}
                              </h4>
                              {product.description && (
                                <p className={`${themeClasses.text.secondary} text-sm mt-1 truncate`}>
                                  {product.description}
                                </p>
                              )}
                              <div className="flex items-center gap-2 mt-1">
                                <span className={`${themeClasses.text.primary} font-medium text-sm`}>
                                  {formatCurrencyLocale(product.price || product.min_price || 0, currency)}
                                </span>
                                {product.min_price !== product.max_price && product.max_price && (
                                  <span className={`${themeClasses.text.secondary} text-xs`}>
                                    - {formatCurrencyLocale(product.max_price, currency)}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Variants */}
                          {product.variants?.length ? (
                            <div className="space-y-2 ml-15">
                              <p className={`${themeClasses.text.secondary} text-xs font-medium mb-2`}>
                                Available Variants:
                              </p>
                              {product.variants.map((variant: any) => (
                                <label
                                  key={variant.id}
                                  className={`flex items-center gap-3 p-3 rounded-lg border transition-all cursor-pointer ${
                                    selectedProducts.has(variant.id) 
                                      ? 'border-blue-500 bg-blue-50' 
                                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                  }`}
                                >
                                  <input
                                    type="checkbox"
                                    checked={selectedProducts.has(variant.id)}
                                    onChange={(e) => {
                                      const next = new Set(selectedProducts);
                                      e.target.checked
                                        ? next.add(variant.id)
                                        : next.delete(variant.id);
                                      setSelectedProducts(next);
                                    }}
                                    className="sr-only"
                                  />
                                  
                                  {/* Custom Checkbox */}
                                  <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                                    selectedProducts.has(variant.id) 
                                      ? 'bg-blue-500 border-blue-500 text-white' 
                                      : 'border-gray-300 hover:border-blue-400'
                                  }`}>
                                    {selectedProducts.has(variant.id) && (
                                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                      </svg>
                                    )}
                                  </div>

                                  {/* Variant Image */}
                                  {variant.images?.[0]?.url ? (
                                    <img
                                      src={variant.images[0].url}
                                      alt={variant.name}
                                      className="w-10 h-10 rounded-lg object-cover border border-border flex-shrink-0"
                                    />
                                  ) : (
                                    <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                                      <PackageIcon className="w-5 h-5 text-gray-400" />
                                    </div>
                                  )}

                                  {/* Variant Info */}
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center justify-between">
                                      <span className={`${themeClasses.text.primary} font-medium text-sm`}>
                                        {variant.name || "Default Variant"}
                                      </span>
                                      <span className={`${themeClasses.text.primary} font-bold text-sm`}>
                                        {formatCurrencyLocale(
                                          variant.current_price || variant.base_price || 0,
                                          currency
                                        )}
                                      </span>
                                    </div>
                                    {variant.description && (
                                      <p className={`${themeClasses.text.secondary} text-xs mt-1 truncate`}>
                                        {variant.description}
                                      </p>
                                    )}
                                    {variant.sku && (
                                      <p className={`${themeClasses.text.muted} text-xs mt-1`}>
                                        SKU: {variant.sku}
                                      </p>
                                    )}
                                  </div>
                                </label>
                              ))}
                            </div>
                          ) : (
                            <div className="ml-15">
                              <label className={`flex items-center gap-3 p-3 rounded-lg border transition-all cursor-pointer ${
                                selectedProducts.has(product.id) 
                                  ? 'border-blue-500 bg-blue-50' 
                                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                              }`}>
                                <input
                                  type="checkbox"
                                  checked={selectedProducts.has(product.id)}
                                  onChange={(e) => {
                                    const next = new Set(selectedProducts);
                                    e.target.checked
                                      ? next.add(product.id)
                                      : next.delete(product.id);
                                    setSelectedProducts(next);
                                  }}
                                  className="sr-only"
                                />
                                
                                {/* Custom Checkbox */}
                                <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                                  selectedProducts.has(product.id) 
                                    ? 'bg-blue-500 border-blue-500 text-white' 
                                    : 'border-gray-300 hover:border-blue-400'
                                }`}>
                                  {selectedProducts.has(product.id) && (
                                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                    </svg>
                                  )}
                                </div>
                                
                                <span className={`${themeClasses.text.primary} font-medium text-sm`}>
                                  Default variant
                                </span>
                                <span className={`${themeClasses.text.primary} font-bold text-sm ml-auto`}>
                                  {formatCurrencyLocale(product.price || 0, currency)}
                                </span>
                              </label>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-4 border-t border-gray-200">
                <div className="flex items-center gap-4">
                  <p className={`${themeClasses.text.secondary} text-sm`}>
                    {selectedProducts.size} of {availableProducts.reduce((total, product) => total + (product.variants?.length || 1), 0)} variants selected
                  </p>
                  {selectedProducts.size > 0 && (
                    <button
                      onClick={() => setSelectedProducts(new Set())}
                      className={`${themeClasses.text.secondary} hover:${themeClasses.text.primary} text-sm underline`}
                    >
                      Clear selection
                    </button>
                  )}
                </div>
                
                <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3 w-full sm:w-auto">
                  <button
                    onClick={() => setShowAddProductModal(false)}
                    className={`${getButtonClasses('outline')} w-full sm:w-auto px-6 py-2`}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAddProducts}
                    disabled={selectedProducts.size === 0 || isLoading}
                    className={`${getButtonClasses('primary')} w-full sm:w-auto px-6 py-2 ${
                      selectedProducts.size === 0 ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    {isLoading ? (
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        Adding...
                      </div>
                    ) : (
                      `Add ${selectedProducts.size} Variant${selectedProducts.size !== 1 ? 's' : ''}`
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Activate Subscription Confirmation Modal */}
      <ConfirmationModal
        isOpen={showActivateModal}
        onClose={() => {
          setShowActivateModal(false);
          setSubscriptionToActivate(null);
        }}
        onConfirm={confirmActivateSubscription}
        title="Activate Subscription"
        message="Are you sure you want to activate this subscription? This will start billing according to your subscription plan."
        confirmText="Activate"
        cancelText="Cancel"
        variant="info"
        loading={false}
      />
    </div>
  );
};