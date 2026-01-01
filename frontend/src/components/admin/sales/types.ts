// frontend/src/components/admin/sales/types.ts

export interface SalesFilters {
  dateRange: string;
  startDate: string;
  endDate: string;
  categories: string[];
  regions: string[];
  salesChannels: string[];
  granularity: 'daily' | 'weekly' | 'monthly';
}

export interface SalesData {
  date: string;
  revenue: number;
  orders: number;
  averageOrderValue: number;
  onlineRevenue: number;
  instoreRevenue: number;
}

export interface SalesMetrics {
  totalRevenue: number;
  totalOrders: number;
  averageOrderValue: number;
  conversionRate: number;
  revenueGrowth: number;
  ordersGrowth: number;
}

export interface SalesOverviewProps {
  salesData?: {
    data: SalesData[];
    metrics: SalesMetrics;
  };
  loading: boolean;
  error?: Error | null;
  onFiltersChange: (filters: SalesFilters) => void;
  onRefresh: () => void;
  availableCategories: { id: string; name: string }[];
  availableRegions: { id: string; name: string }[];
  title?: string;
  subtitle?: string;
}
