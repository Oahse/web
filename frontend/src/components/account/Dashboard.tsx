import { useEffect } from 'react';
import { useAuth } from '../../store/AuthContext';
import { useSubscription } from '../../store/SubscriptionContext';
import { ShoppingBagIcon, HeartIcon, MapPinIcon, CreditCardIcon, PackageIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { SkeletonDashboard } from '../ui/SkeletonDashboard';
import { usePaginatedApi } from '../../hooks/useAsync';
import OrdersAPI from '../../api/orders';
import SubscriptionAPI from '../../api/subscription';

interface DashboardProps {
  animation?: 'shimmer' | 'pulse' | 'wave';
}

interface Order {
  id: string;
  created_at: string;
  status: string;
  total_amount: number;
  subscription_id?: string;
  order_number?: string;
}

interface User {
  firstname?: string;
  lastname?: string;
  email?: string;
  [key: string]: any;
}

export const Dashboard = ({
  animation = 'shimmer' 
}: DashboardProps) => {
  const { user } = useAuth() as { user: User | null };
  const { subscriptions, loading: subscriptionsLoading } = useSubscription();
  const { data: paginatedOrders, loading, error, execute: fetchRecentOrders } = usePaginatedApi();
  const { data: subscriptionOrders, loading: subscriptionOrdersLoading, execute: fetchSubscriptionOrders } = usePaginatedApi();

  // Handle both array and object responses - moved before useEffect
  const recentOrders: Order[] = (() => {
    if (!paginatedOrders) return [];
    // Handle Response.success wrapper
    if ((paginatedOrders as any)?.success) {
      const data = (paginatedOrders as any).data;
      // Check if data has orders array (paginated response)
      if (data && data.orders) {
        return data.orders;
      }
      // Otherwise return data directly if it's an array
      return Array.isArray(data) ? data : [];
    }
    // Handle direct array response
    if (Array.isArray(paginatedOrders)) {
      return paginatedOrders;
    }
    // Handle object with orders property
    if (paginatedOrders && typeof paginatedOrders === 'object' && 'orders' in paginatedOrders) {
      return (paginatedOrders as any).orders || [];
    }
    return [];
  })();

  const recentSubscriptionOrders: Order[] = (() => {
    if (!subscriptionOrders) return [];
    // Handle Response.success wrapper
    if ((subscriptionOrders as any)?.success) {
      const data = (subscriptionOrders as any).data;
      // Check if data has orders array (paginated response)
      if (data && data.orders) {
        return data.orders;
      }
      // Otherwise return data directly if it's an array
      return Array.isArray(data) ? data : [];
    }
    // Handle direct array response
    if (Array.isArray(subscriptionOrders)) {
      return subscriptionOrders;
    }
    // Handle object with orders property
    if (subscriptionOrders && typeof subscriptionOrders === 'object' && 'orders' in subscriptionOrders) {
      return (subscriptionOrders as any).orders || [];
    }
    return [];
  })();

  // Get active subscriptions
  const activeSubscriptions = subscriptions.filter(sub => sub.status === 'active');

  useEffect(() => {
    fetchRecentOrders(() => OrdersAPI.getOrders({ limit: 3 }));
    // Fetch subscription orders if there are active subscriptions
    if (subscriptions.length > 0) {
      const activeSubscription = subscriptions.find(sub => sub.status === 'active');
      if (activeSubscription) {
        fetchSubscriptionOrders(() => SubscriptionAPI.getOrders(activeSubscription.id, 1, 3));
      }
    }
  }, [fetchRecentOrders, fetchSubscriptionOrders, subscriptions]);

  // Debug logging
  useEffect(() => {
    if (paginatedOrders) {
      console.log('Dashboard Orders API Response:', paginatedOrders);
      console.log('Dashboard Processed orders:', recentOrders);
    }
  }, [paginatedOrders, recentOrders]);

  if (loading || subscriptionsLoading) {
    return <SkeletonDashboard className="p-6" animation={animation} />;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return <div>
      <h1 className="text-2xl font-bold text-main dark:text-white mb-6">
        My Account
      </h1>
      {/* Welcome Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-medium text-main dark:text-white mb-2">
          Welcome back, {user?.firstname}!
        </h2>
        <p className="text-gray-600 dark:text-gray-300 mb-4">
          Here's a summary of your account and recent activities.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          <Link to="/account/orders" className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center mr-3">
                <ShoppingBagIcon size={20} className="text-blue-600 dark:text-blue-300" />
              </div>
              <div>
                <h3 className="font-medium text-main dark:text-white">
                  Orders
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {recentOrders.length} recent orders
                </p>
              </div>
            </div>
          </Link>
          <Link to="/account/subscriptions" className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center mr-3">
                <PackageIcon size={20} className="text-green-600 dark:text-green-300" />
              </div>
              <div>
                <h3 className="font-medium text-main dark:text-white">
                  Subscriptions
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {activeSubscriptions.length} active subscriptions
                </p>
              </div>
            </div>
          </Link>
          <Link to="/account/wishlist" className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-full bg-error-light dark:bg-error-dark flex items-center justify-center mr-3">
                <HeartIcon size={20} className="text-error dark:text-error-light" />
              </div>
              <div>
                <h3 className="font-medium text-main dark:text-white">
                  Wishlist
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Saved items for later
                </p>
              </div>
            </div>
          </Link>
          <Link to="/account/addresses" className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-full bg-success-light dark:bg-success-dark flex items-center justify-center mr-3">
                <MapPinIcon size={20} className="text-success dark:text-success-light" />
              </div>
              <div>
                <h3 className="font-medium text-main dark:text-white">
                  Addresses
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Manage shipping addresses
                </p>
              </div>
            </div>
          </Link>
          <Link to="/account/payment-methods" className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center mr-3">
                <CreditCardIcon size={20} className="text-purple-600 dark:text-purple-300" />
              </div>
              <div>
                <h3 className="font-medium text-main dark:text-white">
                  Payment Methods
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Manage payment options
                </p>
              </div>
            </div>
          </Link>
        </div>
      </div>
      
      {/* Active Subscriptions Section */}
      {activeSubscriptions.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-main dark:text-white">
              Active Subscriptions
            </h2>
            <Link to="/account/subscriptions" className="text-primary hover:underline text-sm">
              View all subscriptions
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {activeSubscriptions.slice(0, 2).map((subscription: any) => (
              <div key={subscription.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-medium text-main dark:text-white">
                    {subscription.plan_id} Plan
                  </h3>
                  <span className="px-2 py-1 text-xs rounded-full bg-success-light text-success-dark dark:bg-success-dark dark:text-success-light">
                    Active
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                  {subscription.products?.length || 0} products • {subscription.billing_cycle}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Next billing: {subscription.next_billing_date ? new Date(subscription.next_billing_date).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Recent Orders Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium text-main dark:text-white">
            Recent Orders
          </h2>
          <Link to="/account/orders" className="text-primary hover:underline text-sm">
            View all orders
          </Link>
        </div>
        {recentOrders.length > 0 ? <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="text-xs text-gray-700 dark:text-gray-300 uppercase bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left">
                    Order ID
                  </th>
                  <th scope="col" className="px-4 py-3 text-left">
                    Date
                  </th>
                  <th scope="col" className="px-4 py-3 text-left">
                    Status
                  </th>
                  <th scope="col" className="px-4 py-3 text-right">
                    Total
                  </th>
                </tr>
              </thead>
              <tbody>
                {recentOrders.map((order: Order) => <tr key={order.id} className="border-b dark:border-gray-700">
                    <td className="px-4 py-3">
                      <Link to={`/account/orders/${order.id}`} className="text-primary hover:underline">
                        {order.id}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                      {new Date(order.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${order.status === 'Delivered' ? 'bg-success-light text-success-dark dark:bg-success-dark dark:text-success-light' : 'bg-info-light text-info-dark dark:bg-info-dark dark:text-info-light'}`}>
                        {order.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300 text-right">
                      ${order.total_amount.toFixed(2)}
                    </td>
                  </tr>)}
              </tbody>
            </table>
          </div> : <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400">
              You haven't placed any orders yet.
            </p>
            <Link to="/products" className="mt-2 inline-block text-primary hover:underline">
              Start shopping
            </Link>
          </div>}
      </div>
      
      {/* Subscription Orders Section */}
      {recentSubscriptionOrders.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mt-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium text-main dark:text-white">
              Recent Subscription Orders
            </h2>
            <Link to="/account/subscriptions" className="text-primary hover:underline text-sm">
              View all subscription orders
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="text-xs text-gray-700 dark:text-gray-300 uppercase bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left">
                    Order ID
                  </th>
                  <th scope="col" className="px-4 py-3 text-left">
                    Date
                  </th>
                  <th scope="col" className="px-4 py-3 text-left">
                    Status
                  </th>
                  <th scope="col" className="px-4 py-3 text-left">
                    Type
                  </th>
                  <th scope="col" className="px-4 py-3 text-right">
                    Total
                  </th>
                </tr>
              </thead>
              <tbody>
                {recentSubscriptionOrders.map((order: Order) => (
                  <tr key={order.id} className="border-b dark:border-gray-700">
                    <td className="px-4 py-3">
                      <Link to={`/account/orders/${order.id}`} className="text-primary hover:underline">
                        {order.order_number || order.id}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                      {new Date(order.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        order.status === 'Delivered' 
                          ? 'bg-success-light text-success-dark dark:bg-success-dark dark:text-success-light' 
                          : 'bg-info-light text-info-dark dark:bg-info-dark dark:text-info-light'
                      }`}>
                        {order.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                        Subscription
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300 text-right">
                      ${order.total_amount.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>;
};
export default Dashboard;