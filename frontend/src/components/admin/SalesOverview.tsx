import React, { useState, useEffect } from 'react';
import { 
  DollarSignIcon, 
  TrendingUpIcon, 
  TrendingDownIcon, 
  ShoppingCartIcon, 
  UsersIcon, 
  PackageIcon,
  CalendarIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  RefreshCwIcon
} from 'lucide-react';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import { themeClasses } from '../../lib/theme';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

interface SalesOverviewProps {
  timeRange?: '7d' | '30d' | '3m' | '12m';
  showFilters?: boolean;
  compact?: boolean;
}

interface SalesMetric {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon: React.ReactNode;
  color: string;
  trend?: number[];
}

interface SalesData {
  date: string;
  revenue: number;
  orders: number;
  customers: number;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

export const SalesOverview: React.FC<SalesOverviewProps> = ({ 
  timeRange = '30d', 
  showFilters = true,
  compact = false 
}) => {
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const {
    data: salesData,
    loading: salesLoading,
    error: salesError,
    execute: fetchSalesData,
  } = useApi();

  const {
    data: statsData,
    loading: statsLoading,
    error: statsError,
    execute: fetchStats,
  } = useApi();

  useEffect(() => {
    fetchSalesData(() => AdminAPI.getAdminStats());
    fetchStats(() => AdminAPI.getPlatformOverview());
  }, [selectedTimeRange]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([
      fetchSalesData(() => AdminAPI.getAdminStats()),
      fetchStats(() => AdminAPI.getPlatformOverview())
    ]);
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  const handleTimeRangeChange = (range: string) => {
    setSelectedTimeRange(range as any);
  };

  // Process data for metrics
  const stats = statsData?.data;
  const sales = salesData?.data;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatChange = (change: number | undefined) => {
    if (change === undefined || change === null) return null;
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(1)}%`;
  };

  const salesMetrics: SalesMetric[] = [
    {
      title: 'Total Revenue',
      value: formatCurrency(sales?.revenue?.total_revenue || 0),
      change: formatChange(sales?.revenue_change),
      changeType: (sales?.revenue_change || 0) >= 0 ? 'increase' : 'decrease',
      icon: <DollarSignIcon size={20} />,
      color: 'bg-blue-500',
      trend: [65, 78, 82, 95, 88, 92, 100] // Mock trend data
    },
    {
      title: 'Total Orders',
      value: (sales?.overview?.total_orders || 0).toLocaleString(),
      change: formatChange(sales?.orders_change),
      changeType: (sales?.orders_change || 0) >= 0 ? 'increase' : 'decrease',
      icon: <ShoppingCartIcon size={20} />,
      color: 'bg-green-500',
      trend: [45, 52, 48, 61, 70, 65, 72]
    },
    {
      title: 'New Customers',
      value: (sales?.overview?.total_users || 0).toLocaleString(),
      change: formatChange(sales?.customers_change),
      changeType: (sales?.customers_change || 0) >= 0 ? 'increase' : 'decrease',
      icon: <UsersIcon size={20} />,
      color: 'bg-purple-500',
      trend: [30, 35, 32, 45, 42, 48, 50]
    },
    {
      title: 'Products Sold',
      value: (sales?.overview?.total_products || 0).toLocaleString(),
      change: formatChange(sales?.products_change),
      changeType: (sales?.products_change || 0) >= 0 ? 'increase' : 'decrease',
      icon: <PackageIcon size={20} />,
      color: 'bg-orange-500',
      trend: [120, 135, 128, 145, 152, 148, 160]
    }
  ];

  // Mock chart data - in real app, this would come from API
  const chartData: SalesData[] = [
    { date: 'Mon', revenue: 12000, orders: 45, customers: 12 },
    { date: 'Tue', revenue: 15000, orders: 52, customers: 18 },
    { date: 'Wed', revenue: 18000, orders: 61, customers: 15 },
    { date: 'Thu', revenue: 22000, orders: 68, customers: 22 },
    { date: 'Fri', revenue: 25000, orders: 75, customers: 28 },
    { date: 'Sat', revenue: 28000, orders: 82, customers: 25 },
    { date: 'Sun', revenue: 24000, orders: 70, customers: 20 }
  ];

  const categoryData = [
    { name: 'Supplements', value: 35, color: COLORS[0] },
    { name: 'Herbs', value: 25, color: COLORS[1] },
    { name: 'Oils', value: 20, color: COLORS[2] },
    { name: 'Teas', value: 15, color: COLORS[3] },
    { name: 'Others', value: 5, color: COLORS[4] }
  ];

  if (salesError && statsError) {
    return (
      <div className={`${themeClasses.card.base} p-6`}>
        <div className="text-center">
          <div className="text-red-500 mb-2">Failed to load sales data</div>
          <button
            onClick={handleRefresh}
            className={`${themeClasses.button.primary} px-4 py-2 rounded-md`}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      {!compact && (
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className={`${themeClasses.text.heading} text-2xl font-bold`}>Sales Overview</h2>
            <p className={`${themeClasses.text.muted} text-sm mt-1`}>
              Track your sales performance and key metrics
            </p>
          </div>
          <div className="flex items-center gap-3">
            {showFilters && (
              <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                {['7d', '30d', '3m', '12m'].map((range) => (
                  <button
                    key={range}
                    onClick={() => handleTimeRangeChange(range)}
                    className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                      selectedTimeRange === range
                        ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    {range.toUpperCase()}
                  </button>
                ))}
              </div>
            )}
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className={`${themeClasses.button.outline} flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50`}
            >
              <RefreshCwIcon size={16} className={`mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      )}

