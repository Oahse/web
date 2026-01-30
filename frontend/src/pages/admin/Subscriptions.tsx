import React, { useEffect, useState } from 'react';
import { Loader, AlertCircle, Eye, ChevronLeft, ChevronRight, Calendar, DollarSign, User, Package, SearchIcon, DownloadIcon } from 'lucide-react';
import AdminAPI from '../../api/admin';
import toast from 'react-hot-toast';
import { useTheme } from '../../store/ThemeContext';

const LIMIT = 20;

interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

interface Subscription {
  id: string;
  user_id: string;
  user?: {
    id: string;
    name: string;
    email: string;
  };
  subscription_plan_id: string;
  subscription_plan?: {
    id: string;
    name: string;
    description: string;
    billing_interval: string;
    base_price: number;
  };
  status: 'active' | 'paused' | 'cancelled' | 'expired' | 'pending';
  current_period_start: string;
  current_period_end: string;
  next_billing_date?: string;
  base_cost: number;
  delivery_cost: number;
  tax_amount: number;
  total_cost: number;
  currency: string;
  delivery_address: {
    street: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
  };
  created_at: string;
  updated_at?: string;
  cancelled_at?: string;
  pause_reason?: string;
  cancellation_reason?: string;
}

export const AdminSubscriptions = () => {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState<PaginationInfo>({ 
    page: 1, 
    limit: LIMIT, 
    total: 0, 
    pages: 0 
  });
  const [filters, setFilters] = useState({
    status: '',
    search: '',
    date_from: '',
    date_to: ''
  });

  useEffect(() => {
    const fetchSubscriptions = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await AdminAPI.getSubscriptions({
          page,
          limit: LIMIT,
          status: filters.status || undefined,
          search: filters.search || undefined,
          date_from: filters.date_from || undefined,
          date_to: filters.date_to || undefined
        });
        
        if (response?.success && response?.data) {
          const data = response.data;
          setSubscriptions(data.data || []);
          if (data.pagination) {
            setPagination({
              page: data.pagination.page || page,
              limit: data.pagination.limit || LIMIT,
              total: data.pagination.total || 0,
              pages: data.pagination.pages || 0,
            });
          }
        } else {
          throw new Error(response?.message || 'Failed to load subscriptions');
        }
      } catch (err: any) {
        const message = err?.response?.data?.message || err?.message || 'Failed to load subscriptions';
        setError(message);
        toast.error(message);
      } finally {
        setLoading(false);
      }
    };

    fetchSubscriptions();
  }, [page, filters]);

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(1); // Reset to first page when filters change
  };

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount ?? 0);
  };

  const statusBadge = (status: string) => {
    const config = {
      active: { color: 'bg-success/20 text-success', label: 'Active' },
      paused: { color: 'bg-warning/20 text-warning', label: 'Paused' },
      cancelled: { color: 'bg-destructive/20 text-destructive', label: 'Cancelled' },
      expired: { color: 'bg-gray/20 text-gray', label: 'Expired' },
      pending: { color: 'bg-blue/20 text-blue', label: 'Pending' }
    };
    
    const { color, label } = config[status as keyof typeof config] || config.pending;
    
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${color}`}>
        {label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader className="w-12 h-12 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-copy">Subscriptions Management</h1>
          <p className="text-copy-light mt-2">Manage all customer subscriptions</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-surface rounded-lg border border-border-light p-6">
        <h2 className="text-lg font-semibold text-copy mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-copy-light mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="w-full px-3 py-2 border border-border-light rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="cancelled">Cancelled</option>
              <option value="expired">Expired</option>
              <option value="pending">Pending</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-copy-light mb-1">Search</label>
            <input
              type="text"
              placeholder="Search by email, name..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="w-full px-3 py-2 border border-border-light rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-copy-light mb-1">From Date</label>
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
              className="w-full px-3 py-2 border border-border-light rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-copy-light mb-1">To Date</label>
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
              className="w-full px-3 py-2 border border-border-light rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-destructive">Error</p>
            <p className="text-destructive/80 text-sm">{error}</p>
          </div>
        </div>
      )}

      <div className="bg-surface rounded-lg border border-border-light overflow-hidden">
        <div className="p-6 border-b border-border-light">
          <h2 className="text-xl font-bold text-copy">All Subscriptions ({subscriptions.length})</h2>
        </div>

        {subscriptions.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-surface-dark border-b border-border-light">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Customer</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Plan</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Status</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Monthly Cost</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Next Billing</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Created</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {subscriptions.map((subscription) => (
                    <tr key={subscription.id} className="border-b border-border-light hover:bg-surface-light">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-primary/10 rounded-lg">
                            <User className="w-4 h-4 text-primary" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-copy">
                              {subscription.user?.name || 'Unknown User'}
                            </p>
                            <p className="text-xs text-copy-light">{subscription.user?.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          {subscription.subscription_plan ? (
                            <>
                              <p className="text-copy font-medium">{subscription.subscription_plan.name}</p>
                              <p className="text-copy-light text-xs">
                                {subscription.subscription_plan.billing_interval}
                              </p>
                            </>
                          ) : (
                            <span className="text-copy-light">Unknown plan</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {statusBadge(subscription.status)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          <p className="font-semibold text-copy">
                            {formatCurrency(subscription.total_cost, subscription.currency)}
                          </p>
                          <p className="text-copy-light text-xs">
                            Base: {formatCurrency(subscription.base_cost, subscription.currency)}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-copy-light" />
                            <span className="text-copy">
                              {subscription.next_billing_date 
                                ? new Date(subscription.next_billing_date).toLocaleDateString()
                                : 'N/A'
                              }
                            </span>
                          </div>
                          {subscription.current_period_end && (
                            <p className="text-copy-light text-xs">
                              Period: {new Date(subscription.current_period_end).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-copy-light">
                        {new Date(subscription.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <button className="flex items-center gap-1 px-3 py-1 bg-primary/10 text-primary rounded hover:bg-primary/20 transition">
                          <Eye className="w-4 h-4" />
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {pagination.pages > 1 && (
              <div className="px-6 py-4 border-t border-border-light flex flex-wrap items-center justify-between gap-4">
                <p className="text-sm text-copy-light">
                  Showing {(pagination.page - 1) * pagination.limit + 1}–{Math.min(pagination.page * pagination.limit, pagination.total)} of {pagination.total} subscriptions
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="inline-flex items-center gap-1 px-3 py-2 rounded-lg border border-border-light bg-surface text-copy text-sm font-medium hover:bg-surface-light disabled:opacity-50 disabled:cursor-not-allowed transition"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    Previous
                  </button>
                  <span className="text-sm text-copy-light px-2">
                    Page {pagination.page} of {pagination.pages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(pagination.pages, p + 1))}
                    disabled={page >= pagination.pages}
                    className="inline-flex items-center gap-1 px-3 py-2 rounded-lg border border-border-light bg-surface text-copy text-sm font-medium hover:bg-surface-light disabled:opacity-50 disabled:cursor-not-allowed transition"
                  >
                    Next
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="p-6 text-center text-copy-light">
            <div className="flex flex-col items-center gap-3">
              <Package className="w-12 h-12 text-copy-light/50" />
              <p>No subscriptions found</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminSubscriptions;
