import React, { useState, useEffect } from 'react';
import { 
  DollarSignIcon, 
  ShoppingCartIcon, 
  UsersIcon, 
  PackageIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  RefreshCwIcon
} from 'lucide-react';
import { useApi } from '../../hooks/useAsync';
import { AdminAPI } from '../../apis';
import { themeClasses } from '../../utils/themeClasses';
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

import { CHART_COLORS } from './sales/utils';

const COLORS = [
  CHART_COLORS.primary,
  CHART_COLORS.secondary, 
  CHART_COLORS.accent,
  CHART_COLORS.danger,
  CHART_COLORS.purple
];

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
    if (change === undefined || change === null) return undefined;
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
      <div className={`${themeClasses.card.base} p-4 sm:p-6`}>
        <div className="text-center">
          <div className={`${themeClasses.text.muted} mb-2 text-red-500`}>Failed to load sales data</div>
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
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      {!compact && (
        <div className="flex flex-col space-y-4 sm:space-y-0 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className={`${themeClasses.text.heading} text-xl sm:text-2xl font-bold`}>Sales Overview</h2>
            <p className={`${themeClasses.text.muted} text-sm mt-1`}>
              Track your sales performance and key metrics
            </p>
          </div>
          <div className="flex flex-col space-y-3 sm:space-y-0 sm:flex-row sm:items-center sm:space-x-3">
            {showFilters && (
              <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1 overflow-x-auto">
                {['7d', '30d', '3m', '12m'].map((range) => (
                  <button
                    key={range}
                    onClick={() => handleTimeRangeChange(range)}
                    className={`px-3 py-1.5 text-sm rounded-md transition-colors whitespace-nowrap ${
                      selectedTimeRange === range
                        ? `${themeClasses.card.base} ${themeClasses.text.heading} shadow-sm`
                        : `${themeClasses.text.muted} hover:${themeClasses.text.heading}`
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
              className={`${themeClasses.button.outline} flex items-center justify-center px-3 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50`}
            >
              <RefreshCwIcon size={16} className={`mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          </div>
        </div>
      )}

      {/* Metrics Cards - Responsive Grid */}
      <div className={`grid gap-3 sm:gap-4 ${
        compact 
          ? 'grid-cols-1 xs:grid-cols-2 sm:grid-cols-2 md:grid-cols-4' 
          : 'grid-cols-1 xs:grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4'
      }`}>
        {salesMetrics.map((metric, index) => (
          <div key={index} className={`${themeClasses.card.base} p-4 sm:p-6 hover:shadow-lg transition-shadow`}>
            <div className="flex items-center justify-between mb-3 sm:mb-4">
              <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg ${metric.color} text-white flex items-center justify-center flex-shrink-0`}>
                {React.cloneElement(metric.icon as React.ReactElement, { size: typeof window !== 'undefined' && window.innerWidth < 640 ? 16 : 20 })}
              </div>
              {metric.change && (
                <div className={`flex items-center text-xs sm:text-sm font-medium ${
                  metric.changeType === 'increase' 
                    ? 'text-green-600 dark:text-green-400' 
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {metric.changeType === 'increase' ? (
                    <ArrowUpIcon size={14} className="mr-1" />
                  ) : (
                    <ArrowDownIcon size={14} className="mr-1" />
                  )}
                  {metric.change}
                </div>
              )}
            </div>
            <h3 className={`${themeClasses.text.muted} text-xs sm:text-sm mb-1`}>{metric.title}</h3>
            <div className={`${themeClasses.text.heading} text-lg sm:text-2xl font-bold mb-2 sm:mb-3`}>{metric.value}</div>
            
            {/* Mini trend chart - Hidden on mobile for space */}
            {metric.trend && !compact && (
              <div className="h-6 sm:h-8 hidden sm:block">
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Revenue Trend Chart */}
          <div className={`${themeClasses.card.base} lg:col-span-2 p-4 sm:p-6`}>
            <h3 className={`${themeClasses.text.heading} text-base sm:text-lg font-semibold mb-4`}>Revenue Trend</h3>
            <div className="h-48 sm:h-64">
              {salesLoading ? (
                <div className="h-full flex items-center justify-center">
                  <div className={`${themeClasses.loading.spinner} w-6 h-6 sm:w-8 sm:h-8`}></div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis 
                      dataKey="date" 
                      stroke="var(--color-copy-lighter)" 
                      fontSize={window.innerWidth < 640 ? 10 : 12}
                      tick={{ fontSize: window.innerWidth < 640 ? 10 : 12 }}
                    />
                    <YAxis 
                      stroke="var(--color-copy-lighter)" 
                      fontSize={window.innerWidth < 640 ? 10 : 12}
                      tick={{ fontSize: window.innerWidth < 640 ? 10 : 12 }}
                      tickFormatter={(value) => window.innerWidth < 640 ? `$${value/1000}k` : formatCurrency(value)}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'var(--color-surface-elevated)',
                        borderColor: 'var(--color-border)',
                        color: 'var(--color-copy)',
                        fontSize: window.innerWidth < 640 ? '12px' : '14px',
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
          <div className={`${themeClasses.card.base} p-4 sm:p-6`}>
            <h3 className={`${themeClasses.text.heading} text-base sm:text-lg font-semibold mb-4`}>Sales by Category</h3>
            <div className="h-48 sm:h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={window.innerWidth < 640 ? 30 : 40}
                    outerRadius={window.innerWidth < 640 ? 60 : 80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: any) => [`${value}%`, 'Share']}
                    contentStyle={{
                      fontSize: window.innerWidth < 640 ? '12px' : '14px',
                      backgroundColor: 'var(--color-surface-elevated)',
                      borderColor: 'var(--color-border)',
                      color: 'var(--color-copy)',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 space-y-2">
              {categoryData.map((category, index) => (
                <div key={index} className="flex items-center justify-between text-xs sm:text-sm">
                  <div className="flex items-center min-w-0 flex-1">
                    <div 
                      className="w-2 h-2 sm:w-3 sm:h-3 rounded-full mr-2 flex-shrink-0" 
                      style={{ backgroundColor: category.color }}
                    ></div>
                    <span className={`${themeClasses.text.heading} truncate`}>{category.name}</span>
                  </div>
                  <span className={`${themeClasses.text.muted} font-medium ml-2`}>{category.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Quick Stats - Mobile Optimized */}
      {compact && (
        <div className={`${themeClasses.card.base} p-3 sm:p-4`}>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 text-center">
            <div>
              <div className={`${themeClasses.text.muted} text-xs uppercase tracking-wide mb-1`}>Avg Order</div>
              <div className="text-sm sm:text-lg font-semibold">{formatCurrency(285)}</div>
            </div>
            <div>
              <div className={`${themeClasses.text.muted} text-xs uppercase tracking-wide mb-1`}>Conversion</div>
              <div className="text-sm sm:text-lg font-semibold">3.2%</div>
            </div>
            <div>
              <div className={`${themeClasses.text.muted} text-xs uppercase tracking-wide mb-1`}>Return Rate</div>
              <div className="text-sm sm:text-lg font-semibold">2.1%</div>
            </div>
            <div>
              <div className={`${themeClasses.text.muted} text-xs uppercase tracking-wide mb-1`}>Growth</div>
              <div className={`text-sm sm:text-lg font-semibold text-green-600 dark:text-green-400`}>+12.5%</div>
            </div>
          </div>
        </div>
      )}

      {/* Mobile-specific Revenue Performance Summary */}
      {!compact && (
        <div className="block sm:hidden">
          <div className={`${themeClasses.card.base} p-4`}>
            <h3 className={`${themeClasses.text.heading} text-base font-semibold mb-3`}>Performance Summary</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className={`${themeClasses.text.muted} text-sm`}>This Week</span>
                <span className={`${themeClasses.text.heading} font-semibold`}>{formatCurrency(24000)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className={`${themeClasses.text.muted} text-sm`}>Last Week</span>
                <span className={`${themeClasses.text.muted} text-sm`}>{formatCurrency(18000)}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-gray-200 dark:border-gray-700">
                <span className={`${themeClasses.text.muted} text-sm`}>Growth</span>
                <span className={`text-green-600 dark:text-green-400 font-semibold flex items-center`}>
                  <ArrowUpIcon size={14} className="mr-1" />
                  +33.3%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SalesOverview;