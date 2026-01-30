import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubscription } from '../../store/SubscriptionContext';
import { 
  PlusIcon, 
  PackageIcon,
  EditIcon,
  TrashIcon,
  PauseIcon,
  PlayIcon,
  EyeIcon,
  CalendarIcon,
  DollarSignIcon
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { ProductVariantModal } from '../ui/ProductVariantModal';
import { ConfirmationModal } from '../ui/ConfirmationModal';

interface Subscription {
  id: string;
  status: 'active' | 'paused' | 'cancelled' | 'expired';
  subscription_plan?: {
    name: string;
    billing_interval: string;
    base_price: number;
  };
  current_period_start: string;
  current_period_end: string;
  next_billing_date?: string;
  base_cost: number;
  delivery_cost: number;
  tax_amount: number;
  total_cost: number;
  currency: string;
  product_variants?: Array<{
    id: string;
    name: string;
    sku: string;
    price: number;
    product?: {
      name: string;
      images?: Array<{ url: string }>;
    };
  }>;
  auto_renew: boolean;
  created_at: string;
}

interface SubscriptionsProps {
  mode?: 'list' | 'manage';
  subscriptionId?: string;
}

export const Subscriptions: React.FC<SubscriptionsProps> = ({ mode = 'list', subscriptionId }) => {
  const navigate = useNavigate();
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

  const [activeTab, setActiveTab] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [showAddProductModal, setShowAddProductModal] = useState<boolean>(false);
  const [showProductVariantModal, setShowProductVariantModal] = useState<boolean>(false);
  const [selectedSubscription, setSelectedSubscription] = useState<Subscription | null>(null);
  const [selectedVariants, setSelectedVariants] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showCancelModal, setShowCancelModal] = useState<boolean>(false);
  const [subscriptionToCancel, setSubscriptionToCancel] = useState<string | null>(null);

  useEffect(() => {
    refreshSubscriptions();
  }, [refreshSubscriptions]);

  const filteredSubscriptions = subscriptions.filter((sub: any) => {
    if (activeTab === 'all') return true;
    if (activeTab === 'active') return sub.status === 'active';
    if (activeTab === 'paused') return sub.status === 'paused';
    if (activeTab === 'cancelled') return sub.status === 'cancelled';
    return true;
  });

  const handleCreateSubscription = async (variantIds: string[]) => {
    if (variantIds.length === 0) {
      toast.error('Please select at least one product variant');
      return;
    }

    setIsLoading(true);
    try {
      const subscriptionData = {
        plan_id: 'basic',
        billing_cycle: 'monthly',
        product_variant_ids: variantIds,
        delivery_type: 'standard',
        currency: 'USD',
        auto_renew: true
      };

      await createSubscription(subscriptionData);
      setShowProductVariantModal(false);
      setShowCreateModal(false);
      setSelectedVariants([]);
      toast.success('Subscription created successfully!');
    } catch (error) {
      console.error('Failed to create subscription:', error);
      toast.error('Failed to create subscription');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddProducts = async (variantIds: string[]) => {
    if (!selectedSubscription || variantIds.length === 0) return;

    setIsLoading(true);
    try {
      await addProductsToSubscription(selectedSubscription.id, variantIds);
      setShowProductVariantModal(false);
      setShowAddProductModal(false);
      setSelectedVariants([]);
      toast.success('Products added to subscription successfully!');
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
      toast.success('Product removed from subscription');
    } catch (error) {
      console.error('Failed to remove product:', error);
      toast.error('Failed to remove product');
    }
  };

  const handleCancelSubscription = async () => {
    if (!subscriptionToCancel) return;
    
    try {
      await cancelSubscription(subscriptionToCancel);
      setShowCancelModal(false);
      setSubscriptionToCancel(null);
      toast.success('Subscription cancelled successfully');
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
      toast.error('Failed to cancel subscription');
    }
  };

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount || 0);
  };

  const getStatusBadge = (status: string) => {
    const config = {
      active: { color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200', label: 'Active' },
      paused: { color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200', label: 'Paused' },
      cancelled: { color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200', label: 'Cancelled' },
      expired: { color: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200', label: 'Expired' }
    };
    
    const { color, label } = config[status as keyof typeof config] || config.active;
    
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${color}`}>
        {label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        <p className="ml-4 text-gray-600 dark:text-gray-400">Loading subscriptions...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-6">
        <p className="text-red-600 dark:text-red-400">Error loading subscriptions: {error}</p>
      </div>
    );
  }

  // List mode - show all subscriptions
  if (mode === 'list') {
    return (
      <div className="space-y-3">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-3 gap-3">
          <div>
            <h1 className="text-base font-medium text-gray-900 dark:text-white">My Subscriptions</h1>
            <p className="text-xs text-gray-600 dark:text-gray-300 mt-1">
              {subscriptions.length} {subscriptions.length === 1 ? 'subscription' : 'subscriptions'}
            </p>
          </div>
          <button
            onClick={() => {
              setSelectedVariants([]);
              setShowCreateModal(true);
              setShowProductVariantModal(true);
            }}
            className="flex items-center gap-2 px-3 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors text-xs"
          >
            <PlusIcon size={16} />
            New Subscription
          </button>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-3 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 overflow-x-auto">
          {[
            { key: 'all', label: 'All', count: subscriptions.length },
            { key: 'active', label: 'Active', count: subscriptions.filter((s: any) => s.status === 'active').length },
            { key: 'paused', label: 'Paused', count: subscriptions.filter((s: any) => s.status === 'paused').length },
            { key: 'cancelled', label: 'Cancelled', count: subscriptions.filter((s: any) => s.status === 'cancelled').length }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-2 sm:px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap ${
                activeTab === tab.key
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>

        {/* Subscriptions Grid */}
        {filteredSubscriptions.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center">
            <PackageIcon size={48} className="text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400 mb-3">
              {activeTab === 'all' 
                ? "You don't have any subscriptions yet." 
                : `No ${activeTab} subscriptions found.`
              }
            </p>
            <button
              onClick={() => {
                setSelectedVariants([]);
                setShowCreateModal(true);
                setShowProductVariantModal(true);
              }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
            >
              <PlusIcon size={20} />
              Create Your First Subscription
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredSubscriptions.map((subscription: any) => (
              <div key={subscription.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow">
                {/* Header */}
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                        {subscription.subscription_plan?.name || 'Subscription Plan'}
                      </h3>
                      {getStatusBadge(subscription.status)}
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => navigate(`/account/subscriptions/${subscription.id}/edit`)}
                        className="p-2 text-gray-600 hover:text-primary dark:text-gray-400 dark:hover:text-primary transition-colors"
                        title="Edit Subscription"
                      >
                        <EditIcon size={18} />
                      </button>
                      <button
                        onClick={() => {
                          setSubscriptionToCancel(subscription.id);
                          setShowCancelModal(true);
                        }}
                        className="p-2 text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 transition-colors"
                        title="Cancel Subscription"
                      >
                        <TrashIcon size={18} />
                      </button>
                    </div>
                  </div>

                  {/* Billing Info */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Monthly Cost:</span>
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {formatCurrency(subscription.total_cost, subscription.currency)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Next Billing:</span>
                      <span className="text-sm text-gray-900 dark:text-white">
                        {subscription.next_billing_date 
                          ? new Date(subscription.next_billing_date).toLocaleDateString()
                          : 'N/A'
                        }
                      </span>
                    </div>
                  </div>
                </div>

                {/* Products */}
                <div className="p-6">
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      Products ({subscription.product_variants?.length || 0})
                    </h4>
                    <button
                      onClick={() => {
                        setSelectedSubscription(subscription);
                        setSelectedVariants([]);
                        setShowAddProductModal(true);
                        setShowProductVariantModal(true);
                      }}
                      className="text-primary hover:text-primary-dark text-sm font-medium"
                    >
                      Add Products
                    </button>
                  </div>
                  
                  <div className="space-y-2">
                    {subscription.product_variants?.slice(0, 3).map((variant: any) => (
                      <div key={variant.id} className="flex items-center gap-3 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                        <div className="w-8 h-8 bg-gray-200 dark:bg-gray-600 rounded flex items-center justify-center">
                          <PackageIcon className="w-4 h-4 text-gray-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {variant.name}
                          </p>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            {variant.product?.name}
                          </p>
                        </div>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {formatCurrency(variant.price, subscription.currency)}
                        </span>
                      </div>
                    ))}
                    {subscription.product_variants?.length > 3 && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                        +{subscription.product_variants.length - 3} more items
                      </p>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                  <button
                    onClick={() => navigate(`/account/subscriptions/${subscription.id}/edit`)}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
                  >
                    <EyeIcon size={16} />
                    View Details
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Product Variant Modal */}
        <ProductVariantModal
          isOpen={showProductVariantModal}
          onClose={() => {
            setShowProductVariantModal(false);
            setSelectedVariants([]);
          }}
          onSelectionChange={(variants) => {
            setSelectedVariants(variants);
          }}
          selectedVariants={selectedVariants}
          multiSelect={true}
          title={showAddProductModal ? 'Add Products to Subscription' : 'Select Products for New Subscription'}
        />

        {/* Confirmation Modals */}
        {showCreateModal && (
          <ConfirmationModal
            isOpen={true}
            onClose={() => {
              setShowCreateModal(false);
              setShowProductVariantModal(false);
              setSelectedVariants([]);
            }}
            onConfirm={() => handleCreateSubscription(selectedVariants)}
            title="Create New Subscription"
            message={`Are you sure you want to create a subscription with ${selectedVariants.length} product variant${selectedVariants.length !== 1 ? 's' : ''}?`}
            confirmText="Create Subscription"
            cancelText="Cancel"
            loading={isLoading}
          />
        )}

        {showAddProductModal && selectedSubscription && (
          <ConfirmationModal
            isOpen={true}
            onClose={() => {
              setShowAddProductModal(false);
              setShowProductVariantModal(false);
              setSelectedVariants([]);
            }}
            onConfirm={() => handleAddProducts(selectedVariants)}
            title="Add Products to Subscription"
            message={`Are you sure you want to add ${selectedVariants.length} product variant${selectedVariants.length !== 1 ? 's' : ''} to this subscription?`}
            confirmText="Add Products"
            cancelText="Cancel"
            loading={isLoading}
          />
        )}

        {showCancelModal && (
          <ConfirmationModal
            isOpen={true}
            onClose={() => {
              setShowCancelModal(false);
              setSubscriptionToCancel(null);
            }}
            onConfirm={handleCancelSubscription}
            title="Cancel Subscription"
            message="Are you sure you want to cancel this subscription? This action cannot be undone."
            confirmText="Cancel Subscription"
            cancelText="Keep Subscription"
            loading={isLoading}
          />
        )}
      </div>
    );
  }

  // Manage mode - show single subscription details
  // This would be implemented for the detailed view
  return (
    <div className="p-4 sm:p-6">
      <div className="text-center">
        <p>Subscription management view would be implemented here</p>
        <button 
          onClick={() => navigate('/account/subscriptions')}
          className="mt-4 text-primary hover:underline"
        >
          Back to Subscriptions
        </button>
      </div>
    </div>
  );
};

export default Subscriptions;
