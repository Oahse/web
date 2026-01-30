import React, { useState, useEffect } from 'react';
import { useSubscription } from '../../store/SubscriptionContext';
import { useLocale } from '../../store/LocaleContext';
import { 
  PlusIcon, 
  PackageIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  XIcon,
  SearchIcon
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { SubscriptionCard } from '../subscription/SubscriptionCard';
import { ConfirmationModal } from '../ui/ConfirmationModal';
import ProductsAPI from '../../api/products';
import { Product } from '../../types';

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
  const { currency = 'USD', formatCurrency: formatCurrencyLocale } = useLocale();
  const [activeTab, setActiveTab] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [newSubscriptionData, setNewSubscriptionData] = useState({
    plan_id: 'basic',
    billing_cycle: 'monthly',
    delivery_type: 'standard',
    auto_renew: true
  });
  const [availableProducts, setAvailableProducts] = useState<Product[]>([]);
  const [selectedProducts, setSelectedProducts] = useState<Set<string>>(new Set());
  const [productSearchQuery, setProductSearchQuery] = useState<string>('');
  const itemsPerPage = 6;

  useEffect(() => {
    refreshSubscriptions();
  }, [refreshSubscriptions]);

  useEffect(() => {
    if (showCreateModal) {
      loadProducts();
    }
  }, [showCreateModal]);

  const loadProducts = async () => {
    try {
      const response = await ProductsAPI.getProducts({ 
        q: productSearchQuery,
        page: 1,
        limit: 20 
      });
      const products = response.data?.data || response.data || [];
      setAvailableProducts(Array.isArray(products) ? products : []);
    } catch (error) {
      console.error('Failed to load products:', error);
      setAvailableProducts([]);
    }
  };

  const filteredSubscriptions = subscriptions.filter((sub: any) => {
    if (activeTab === 'all') return true;
    if (activeTab === 'active') return sub.status === 'active';
    if (activeTab === 'paused') return sub.status === 'paused';
    if (activeTab === 'cancelled') return sub.status === 'cancelled';
    return true;
  });

  // Pagination calculations
  const totalPages = Math.ceil(filteredSubscriptions.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentSubscriptions = filteredSubscriptions.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin w-12 h-12 border-4 border-gray-200 border-t-blue-600 rounded-full mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400 mt-4">Loading your subscriptions...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 border border-dashed border-gray-300 dark:border-gray-700 rounded-lg">
        <PackageIcon size={48} className="text-gray-400 dark:text-gray-500 mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-400 mb-3">
          Unable to load subscriptions
        </p>
        <button 
          onClick={() => refreshSubscriptions()} 
          className="text-primary hover:text-primary-dark underline"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <p className="text-xs text-gray-600 dark:text-gray-300">
            Manage your active and past subscriptions
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-primary hover:bg-primary-dark text-white py-2 px-4 rounded-md transition-colors flex items-center text-xs"
        >
          <PlusIcon size={16} className="mr-2" />
          Create
        </button>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1 overflow-x-auto">
        {[
          { key: 'all', label: 'All', count: subscriptions.length },
          { key: 'active', label: 'Active', count: subscriptions.filter((s: any) => s.status === 'active').length },
          { key: 'paused', label: 'Paused', count: subscriptions.filter((s: any) => s.status === 'paused').length },
          { key: 'cancelled', label: 'Cancelled', count: subscriptions.filter((s: any) => s.status === 'cancelled').length }
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 min-w-[80px] px-2 py-1 text-xs font-medium rounded-md transition-colors ${
              activeTab === tab.key
                ? 'bg-white dark:bg-gray-800 text-primary shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-main dark:hover:text-white'
            }`}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      {/* Subscriptions List */}
      {subscriptions.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm text-center py-8">
          <PackageIcon size={32} className="text-gray-400 dark:text-gray-500 mx-auto mb-3" />
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
            {activeTab === 'all' 
              ? "You don't have any subscriptions yet." 
              : `No ${activeTab} subscriptions found.`
            }
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-primary hover:bg-primary-dark text-white py-2 px-4 rounded-md transition-colors text-xs"
          >
            Create Your First Subscription
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-2">
            {currentSubscriptions.map((subscription: any) => (
              <SubscriptionCard
                key={subscription.id}
                subscription={subscription}
                onUpdate={async (subscriptionId: any, data: any) => {
                  await updateSubscription(subscriptionId, data);
                }}
                onCancel={async (subscriptionId: any, reason?: string) => {
                  await cancelSubscription(subscriptionId, reason);
                }}
                onActivate={async (subscriptionId: any) => {
                  await activateSubscription(subscriptionId);
                }}
                onPause={async (subscriptionId: any, reason?: string) => {
                  await pauseSubscription(subscriptionId, reason);
                }}
                onResume={async (subscriptionId: any) => {
                  await resumeSubscription(subscriptionId);
                }}
                onAddProducts={async (subscriptionId: any, productIds: any) => {
                  await addProductsToSubscription(subscriptionId, productIds);
                }}
                onRemoveProducts={async (subscriptionId: any, productIds: any) => {
                  await removeProductsFromSubscription(subscriptionId, productIds);
                }}
                onToggleAutoRenew={async (subscriptionId: any, autoRenew: any) => {
                  await updateSubscription(subscriptionId, { auto_renew: autoRenew });
                }}
              />
            ))}
          </div>

          {/* Pagination */}
          <div className="flex justify-center items-center space-x-2 pt-4">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="flex items-center px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeftIcon size={14} className="mr-1" />
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
                    className={`px-3 py-2 text-xs rounded transition-colors ${
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
              className="flex items-center px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
              <ChevronRightIcon size={14} className="ml-1" />
            </button>
          </div>
        </>
      )}

      {/* Create Subscription Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-base font-medium text-main dark:text-white">
                  Create New Subscription
                </h2>
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setSelectedProducts(new Set());
                  }}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <XIcon size={20} />
                </button>
              </div>

              <div className="space-y-6">
                {/* Subscription Settings */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Subscription Plan
                    </label>
                    <select
                      value={newSubscriptionData.plan_id}
                      onChange={(e) => setNewSubscriptionData({...newSubscriptionData, plan_id: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-xs"
                    >
                      <option value="basic">Basic Plan</option>
                      <option value="premium">Premium Plan</option>
                      <option value="enterprise">Enterprise Plan</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Billing Cycle
                    </label>
                    <select
                      value={newSubscriptionData.billing_cycle}
                      onChange={(e) => setNewSubscriptionData({...newSubscriptionData, billing_cycle: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-xs"
                    >
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                      <option value="yearly">Yearly</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Delivery Type
                    </label>
                    <select
                      value={newSubscriptionData.delivery_type}
                      onChange={(e) => setNewSubscriptionData({...newSubscriptionData, delivery_type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-xs"
                    >
                      <option value="standard">Standard Delivery</option>
                      <option value="express">Express Delivery</option>
                      <option value="overnight">Overnight Delivery</option>
                    </select>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="auto_renew"
                      checked={newSubscriptionData.auto_renew}
                      onChange={(e) => setNewSubscriptionData({...newSubscriptionData, auto_renew: e.target.checked})}
                      className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                    />
                    <label htmlFor="auto_renew" className="ml-2 block text-xs text-gray-700 dark:text-gray-300">
                      Enable auto-renewal
                    </label>
                  </div>
                </div>

                {/* Product Selection */}
                <div>
                  <div className="flex justify-between items-center mb-3">
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
                      Select Products ({selectedProducts.size} selected)
                    </label>
                    <div className="relative">
                      <SearchIcon size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                      <input
                        type="text"
                        value={productSearchQuery}
                        onChange={(e) => {
                          setProductSearchQuery(e.target.value);
                          loadProducts();
                        }}
                        placeholder="Search products..."
                        className="pl-9 pr-3 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white w-48"
                      />
                    </div>
                  </div>

                  <div className="border border-gray-200 dark:border-gray-600 rounded-lg max-h-60 overflow-y-auto">
                    {availableProducts.length === 0 ? (
                      <div className="text-center py-8">
                        <PackageIcon size={32} className="text-gray-400 mx-auto mb-2" />
                        <p className="text-xs text-gray-500">No products found</p>
                      </div>
                    ) : (
                      <div className="divide-y divide-gray-200 dark:divide-gray-600">
                        {availableProducts.map((product) => (
                          <div key={product.id} className="p-3">
                            <label className="flex items-center space-x-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 p-2 rounded">
                              <input
                                type="checkbox"
                                checked={selectedProducts.has(product.id)}
                                onChange={(e) => {
                                  const newSelected = new Set(selectedProducts);
                                  if (e.target.checked) {
                                    newSelected.add(product.id);
                                  } else {
                                    newSelected.delete(product.id);
                                  }
                                  setSelectedProducts(newSelected);
                                }}
                                className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                              />
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-gray-900 dark:text-white truncate">
                                  {product.name}
                                </p>
                                <p className="text-xs text-gray-500">
                                  {product.price ? `$${product.price}` : 'Price not available'}
                                </p>
                              </div>
                            </label>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setSelectedProducts(new Set());
                    setNewSubscriptionData({
                      plan_id: 'basic',
                      billing_cycle: 'monthly',
                      delivery_type: 'standard',
                      auto_renew: true
                    });
                  }}
                  className="px-4 py-2 text-xs font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={async () => {
                    if (selectedProducts.size === 0) {
                      toast.error('Please select at least one product');
                      return;
                    }

                    setIsLoading(true);
                    try {
                      const subscriptionData = {
                        ...newSubscriptionData,
                        currency: currency,
                        product_variant_ids: Array.from(selectedProducts)
                      };

                      const result = await createSubscription(subscriptionData);
                      if (result) {
                        setShowCreateModal(false);
                        setSelectedProducts(new Set());
                        setNewSubscriptionData({
                          plan_id: 'basic',
                          billing_cycle: 'monthly',
                          delivery_type: 'standard',
                          auto_renew: true
                        });
                        setCurrentPage(1);
                        toast.success('Subscription created successfully!');
                      }
                    } catch (error) {
                      console.error('Failed to create subscription:', error);
                      toast.error('Failed to create subscription');
                    } finally {
                      setIsLoading(false);
                    }
                  }}
                  disabled={isLoading || selectedProducts.size === 0}
                  className="px-4 py-2 text-xs font-medium text-white bg-primary hover:bg-primary-dark rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Creating...' : `Create Subscription (${selectedProducts.size} products)`}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MySubscriptions;
