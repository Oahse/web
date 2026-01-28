import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeftIcon, PackageIcon, CalendarIcon } from 'lucide-react';
import { themeClasses, getButtonClasses } from '../../utils/themeClasses';
import SubscriptionAPI from '../../api/subscription';
import { toast } from 'react-hot-toast';

interface Order {
  id: string;
  order_number: string;
  created_at: string;
  status: string;
  total_amount: number;
  items: any[];
}

export const SubscriptionOrders = () => {
  const { subscriptionId } = useParams<{ subscriptionId: string }>();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (subscriptionId) {
      fetchSubscriptionOrders();
    }
  }, [subscriptionId]);

  const fetchSubscriptionOrders = async () => {
    try {
      setLoading(true);
      const response = await SubscriptionAPI.getOrders(subscriptionId!, 1, 50);
      
      // Handle the response structure properly
      let ordersData = [];
      if (response?.success) {
        const data = response.data;
        // Check if data has orders array (paginated response)
        if (data && data.orders) {
          ordersData = data.orders;
        } else if (Array.isArray(data)) {
          ordersData = data;
        }
      } else if (response?.data) {
        if (Array.isArray(response.data)) {
          ordersData = response.data;
        } else if (response.data.orders) {
          ordersData = response.data.orders;
        }
      }
      
      setOrders(ordersData);
    } catch (error) {
      console.error('Failed to fetch subscription orders:', error);
      setError('Failed to load subscription orders');
      toast.error('Failed to load subscription orders');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className={`${themeClasses.loading.spinner} w-12 h-12 mx-auto`}></div>
        <p className={`${themeClasses.text.secondary} mt-4 text-center`}>Loading subscription orders...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <p className={themeClasses.text.error}>{error}</p>
        <button
          onClick={fetchSubscriptionOrders}
          className={`${getButtonClasses('primary')} mt-4`}
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6">
      {/* Header */}
      <div className="flex items-center mb-6">
        <Link
          to="/account/subscriptions"
          className={`${themeClasses.text.secondary} hover:${themeClasses.text.primary} mr-4`}
        >
          <ArrowLeftIcon size={20} />
        </Link>
        <div>
          <h1 className={`${themeClasses.text.heading} text-2xl`}>Subscription Orders</h1>
          <p className={`${themeClasses.text.secondary} text-sm mt-1`}>
            Orders generated from your subscription
          </p>
        </div>
      </div>

      {/* Orders List */}
      {orders.length === 0 ? (
        <div className={`${themeClasses.card.base} text-center py-12`}>
          <PackageIcon size={48} className={`${themeClasses.text.muted} mx-auto mb-4`} />
          <p className={`${themeClasses.text.secondary} mb-3`}>
            No orders have been generated from this subscription yet.
          </p>
          <p className={`${themeClasses.text.muted} text-sm`}>
            Orders will appear here when your subscription billing cycle processes.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <div key={order.id} className={`${themeClasses.card.base} p-4 sm:p-6`}>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
                <div className="mb-2 sm:mb-0">
                  <h3 className={`${themeClasses.text.heading} text-lg`}>
                    Order #{order.order_number || order.id}
                  </h3>
                  <div className="flex items-center mt-1">
                    <CalendarIcon size={16} className={`${themeClasses.text.muted} mr-2`} />
                    <span className={`${themeClasses.text.secondary} text-sm`}>
                      {new Date(order.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <span className={`px-3 py-1 text-sm rounded-full ${
                    order.status === 'delivered' 
                      ? themeClasses.status.success
                      : order.status === 'shipped'
                      ? themeClasses.status.info
                      : order.status === 'processing'
                      ? themeClasses.status.warning
                      : themeClasses.status.neutral
                  }`}>
                    {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                  </span>
                  <span className={`${themeClasses.text.heading} font-semibold`}>
                    ${order.total_amount.toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Order Items */}
              {order.items && order.items.length > 0 && (
                <div className="mb-4">
                  <h4 className={`${themeClasses.text.heading} text-sm mb-2`}>Items:</h4>
                  <div className="space-y-2">
                    {order.items.slice(0, 3).map((item, index) => (
                      <div key={index} className={`${themeClasses.background.elevated} rounded-md p-2 flex items-center`}>
                        {item.product?.images?.[0] && (
                          <img 
                            src={item.product.images[0].url} 
                            alt={item.product.name}
                            className="w-10 h-10 rounded object-cover mr-3"
                          />
                        )}
                        <div className="flex-1">
                          <span className={`${themeClasses.text.primary} text-sm`}>
                            {item.product?.name || 'Product'}
                          </span>
                          <span className={`${themeClasses.text.muted} text-xs ml-2`}>
                            Qty: {item.quantity}
                          </span>
                        </div>
                        <span className={`${themeClasses.text.secondary} text-sm`}>
                          ${(item.price * item.quantity).toFixed(2)}
                        </span>
                      </div>
                    ))}
                    {order.items.length > 3 && (
                      <p className={`${themeClasses.text.muted} text-xs`}>
                        +{order.items.length - 3} more items
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end">
                <Link
                  to={`/account/orders/${order.id}`}
                  className={`${getButtonClasses('outline')} text-sm`}
                >
                  View Details
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SubscriptionOrders;