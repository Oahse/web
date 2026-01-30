import React, { useEffect, useState } from 'react';
import { Loader, AlertCircle, Plus, Filter, ChevronLeft, ChevronRight, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import AdminAPI from '@/api/admin';
import toast from 'react-hot-toast';

const LIMIT = 20;

interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

interface InventoryAdjustment {
  id: string;
  inventory_id: string;
  adjustment_type: 'increase' | 'decrease' | 'transfer';
  quantity: number;
  reason: string;
  notes?: string;
  reference_number?: string;
  adjusted_by: string;
  adjusted_by_user?: {
    name: string;
    email: string;
  };
  product_variant?: {
    id: string;
    name: string;
    sku: string;
    product_name: string;
  };
  warehouse_location?: {
    id: string;
    name: string;
    code: string;
  };
  created_at: string;
}

export const AdminInventoryAdjustments = () => {
  const [adjustments, setAdjustments] = useState<InventoryAdjustment[]>([]);
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
    adjustment_type: '',
    date_from: '',
    date_to: '',
    search: ''
  });

  useEffect(() => {
    const fetchAdjustments = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await AdminAPI.getAllStockAdjustments();
        const data = response?.data || response;
        setAdjustments(Array.isArray(data) ? data : []);
      } catch (err: any) {
        const message = err?.response?.data?.message || 'Failed to load inventory adjustments';
        setError(message);
        toast.error(message);
      } finally {
        setLoading(false);
      }
    };

    fetchAdjustments();
  }, [page, filters]);

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(1); // Reset to first page when filters change
  };

  const adjustmentTypeBadge = (type: string) => {
    const config = {
      increase: { icon: TrendingUp, color: 'text-success', bg: 'bg-success/10', label: 'Increase' },
      decrease: { icon: TrendingDown, color: 'text-destructive', bg: 'bg-destructive/10', label: 'Decrease' },
      transfer: { icon: Minus, color: 'text-blue', bg: 'bg-blue/10', label: 'Transfer' }
    };
    
    const { icon: Icon, color, bg, label } = config[type as keyof typeof config] || config.increase;
    
    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${bg} ${color}`}>
        <Icon className="w-3 h-3" />
        {label}
      </span>
    );
  };

  const quantityBadge = (type: string, quantity: number) => {
    const colorClass = 
      type === 'increase' ? 'text-success' :
      type === 'decrease' ? 'text-destructive' :
      'text-blue';
    
    const sign = type === 'increase' ? '+' : type === 'decrease' ? '-' : '';
    
    return (
      <span className={`font-semibold ${colorClass}`}>
        {sign}{quantity}
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
          <h1 className="text-3xl font-bold text-copy">Inventory Adjustments</h1>
          <p className="text-copy-light mt-2">Track all inventory changes and adjustments</p>
        </div>
        <button className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors">
          <Plus className="w-4 h-4" />
          New Adjustment
        </button>
      </div>

      {/* Filters */}
      <div className="bg-surface rounded-lg border border-border-light p-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-4 h-4 text-copy-light" />
          <h2 className="text-lg font-semibold text-copy">Filters</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-copy-light mb-1">Adjustment Type</label>
            <select
              value={filters.adjustment_type}
              onChange={(e) => handleFilterChange('adjustment_type', e.target.value)}
              className="w-full px-3 py-2 border border-border-light rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="">All Types</option>
              <option value="increase">Increase</option>
              <option value="decrease">Decrease</option>
              <option value="transfer">Transfer</option>
            </select>
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
          <div>
            <label className="block text-sm font-medium text-copy-light mb-1">Search</label>
            <input
              type="text"
              placeholder="Search by SKU, product..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
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
          <h2 className="text-xl font-bold text-copy">All Adjustments ({adjustments.length})</h2>
        </div>

        {adjustments.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-surface-dark border-b border-border-light">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Date</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Type</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Product</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Quantity</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Reason</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Location</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Adjusted By</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Reference</th>
                  </tr>
                </thead>
                <tbody>
                  {adjustments.map((adjustment) => (
                    <tr key={adjustment.id} className="border-b border-border-light hover:bg-surface-light">
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          <p className="text-copy">{new Date(adjustment.created_at).toLocaleDateString()}</p>
                          <p className="text-copy-light text-xs">
                            {new Date(adjustment.created_at).toLocaleTimeString()}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {adjustmentTypeBadge(adjustment.adjustment_type)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          {adjustment.product_variant ? (
                            <>
                              <p className="text-copy font-medium">{adjustment.product_variant.name}</p>
                              <p className="text-copy-light text-xs">SKU: {adjustment.product_variant.sku}</p>
                              <p className="text-copy-light text-xs">{adjustment.product_variant.product_name}</p>
                            </>
                          ) : (
                            <span className="text-copy-light">Unknown product</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {quantityBadge(adjustment.adjustment_type, adjustment.quantity)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          <p className="text-copy">{adjustment.reason}</p>
                          {adjustment.notes && (
                            <p className="text-copy-light text-xs mt-1">{adjustment.notes}</p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          {adjustment.warehouse_location ? (
                            <>
                              <p className="text-copy">{adjustment.warehouse_location.name}</p>
                              <p className="text-copy-light text-xs">{adjustment.warehouse_location.code}</p>
                            </>
                          ) : (
                            <span className="text-copy-light">N/A</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          {adjustment.adjusted_by_user ? (
                            <>
                              <p className="text-copy">{adjustment.adjusted_by_user.name}</p>
                              <p className="text-copy-light text-xs">{adjustment.adjusted_by_user.email}</p>
                            </>
                          ) : (
                            <span className="text-copy-light">{adjustment.adjusted_by}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          {adjustment.reference_number ? (
                            <p className="text-copy font-mono text-xs">{adjustment.reference_number}</p>
                          ) : (
                            <span className="text-copy-light">N/A</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="px-6 py-4 border-t border-border-light flex flex-wrap items-center justify-between gap-4">
              <p className="text-sm text-copy-light">
                Showing {(page - 1) * LIMIT + 1}–{Math.min(page * LIMIT, adjustments.length)} of {adjustments.length} adjustments
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
                  Page {page}
                </span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={adjustments.length < LIMIT}
                  className="inline-flex items-center gap-1 px-3 py-2 rounded-lg border border-border-light bg-surface text-copy text-sm font-medium hover:bg-surface-light disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="p-6 text-center text-copy-light">
            <div className="flex flex-col items-center gap-3">
              <Minus className="w-12 h-12 text-copy-light/50" />
              <p>No inventory adjustments found</p>
              <button className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors">
                <Plus className="w-4 h-4" />
                Make First Adjustment
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminInventoryAdjustments;
