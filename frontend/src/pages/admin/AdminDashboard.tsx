import { useState, useEffect } from 'react';
import { ShoppingCartIcon, UsersIcon, DollarSignIcon, ArrowUpIcon, ArrowDownIcon, PackageIcon, Activity, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import { SalesChart } from '../../components/admin/SalesChart';
import { themeClasses } from '../../lib/theme';
import ErrorMessage from '../../components/common/ErrorMessage';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string | null;
  increasing?: boolean;
  icon: React.ReactNode;
  color: string;
  loading?: boolean;
}

const StatCard = ({ title, value, change, increasing, icon, color, loading }: StatCardProps) => {
  if (loading) {
    return (
      <div className={`${themeClasses.card.base} p-6 animate-pulse`}>
        <div className="flex items-center justify-between mb-4">
          <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
          {change && <div className="w-16 h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>}
        </div>
        <div className="w-20 h-4 bg-gray-200 dark:bg-gray-700 rounded mb-1"></div>
        <div className="w-24 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    );
  }

  return (
    <div className={`${themeClasses.card.base} p-6 hover:shadow-lg transition-shadow`}>
      <div className="flex items-center justify-between mb-4">
        <div className={`w-10 h-10 rounded-lg ${color} text-white flex items-center justify-center`}>
          {icon}
        </div>
        {change && (
          <div className={`flex items-center text-sm font-medium ${increasing ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
            {increasing ? <ArrowUpIcon size={16} className="mr-1" /> : <ArrowDownIcon size={16} className="mr-1" />}
            {change}
          </div>
        )}
      </div>
      <h3 className={`${themeClasses.text.muted} text-sm mb-1`}>{title}</h3>
      <div className="text-gray-900 dark:text-white text-2xl font-bold">{value}</div>
    </div>
  );
};

interface OrderRowProps {
  order: any;
}

const OrderRow = ({ order }: OrderRowProps) => {
  const getStatusColor = (status: string) => {
    const statusLower = status?.toLowerCase() || '';
    if (statusLower === 'delivered') return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
    if (statusLower === 'shipped') return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
    if (statusLower === 'cancelled') return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
    return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
  };

  const customerName = order.user 
    ? `${order.user.firstname || ''} ${order.user.lastname || ''}`.trim() || 'N/A'
    : order.customer || 'N/A';

  const orderDate = order.date || (order.created_at ? new Date(order.created_at).toLocaleDateString() : 'N/A');
  const orderTotal = order.total || order.total_amount || 0;
  const orderStatus = order.status || 'pending';

  return (
    <tr className="border-b dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
      <td className="text-gray-900 dark:text-white py-3 px-2">
        <Link 
          to={`/admin/orders/${order.id}`} 
          className="text-primary hover:underline font-mono text-sm"
        >
          #{String(order.id).slice(0, 8)}
        </Link>
      </td>
      <td className="text-gray-900 dark:text-white py-3 px-2">
        {customerName}
      </td>
      <td className={`${themeClasses.text.muted} py-3 px-2 text-sm`}>
        {orderDate}
      </td>
      <td className="py-3 px-2">
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(orderStatus)}`}>
          {orderStatus.charAt(0).toUpperCase() + orderStatus.slice(1)}
        </span>
      </td>
      <td className="py-3 px-2 font-medium text-right">
        ${orderTotal.toFixed(2)}
      </td>
    </tr>
  );
};

interface ProductCardProps {
  product: any;
}

const ProductCard = ({ product }: ProductCardProps) => {
  const imageUrl = product.image_url || product.image || 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?ixlib=rb-4.0.3&auto=format&fit=crop&w=100&q=80';
  
  return (
    <div className="flex items-center hover:bg-gray-50 dark:hover:bg-gray-800 p-2 rounded-lg transition-colors">
      <img 
        src={imageUrl} 
        alt={product.name} 
        className="w-12 h-12 rounded-md object-cover mr-3 border border-gray-200 dark:border-gray-700" 
        onError={(e) => {
          (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?ixlib=rb-4.0.3&auto=format&fit=crop&w=100&q=80';
        }}
      />
      <div className="flex-grow min-w-0">
        <h3 className="text-gray-900 dark:text-white font-medium text-sm truncate">
          {product.name}
        </h3>
        <p className={`${themeClasses.text.muted} text-xs`}>
          {product.sales || 0} sales
        </p>
      </div>
      <div className="text-right ml-2">
        <p className="text-gray-900 dark:text-white font-semibold text-sm">
          ${(product.revenue || 0).toFixed(2)}
        </p>
      </div>
    </div>
  );
};

export const AdminDashboard = () => {
  const [isRefreshing, setIsRefreshing] = useState(false);

  // API calls for dashboard data
  const {
    data: adminStats,
    loading: statsLoading,
    error: statsError,
    execute: executeStats,
  } = useApi();

  const {
    data: platformOverview,
    loading: overviewLoading,
    error: overviewError,
    execute: executeOverview,
  } = useApi();

  const {
    data: recentOrdersData,
    loading: ordersLoading,
    error: ordersError,
    execute: executeOrders,
  } = useApi();

  // Initial data fetch
  useEffect(() => {
    executeStats(AdminAPI.getAdminStats);
    executeOverview(AdminAPI.getPlatformOverview);
    executeOrders(() => AdminAPI.getAllOrders({ page: 1, limit: 10 }));
  }, []);

  const handleRefresh = () => {
    setIsRefreshing(true);
    executeStats(AdminAPI.getAdminStats);
    executeOverview(AdminAPI.getPlatformOverview);
    executeOrders(() => AdminAPI.getAllOrders({ page: 1, limit: 10 }));
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  // Extract real data from API responses
  const statsData = adminStats?.data;
  
  const formatChange = (change: number | undefined) => {
    if (change === undefined || change === null) return null;
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(1)}%`;
  };
  
  const stats = [
    {
      title: 'Total Revenue',
      value: statsData?.total_revenue 
        ? `$${statsData.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
        : '$0.00',
      change: formatChange(statsData?.revenue_change),
      increasing: (statsData?.revenue_change || 0) >= 0,
      icon: <DollarSignIcon size={20} />,
      color: 'bg-blue-500'
    },
    {
      title: 'Total Orders',
      value: statsData?.total_orders?.toLocaleString() || '0',
      change: formatChange(statsData?.orders_change),
      increasing: (statsData?.orders_change || 0) >= 0,
      icon: <ShoppingCartIcon size={20} />,
      color: 'bg-green-500'
    },
    {
      title: 'Total Customers',
      value: statsData?.total_customers?.toLocaleString() || '0',
      change: formatChange(statsData?.customers_change),
      increasing: (statsData?.customers_change || 0) >= 0,
      icon: <UsersIcon size={20} />,
      color: 'bg-purple-500'
    },
    {
      title: 'Total Products',
      value: statsData?.total_products?.toLocaleString() || '0',
      change: formatChange(statsData?.products_change),
      increasing: (statsData?.products_change || 0) >= 0,
      icon: <PackageIcon size={20} />,
      color: 'bg-orange-500'
    }
  ];

  // Extract orders and products from API responses
  const recentOrders = recentOrdersData?.data?.data || [];
  const topProducts = platformOverview?.data?.top_products || [];

  if (statsError && overviewError && ordersError) {
    return (
      <div className="p-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200 mb-2">Failed to load dashboard data</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className={`${themeClasses.text.heading} text-3xl font-bold`}>Admin Dashboard</h1>
          <p className={`${themeClasses.text.muted} text-sm mt-1`}>
            Welcome back! Here's what's happening with your store today.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={handleRefresh}
            disabled={isRefreshing}
            className={`${themeClasses.button.outline} flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50`}
          >
            <RefreshCw size={16} className={`mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <StatCard key={index} {...stat} loading={statsLoading} />
        ))}
      </div>

      {/* Sales Chart */}
      <div className={`${themeClasses.card.base} p-6`}>
        <h2 className={`${themeClasses.text.heading} text-lg font-semibold mb-4`}>Sales Overview</h2>
        <SalesChart />
      </div>

      {/* Recent Orders and Top Products */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Orders */}
        <div className={`${themeClasses.card.base} lg:col-span-2 p-6`}>
          <div className="flex items-center justify-between mb-4">
            <h2 className={`${themeClasses.text.heading} text-lg font-semibold`}>Recent Orders</h2>
            <Link to="/admin/orders" className="text-primary hover:underline text-sm font-medium">
              View All →
            </Link>
          </div>
          
          {ordersLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse flex items-center gap-4">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                  <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded-full w-20"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 ml-auto"></div>
                </div>
              ))}
            </div>
          ) : recentOrders.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className={`${themeClasses.text.muted} text-left border-b dark:border-gray-700 text-xs uppercase`}>
                    <th className="pb-3 px-2 font-semibold">Order ID</th>
                    <th className="pb-3 px-2 font-semibold">Customer</th>
                    <th className="pb-3 px-2 font-semibold">Date</th>
                    <th className="pb-3 px-2 font-semibold">Status</th>
                    <th className="pb-3 px-2 font-semibold text-right">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {recentOrders.map((order: any) => (
                    <OrderRow key={order.id} order={order} />
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <ShoppingCartIcon size={48} className="mx-auto text-gray-300 dark:text-gray-600 mb-3" />
              <p className={`${themeClasses.text.muted} text-sm`}>No orders yet</p>
            </div>
          )}
        </div>

        {/* Top Products */}
        <div className={`${themeClasses.card.base} p-6`}>
          <div className="flex items-center justify-between mb-4">
            <h2 className={`${themeClasses.text.heading} text-lg font-semibold`}>Top Products</h2>
            <Link to="/admin/products" className="text-primary hover:underline text-sm font-medium">
              View All →
            </Link>
          </div>
          
          {overviewLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse flex items-center gap-3">
                  <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                  <div className="flex-grow">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-2"></div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
                  </div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
                </div>
              ))}
            </div>
          ) : topProducts.length > 0 ? (
            <div className="space-y-2">
              {topProducts.map((product: any) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <PackageIcon size={48} className="mx-auto text-gray-300 dark:text-gray-600 mb-3" />
              <p className={`${themeClasses.text.muted} text-sm`}>No products yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
