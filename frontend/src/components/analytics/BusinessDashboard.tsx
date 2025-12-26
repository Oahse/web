/**
 * Business Analytics Dashboard
 * Comprehensive dashboard showing key e-commerce metrics
 */
import React, { useState, useEffect } from 'react';
import { AnalyticsAPI } from '../../apis/analytics';
import { toast } from 'react-hot-toast';
import { 
  ChartBarIcon, 
  ShoppingCartIcon, 
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
  UserGroupIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface KPI {
  label: string;
  value: number | string;
  change?: number;
  format: 'percentage' | 'currency' | 'number' | 'days';
  icon: React.ComponentType<any>;
  color: string;
}

export const BusinessDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [dateRange, setDateRange] = useState('30'); // days
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, [dateRange]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [dashboardResponse, kpisResponse] = await Promise.all([
        AnalyticsAPI.getDashboardData({ days: parseInt(dateRange) }),
        AnalyticsAPI.getKPIs({ days: parseInt(dateRange), compare_previous: true })
      ]);

      if (dashboardResponse.success) {
        setDashboardData(dashboardResponse.data);
      }

      if (kpisResponse.success) {
        setKpis(kpisResponse.data);
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setError('Failed to load dashboard data');
      toast.error('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value: number, format: string): string => {
    switch (format) {
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'currency':
        return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
      case 'number':
        return value.toLocaleString();
      case 'days':
        return `${value.toFixed(1)} days`;
      default:
        return value.toString();
    }
  };

  const getChangeColor = (change: number): string => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) return <ArrowTrendingUpIcon className="w-4 h-4" />;
    if (change < 0) return <ArrowTrendingDownIcon className="w-4 h-4" />;
    return null;
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/3"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
          <ExclamationTriangleIcon className="w-5 h-5 text-red-600 mr-3" />
          <div>
            <h3 className="text-red-800 font-medium">Error Loading Dashboard</h3>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  const kpiData: KPI[] = kpis ? [
    {
      label: 'Conversion Rate',
      value: kpis.kpis.conversion_rate,
      change: kpis.comparison?.changes?.conversion_rate,
      format: 'percentage',
      icon: ChartBarIcon,
      color: 'bg-blue-500'
    },
    {
      label: 'Cart Abandonment',
      value: kpis.kpis.cart_abandonment_rate,
      change: kpis.comparison?.changes?.cart_abandonment_rate,
      format: 'percentage',
      icon: ShoppingCartIcon,
      color: 'bg-orange-500'
    },
    {
      label: 'Average Order Value',
      value: kpis.kpis.average_order_value,
      change: kpis.comparison?.changes?.average_order_value,
      format: 'currency',
      icon: CurrencyDollarIcon,
      color: 'bg-green-500'
    },
    {
      label: 'Total Revenue',
      value: kpis.kpis.total_revenue,
      change: kpis.comparison?.changes?.total_revenue,
      format: 'currency',
      icon: CurrencyDollarIcon,
      color: 'bg-purple-500'
    },
    {
      label: 'Refund Rate',
      value: kpis.kpis.refund_rate,
      change: kpis.comparison?.changes?.refund_rate,
      format: 'percentage',
      icon: ExclamationTriangleIcon,
      color: 'bg-red-500'
    },
    {
      label: 'Repeat Customer Rate',
      value: kpis.kpis.repeat_customer_rate,
      change: kpis.comparison?.changes?.repeat_customer_rate,
      format: 'percentage',
      icon: UserGroupIcon,
      color: 'bg-indigo-500'
    },
    {
      label: 'Time to First Purchase',
      value: kpis.kpis.avg_time_to_first_purchase_days,
      format: 'days',
      icon: ClockIcon,
      color: 'bg-yellow-500'
    },
    {
      label: 'Total Orders',
      value: kpis.kpis.total_orders,
      format: 'number',
      icon: ShoppingCartIcon,
      color: 'bg-teal-500'
    }
  ] : [];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Business Analytics</h1>
          <p className="text-gray-600">Key performance indicators and metrics</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="365">Last year</option>
          </select>
          
          <button
            onClick={loadDashboardData}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiData.map((kpi, index) => (
          <div key={index} className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-2 rounded-lg ${kpi.color}`}>
                <kpi.icon className="w-6 h-6 text-white" />
              </div>
              {kpi.change !== undefined && (
                <div className={`flex items-center space-x-1 ${getChangeColor(kpi.change)}`}>
                  {getChangeIcon(kpi.change)}
                  <span className="text-sm font-medium">
                    {kpi.change > 0 ? '+' : ''}{kpi.change.toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
            
            <div>
              <div className="text-2xl font-bold text-gray-900 mb-1">
                {formatValue(Number(kpi.value), kpi.format)}
              </div>
              <div className="text-sm text-gray-600">{kpi.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Detailed Metrics */}
      {dashboardData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Conversion Funnel */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4">Conversion Funnel</h3>
            <div className="space-y-3">
              {dashboardData.cart_abandonment.conversion_funnel.map((step, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{step.step_name}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{
                          width: `${(step.count / Math.max(...dashboardData.cart_abandonment.conversion_funnel.map(s => s.count))) * 100}%`
                        }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium w-12 text-right">
                      {step.count.toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Traffic Sources */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4">Conversion by Traffic Source</h3>
            <div className="space-y-3">
              {dashboardData.conversion.by_traffic_source.map((source, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">
                    {source.traffic_source.replace('_', ' ')}
                  </span>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-900">
                      {source.conversion_rate}%
                    </span>
                    <span className="text-sm text-gray-600">
                      ({source.converted_sessions}/{source.total_sessions})
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Refund Reasons */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4">Refund Reasons</h3>
            <div className="space-y-3">
              {dashboardData.refunds.by_reason.slice(0, 5).map((reason, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">
                    {reason.reason.replace('_', ' ')}
                  </span>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-900">
                      {reason.percentage}%
                    </span>
                    <span className="text-sm text-gray-600">
                      ({reason.count})
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Customer Segments */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4">Customer Segments</h3>
            <div className="space-y-3">
              {dashboardData.repeat_customers.by_segment.map((segment, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">
                    {segment.segment.replace('_', ' ')}
                  </span>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-900">
                      {segment.count.toLocaleString()}
                    </span>
                    <span className="text-sm text-gray-600">
                      ${segment.average_ltv.toFixed(0)} LTV
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Time to Purchase Distribution */}
      {dashboardData?.time_to_purchase?.distribution && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold mb-4">Time to First Purchase Distribution</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {dashboardData.time_to_purchase.distribution.map((bucket, index) => (
              <div key={index} className="text-center">
                <div className="text-2xl font-bold text-gray-900 mb-1">
                  {bucket.count}
                </div>
                <div className="text-sm text-gray-600">{bucket.range}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BusinessDashboard;