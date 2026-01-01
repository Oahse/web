// frontend/src/components/admin/sales/SalesOverview.tsx

import React, { useState } from 'react';
import { 
  TrendingUpIcon, 
  DollarSignIcon, 
  ShoppingCartIcon, 
  UsersIcon,
  CalendarIcon,
  FilterIcon,
  XIcon,
  BarChart3Icon,
  LineChartIcon,
  RefreshCwIcon
} from 'lucide-react';
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
import { SalesOverviewProps, SalesFilters } from './types';
import { CHART_COLORS, formatCurrency, formatNumber } from './utils';
import { SkeletonDashboard } from '../../ui/SkeletonDashboard';

export const SalesOverview: React.FC<SalesOverviewProps> = ({
  salesData,
  loading,
  onFiltersChange,
  onRefresh,
  availableCategories,
  availableRegions,
  title = "Sales Overview",
  subtitle = "Track your revenue performance and sales metrics"
}) => {
  const [filters, setFilters] = useState<SalesFilters>({
    dateRange: '30d',
    startDate: '',
    endDate: '',
    categories: [],
    regions: [],
    salesChannels: ['online', 'instore'],
    granularity: 'daily'
  });

  const [chartType, setChartType] = useState<'line' | 'bar' | 'area'>('line');
  const [showFilters, setShowFilters] = useState(false);
  const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['revenue', 'orders']);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await onRefresh();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const handleFilterChange = (key: keyof SalesFilters, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };
  
  const handleCategoryToggle = (categoryId: string) => {
    const newCategories = filters.categories.includes(categoryId)
      ? filters.categories.filter(id => id !== categoryId)
      : [...filters.categories, categoryId];
    handleFilterChange('categories', newCategories);
  };

  const handleRegionToggle = (regionId: string) => {
    const newRegions = filters.regions.includes(regionId)
      ? filters.regions.filter(id => id !== regionId)
      : [...filters.regions, regionId];
    handleFilterChange('regions', newRegions);
  };

  const handleSalesChannelToggle = (channel: string) => {
    const newSalesChannels = filters.salesChannels.includes(channel)
      ? filters.salesChannels.filter(c => c !== channel)
      : [...filters.salesChannels, channel];
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
    setFilters(defaultFilters);
    onFiltersChange(defaultFilters);
    setShowCustomDatePicker(false);
  };

  const hasActiveFilters = filters.categories.length > 0 || 
                          filters.regions.length > 0 || 
                          filters.salesChannels.length !== 2 ||
                          filters.dateRange === 'custom';

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-surface-elevated border border-border rounded-lg shadow-lg p-4 min-w-[200px]">
          <p className="text-sm font-medium text-main mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between mb-1">
              <div className="flex items-center">
                <div 
                  className="w-3 h-3 rounded-full mr-2" 
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-copy-light">{entry.name}:</span>
              </div>
              <span className="text-sm font-medium text-main ml-2">
                {entry.name === 'Revenue' || entry.name.includes('Revenue') 
                  ? formatCurrency(entry.value)
                  : formatNumber(entry.value)
                }
              </span>
            </div>
          ))}
          {payload[0]?.payload && (
            <div className="border-t border-border pt-2 mt-2">
              <div className="flex items-center justify-between text-xs text-copy-lighter">
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

  const renderChart = () => {
    if (!salesData?.data || salesData.data.length === 0) {
      return (
        <div className="h-full flex items-center justify-center">
          <div className="text-center">
            <BarChart3Icon size={48} className="mx-auto text-copy-lighter mb-4" />
            <p className="text-copy-light text-lg mb-2">No sales data available</p>
            <p className="text-copy-lighter text-sm">
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
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.3} />
          <XAxis 
            dataKey="date" 
            stroke="var(--color-copy-lighter)" 
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis 
            stroke="var(--color-copy-lighter)" 
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
              stroke="var(--color-copy-lighter)" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
          )}
        </ChartComponent>
      </ResponsiveContainer>
    );
  };

  if (loading && !salesData) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-main mb-2">{title}</h1>
          <p className="text-copy-lighter">{subtitle}</p>
        </div>
        <SkeletonDashboard />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-main mb-2">{title}</h1>
          <p className="text-copy-lighter">{subtitle}</p>
        </div>
        
        <div className="flex items-center space-x-3 mt-4 lg:mt-0">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center px-3 py-2 text-sm border border-border rounded-lg hover:bg-surface-hover transition-colors disabled:opacity-50"
          >
            <RefreshCwIcon 
              size={16} 
              className={`mr-2 ${isRefreshing ? 'animate-spin' : ''}`} 
            />
            Refresh
          </button>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center px-3 py-2 text-sm border rounded-lg transition-colors ${
              showFilters || hasActiveFilters
                ? 'bg-primary text-white border-primary'
                : 'border-border hover:bg-surface-hover'
            }`}
          >
            <FilterIcon size={16} className="mr-2" />
            Filters
            {hasActiveFilters && (
              <span className="ml-2 bg-white text-primary rounded-full w-5 h-5 text-xs flex items-center justify-center font-medium">
                !
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-surface border border-border rounded-xl p-6 shadow-sm"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-main">Filters & Settings</h3>
              <div className="flex items-center space-x-3">
                <button
                  onClick={resetFilters}
                  className="text-sm text-primary hover:underline"
                >
                  Reset All
                </button>
                <button
                  onClick={() => setShowFilters(false)}
                  className="text-copy-lighter hover:text-main"
                >
                  <XIcon size={20} />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Date Range */}
              <div className="space-y-4">
                <h4 className="font-medium text-main">Date Range</h4>
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
                      className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                        filters.dateRange === value
                          ? 'bg-primary text-white border-primary'
                          : 'border-border hover:bg-surface-hover'
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
                  className={`w-full flex items-center justify-center px-3 py-2 text-sm rounded-lg border transition-colors ${
                    filters.dateRange === 'custom'
                      ? 'bg-primary text-white border-primary'
                      : 'border-border hover:bg-surface-hover'
                  }`}
                >
                  <CalendarIcon size={16} className="mr-2" />
                  Custom Range
                </button>

                {showCustomDatePicker && (
                  <div className="grid grid-cols-2 gap-3 pt-3 border-t border-border">
                    <div>
                      <label className="block text-xs text-copy-lighter mb-1">Start Date</label>
                      <input
                        type="date"
                        value={filters.startDate}
                        onChange={(e) => handleFilterChange('startDate', e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-border rounded-lg bg-background"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-copy-lighter mb-1">End Date</label>
                      <input
                        type="date"
                        value={filters.endDate}
                        onChange={(e) => handleFilterChange('endDate', e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-border rounded-lg bg-background"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Categories */}
              <div className="space-y-4">
                <h4 className="font-medium text-main">Product Categories</h4>
                <div className="space-y-2">
                  {availableCategories.map((category) => (
                    <label key={category.id} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.categories.includes(category.id)}
                        onChange={() => handleCategoryToggle(category.id)}
                        className="rounded border-border text-primary focus:ring-primary"
                      />
                      <span className="ml-2 text-sm text-copy">{category.name}</span>
                    </label>
                  ))}
                </div>

                <div className="pt-4 border-t border-border">
                  <h4 className="font-medium text-main mb-3">Sales Channels</h4>
                  <div className="space-y-2">
                    {[
                      { value: 'online', label: 'Online Store' },
                      { value: 'instore', label: 'Physical Store' }
                    ].map(({ value, label }) => (
                      <label key={value} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={filters.salesChannels.includes(value)}
                          onChange={() => handleSalesChannelToggle(value)}
                          className="rounded border-border text-primary focus:ring-primary"
                        />
                        <span className="ml-2 text-sm text-copy">{label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {/* Regions & Settings */}
              <div className="space-y-4">
                <h4 className="font-medium text-main">Regions</h4>
                <div className="space-y-2">
                  {availableRegions.map((region) => (
                    <label key={region.id} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.regions.includes(region.id)}
                        onChange={() => handleRegionToggle(region.id)}
                        className="rounded border-border text-primary focus:ring-primary"
                      />
                      <span className="ml-2 text-sm text-copy">{region.name}</span>
                    </label>
                  ))}
                </div>

                <div className="pt-4 border-t border-border">
                  <h4 className="font-medium text-main mb-3">Data Granularity</h4>
                  <select
                    value={filters.granularity}
                    onChange={(e) => handleFilterChange('granularity', e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-border rounded-lg bg-background"
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

      {/* Metrics Cards */}
      {salesData?.metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              title: 'Total Revenue',
              value: formatCurrency(salesData.metrics.totalRevenue),
              change: salesData.metrics.revenueGrowth,
              icon: <DollarSignIcon size={24} />,
              color: 'bg-blue-500'
            },
            {
              title: 'Total Orders',
              value: formatNumber(salesData.metrics.totalOrders),
              change: salesData.metrics.ordersGrowth,
              icon: <ShoppingCartIcon size={24} />,
              color: 'bg-green-500'
            },
            {
              title: 'Average Order Value',
              value: formatCurrency(salesData.metrics.averageOrderValue),
              change: 5.2,
              icon: <TrendingUpIcon size={24} />,
              color: 'bg-purple-500'
            },
            {
              title: 'Conversion Rate',
              value: `${salesData.metrics.conversionRate.toFixed(2)}%`,
              change: -1.3,
              icon: <UsersIcon size={24} />,
              color: 'bg-orange-500'
            }
          ].map((metric, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-surface border border-border rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`w-12 h-12 rounded-xl ${metric.color} text-white flex items-center justify-center`}>
                  {metric.icon}
                </div>
                <div className={`flex items-center text-sm font-medium ${
                  metric.change >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  <TrendingUpIcon 
                    size={16} 
                    className={`mr-1 ${metric.change < 0 ? 'rotate-180' : ''}`} 
                  />
                  {Math.abs(metric.change).toFixed(1)}%
                </div>
              </div>
              <h3 className="text-copy-lighter text-sm mb-1">{metric.title}</h3>
              <p className="text-2xl font-bold text-main">{metric.value}</p>
            </motion.div>
          ))}
        </div>
      )}

      {/* Main Chart */}
      <div className="bg-surface border border-border rounded-xl shadow-sm">
        <div className="p-6 border-b border-border">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-main mb-1">Sales Performance</h2>
              <p className="text-copy-lighter text-sm">
                Revenue and order trends over time
              </p>
            </div>
            
            <div className="flex items-center space-x-3 mt-4 lg:mt-0">
              {/* Chart Type Selector */}
              <div className="flex items-center bg-background border border-border rounded-lg p-1">
                {[
                  { type: 'line' as const, icon: LineChartIcon },
                  { type: 'bar' as const, icon: BarChart3Icon },
                  { type: 'area' as const, icon: TrendingUpIcon }
                ].map(({ type, icon: Icon }) => (
                  <button
                    key={type}
                    onClick={() => setChartType(type)}
                    className={`p-2 rounded-md transition-colors ${
                      chartType === type
                        ? 'bg-primary text-white'
                        : 'text-copy-lighter hover:text-main hover:bg-surface-hover'
                    }`}
                  >
                    <Icon size={16} />
                  </button>
                ))}
.              </div>

              {/* Metrics Selector */}
              <div className="flex items-center space-x-2">
                {[
                  { key: 'revenue', label: 'Revenue', color: CHART_COLORS.primary },
                  { key: 'orders', label: 'Orders', color: CHART_COLORS.secondary },
                  { key: 'online', label: 'Online', color: CHART_COLORS.accent },
                  { key: 'instore', label: 'In-store', color: CHART_COLORS.purple }
                ].map(({ key, label, color }) => (
                  <button
                    key={key}
                    onClick={() => handleMetricToggle(key)}
                    className={`flex items-center px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                      selectedMetrics.includes(key)
                        ? 'border-transparent text-white'
                        : 'border-border text-copy-lighter hover:text-main hover:bg-surface-hover'
                    }`}
                    style={{
                      backgroundColor: selectedMetrics.includes(key) ? color : 'transparent'
                    }}
                  >
                    <div 
                      className="w-2 h-2 rounded-full mr-2" 
                      style={{ backgroundColor: color }}
                    />
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="h-96">
            {loading ? (
              <div className="h-full flex items-center justify-center">
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-copy-lighter">Loading chart data...</span>
                </div>
              </div>
            ) : (
              renderChart()
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
