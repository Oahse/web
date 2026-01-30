import React, { useEffect, useState } from 'react';
import { 
  BarChart3Icon, 
  UsersIcon, 
  ShoppingCartIcon, 
  DollarSignIcon, 
  TrendingUpIcon, 
  PackageIcon, 
  CreditCardIcon, 
  ActivityIcon, 
  EyeIcon,
  ArrowRightIcon
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import AdminAPI from '../../api/admin';
import toast from 'react-hot-toast';
import { useTheme } from '../../store/ThemeContext';
import { useLocale } from '../../store/LocaleContext';
import { 
  PageLayout, 
  StatsCard, 
  DataTable 
} from './shared';

// Types
interface AdminStats {
  overview: {
    total_users: number;
    active_users: number;
    total_orders: number;
    orders_today: number;
    total_products: number;
    active_products: number;
    total_subscriptions: number;
    active_subscriptions: number;
  };
  revenue: {
    total_revenue: number;
    revenue_today: number;
    revenue_this_month: number;
    currency: string;
  };
  recent_orders: Array<{
    id: string;
    user_email: string;
    total_amount: number;
    status: string;
    created_at: string;
  }>;
  generated_at: string;
}

export const Dashboard = () => {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { theme } = useTheme();
  const { formatCurrency } = useLocale();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await AdminAPI.getAdminStats();
        
        if (response?.success && response?.data) {
          setStats(response.data);
        } else {
          throw new Error('Failed to fetch admin stats');
        }
      } catch (err: any) {
        const errorMessage = err.response?.data?.message || err.message || 'Failed to load dashboard data';
        setError(errorMessage);
        toast.error(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  // Stats cards configuration
  const statsCards = [
    {
      title: 'Total Users',
      value: stats?.overview.total_users || 0,
      change: {
        value: 12,
        type: 'increase' as const,
        period: 'from last month'
      },
      icon: UsersIcon,
      color: 'blue' as const,
      onClick: () => navigate('/admin/users')
    },
    {
      title: 'Total Orders',
      value: stats?.overview.total_orders || 0,
      change: {
        value: 8,
        type: 'increase' as const,
        period: 'from last month'
      },
      icon: ShoppingCartIcon,
      color: 'green' as const,
      onClick: () => navigate('/admin/orders')
    },
    {
      title: 'Total Products',
      value: stats?.overview.total_products || 0,
      change: {
        value: 5,
        type: 'increase' as const,
        period: 'from last month'
      },
      icon: PackageIcon,
      color: 'purple' as const,
      onClick: () => navigate('/admin/products')
    },
    {
      title: 'Total Revenue',
      value: formatCurrency(stats?.revenue.total_revenue || 0),
      change: {
        value: 15,
        type: 'increase' as const,
        period: 'from last month'
      },
      icon: DollarSignIcon,
      color: 'green' as const
    },
    {
      title: 'Active Subscriptions',
      value: stats?.overview.active_subscriptions || 0,
      change: {
        value: 3,
        type: 'decrease' as const,
        period: 'from last month'
      },
      icon: CreditCardIcon,
      color: 'indigo' as const,
      onClick: () => navigate('/admin/subscriptions')
    },
    {
      title: 'Orders Today',
      value: stats?.overview.orders_today || 0,
      icon: ActivityIcon,
      color: 'yellow' as const
    }
  ];

  // Recent orders table configuration
  const recentOrdersColumns = [
    {
      key: 'id',
      label: 'Order ID',
      render: (value: string) => (
        <span className="font-mono text-sm">#{value.slice(-8)}</span>
      )
    },
    {
      key: 'user_email',
      label: 'Customer',
      render: (value: string) => (
        <span className="text-sm text-gray-900">{value}</span>
      )
    },
    {
      key: 'total_amount',
      label: 'Amount',
      render: (value: number) => (
        <span className="text-sm font-medium text-gray-900">
          {formatCurrency(value)}
        </span>
      ),
      align: 'right' as const
    },
    {
      key: 'status',
      label: 'Status',
      render: (value: string) => {
        const statusColors = {
          pending: 'bg-yellow-100 text-yellow-800',
          confirmed: 'bg-blue-100 text-blue-800',
          shipped: 'bg-purple-100 text-purple-800',
          delivered: 'bg-green-100 text-green-800',
          cancelled: 'bg-red-100 text-red-800'
        };
        
        return (
          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
            statusColors[value as keyof typeof statusColors] || 'bg-gray-100 text-gray-800'
          }`}>
            {value}
          </span>
        );
      }
    },
    {
      key: 'created_at',
      label: 'Date',
      render: (value: string) => (
        <span className="text-sm text-gray-500">
          {new Date(value).toLocaleDateString()}
        </span>
      )
    }
  ];

  const handleViewOrder = (order: any) => {
    navigate(`/admin/orders/${order.id}`);
  };

  return (
    <PageLayout
      title="Dashboard"
      subtitle="Welcome back to your admin dashboard"
      description="Here's what's happening with your business today"
      icon={BarChart3Icon}
      actions={
        <button
          onClick={() => window.location.reload()}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <ActivityIcon className="h-4 w-4" />
          Refresh
        </button>
      }
      breadcrumbs={[
        { label: 'Home', href: '/' },
        { label: 'Admin' },
        { label: 'Dashboard' }
      ]}
    >
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {statsCards.map((card, index) => (
            <StatsCard
              key={index}
              {...card}
              loading={loading}
              error={error || undefined}
            />
          ))}
        </div>

        {/* Recent Orders */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Orders Table */}
          <div className="lg:col-span-2">
            <DataTable
              data={stats?.recent_orders || []}
              loading={loading}
              error={error}
              pagination={{
                page: 1,
                limit: 5,
                total: stats?.recent_orders?.length || 0,
                pages: 1
              }}
              columns={recentOrdersColumns}
              fetchData={async () => {}} // No-op for static data
              onView={handleViewOrder}
              searchable={false} // Search is handled by AdminFilterBar
              filterable={false} // Filters are handled by AdminFilterBar
              emptyMessage="No recent orders"
              className="h-96"
            />
          </div>

          {/* Quick Actions */}
          <div className="space-y-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button
                  onClick={() => navigate('/admin/products/new')}
                  className="w-full flex items-center justify-between p-3 text-left border border-gray-200 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <PackageIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">Add New Product</span>
                  </div>
                  <ArrowRightIcon className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                </button>
                
                <button
                  onClick={() => navigate('/admin/orders')}
                  className="w-full flex items-center justify-between p-3 text-left border border-gray-200 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <ShoppingCartIcon className="h-5 w-5 text-green-600 dark:text-green-400" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">View All Orders</span>
                  </div>
                  <ArrowRightIcon className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                </button>
                
                <button
                  onClick={() => navigate('/admin/users')}
                  className="w-full flex items-center justify-between p-3 text-left border border-gray-200 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <UsersIcon className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">Manage Users</span>
                  </div>
                  <ArrowRightIcon className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                </button>
                
                <button
                  onClick={() => navigate('/admin/analytics')}
                  className="w-full flex items-center justify-between p-3 text-left border border-gray-200 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <TrendingUpIcon className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">View Analytics</span>
                  </div>
                  <ArrowRightIcon className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                </button>
              </div>
            </div>

            {/* System Status */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">System Status</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">API Status</span>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                    Operational
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Database</span>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                    Connected
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Last Sync</span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {stats?.generated_at ? new Date(stats.generated_at).toLocaleString() : 'Never'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

export default Dashboard;
