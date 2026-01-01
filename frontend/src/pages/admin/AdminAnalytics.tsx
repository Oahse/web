import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../hooks/useApi';
import AnalyticsAPI from '../../apis/analytics';
import { SalesOverview } from '../../components/admin/sales/SalesOverview';
import { SalesFilters, SalesData, SalesMetrics } from '../../components/admin/sales/types';
import { apiClient } from '../../apis/client'; // Import apiClient

export const AdminAnalytics = () => {
  const [filters, setFilters] = useState<SalesFilters>({
    dateRange: '30d',
    startDate: '',
    endDate: '',
    categories: [],
    regions: [],
    salesChannels: ['online', 'instore'],
    granularity: 'daily'
  });

  const { data: salesData, loading, error, execute: fetchSalesData } = useApi<{
    data: SalesData[];
    metrics: SalesMetrics;
  }>();

  const { data: categoriesData, loading: categoriesLoading, error: categoriesError, execute: fetchCategories } = useApi<{
    categories: { id: string; name: string }[];
  }>();

  // Fetch categories on component mount
  useEffect(() => {
    fetchCategories(apiClient.getCategories);
  }, [fetchCategories]);

  const availableCategories = categoriesData?.categories || [];

  const availableRegions = [
    { id: 'north-america', name: 'North America' },
    { id: 'europe', name: 'Europe' },
    { id: 'asia-pacific', name: 'Asia Pacific' },
    { id: 'africa', name: 'Africa' }
  ];

  const fetchData = useCallback(async () => {
    const response = await AnalyticsAPI.getSalesOverview({
      days: filters.dateRange === '7d' ? 7 : 
            filters.dateRange === '30d' ? 30 : 
            filters.dateRange === '3m' ? 90 : 
            filters.dateRange === '12m' ? 365 : 30,
      granularity: filters.granularity,
      categories: filters.categories.length > 0 ? filters.categories : undefined,
      regions: filters.regions.length > 0 ? filters.regions : undefined,
      sales_channels: filters.salesChannels.length > 0 ? filters.salesChannels : undefined,
      start_date: filters.dateRange === 'custom' && filters.startDate ? filters.startDate : undefined,
      end_date: filters.dateRange === 'custom' && filters.endDate ? filters.endDate : undefined
    });
    
    return response.data;
  }, [filters]);

  useEffect(() => {
    if (salesData) {
      console.log('Sales Data from API:', salesData);
    }
    if (categoriesData) {
      console.log('Categories Data from API:', categoriesData);
    }
  }, [salesData, categoriesData]);

  useEffect(() => {
    fetchSalesData(fetchData);
  }, [fetchSalesData, fetchData]);

  const handleRefresh = () => {
    fetchSalesData(fetchData);
    fetchCategories(apiClient.getCategories);
  };

  const handleFiltersChange = (newFilters: SalesFilters) => {
    setFilters(newFilters);
  };

  return (
    <SalesOverview
      salesData={salesData || undefined}
      loading={loading}
      error={error}
      onFiltersChange={handleFiltersChange}
      onRefresh={handleRefresh}
      availableCategories={availableCategories}
      availableRegions={availableRegions}
      title="Sales Analytics"
      subtitle="Detailed sales performance and analytics"
    />
  );
};