      {/* Metrics Cards */}
      <div className={`grid grid-cols-1 ${compact ? 'md:grid-cols-2' : 'md:grid-cols-2 lg:grid-cols-4'} gap-4`}>
        {salesMetrics.map((metric, index) => (
          <div key={index} className={`${themeClasses.card.base} p-6 hover:shadow-lg transition-shadow`}>
            <div className="flex items-center justify-between mb-4">
              <div className={`w-10 h-10 rounded-lg ${metric.color} text-white flex items-center justify-center`}>
                {metric.icon}
              </div>
              {metric.change && (
                <div className={`flex items-center text-sm font-medium ${
                  metric.changeType === 'increase' 
                    ? 'text-green-600 dark:text-green-400' 
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {metric.changeType === 'increase' ? (
                    <ArrowUpIcon size={16} className="mr-1" />
                  ) : (
                    <ArrowDownIcon size={16} className="mr-1" />
                  )}
                  {metric.change}
                </div>
              )}
            </div>
            <h3 className={`${themeClasses.text.muted} text-sm mb-1`}>{metric.title}</h3>
            <div className="text-gray-900 dark:text-white text-2xl font-bold mb-3">{metric.value}</div>
            
            {/* Mini trend chart */}
            {metric.trend && !compact && (
              <div className="h-8">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={metric.trend.map((value, i) => ({ value, index: i }))}>
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke={metric.color.replace('bg-', '#')} 
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Charts Section */}
      {!compact && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Revenue Trend Chart */}
          <div className={`${themeClasses.card.base} lg:col-span-2 p-6`}>
            <h3 className={`${themeClasses.text.heading} text-lg font-semibold mb-4`}>Revenue Trend</h3>
            <div className="h-64">
              {salesLoading ? (
                <div className="h-full flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="date" stroke="var(--color-copy-lighter)" fontSize={12} />
                    <YAxis stroke="var(--color-copy-lighter)" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'var(--color-surface-elevated)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-copy)',
                      }}
                      formatter={(value: any) => [formatCurrency(value), 'Revenue']}
                    />
                    <Bar dataKey="revenue" fill="var(--color-primary)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Sales by Category */}
          <div className={`${themeClasses.card.base} p-6`}>
            <h3 className={`${themeClasses.text.heading} text-lg font-semibold mb-4`}>Sales by Category</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: any) => [`${value}%`, 'Share']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 space-y-2">
              {categoryData.map((category, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <div className="flex items-center">
                    <div 
                      className="w-3 h-3 rounded-full mr-2" 
                      style={{ backgroundColor: category.color }}
                    ></div>
                    <span className={themeClasses.text.body}>{category.name}</span>
                  </div>
                  <span className={`${themeClasses.text.muted} font-medium`}>{category.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Quick Stats */}
      {compact && (
        <div className={`${themeClasses.card.base} p-4`}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className={`${themeClasses.text.muted} text-xs uppercase tracking-wide mb-1`}>Avg Order</div>
              <div className="text-lg font-semibold">{formatCurrency(285)}</div>
            </div>
            <div>
              <div className={`${themeClasses.text.muted} text-xs uppercase tracking-wide mb-1`}>Conversion</div>
              <div className="text-lg font-semibold">3.2%</div>
            </div>
            <div>
              <div className={`${themeClasses.text.muted} text-xs uppercase tracking-wide mb-1`}>Return Rate</div>
              <div className="text-lg font-semibold">2.1%</div>
            </div>
            <div>
              <div className={`${themeClasses.text.muted} text-xs uppercase tracking-wide mb-1`}>Growth</div>
              <div className="text-lg font-semibold text-green-600">+12.5%</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SalesOverview;