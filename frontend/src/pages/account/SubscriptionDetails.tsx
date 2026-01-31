import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSubscription } from '../../store/SubscriptionContext';
import { themeClasses, combineThemeClasses } from '../../utils/themeClasses';
import { formatCurrency } from '../../utils/orderCalculations';
import { toast } from 'react-hot-toast';
import { SubscriptionAPI } from '../../api/subscription';
import { Dropdown } from '../../components/ui/Dropdown';
import { 
  ArrowLeftIcon,
  EyeIcon,
  TagIcon,
  PackageIcon,
  CalendarIcon,
  CreditCardIcon,
  TruckIcon,
  PercentIcon,
  PauseIcon,
  TrashIcon
} from 'lucide-react';
import SubscriptionItem from '../../components/subscription/SubscriptionItem';
import { AutoRenewToggle } from '../../components/subscription/AutoRenewToggle';
import { ConfirmationModal } from '../../components/ui/ConfirmationModal';

interface SubscriptionDetailsProps {}

export const SubscriptionDetails: React.FC<SubscriptionDetailsProps> = () => {
  const { subscriptionId } = useParams<{ subscriptionId: string }>();
  const navigate = useNavigate();
  const { subscriptions, refreshSubscriptions, updateSubscription, cancelSubscription, deleteSubscription, activateSubscription, pauseSubscription, resumeSubscription } = useSubscription();
  
  const [subscription, setSubscription] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showProducts, setShowProducts] = useState(true);
  const [showBillingSummary, setShowBillingSummary] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    name: '',
    billing_cycle: 'monthly' as 'weekly' | 'monthly' | 'yearly',
    delivery_type: 'standard' as 'standard' | 'express' | 'overnight'
  });

  useEffect(() => {
    let isCancelled = false;

    const normalizeBillingCycle = (value: any): 'weekly' | 'monthly' | 'yearly' => {
      if (value === 'weekly' || value === 'monthly' || value === 'yearly') return value;
      return 'monthly';
    };

    const load = async () => {
      if (!subscriptionId) return;
      setLoading(true);

      const foundSubscription = subscriptions.find(sub => sub.id === subscriptionId);
      if (foundSubscription) {
        if (!isCancelled) {
          setSubscription(foundSubscription);
          setEditData({
            name: foundSubscription.name || '',
            billing_cycle: normalizeBillingCycle(foundSubscription.billing_cycle),
            delivery_type: (foundSubscription as any).delivery_type || 'standard'
          });
          setLoading(false);
        }
        return;
      }

      try {
        const response = await SubscriptionAPI.getSubscription(subscriptionId);
        const fetched = (response as any)?.data ?? response;
        if (!isCancelled) {
          if (fetched) {
            setSubscription(fetched);
            setEditData({
              name: fetched.name || '',
              billing_cycle: normalizeBillingCycle(fetched.billing_cycle),
              delivery_type: fetched.delivery_type || 'standard'
            });
          } else {
            toast.error('Subscription not found');
            navigate('/account/subscriptions');
          }
        }
      } catch (error) {
        if (!isCancelled) {
          toast.error('Failed to load subscription');
          navigate('/account/subscriptions');
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };

    load();
    return () => {
      isCancelled = true;
    };
  }, [subscriptionId, subscriptions, navigate]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'cancelled':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const handleAutoRenewToggle = async () => {
    if (!subscription) return;
    
    const newAutoRenewState = !subscription.auto_renew;
    
    try {
      // Update local state immediately for real-time UI feedback
      setSubscription({ ...subscription, auto_renew: newAutoRenewState });
      
      // Update via API
      await updateSubscription(subscription.id, { auto_renew: newAutoRenewState });
      
      // Refresh subscriptions to ensure global state is updated
      await refreshSubscriptions();
      
      toast.success(`Auto-renew ${newAutoRenewState ? 'enabled' : 'disabled'}`);
    } catch (error) {
      // Revert local state if API call fails
      setSubscription({ ...subscription, auto_renew: subscription.auto_renew });
      toast.error('Failed to update auto-renewal');
    }
  };

  const handleSave = async () => {
    if (!subscription) return;

    try {
      // Update local state immediately for real-time UI feedback
      const updatedSubscription = {
        ...subscription,
        name: editData.name,
        billing_cycle: editData.billing_cycle,
        delivery_type: editData.delivery_type,
        auto_renew: subscription.auto_renew
      };
      setSubscription(updatedSubscription);

      // Update via API
      const updated = await updateSubscription(subscription.id, {
        name: editData.name,
        billing_cycle: editData.billing_cycle,
        delivery_type: editData.delivery_type
      });

      if (updated) {
        const normalized = (updated as any)?.data ?? updated;
        setSubscription(normalized);
      }

      // Refresh subscriptions to ensure global state is updated
      await refreshSubscriptions();
      setIsEditing(false);
      toast.success('Subscription updated');
    } catch (error) {
      // Revert local state if API call fails
      setSubscription({
        ...subscription,
        name: editData.name,
        billing_cycle: editData.billing_cycle,
        delivery_type: editData.delivery_type,
        auto_renew: subscription.auto_renew
      });
      toast.error('Failed to update subscription');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
          <div className="h-5 w-40 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className="h-7 w-40 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                  <div className="h-6 w-24 bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  <div className="space-y-2">
                    <div className="h-4 w-28 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                    <div className="h-6 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                  </div>
                  <div className="space-y-2">
                    <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                    <div className="h-6 w-28 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                  </div>
                  <div className="space-y-2">
                    <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                    <div className="h-6 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                  </div>
                </div>
              </div>

              <div className="h-10 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            </div>
          </div>

          <div className="space-y-4">
            <div className="h-5 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
              <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
              <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
              <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            </div>
          </div>

          <div className="space-y-4">
            <div className="h-5 w-40 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 space-y-3">
              <div className="h-4 w-48 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
              <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
              <div className="h-4 w-5/6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
              <div className="h-4 w-2/3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <PackageIcon size={48} className="text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Subscription not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/account/subscriptions')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white mb-4"
          >
            <ArrowLeftIcon size={20} />
            Back to Subscriptions
          </button>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
            {/* Subscription Header */}
            <div className="border-b border-gray-200 dark:border-gray-700 pb-4 mb-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h1 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {subscription.name}
                  </h1>
                  <span className={`
                    inline-flex px-2 py-1 text-xs font-medium rounded-full
                    ${getStatusColor(subscription.status)}
                  `}>
                    {subscription.status?.charAt(0).toUpperCase() + subscription.status?.slice(1)}
                  </span>
                </div>
                
                <div className="flex items-center gap-3">
                  {isEditing ? (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleSave}
                        className="px-3 py-1.5 bg-primary text-white text-xs font-medium rounded-md hover:bg-primary-dark transition-colors"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => {
                          setIsEditing(false);
                          setEditData({
                            name: subscription.name || '',
                            billing_cycle: subscription.billing_cycle,
                            delivery_type: subscription.delivery_type || 'standard'
                          });
                        }}
                        className="px-3 py-1.5 bg-gray-100 text-gray-700 text-xs font-medium rounded-md hover:bg-gray-200 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="px-3 py-1.5 bg-primary text-white text-xs font-medium rounded-md hover:bg-primary-dark transition-colors"
                    >
                      Edit
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Edit Form */}
            {isEditing && (
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Subscription Name
                    </label>
                    <Dropdown
                      options={[
                        { value: 'Premium Plan', label: 'Premium Plan' },
                        { value: 'Basic Plan', label: 'Basic Plan' },
                        { value: 'Standard Plan', label: 'Standard Plan' },
                        { value: 'Family Plan', label: 'Family Plan' },
                        { value: 'Pro Plan', label: 'Pro Plan' },
                        { value: 'Business Plan', label: 'Business Plan' },
                        { value: 'Student Plan', label: 'Student Plan' },
                        { value: 'Custom Subscription', label: 'Custom Subscription' }
                      ]}
                      value={editData.name}
                      placeholder="Select a subscription name..."
                      onChange={(value) => setEditData({ ...editData, name: value })}
                      className="text-sm"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Billing Cycle
                    </label>
                    <Dropdown
                      options={[
                        { value: 'weekly', label: 'Weekly (Every 7 days)' },
                        { value: 'monthly', label: 'Monthly (Every 30 days)' },
                        { value: 'yearly', label: 'Yearly (Every 365 days)' }
                      ]}
                      value={editData.billing_cycle}
                      placeholder="Select billing cycle..."
                      onChange={(value) => setEditData({ ...editData, billing_cycle: value as any })}
                      className="text-sm"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Delivery Type
                    </label>
                    <Dropdown
                      options={[
                        { value: 'standard', label: 'Standard (5-7 business days)' },
                        { value: 'express', label: 'Express (2-3 business days)' },
                        { value: 'overnight', label: 'Overnight (1 business day)' }
                      ]}
                      value={editData.delivery_type}
                      placeholder="Select delivery type..."
                      onChange={(value) => setEditData({ ...editData, delivery_type: value as any })}
                      className="text-sm"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Subscription Information Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
              {/* Monthly Amount */}
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-full mb-3">
                  <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2-3-.895-3-2z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 0l2.83-2.83M4.93 19.07l2.83-2.83m8.48 0l2.83 2.83" />
                  </svg>
                </div>
                <h3 className="text-xs text-gray-600 dark:text-gray-400 mb-1">Monthly Amount</h3>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {formatCurrency(subscription.price || 0, subscription.currency)}
                </p>
              </div>

              {/* Billing Cycle */}
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-10 h-10 bg-green-100 dark:bg-green-900 rounded-full mb-3">
                  <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="text-xs text-gray-600 dark:text-gray-400 mb-1">Billing Cycle</h3>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {subscription.billing_cycle?.charAt(0).toUpperCase() + subscription.billing_cycle?.slice(1)}
                </p>
              </div>

              {/* Next Billing */}
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-10 h-10 bg-purple-100 dark:bg-purple-900 rounded-full mb-3">
                  <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-xs text-gray-600 dark:text-gray-400 mb-1">Next Billing</h3>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {subscription.next_billing_date ? formatDate(subscription.next_billing_date) : 'Not set'}
                </p>
              </div>

              {/* Status */}
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-10 h-10 bg-orange-100 dark:bg-orange-900 rounded-full mb-3">
                  <svg className="w-5 h-5 text-orange-600 dark:text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-xs text-gray-600 dark:text-gray-400 mb-1">Status</h3>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {subscription.status?.charAt(0).toUpperCase() + subscription.status?.slice(1)}
                </p>
              </div>
            </div>

            {/* Auto-Renew Section */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-700 dark:to-gray-600 rounded-lg p-6 border border-blue-100 dark:border-gray-600">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    subscription.auto_renew 
                      ? 'bg-green-100 dark:bg-green-900' 
                      : 'bg-gray-100 dark:bg-gray-700'
                  }`}>
                    <svg 
                      className={`w-4 h-4 ${
                        subscription.auto_renew 
                          ? 'text-green-600 dark:text-green-400' 
                          : 'text-gray-400 dark:text-gray-500'
                      }`} 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">Auto-Renew</h3>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      {subscription.auto_renew 
                        ? 'Your subscription will automatically renew at the end of each billing period.'
                        : "Your subscription will not renew automatically. You'll need to manually renew it."
                      }
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={() => handleAutoRenewToggle()}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 ${
                    subscription.auto_renew ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                      subscription.auto_renew ? 'translate-x-4' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {subscription.status === 'active' && (
              <button
                onClick={() => pauseSubscription(subscription.id)}
                className="flex items-center justify-center gap-1.5 px-3 py-2 bg-yellow-50 text-yellow-700 rounded-md hover:bg-yellow-100 transition-colors text-xs"
              >
                <PauseIcon size={16} />
                Pause
              </button>
            )}
            
            {subscription.status === 'paused' && (
              <button
                onClick={() => resumeSubscription(subscription.id)}
                className="flex items-center justify-center gap-1.5 px-3 py-2 bg-green-50 text-green-700 rounded-md hover:bg-green-100 transition-colors text-xs"
              >
                <CalendarIcon size={16} />
                Resume
              </button>
            )}

            {subscription.status !== 'cancelled' ? (
              <button
                onClick={() => cancelSubscription(subscription.id)}
                className="flex items-center justify-center gap-1.5 px-3 py-2 bg-white text-gray-700 rounded-md hover:bg-gray-50 transition-colors border border-gray-200 text-xs"
              >
                <CreditCardIcon size={16} />
                Cancel
              </button>
            ) : (
              <button
                onClick={() => activateSubscription(subscription.id)}
                className="flex items-center justify-center gap-1.5 px-3 py-2 bg-green-50 text-green-700 rounded-md hover:bg-green-100 transition-colors text-xs"
              >
                <CalendarIcon size={16} />
                Reactivate
              </button>
            )}

            <button
              onClick={() => setShowDeleteModal(true)}
              className="flex items-center justify-center gap-1.5 px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-xs"
            >
              <TrashIcon size={16} />
              Delete
            </button>
          </div>
        </div>

        
        {/* Detailed Information */}
        <div className="space-y-4">
          {/* Subscription Item Component */}
          <SubscriptionItem
            subscription={subscription}
            isExpanded={true}
          />

          {/* Additional Details */}
          <div className="bg-white dark:bg-gray-800 rounded-md shadow-sm border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Subscription Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Subscription ID</p>
                  <p className="font-medium text-xs text-gray-900 dark:text-white">{subscription.id}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Created Date</p>
                  <p className="font-medium text-xs text-gray-900 dark:text-white">
                    {subscription.created_at ? formatDate(subscription.created_at) : 'Not available'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Current Period</p>
                  <p className="font-medium text-xs text-gray-900 dark:text-white">
                    {subscription.current_period_start && subscription.current_period_end
                      ? `${formatDate(subscription.current_period_start)} - ${formatDate(subscription.current_period_end)}`
                      : 'Not available'
                    }
                  </p>
                </div>
              </div>
              
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Payment Method</p>
                  <p className="font-medium text-xs text-gray-900 dark:text-white">•••• •••• •••• 4242</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Delivery Type</p>
                  <p className="font-medium text-xs text-gray-900 dark:text-white">
                    {subscription.delivery_type || 'Standard'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Customer Support</p>
                  <p className="font-medium text-xs text-gray-900 dark:text-white">support@example.com</p>
                </div>
              </div>
            </div>
          </div>
        </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <ConfirmationModal
          isOpen={showDeleteModal}
          onClose={() => setShowDeleteModal(false)}
          onConfirm={async () => {
            const ok = await deleteSubscription(subscription.id);
            if (ok) {
              navigate('/account/subscriptions');
            }
          }}
          title="Delete Subscription"
          message="Delete this subscription permanently? This cannot be undone."
          confirmText="Delete"
          cancelText="Cancel"
          variant="danger"
        />
      )}
      </div>
    </div>
  );
};

export default SubscriptionDetails;
