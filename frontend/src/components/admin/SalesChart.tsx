import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import { themeClasses } from '../../lib/theme';
import { BarChart3Icon } from 'lucide-react';

type ChartView = 'sales' | 'orders';

export const SalesChart = () => {
  const [days, setDays] = useState<number>(30);
  const [chartView, setChartView] = useState<ChartView>('sales');
  const { data: salesData, loading, error, execute: fetchSalesData } = useApi();

  useEffect(() => {
    fetchSalesData(() => AdminAPI.getSalesTrend(days));
  }, [days, fetchSalesData]);

  const handleTimeRangeChange = (newDays: number) => {
    setDays(newDays);
  };

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-md border border-gray-200">
        <p className={themeClasses.text.muted}>Loading chart...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-md border border-gray-200">
        <p className={themeClasses.text.muted}>Error loading chart data.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setChartView('sales')}
            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
              chartView === 'sales' 
                ? 'bg-primary text-white' 
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            Sales ($)
          </button>
          <button
            onClick={() => setChartView('orders')}
            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
              chartView === 'orders' 
                ? 'bg-primary text-white' 
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            Orders (#)
          </button>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => handleTimeRangeChange(7)}
            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
              days === 7 
                ? 'bg-primary/10 text-primary dark:bg-primary/20' 
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            7 Days
          </button>
          <button
            onClick={() => handleTimeRangeChange(30)}
            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
              days === 30 
                ? 'bg-primary/10 text-primary dark:bg-primary/20' 
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            30 Days
          </button>
          <button
            onClick={() => handleTimeRangeChange(90)}
            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
              days === 90 
                ? 'bg-primary/10 text-primary dark:bg-primary/20' 
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            90 Days
          </button>
        </div>
      </div>
      <div className="h-64">
        {salesData?.sales_trend && salesData.sales_trend.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={salesData.sales_trend}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
              <XAxis 
                dataKey="date" 
                className="text-gray-600 dark:text-gray-400" 
                fontSize={12}
                tick={{ fill: 'currentColor' }}
              />
              <YAxis 
                className="text-gray-600 dark:text-gray-400" 
                fontSize={12}
                tick={{ fill: 'currentColor' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--color-surface-elevated, #ffffff)',
                  borderColor: 'var(--color-border, #e5e7eb)',
                  color: 'var(--color-copy, #000000)',
                  borderRadius: '0.5rem',
                }}
                labelStyle={{ color: 'var(--color-copy, #000000)' }}
              />
              <Legend />
              <Bar 
                dataKey={chartView === 'sales' ? 'sales' : 'orders'} 
                fill="var(--color-primary, #3b82f6)" 
                radius={[4, 4, 0, 0]}
                name={chartView === 'sales' ? 'Sales ($)' : 'Orders'}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700">
            <div className="text-center">
              <BarChart3Icon size={48} className="mx-auto text-gray-300 dark:text-gray-600 mb-2" />
              <p className="text-gray-500 dark:text-gray-400">No data available for the selected period</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
