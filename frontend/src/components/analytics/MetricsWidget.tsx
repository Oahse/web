/**
 * Metrics Widget Component
 * Displays individual business metrics with trends and comparisons
 */
import React, { useState, useEffect } from 'react';
import { AnalyticsAPI } from '../../apis/analytics';
import { 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

interface MetricsWidgetProps {
  metric: 'conversion' | 'abandonment' | 'refunds' | 'repeat' | 'time-to-purchase';
  title: string;
  description?: string;
  days?: number;
  showComparison?: boolean;
}

export const MetricsWidget: React.FC<MetricsWidgetProps> = ({
  metric,
  title,
  description,
  days = 30,
  showComparison = true
}) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadMetricData();
  }, [metric, days]);

  const loadMetricData = async () => {
    setLoading(true);
    setError(null);

    try {
      let response;
      
      switch (metric) {
        case 'conversion':
          response = await AnalyticsAPI.getConversionRates({ days });
          break;
        case 'abandonment':
          response = await AnalyticsAPI.getCartAbandonment({ days });
          break;
        case 'refunds':
          response = await AnalyticsAPI.getRefundRates({ days });
          break;
        case 'repeat':
          response = await AnalyticsAPI.getRepeatCustomers({ days });
          break;
        case 'time-to-purchase':
          response = await AnalyticsAPI.getTimeToPurchase({ days });
          break;
        default:
          throw new Error('Invalid metric type');
      }

      if (response.success) {
        setData(response.data);
      } else {
        throw new Error('Failed to load metric data');
      }
    } catch (error) {
      console.error(`Failed to load ${metric} data:`, error);
      setError(`Failed to load ${metric} data`);
    } finally {
      setLoading(false);
    }
  };

  const renderMetricValue = () => {
    if (!data) return null;

    switch (metric) {
      case 'conversion':
        return (
          <div>
            <div className="text-3xl font-bold text-gray-900 mb-2">
              {data.overall.conversion_rate.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600 mb-4">
              {data.overall.converted_sessions.toLocaleString()} of {data.overall.total_sessions.toLocaleString()} sessions
            </div>
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-700">By Traffic Source:</div>
              {data.by_traffic_source.slice(0, 3).map((source, index) => (
                <div key={index} className="flex justify-between text-sm">
                  <span className="capitalize text-gray-600">
                    {source.traffic_source.replace('_', ' ')}
                  </span>
                  <span className="font-medium">{source.conversion_rate}%</span>
                </div>
              ))}
            </div>
          </div>
        );

      case 'abandonment':
        return (
          <div>
            <div className="text-3xl font-bold text-gray-900 mb-2">
              {data.abandonment_rates.overall_abandonment_rate.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600 mb-4">
              Overall cart abandonment rate
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Cart Abandonment</span>
                <span className="font-medium">{data.abandonment_rates.cart_abandonment_rate.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Checkout Abandonment</span>
                <span className="font-medium">{data.abandonment_rates.checkout_abandonment_rate.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        );

      case 'refunds':
        return (
          <div>
            <div className="text-3xl font-bold text-gray-900 mb-2">
              {data.overall.refund_rate.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600 mb-4">
              {data.overall.total_refunds.toLocaleString()} of {data.overall.total_orders.toLocaleString()} orders
            </div>
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-700">Top Reasons:</div>
              {data.by_reason.slice(0, 3).map((reason, index) => (
                <div key={index} className="flex justify-between text-sm">
                  <span className="capitalize text-gray-600">
                    {reason.reason.replace('_', ' ')}
                  </span>
                  <span className="font-medium">{reason.percentage}%</span>
                </div>
              ))}
            </div>
          </div>
        );

      case 'repeat':
        return (
          <div>
            <div className="text-3xl font-bold text-gray-900 mb-2">
              {data.overall.repeat_rate.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600 mb-4">
              {data.overall.repeat_customers.toLocaleString()} repeat customers
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Avg. Days Between Orders</span>
                <span className="font-medium">{data.overall.average_days_between_orders.toFixed(0)}</span>
              </div>
            </div>
          </div>
        );

      case 'time-to-purchase':
        return (
          <div>
            <div className="text-3xl font-bold text-gray-900 mb-2">
              {data.metrics.average_days.toFixed(1)} days
            </div>
            <div className="text-sm text-gray-600 mb-4">
              Average time to first purchase
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Median</span>
                <span className="font-medium">{(data.metrics.median_hours / 24).toFixed(1)} days</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">First Purchases</span>
                <span className="font-medium">{data.metrics.total_first_purchases.toLocaleString()}</span>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center text-red-600">
          <InformationCircleIcon className="w-5 h-5 mr-2" />
          <span className="text-sm">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <button
          onClick={loadMetricData}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {description && (
        <p className="text-sm text-gray-600 mb-4">{description}</p>
      )}

      {renderMetricValue()}
    </div>
  );
};

export default MetricsWidget;