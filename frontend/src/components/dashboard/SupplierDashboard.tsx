import React, { useState, useEffect } from 'react';
import { CustomizableDashboard } from './widgets/CustomizableDashboard';
import { InteractiveChart } from './charts/InteractiveChart';
import { TimeSeriesChart } from './charts/TimeSeriesChart';
import { AdvancedTable } from './tables/AdvancedTable';
import {
  PackageIcon,
  DollarSignIcon,
  TrendingUpIcon,
  StarIcon,
  ShoppingCartIcon,
  BarChart3Icon,
  LineChartIcon,
  TableIcon,
  AlertTriangleIcon
} from 'lucide-react';

/**
 * @typedef {object} SupplierDashboardProps
 * @property {string} [supplierId]
 * @property {(widgetId?: string) => void} [onRefresh]
 * @property {(widgetId: string, format: string) => void} [onExport]
 */

// Supplier Metric Widget
const SupplierMetricWidget = ({ value, change, label, icon, color = 'blue' }) => (
  <div className="text-center">
    <div className="flex items-center justify-center mb-3">
      {icon && (
        <div className={`p-3 rounded-full bg-${color}-100 text-${color}-600`}>
          {icon}
        </div>
      )}
    </div>
    <div className="text-2xl font-bold text-gray-900 mb-1">{value}</div>
    <div className="text-sm text-gray-500 mb-2">{label}</div>
    <div className={`text-sm font-medium ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
      {change > 0 ? '+' : ''}{change}% vs last month
    </div>
  </div>
);

// Performance Chart Widget
const PerformanceChartWidget = ({ data, type }) => (
  <InteractiveChart
    type={type}
    data={data}
    height={250}
    showTooltips={true}
    showLegend={true}
    enableDrillDown={true}
    className="border-0 shadow-none"
  />
);

// Order Analytics Widget
const OrderAnalyticsWidget = () => {
  
  const generateTimeSeriesData = () => {
    const now = new Date();
    const data = [
      {
        label: 'Orders',
        data: Array.from({ length: 30 }, (_, i) => ({
          timestamp: new Date(now.getTime() - (29 - i) * 24 * 60 * 60 * 1000),
          value: Math.floor(Math.random() * 50) + 10
        })),
        color: 'var(--color-info)'
      },
      {
        label: 'Revenue',
        data: Array.from({ length: 30 }, (_, i) => ({
          timestamp: new Date(now.getTime() - (29 - i) * 24 * 60 * 60 * 1000),
          value: Math.floor(Math.random() * 5000) + 1000
        })),
        color: 'var(--color-success)'
      }
    ];
    return data;
  };

  return (
    <TimeSeriesChart
      datasets={generateTimeSeriesData()}
      height={300}
      defaultTimeRange="30d"
      showComparison={true}
      showTrend={true}
      className="border-0 shadow-none"
    />
  );
};

// Product Performance Table
const ProductPerformanceWidget = () => {
  const productData = [
    {
      id: 1,
      product_name: 'Wireless Headphones Pro',
      sku: 'WHP-001',
      orders: 156,
      revenue: 23400,
      rating: 4.8,
      stock: 45,
      status: 'Active'
    },
    {
      id: 2,
      product_name: 'Smart Fitness Watch',
      sku: 'SFW-002',
      orders: 89,
      revenue: 17800,
      rating: 4.6,
      stock: 12,
      status: 'Low Stock'
    },
    {
      id: 3,
      product_name: 'Bluetooth Speaker Mini',
      sku: 'BSM-003',
      orders: 234,
      revenue: 11700,
      rating: 4.9,
      stock: 78,
      status: 'Active'
    },
    {
      id: 4,
      product_name: 'USB-C Hub Deluxe',
      sku: 'UCH-004',
      orders: 67,
      revenue: 8040,
      rating: 4.4,
      stock: 0,
      status: 'Out of Stock'
    },
    {
      id: 5,
      product_name: 'Laptop Stand Adjustable',
      sku: 'LSA-005',
      orders: 123,
      revenue: 6150,
      rating: 4.7,
      stock: 34,
      status: 'Active'
    }
  ];

  const columns = [
    {
      key: 'product_name',
      label: 'Product',
      sortable: true,
      render: (value, row) => (
        <div>
          <div className="font-medium text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">{row.sku}</div>
        </div>
      )
    },
    {
      key: 'orders',
      label: 'Orders',
      sortable: true,
      format: 'number',
      align: 'center'
    },
    {
      key: 'revenue',
      label: 'Revenue',
      sortable: true,
      format: 'currency',
      align: 'right'
    },
    {
      key: 'rating',
      label: 'Rating',
      sortable: true,
      align: 'center',
      render: (value) => (
        <div className="flex items-center justify-center gap-1">
          <StarIcon size={14} className="text-yellow-400 fill-current" />
          <span className="font-medium">{value}</span>
        </div>
      )
    },
    {
      key: 'stock',
      label: 'Stock',
      sortable: true,
      align: 'center',
      render: (value) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          value === 0 ? 'bg-red-100 text-red-800' :
          value < 20 ? 'bg-yellow-100 text-yellow-800' :
          'bg-green-100 text-green-800'
        }`}>
          {value}
        </span>
      )
    },
    {
      key: 'status',
      label: 'Status',
      sortable: true,
      align: 'center',
      render: (value) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          value === 'Active' ? 'bg-green-100 text-green-800' :
          value === 'Low Stock' ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        }`}>
          {value}
        </span>
      )
    }
  ];

  return (
    <AdvancedTable
      columns={columns}
      data={productData}
      searchable={true}
      sortable={true}
      exportable={true}
      pagination={false}
      className="border-0 shadow-none"
    />
  );
};

// Inventory Alert Widget
const InventoryAlertWidget = () => {
  const alerts = [
    { product: 'Smart Fitness Watch', sku: 'SFW-002', stock: 12, threshold: 20, type: 'low' },
    { product: 'USB-C Hub Deluxe', sku: 'UCH-004', stock: 0, threshold: 10, type: 'out' },
    { product: 'Wireless Mouse Pro', sku: 'WMP-006', stock: 8, threshold: 15, type: 'low' },
    { product: 'Phone Case Clear', sku: 'PCC-007', stock: 0, threshold: 25, type: 'out' }
  ];

  return (
    <div className="space-y-3">
      {alerts.map((alert, index) => (
        <div key={index} className={`p-3 rounded-lg border-l-4 ${
          alert.type === 'out' ? 'bg-red-50 border-red-400' : 'bg-yellow-50 border-yellow-400'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900">{alert.product}</div>
              <div className="text-sm text-gray-500">{alert.sku}</div>
            </div>
            <div className="text-right">
              <div className={`font-bold ${
                alert.type === 'out' ? 'text-red-600' : 'text-yellow-600'
              }`}>
                {alert.stock} units
              </div>
              <div className="text-xs text-gray-500">
                Threshold: {alert.threshold}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export const SupplierDashboard = () => {
  const [widgets, setWidgets] = useState([]);

  const widgetTemplates = [
    {
      id: 'supplier-metric-template',
      name: 'Business Metric',
      description: 'Key performance indicators for suppliers',
      type: 'metric',
      component: SupplierMetricWidget,
      defaultLayout: { w: 3, h: 4, minW: 2, minH: 3 },
      icon: <BarChart3Icon size={20} />,
      category: 'sales'
    },
    {
      id: 'performance-chart-template',
      name: 'Performance Chart',
      description: 'Track business performance over time',
      type: 'chart',
      component: PerformanceChartWidget,
      defaultLayout: { w: 6, h: 4, minW: 4, minH: 3 },
      icon: <LineChartIcon size={20} />,
      category: 'analytics'
    },
    {
      id: 'order-analytics-template',
      name: 'Order Analytics',
      description: 'Time-series analysis of orders and revenue',
      type: 'chart',
      component: OrderAnalyticsWidget,
      defaultLayout: { w: 8, h: 5, minW: 6, minH: 4 },
      icon: <TrendingUpIcon size={20} />,
      category: 'sales'
    },
    {
      id: 'product-performance-template',
      name: 'Product Performance',
      description: 'Detailed product analytics table',
      type: 'table',
      component: ProductPerformanceWidget,
      defaultLayout: { w: 12, h: 6, minW: 8, minH: 5 },
      icon: <TableIcon size={20} />,
      category: 'inventory'
    },
    {
      id: 'inventory-alerts-template',
      name: 'Inventory Alerts',
      description: 'Low stock and out-of-stock alerts',
      type: 'custom',
      component: InventoryAlertWidget,
      defaultLayout: { w: 4, h: 5, minW: 3, minH: 4 },
      icon: <AlertTriangleIcon size={20} />,
      category: 'inventory'
    }
  ];

  useEffect(() => {
    // Initialize supplier-specific widgets
    const defaultWidgets = [
      {
        id: 'total-products',
        type: 'metric',
        title: 'Total Products',
        component: SupplierMetricWidget,
        props: {
          title: 'Total Products',
          value: '47',
          label: 'Active Listings',
          change: 8.5,
          icon: <PackageIcon size={20} />,
          color: 'blue'
        },
        layout: { x: 0, y: 0, w: 3, h: 4 }
      },
      {
        id: 'monthly-revenue',
        type: 'metric',
        title: 'Monthly Revenue',
        component: SupplierMetricWidget,
        props: {
          title: 'Monthly Revenue',
          value: '$18,420',
          label: 'This Month',
          change: 12.3,
          icon: <DollarSignIcon size={20} />,
          color: 'green'
        },
        layout: { x: 3, y: 0, w: 3, h: 4 }
      },
      {
        id: 'total-orders',
        type: 'metric',
        title: 'Total Orders',
        component: SupplierMetricWidget,
        props: {
          title: 'Total Orders',
          value: '234',
          label: 'This Month',
          change: 15.7,
          icon: <ShoppingCartIcon size={20} />,
          color: 'purple'
        },
        layout: { x: 6, y: 0, w: 3, h: 4 }
      },
      {
        id: 'avg-rating',
        type: 'metric',
        title: 'Average Rating',
        component: SupplierMetricWidget,
        props: {
          title: 'Average Rating',
          value: '4.7',
          label: 'Customer Rating',
          change: 2.1,
          icon: <StarIcon size={20} />,
          color: 'yellow'
        },
        layout: { x: 9, y: 0, w: 3, h: 4 }
      },
      {
        id: 'order-analytics',
        type: 'chart',
        title: 'Orders & Revenue Trends',
        component: OrderAnalyticsWidget,
        props: {},
        layout: { x: 0, y: 4, w: 8, h: 5 }
      },
      {
        id: 'inventory-alerts',
        type: 'custom',
        title: 'Inventory Alerts',
        component: InventoryAlertWidget,
        props: {},
        layout: { x: 8, y: 4, w: 4, h: 5 }
      },
      {
        id: 'product-performance',
        type: 'table',
        title: 'Product Performance',
        component: ProductPerformanceWidget,
        props: {},
        layout: { x: 0, y: 9, w: 12, h: 6 }
      },
      {
        id: 'sales-by-category',
        type: 'chart',
        title: 'Sales by Category',
        component: PerformanceChartWidget,
        props: {
          type: 'bar',
          data: {
            labels: ['Electronics', 'Accessories', 'Audio', 'Computing', 'Mobile'],
            datasets: [{
              label: 'Sales',
              data: [45, 32, 28, 19, 15],
              backgroundColor: ['var(--color-info)', 'var(--color-success)', 'var(--color-warning)', 'var(--color-error)', 'var(--color-purple)']
            }]
          }
        },
        layout: { x: 0, y: 15, w: 6, h: 4 }
      },
      {
        id: 'monthly-comparison',
        type: 'chart',
        title: 'Monthly Comparison',
        component: PerformanceChartWidget,
        props: {
          type: 'line',
          data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [
              {
                label: 'This Year',
                data: [12000, 15000, 18000, 16000, 20000, 18420],
                borderColor: 'var(--color-info)',
                backgroundColor: 'var(--color-info)20'
              },
              {
                label: 'Last Year',
                data: [10000, 12000, 14000, 13000, 16000, 15000],
                borderColor: 'var(--color-success)',
                backgroundColor: 'var(--color-success)20'
              }
            ]
          }
        },
        layout: { x: 6, y: 15, w: 6, h: 4 }
      }
    ];

    setWidgets(defaultWidgets);
  }, []);

  const handleWidgetsChange = (updatedWidgets) => {
    setWidgets(updatedWidgets);
  };

  const handleSave = (layout) => {
    // Save dashboard layout to backend
    // API call to persist layout preferences to be implemented
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Supplier Dashboard</h1>
          <p className="text-gray-600">Monitor your business performance and manage your products</p>
        </div>
        
        <CustomizableDashboard
          widgets={widgets}
          widgetTemplates={widgetTemplates}
          editable={true}
          onWidgetsChange={handleWidgetsChange}
          onSave={handleSave}
        />
      </div>
    </div>
  );
};