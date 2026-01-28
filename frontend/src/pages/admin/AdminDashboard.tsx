import { useState, useEffect, useCallback } from 'react';
import { 
  ShoppingCartIcon, 
  UsersIcon, 
  DollarSignIcon, 
  ArrowUpIcon, 
  ArrowDownIcon, 
  PackageIcon, 
  Activity, 
  RefreshCw,
  TrendingUpIcon,
  CalendarIcon,
  FilterIcon,
  XIcon,
  BarChart3Icon,
  LineChartIcon
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend,
  Area,
  AreaChart
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { useApi } from '../../hooks/useAsync';
import { AdminAPI, CategoriesAPI } from '../../apis';

import { SalesFilters, SalesData, SalesMetrics } from '../../components/admin/sales/types';
import AnalyticsAPI from '../../api/analytics';
import { themeClasses } from '../../utils/theme';
import ErrorMessage from '../../components/common/ErrorMessage';

// Chart utilities
const CHART_COLORS = {
  primary: '#3B82F6',
  secondary: '#10B981',
  accent: '#F59E0B',
  danger: '#EF4444',
  purple: '#8B5CF6'
};

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

const formatNumber = (value: number) => {
  return new Intl.NumberFormat('en-US').format(value);
};

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
      <div className={`${themeClasses.card.base} p-4 sm:p-6 animate-pulse`}>
        <div className="flex items-center justify-between mb-3 sm:mb-4">
          <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
          {change && <div className="w-12 sm:w-16 h-3 sm:h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>}
        </div>
        <div className="w-16 sm:w-20 h-3 sm:h-4 bg-gray-200 dark:bg-gray-700 rounded mb-1"></div>
        <div className="w-20 sm:w-24 h-6 sm:h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    );
  }

  return (
    <div className={`${themeClasses.card.base} p-4 sm:p-6 hover:shadow-lg transition-shadow`}>
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg ${color} text-white flex items-center justify-center`}>
          {icon}
        </div>
        {change && (
          <div className={`flex items-center text-xs sm:text-sm font-medium ${increasing ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
            {increasing ? <ArrowUpIcon size={14} className="mr-1 sm:mr-1" /> : <ArrowDownIcon size={14} className="mr-1 sm:mr-1" />}
            <span className="hidden xs:inline">{change}</span>
            <span className="xs:hidden">{change?.replace('%', '')}</span>
          </div>
        )}
      </div>
      <h3 className={`${themeClasses.text.muted} text-xs sm:text-sm mb-1`}>{title}</h3>
      <div className="text-gray-900 dark:text-white text-lg sm:text-2xl font-bold truncate">{value}</div>
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

  // Extract customer information from order
  const customer = order.user || order.customer;
  const customerName = customer 
    ? (typeof customer === 'string' 
        ? customer 
        : `${customer.firstname || customer.firstname || ''} ${customer.lastname || customer.lastname || ''}`.trim() || customer.email || customer.name || 'Unknown Customer'
      )
    : 'Guest Customer';
  
  const customerId = customer && typeof customer === 'object' ? customer.id : null;
  const truncatedName = customerName.length > 15 ? `${customerName.substring(0, 15)}...` : customerName;

  const orderDate = order.date || (order.created_at ? new Date(order.created_at).toLocaleDateString() : 'N/A');
  const orderTotal = order.total || order.total_amount || 0;
  const orderStatus = order.status || 'pending';

  return (
    <tr className="border-b dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
      <td className="text-gray-900 dark:text-white py-2 sm:py-3 px-1 sm:px-2">
        <Link 
          to={`/admin/orders/${order.id}`} 
          className="text-primary hover:underline font-mono text-xs sm:text-sm"
        >
          #{String(order.id).slice(0, 6)}
        </Link>
      </td>
      <td className="text-gray-900 dark:text-white py-2 sm:py-3 px-1 sm:px-2">
        {customerId ? (
          <Link 
            to={`/admin/users/${customerId}`} 
            className="text-primary hover:underline cursor-pointer text-xs sm:text-sm"
            title={customerName}
          >
            {truncatedName}
          </Link>
        ) : (
          <span title={customerName} className="text-xs sm:text-sm">{truncatedName}</span>
        )}
      </td>
      <td className={`${themeClasses.text.muted} py-2 sm:py-3 px-1 sm:px-2 text-xs sm:text-sm hidden sm:table-cell`}>
        {orderDate}
      </td>
      <td className="py-2 sm:py-3 px-1 sm:px-2">
        <span className={`px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full text-xs font-medium ${getStatusColor(orderStatus)}`}>
          <span className="hidden sm:inline">{orderStatus.charAt(0).toUpperCase() + orderStatus.slice(1)}</span>
          <span className="sm:hidden">{orderStatus.charAt(0).toUpperCase()}</span>
        </span>
      </td>
      <td className="py-2 sm:py-3 px-1 sm:px-2 font-medium text-right text-xs sm:text-sm">
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
        className="w-10 h-10 sm:w-12 sm:h-12 rounded-md object-cover mr-2 sm:mr-3 border border-gray-200 dark:border-gray-700" 
        onError={(e) => {
          (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?ixlib=rb-4.0.3&auto=format&fit=crop&w=100&q=80';
        }}
      />
      <div className="flex-grow min-w-0">
        <h3 className="text-gray-900 dark:text-white font-medium text-xs sm:text-sm truncate">
          {product.name}
        </h3>
        <p className={`${themeClasses.text.muted} text-xs`}>
          {product.sales || 0} sales
        </p>
      </div>
      <div className="text-right ml-2">
        <p className="text-gray-900 dark:text-white font-semibold text-xs sm:text-sm">
          ${(product.revenue || 0).toFixed(2)}
        </p>
      </div>
    </div>
  );
};

export const AdminDashboard = () => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'analytics'>('overview');
  
  // Analytics state
  const [chartType, setChartType] = useState<'line' | 'bar' | 'area'>('line');
  const [showFilters, setShowFilters] = useState(false);
  const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['revenue', 'orders']);

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

  const {
    data: salesData,
    loading: salesLoading,
    error: salesError,
    execute: fetchSalesData,
  } = useApi<{
    data: SalesData[];
    metrics: SalesMetrics;
  }>();

  const { data: categoriesData, loading: categoriesLoading, error: categoriesError, execute: fetchCategories } = useApi<{
    categories: { id: string; name: string }[];
  }>();

  const [salesFilters, setSalesFilters] = useState<SalesFilters>({
    dateRange: '30d',
    startDate: '',
    endDate: '',
    categories: [],
    regions: [],
    salesChannels: ['online', 'instore'],
    granularity: 'daily'
  });

  // Fetch categories on component mount
  useEffect(() => {
    fetchCategories(CategoriesAPI.getCategories);
  }, [fetchCategories]);

  const availableCategories = categoriesData?.categories || [];

  const availableRegions = [
    { id: 'north-america', name: 'North America' },
    { id: 'europe', name: 'Europe' },
    { id: 'asia-pacific', name: 'Asia Pacific' },
    { id: 'africa', name: 'Africa' }
  ];

  const fetchSales = useCallback(async () => {
    const response = await AnalyticsAPI.getSalesOverview({
      days: salesFilters.dateRange === '7d' ? 7 : 
            salesFilters.dateRange === '30d' ? 30 : 
            salesFilters.dateRange === '3m' ? 90 : 
            salesFilters.dateRange === '12m' ? 365 : 30,
      granularity: salesFilters.granularity,
      categories: salesFilters.categories.length > 0 ? salesFilters.categories : undefined,
      regions: salesFilters.regions.length > 0 ? salesFilters.regions : undefined,
      sales_channels: salesFilters.salesChannels.length > 0 ? salesFilters.salesChannels : undefined,
      start_date: salesFilters.dateRange === 'custom' && salesFilters.startDate ? salesFilters.startDate : undefined,
      end_date: salesFilters.dateRange === 'custom' && salesFilters.endDate ? salesFilters.endDate : undefined
    });
    
    return response.data;
  }, [salesFilters]);

  // Log data to console for verification
  useEffect(() => {
    if (salesData) {
      console.log('Sales Data from API:', salesData);
    }
    if (categoriesData) {
      console.log('Categories Data from API:', categoriesData);
    }
  }, [salesData, categoriesData]);

  // Initial data fetch
  useEffect(() => {
    executeStats(AdminAPI.getAdminStats);
    executeOverview(AdminAPI.getPlatformOverview);
    executeOrders(() => AdminAPI.getAllOrders({ page: 1, limit: 10 }));
    fetchSalesData(fetchSales);
  }, [executeStats, executeOverview, executeOrders, fetchSalesData, fetchSales]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    executeStats(AdminAPI.getAdminStats);
    executeOverview(AdminAPI.getPlatformOverview);
    executeOrders(() => AdminAPI.getAllOrders({ page: 1, limit: 10 }));
    fetchSalesData(fetchSales);
    fetchCategories(CategoriesAPI.getCategories);
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  const handleSalesFiltersChange = (newFilters: SalesFilters) => {
    setSalesFilters(newFilters);
  };

  // Analytics functions
  const handleFilterChange = (key: keyof SalesFilters, value: any) => {
    const newFilters = { ...salesFilters, [key]: value };
    setSalesFilters(newFilters);
    handleSalesFiltersChange(newFilters);
  };
  
  const handleCategoryToggle = (categoryId: string) => {
    const newCategories = salesFilters.categories.includes(categoryId)
      ? salesFilters.categories.filter(id => id !== categoryId)
      : [...salesFilters.categories, categoryId];
    handleFilterChange('categories', newCategories);
  };

  const handleRegionToggle = (regionId: string) => {
    const newRegions = salesFilters.regions.includes(regionId)
      ? salesFilters.regions.filter(id => id !== regionId)
      : [...salesFilters.regions, regionId];
    handleFilterChange('regions', newRegions);
  };

  const handleSalesChannelToggle = (channel: string) => {
    const newSalesChannels = salesFilters.salesChannels.includes(channel)
      ? salesFilters.salesChannels.filter(c => c !== channel)
      : [...salesFilters.salesChannels, channel];
    handleFilterChange('salesChannels', newSalesChannels);
  };

  const handleMetricToggle = (metric: string) => {
    setSelectedMetrics(prev => 
      prev.includes(metric)
        ? prev.filter(m => m !== metric)
        : [...prev, metric]
    );
  };

  const resetFilters = () => {
    const defaultFilters: SalesFilters = {
      dateRange: '30d',
      startDate: '',
      endDate: '',
      categories: [],
      regions: [],
      salesChannels: ['online', 'instore'],
      granularity: 'daily'
    };
    setSalesFilters(defaultFilters);
    handleSalesFiltersChange(defaultFilters);
    setShowCustomDatePicker(false);
  };

  const hasActiveFilters = salesFilters.categories.length > 0 || 
                          salesFilters.regions.length > 0 || 
                          salesFilters.salesChannels.length !== 2 ||
                          salesFilters.dateRange === 'custom';

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-4 min-w-[200px]">
          <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between mb-1">
              <div className="flex items-center">
                <div 
                  className="w-3 h-3 rounded-full mr-2" 
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-gray-600 dark:text-gray-300">{entry.name}:</span>
              </div>
              <span className="text-sm font-medium text-gray-900 dark:text-white ml-2">
                {entry.name === 'Revenue' || entry.name.includes('Revenue') 
                  ? formatCurrency(entry.value)
                  : formatNumber(entry.value)
                }
              </span>
            </div>
          ))}
          {payload[0]?.payload && (
            <div className="border-t border-gray-200 dark:border-gray-700 pt-2 mt-2">
              <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                <span>Avg Order Value:</span>
                <span>{formatCurrency(payload[0].payload.averageOrderValue)}</span>
              </div>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  // Render chart function
  const renderChart = () => {
    if (!salesData?.data || salesData.data.length === 0) {
      return (
        <div className="h-full flex items-center justify-center">
          <div className="text-center">
            <BarChart3Icon size={48} className="mx-auto text-gray-300 dark:text-gray-600 mb-4" />
            <p className="text-gray-600 dark:text-gray-300 text-lg mb-2">No sales data available</p>
            <p className="text-gray-400 dark:text-gray-500 text-sm">
              Try adjusting your filters or date range
            </p>
          </div>
        </div>
      );
    }

    const chartData = salesData.data;
    const ChartComponent = chartType === 'line' ? LineChart : chartType === 'bar' ? BarChart : AreaChart;

    return (
      <ResponsiveContainer width="100%" height="100%">
        <ChartComponent data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.3} />
          <XAxis 
            dataKey="date" 
            stroke="#6b7280" 
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis 
            stroke="#6b7280" 
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => formatCurrency(value)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          
          {selectedMetrics.includes('revenue') && (
            chartType === 'area' ? (
              <Area
                type="monotone"
                dataKey="revenue"
                stroke={CHART_COLORS.primary}
                fill={CHART_COLORS.primary}
                fillOpacity={0.1}
                strokeWidth={2}
                name="Revenue"
              />
            ) : chartType === 'line' ? (
              <Line
                type="monotone"
                dataKey="revenue"
                stroke={CHART_COLORS.primary}
                strokeWidth={3}
                dot={{ fill: CHART_COLORS.primary, strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: CHART_COLORS.primary, strokeWidth: 2 }}
                name="Revenue"
              />
            ) : (
              <Bar
                dataKey="revenue"
                fill={CHART_COLORS.primary}
                radius={[4, 4, 0, 0]}
                name="Revenue"
              />
            )
          )}
          
          {selectedMetrics.includes('orders') && (
            chartType === 'area' ? (
              <Area
                type="monotone"
                dataKey="orders"
                stroke={CHART_COLORS.secondary}
                fill={CHART_COLORS.secondary}
                fillOpacity={0.1}
                strokeWidth={2}
                name="Orders"
                yAxisId="right"
              />
            ) : chartType === 'line' ? (
              <Line
                type="monotone"
                dataKey="orders"
                stroke={CHART_COLORS.secondary}
                strokeWidth={3}
                dot={{ fill: CHART_COLORS.secondary, strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: CHART_COLORS.secondary, strokeWidth: 2 }}
                name="Orders"
                yAxisId="right"
              />
            ) : (
              <Bar
                dataKey="orders"
                fill={CHART_COLORS.secondary}
                radius={[4, 4, 0, 0]}
                name="Orders"
                yAxisId="right"
              />
            )
          )}

          {selectedMetrics.includes('online') && (
            chartType === 'line' ? (
              <Line
                type="monotone"
                dataKey="onlineRevenue"
                stroke={CHART_COLORS.accent}
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: CHART_COLORS.accent, strokeWidth: 2, r: 3 }}
                name="Online Revenue"
              />
            ) : (
              <Bar
                dataKey="onlineRevenue"
                fill={CHART_COLORS.accent}
                radius={[4, 4, 0, 0]}
                name="Online Revenue"
              />
            )
          )}

          {selectedMetrics.includes('instore') && (
            chartType === 'line' ? (
              <Line
                type="monotone"
                dataKey="instoreRevenue"
                stroke={CHART_COLORS.purple}
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: CHART_COLORS.purple, strokeWidth: 2, r: 3 }}
                name="In-store Revenue"
              />
            ) : (
              <Bar
                dataKey="instoreRevenue"
                fill={CHART_COLORS.purple}
                radius={[4, 4, 0, 0]}
                name="In-store Revenue"
              />
            )
          )}

          {selectedMetrics.includes('orders') && (
            <YAxis 
              yAxisId="right" 
              orientation="right" 
              stroke="#6b7280" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
          )}
        </ChartComponent>
      </ResponsiveContainer>
    );
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
      value: statsData?.revenue?.total_revenue 
        ? `$${statsData.revenue.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
        : '$0.00',
      change: formatChange(statsData?.revenue_change),
      increasing: (statsData?.revenue_change || 0) >= 0,
      icon: <DollarSignIcon size={20} />,
      color: 'bg-blue-500'
    },
    {
      title: 'Total Orders',
      value: statsData?.overview?.total_orders?.toLocaleString() || '0',
      change: formatChange(statsData?.orders_change),
      increasing: (statsData?.orders_change || 0) >= 0,
      icon: <ShoppingCartIcon size={20} />,
      color: 'bg-green-500'
    },
    {
      title: 'Total Customers',
      value: statsData?.overview?.total_users?.toLocaleString() || '0',
      change: formatChange(statsData?.customers_change),
      increasing: (statsData?.customers_change || 0) >= 0,
      icon: <UsersIcon size={20} />,
      color: 'bg-purple-500'
    },
    {
      title: 'Total Products',
      value: statsData?.overview?.total_products?.toLocaleString() || '0',
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
    <div className="p-3 sm:p-6 space-y-4 sm:space-y-6">
      {/* Header with Tabs */}
      <div className="flex flex-col space-y-4 sm:space-y-0 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className={`${themeClasses.text.heading} text-2xl sm:text-3xl font-bold`}>Admin Dashboard</h1>
          <p className={`${themeClasses.text.muted} text-xs sm:text-sm mt-1`}>
            Welcome back! Here's what's happening with your store today.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-2">
          <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1 w-full sm:w-auto">
            <button
              onClick={() => setActiveTab('overview')}
              className={`flex-1 sm:flex-none px-3 sm:px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'overview'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`flex-1 sm:flex-none px-3 sm:px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'analytics'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              Analytics
            </button>
          </div>
          <div className="flex gap-2">
            <button 
              onClick={handleRefresh}
              disabled={isRefreshing}
              className={`${themeClasses.button.outline} flex items-center justify-center px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 flex-1 sm:flex-none`}
            >
              <RefreshCw size={16} className={`${isRefreshing ? 'animate-spin' : ''} sm:mr-2`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
            {activeTab === 'analytics' && (
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`flex items-center justify-center px-3 py-2 text-sm border rounded-lg transition-colors flex-1 sm:flex-none ${
                  showFilters || hasActiveFilters
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
              >
                <FilterIcon size={16} className="sm:mr-2" />
                <span className="hidden sm:inline">Filters</span>
                {hasActiveFilters && (
                  <span className="ml-1 sm:ml-2 bg-white text-blue-600 rounded-full w-4 h-4 sm:w-5 sm:h-5 text-xs flex items-center justify-center font-medium">
                    !
                  </span>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Analytics Filters Panel */}
      {activeTab === 'analytics' && (
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className={`${themeClasses.card.base} p-4 sm:p-6 shadow-sm`}
            >
              <div className="flex items-center justify-between mb-4 sm:mb-6">
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Filters & Settings</h3>
                <div className="flex items-center space-x-2 sm:space-x-3">
                  <button
                    onClick={resetFilters}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    Reset All
                  </button>
                  <button
                    onClick={() => setShowFilters(false)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    <XIcon size={20} />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                {/* Date Range */}
                <div className="space-y-3 sm:space-y-4">
                  <h4 className="font-medium text-gray-900 dark:text-white text-sm sm:text-base">Date Range</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { value: '7d', label: '7 Days' },
                      { value: '30d', label: '30 Days' },
                      { value: '3m', label: '3 Months' },
                      { value: '12m', label: '12 Months' }
                    ].map(({ value, label }) => (
                      <button
                        key={value}
                        onClick={() => {
                          handleFilterChange('dateRange', value);
                          setShowCustomDatePicker(false);
                        }}
                        className={`px-2 sm:px-3 py-2 text-xs sm:text-sm rounded-lg border transition-colors ${
                          salesFilters.dateRange === value
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800'
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  
                  <button
                    onClick={() => {
                      setShowCustomDatePicker(!showCustomDatePicker);
                      handleFilterChange('dateRange', 'custom');
                    }}
                    className={`w-full flex items-center justify-center px-2 sm:px-3 py-2 text-xs sm:text-sm rounded-lg border transition-colors ${
                      salesFilters.dateRange === 'custom'
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}
                  >
                    <CalendarIcon size={14} className="mr-2" />
                    Custom Range
                  </button>

                  {showCustomDatePicker && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                      <div>
                        <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Start Date</label>
                        <input
                          type="date"
                          value={salesFilters.startDate}
                          onChange={(e) => handleFilterChange('startDate', e.target.value)}
                          className="w-full px-2 sm:px-3 py-2 text-xs sm:text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">End Date</label>
                        <input
                          type="date"
                          value={salesFilters.endDate}
                          onChange={(e) => handleFilterChange('endDate', e.target.value)}
                          className="w-full px-2 sm:px-3 py-2 text-xs sm:text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Categories */}
                <div className="space-y-3 sm:space-y-4">
                  <h4 className="font-medium text-gray-900 dark:text-white text-sm sm:text-base">Product Categories</h4>
                  <div className="space-y-2 max-h-32 sm:max-h-40 overflow-y-auto">
                    {availableCategories.map((category) => (
                      <label key={category.id} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={salesFilters.categories.includes(category.id)}
                          onChange={() => handleCategoryToggle(category.id)}
                          className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-xs sm:text-sm text-gray-700 dark:text-gray-300">{category.name}</span>
                      </label>
                    ))}
                  </div>

                  <div className="pt-3 sm:pt-4 border-t border-gray-200 dark:border-gray-700">
                    <h4 className="font-medium text-gray-900 dark:text-white mb-2 sm:mb-3 text-sm sm:text-base">Sales Channels</h4>
                    <div className="space-y-2">
                      {[
                        { value: 'online', label: 'Online Store' },
                        { value: 'instore', label: 'Physical Store' }
                      ].map(({ value, label }) => (
                        <label key={value} className="flex items-center">
                          <input
                            type="checkbox"
                            checked={salesFilters.salesChannels.includes(value)}
                            onChange={() => handleSalesChannelToggle(value)}
                            className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="ml-2 text-xs sm:text-sm text-gray-700 dark:text-gray-300">{label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Regions & Settings */}
                <div className="space-y-3 sm:space-y-4">
                  <h4 className="font-medium text-gray-900 dark:text-white text-sm sm:text-base">Regions</h4>
                  <div className="space-y-2 max-h-32 sm:max-h-40 overflow-y-auto">
                    {availableRegions.map((region) => (
                      <label key={region.id} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={salesFilters.regions.includes(region.id)}
                          onChange={() => handleRegionToggle(region.id)}
                          className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-xs sm:text-sm text-gray-700 dark:text-gray-300">{region.name}</span>
                      </label>
                    ))}
                  </div>

                  <div className="pt-3 sm:pt-4 border-t border-gray-200 dark:border-gray-700">
                    <h4 className="font-medium text-gray-900 dark:text-white mb-2 sm:mb-3 text-sm sm:text-base">Data Granularity</h4>
                    <select
                      value={salesFilters.granularity}
                      onChange={(e) => handleFilterChange('granularity', e.target.value)}
                      className="w-full px-2 sm:px-3 py-2 text-xs sm:text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                    >
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                    </select>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
        {activeTab === 'overview' ? (
          // Overview stats
          stats.map((stat, index) => (
            <StatCard key={index} {...stat} loading={statsLoading} />
          ))
        ) : (
          // Analytics metrics
          salesData?.metrics ? [
            {
              title: 'Total Revenue',
              value: formatCurrency(salesData.metrics.totalRevenue),
              change: salesData.metrics.revenueGrowth,
              icon: <DollarSignIcon size={20} />,
              color: 'bg-blue-500'
            },
            {
              title: 'Total Orders',
              value: formatNumber(salesData.metrics.totalOrders),
              change: salesData.metrics.ordersGrowth,
              icon: <ShoppingCartIcon size={20} />,
              color: 'bg-green-500'
            },
            {
              title: 'Average Order Value',
              value: formatCurrency(salesData.metrics.averageOrderValue),
              change: 5.2,
              icon: <TrendingUpIcon size={20} />,
              color: 'bg-purple-500'
            },
            {
              title: 'Conversion Rate',
              value: `${salesData.metrics.conversionRate.toFixed(2)}%`,
              change: -1.3,
              icon: <UsersIcon size={20} />,
              color: 'bg-orange-500'
            }
          ].map((metric, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`${themeClasses.card.base} p-4 sm:p-6 shadow-sm hover:shadow-md transition-shadow`}
            >
              <div className="flex items-center justify-between mb-3 sm:mb-4">
                <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl ${metric.color} text-white flex items-center justify-center`}>
                  {metric.icon}
                </div>
                <div className={`flex items-center text-xs sm:text-sm font-medium ${
                  metric.change >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  <TrendingUpIcon 
                    size={14} 
                    className={`mr-1 ${metric.change < 0 ? 'rotate-180' : ''}`} 
                  />
                  <span className="hidden xs:inline">{Math.abs(metric.change).toFixed(1)}%</span>
                  <span className="xs:hidden">{Math.abs(metric.change).toFixed(0)}</span>
                </div>
              </div>
              <h3 className={`${themeClasses.text.muted} text-xs sm:text-sm mb-1`}>{metric.title}</h3>
              <p className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white truncate">{metric.value}</p>
            </motion.div>
          )) : (
            // Loading state for analytics
            [...Array(4)].map((_, index) => (
              <StatCard key={index} title="" value="" icon={<div />} color="" loading={true} />
            ))
          )
        )}
      </div>

      {activeTab === 'overview' ? (
        /* Overview Content */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Recent Orders */}
          <div className={`${themeClasses.card.base} lg:col-span-2 p-4 sm:p-6`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className={`${themeClasses.text.heading} text-base sm:text-lg font-semibold`}>Recent Orders</h2>
              <Link to="/admin/orders" className="text-primary hover:underline text-xs sm:text-sm font-medium">
                View All →
              </Link>
            </div>
            
            {ordersLoading ? (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="animate-pulse flex items-center gap-2 sm:gap-4">
                    <div className="h-3 sm:h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 sm:w-20"></div>
                    <div className="h-3 sm:h-4 bg-gray-200 dark:bg-gray-700 rounded w-20 sm:w-32"></div>
                    <div className="h-3 sm:h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 sm:w-24 hidden sm:block"></div>
                    <div className="h-5 sm:h-6 bg-gray-200 dark:bg-gray-700 rounded-full w-12 sm:w-20"></div>
                    <div className="h-3 sm:h-4 bg-gray-200 dark:bg-gray-700 rounded w-12 sm:w-16 ml-auto"></div>
                  </div>
                ))}
              </div>
            ) : recentOrders.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className={`${themeClasses.text.muted} text-left border-b dark:border-gray-700 text-xs uppercase`}>
                      <th className="pb-2 sm:pb-3 px-1 sm:px-2 font-semibold">Order ID</th>
                      <th className="pb-2 sm:pb-3 px-1 sm:px-2 font-semibold">Customer</th>
                      <th className="pb-2 sm:pb-3 px-1 sm:px-2 font-semibold hidden sm:table-cell">Date</th>
                      <th className="pb-2 sm:pb-3 px-1 sm:px-2 font-semibold">Status</th>
                      <th className="pb-2 sm:pb-3 px-1 sm:px-2 font-semibold text-right">Total</th>
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
              <div className="text-center py-8 sm:py-12">
                <ShoppingCartIcon size={40} className="mx-auto text-gray-300 dark:text-gray-600 mb-3 sm:mb-3" />
                <p className={`${themeClasses.text.muted} text-xs sm:text-sm`}>No orders yet</p>
              </div>
            )}
          </div>

          {/* Top Products */}
          <div className={`${themeClasses.card.base} p-4 sm:p-6`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className={`${themeClasses.text.heading} text-base sm:text-lg font-semibold`}>Top Products</h2>
              <Link to="/admin/products" className="text-primary hover:underline text-xs sm:text-sm font-medium">
                View All →
              </Link>
            </div>
            
            {overviewLoading ? (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="animate-pulse flex items-center gap-2 sm:gap-3">
                    <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gray-200 dark:bg-gray-700 rounded-md"></div>
                    <div className="flex-grow">
                      <div className="h-3 sm:h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 sm:w-32 mb-2"></div>
                      <div className="h-2 sm:h-3 bg-gray-200 dark:bg-gray-700 rounded w-12 sm:w-16"></div>
                    </div>
                    <div className="h-3 sm:h-4 bg-gray-200 dark:bg-gray-700 rounded w-12 sm:w-16"></div>
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
              <div className="text-center py-8 sm:py-12">
                <PackageIcon size={40} className="mx-auto text-gray-300 dark:text-gray-600 mb-3" />
                <p className={`${themeClasses.text.muted} text-xs sm:text-sm`}>No products yet</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Analytics Content */
        <div className={`${themeClasses.card.base} shadow-sm`}>
          <div className="p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex flex-col space-y-4 lg:flex-row lg:items-center lg:justify-between lg:space-y-0">
              <div>
                <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white mb-1">Sales Performance</h2>
                <p className="text-gray-600 dark:text-gray-300 text-xs sm:text-sm">
                  Revenue and order trends over time
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-3 sm:space-y-0 sm:space-x-3">
                {/* Chart Type Selector */}
                <div className="flex items-center bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-1">
                  {[
                    { type: 'line' as const, icon: LineChartIcon },
                    { type: 'bar' as const, icon: BarChart3Icon },
                    { type: 'area' as const, icon: TrendingUpIcon }
                  ].map(({ type, icon: Icon }) => (
                    <button
                      key={type}
                      onClick={() => setChartType(type)}
                      className={`flex-1 sm:flex-none p-2 rounded-md transition-colors ${
                        chartType === type
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700'
                      }`}
                    >
                      <Icon size={16} />
                    </button>
                  ))}
                </div>

                {/* Metrics Selector */}
                <div className="grid grid-cols-2 sm:flex sm:items-center gap-2 sm:space-x-2">
                  {[
                    { key: 'revenue', label: 'Revenue', color: CHART_COLORS.primary },
                    { key: 'orders', label: 'Orders', color: CHART_COLORS.secondary },
                    { key: 'online', label: 'Online', color: CHART_COLORS.accent },
                    { key: 'instore', label: 'In-store', color: CHART_COLORS.purple }
                  ].map(({ key, label, color }) => (
                    <button
                      key={key}
                      onClick={() => handleMetricToggle(key)}
                      className={`flex items-center justify-center px-2 sm:px-3 py-1.5 text-xs sm:text-sm rounded-lg border transition-colors ${
                        selectedMetrics.includes(key)
                          ? 'border-transparent text-white'
                          : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-800'
                      }`}
                      style={{
                        backgroundColor: selectedMetrics.includes(key) ? color : 'transparent'
                      }}
                    >
                      <div 
                        className="w-2 h-2 rounded-full mr-1 sm:mr-2" 
                        style={{ backgroundColor: color }}
                      />
                      <span className="hidden sm:inline">{label}</span>
                      <span className="sm:hidden">{label.charAt(0)}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="p-4 sm:p-6">
            <div className="h-64 sm:h-80 lg:h-96">
              {salesLoading ? (
                <div className="h-full flex items-center justify-center">
                  <div className="flex flex-col items-center space-y-2">
                    <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-gray-600 dark:text-gray-300 text-xs sm:text-sm">Loading chart data...</span>
                  </div>
                </div>
              ) : (
                renderChart()
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
