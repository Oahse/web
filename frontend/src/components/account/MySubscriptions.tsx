import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { 
  CalendarIcon, 
  CreditCardIcon, 
  ShoppingBagIcon, 
  PlusIcon, 
  MinusIcon, 
  EditIcon, 
  TrashIcon,
  SearchIcon,
  FilterIcon,
  MoreVerticalIcon,
  PackageIcon,
  ClockIcon,
  XIcon
} from 'lucide-react';
import { formatCurrency } from '../../lib/locale-config';
import { themeClasses, getButtonClasses } from '../../lib/themeClasses';
import { ProductsAPI } from '../../apis/products';
import SubscriptionAPI from '../../apis/subscription';
import { toast } from 'react-hot-toast';

export const MySubscriptions = () => {
  const { subscriptions, loading, error, refreshSubscriptions } = useSubscription();
  const [activeTab, setActiveTab] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAddProductModal, setShowAddProductModal] = useState(false);
  const [selectedSubscription, setSelectedSubscription] = useState(null);
  const [availableProducts, setAvailableProducts] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProducts, setSelectedProducts] = useState(new Set());
  const [isLoading, setIsLoading] = useState(false);

  // New subscription form state
  const [newSubscription, setNewSubscription] = useState({
    name: '',
    billing_cycle: 'monthly',
    price: 0,
    currency: 'USD'
  });

  useEffect(() => {
    refreshSubscriptions();
  }, [refreshSubscriptions]);

  useEffect(() => {
    if (showAddProductModal) {
      loadAvailableProducts();
    }
  }, [showAddProductModal, searchQuery]);

  const loadAvailableProducts = async () => {
    try {
      const response = await ProductsAPI.getProducts({ 
        search: searchQuery,
        page: 1,
        limit: 20 
      });
      setAvailableProducts(response.data.products || []);
    } catch (error) {
      console.error('Failed to load products:', error);
      toast.error('Failed to load products');
    }
  };

  const handleCreateSubscription = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      await SubscriptionAPI.createSubscription(newSubscription);
      toast.success('Subscription created successfully!');
      setShowCreateModal(false);
      setNewSubscription({
        name: '',
        billing_cycle: 'monthly',
        price: 0,
        currency: 'USD'
      });
      refreshSubscriptions();
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

    setIsLoading(true);
    try {
      const variantIds = Array.from(selectedProducts);
      await SubscriptionAPI.addProductsToSubscription(selectedSubscription.id, variantIds);
      toast.success(`Added ${selectedProducts.size} product(s) to subscription!`);
      setShowAddProductModal(false);
      setSelectedProducts(new Set());
      refreshSubscriptions();
    } catch (error) {
      console.error('Failed to add products:', error);
      toast.error('Failed to add products to subscription');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveProduct = async (subscriptionId, variantId) => {
    try {
      await SubscriptionAPI.removeProductsFromSubscription(subscriptionId, [variantId]);
      toast.success('Product removed from subscription');
      refreshSubscriptions();
    } catch (error) {
      console.error('Failed to remove product:', error);
      toast.error('Failed to remove product');
    }
  };

  const handleUpdatePeriod = async (subscriptionId, newPeriod) => {
    try {
      await SubscriptionAPI.updateSubscription(subscriptionId, { billing_cycle: newPeriod });
      toast.success('Subscription period updated');
      refreshSubscriptions();
    } catch (error) {
      console.error('Failed to update subscription:', error);
      toast.error('Failed to update subscription period');
    }
  };

  const handleDeleteSubscription = async (subscriptionId) => {
    if (!confirm('Are you sure you want to delete this subscription?')) return;
    
    try {
      await SubscriptionAPI.deleteSubscription(subscriptionId);
      toast.success('Subscription deleted successfully');
      refreshSubscriptions();
    } catch (error) {
      console.error('Failed to delete subscription:', error);
      toast.error('Failed to delete subscription');
    }
  };

  const filteredSubscriptions = subscriptions.filter(sub => {
    if (activeTab === 'all') return true;
    if (activeTab === 'active') return sub.status === 'active';
    if (activeTab === 'paused') return sub.status === 'paused';
    if (activeTab === 'cancelled') return sub.status === 'cancelled';
    return true;
  });

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
    <div className="p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
        <h1 className={`${themeClasses.text.heading} text-2xl mb-4 sm:mb-0`}>My Subscriptions</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className={`${getButtonClasses('primary')} flex items-center`}
        >
          <PlusIcon size={20} className="mr-2" />
          New Subscription
        </button>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 mb-6 bg-surface-elevated rounded-lg p-1">
        {[
          { key: 'all', label: 'All', count: subscriptions.length },
          { key: 'active', label: 'Active', count: subscriptions.filter(s => s.status === 'active').length },
          { key: 'paused', label: 'Paused', count: subscriptions.filter(s => s.status === 'paused').length },
          { key: 'cancelled', label: 'Cancelled', count: subscriptions.filter(s => s.status === 'cancelled').length }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredSubscriptions.map((subscription) => (
            <div key={subscription.id} className={`${themeClasses.card.base} p-6`}>
              {/* Subscription Header */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className={`${themeClasses.text.heading} text-lg`}>
                    {subscription.name || `${subscription.billing_cycle} Subscription`}
                  </h3>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    subscription.status === 'active' 
                      ? themeClasses.status.success
                      : subscription.status === 'paused'
                      ? themeClasses.status.warning
                      : themeClasses.status.error
                  }`}>
                    {subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => {
                      setSelectedSubscription(subscription);
                      setShowAddProductModal(true);
                    }}
                    className={`${getButtonClasses('outline')} p-2`}
                    title="Add Products"
                  >
                    <PlusIcon size={16} />
                  </button>
                  <button
                    onClick={() => handleDeleteSubscription(subscription.id)}
                    className={`${getButtonClasses('danger')} p-2`}
                    title="Delete Subscription"
                  >
                    <TrashIcon size={16} />
                  </button>
                </div>
              </div>

              {/* Subscription Details */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="flex items-center">
                  <CreditCardIcon size={16} className={`${themeClasses.text.muted} mr-2`} />
                  <span className={`${themeClasses.text.secondary} text-sm`}>
                    {formatCurrency(subscription.price, subscription.currency || 'USD')} / {subscription.billing_cycle}
                  </span>
                </div>
                <div className="flex items-center">
                  <CalendarIcon size={16} className={`${themeClasses.text.muted} mr-2`} />
                  <span className={`${themeClasses.text.secondary} text-sm`}>
                    Next: {new Date(subscription.next_billing_date).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex items-center">
                  <ShoppingBagIcon size={16} className={`${themeClasses.text.muted} mr-2`} />
                  <span className={`${themeClasses.text.secondary} text-sm`}>
                    {subscription.products?.length || 0} products
                  </span>
                </div>
                <div className="flex items-center">
                  <ClockIcon size={16} className={`${themeClasses.text.muted} mr-2`} />
                  <select
                    value={subscription.billing_cycle}
                    onChange={(e) => handleUpdatePeriod(subscription.id, e.target.value)}
                    className={`${themeClasses.input.base} ${themeClasses.input.default} text-sm py-1`}
                  >
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
              </div>

              {/* Products List */}
              {subscription.products && subscription.products.length > 0 && (
                <div className="mb-4">
                  <h4 className={`${themeClasses.text.heading} text-sm mb-2`}>Products:</h4>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {subscription.products.map((product) => (
                      <div key={product.id} className={`${themeClasses.background.elevated} rounded-md p-2 flex justify-between items-center`}>
                        <div className="flex items-center">
                          {product.image && (
                            <img 
                              src={product.image} 
                              alt={product.name}
                              className="w-8 h-8 rounded object-cover mr-2"
                            />
                          )}
                          <span className={`${themeClasses.text.primary} text-sm`}>{product.name}</span>
                        </div>
                        <button
                          onClick={() => handleRemoveProduct(subscription.id, product.id)}
                          className={`${themeClasses.text.error} hover:${themeClasses.background.hover} p-1 rounded`}
                          title="Remove product"
                        >
                          <XIcon size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end">
                <Link 
                  to={`/subscription/${subscription.id}/manage`} 
                  className={`${getButtonClasses('outline')} text-sm`}
                >
                  Manage Details
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Subscription Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`${themeClasses.card.base} w-full max-w-md mx-4`}>
            <div className="p-6">
              <h2 className={`${themeClasses.text.heading} text-xl mb-4`}>Create New Subscription</h2>
              <form onSubmit={handleCreateSubscription}>
                <div className="space-y-4">
                  <div>
                    <label className={`${themeClasses.text.primary} block text-sm font-medium mb-1`}>
                      Subscription Name
                    </label>
                    <input
                      type="text"
                      value={newSubscription.name}
                      onChange={(e) => setNewSubscription({...newSubscription, name: e.target.value})}
                      className={`${themeClasses.input.base} ${themeClasses.input.default}`}
                      placeholder="e.g., Monthly Wellness Box"
                      required
                    />
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
                      <option value="quarterly">Quarterly</option>
                      <option value="yearly">Yearly</option>
                    </select>
                  </div>
                  <div>
                    <label className={`${themeClasses.text.primary} block text-sm font-medium mb-1`}>
                      Price
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={newSubscription.price}
                      onChange={(e) => setNewSubscription({...newSubscription, price: parseFloat(e.target.value)})}
                      className={`${themeClasses.input.base} ${themeClasses.input.default}`}
                      placeholder="0.00"
                      required
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className={getButtonClasses('outline')}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className={getButtonClasses('primary')}
                  >
                    {isLoading ? 'Creating...' : 'Create Subscription'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Add Products Modal */}
      {showAddProductModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`${themeClasses.card.base} w-full max-w-4xl mx-4 max-h-[80vh] overflow-hidden`}>
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className={`${themeClasses.text.heading} text-xl`}>Add Products to Subscription</h2>
                <button
                  onClick={() => setShowAddProductModal(false)}
                  className={`${themeClasses.text.muted} hover:${themeClasses.text.primary}`}
                >
                  <XIcon size={24} />
                </button>
              </div>
              
              {/* Search */}
              <div className="mb-4">
                <div className="relative">
                  <SearchIcon size={20} className={`${themeClasses.text.muted} absolute left-3 top-1/2 transform -translate-y-1/2`} />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search products..."
                    className={`${themeClasses.input.base} ${themeClasses.input.default} pl-10`}
                  />
                </div>
              </div>

              {/* Products Grid */}
              <div className="max-h-96 overflow-y-auto mb-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {availableProducts.map((product) => (
                    <div key={product.id} className={`${themeClasses.card.base} p-4`}>
                      <div className="flex items-start space-x-3">
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
                          className={`${themeClasses.input.base} mt-1`}
                        />
                        <div className="flex-1">
                          {product.image && (
                            <img 
                              src={product.image} 
                              alt={product.name}
                              className="w-full h-24 object-cover rounded mb-2"
                            />
                          )}
                          <h3 className={`${themeClasses.text.primary} font-medium text-sm`}>{product.name}</h3>
                          <p className={`${themeClasses.text.secondary} text-xs mt-1`}>
                            {formatCurrency(product.price, product.currency || 'USD')}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-between items-center">
                <p className={themeClasses.text.secondary}>
                  {selectedProducts.size} product(s) selected
                </p>
                <div className="flex space-x-3">
                  <button
                    onClick={() => setShowAddProductModal(false)}
                    className={getButtonClasses('outline')}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAddProducts}
                    disabled={selectedProducts.size === 0 || isLoading}
                    className={getButtonClasses('primary')}
                  >
                    {isLoading ? 'Adding...' : `Add ${selectedProducts.size} Product(s)`}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
