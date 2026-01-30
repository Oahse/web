import React, { useEffect, useState } from 'react';
import { Loader, AlertCircle, ChevronLeft, ChevronRight, SearchIcon, DownloadIcon, EditIcon, ArrowUpDownIcon } from 'lucide-react';
import AdminAPI from '../../api/admin';
import toast from 'react-hot-toast';
import { useTheme } from '../../store/ThemeContext';
import Dropdown from '../../components/ui/Dropdown';

const LIMIT = 10;

interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export const AdminInventory = () => {
  const { theme } = useTheme();
  const [inventory, setInventory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState<PaginationInfo>({ page: 1, limit: LIMIT, total: 0, pages: 0 });
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    const fetchInventory = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await AdminAPI.getInventory({
          page, 
          limit: LIMIT,
          search: searchQuery || undefined,
          status: statusFilter || undefined,
          sort_by: sortBy,
          sort_order: sortOrder
        });
        
        if (response?.success && response?.data) {
          const data = response.data;
          setInventory(data.data || []);
          if (data.pagination) {
            setPagination({
              page: data.pagination.page || page,
              limit: data.pagination.limit || LIMIT,
              total: data.pagination.total || 0,
              pages: data.pagination.pages || 0,
            });
          }
        } else {
          throw new Error(response?.message || 'Failed to load inventory');
        }
      } catch (err: any) {
        const message = err?.response?.data?.message || err?.message || 'Failed to load inventory';
        setError(message);
        toast.error(message);
      } finally {
        setLoading(false);
      }
    };

    fetchInventory();
  }, [page, searchQuery, statusFilter, sortBy, sortOrder]);

  const getItemDisplay = (item: any) => ({
    productName: item.variant?.product?.name ?? item.product_name ?? 'N/A',
    locationName: item.location?.name ?? item.location_name ?? 'N/A',
    stockLevel: item.quantity_available ?? item.quantity ?? item.stock_level ?? 0,
  });

  const stockStatus = (item: any) => {
    const level = getItemDisplay(item).stockLevel;
    if (level > 10) return { label: 'In Stock', cls: 'bg-success/20 text-success' };
    if (level > 0) return { label: 'Low Stock', cls: 'bg-warning/20 text-warning' };
    return { label: 'Out of Stock', cls: 'bg-destructive/20 text-destructive' };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader className="w-12 h-12 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Inventory Management</h1>
          <p className={`mt-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>Manage stock levels and locations</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => {/* TODO: Add download functionality */}}
            className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <DownloadIcon size={20} />
            Download CSV
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className={`p-4 rounded-lg border ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search inventory..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent ${
                  theme === 'dark' 
                    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                    : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                }`}
              />
            </div>
          </div>
          
          <div className="flex flex-wrap gap-2">
            <Dropdown
              options={[
                { value: '', label: 'All Status' },
                { value: 'in_stock', label: 'In Stock' },
                { value: 'low_stock', label: 'Low Stock' },
                { value: 'out_of_stock', label: 'Out of Stock' }
              ]}
              value={statusFilter}
              onChange={setStatusFilter}
              placeholder="All Status"
            />
            
            <Dropdown
              options={[
                { value: 'created_at', label: 'Created' },
                { value: 'product_name', label: 'Product Name' },
                { value: 'quantity', label: 'Stock Level' },
                { value: 'location_name', label: 'Location' }
              ]}
              value={sortBy}
              onChange={setSortBy}
              placeholder="Sort by"
            />
            
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className={`inline-flex items-center gap-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent ${
                theme === 'dark' 
                  ? 'bg-gray-700 border-gray-600 text-white hover:bg-gray-600' 
                  : 'bg-white border-gray-300 text-gray-900 hover:bg-gray-50'
              }`}
            >
              <ArrowUpDownIcon size={16} />
              {sortOrder === 'asc' ? 'A-Z' : 'Z-A'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className={`p-4 rounded-lg border flex items-start gap-3 ${
          theme === 'dark' 
            ? 'bg-red-900/20 border-red-800 text-red-200' 
            : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      <div className={`rounded-lg border overflow-hidden ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
        <div className={`p-6 border-b ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
          <h2 className="text-xl font-bold">Inventory Items</h2>
        </div>

        {inventory.length > 0 ? (
          <>
            {/* Desktop table */}
            <div className="overflow-x-auto hidden md:block">
              <table className="w-full">
                <thead className="bg-surface-dark border-b border-border-light">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Product</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Location</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Stock Level</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {inventory.map((item) => {
                    const status = stockStatus(item);
                    const d = getItemDisplay(item);
                    return (
                      <tr key={item.id} className="border-b border-border-light hover:bg-surface-light">
                        <td className="px-6 py-4 text-sm text-copy">{d.productName}</td>
                        <td className="px-6 py-4 text-sm text-copy-light">{d.locationName}</td>
                        <td className="px-6 py-4 text-sm font-semibold">{d.stockLevel}</td>
                        <td className="px-6 py-4 text-sm">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${status.cls}`}>
                            {status.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="md:hidden divide-y divide-border-light">
              {inventory.map((item) => {
                const status = stockStatus(item);
                const d = getItemDisplay(item);
                return (
                  <div
                    key={item.id}
                    className="p-4 flex flex-col gap-2 bg-surface hover:bg-surface-light transition"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-copy">{d.productName}</span>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${status.cls}`}>
                        {status.label}
                      </span>
                    </div>
                    <div className="text-sm text-copy-light">{d.locationName}</div>
                    <div className="text-sm font-semibold">Stock: {d.stockLevel}</div>
                  </div>
                );
              })}
            </div>

            {pagination.pages > 1 && (
              <div className={`px-6 py-4 border-t ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} flex flex-wrap items-center justify-between gap-4`}>
                <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                  Showing {(pagination.page - 1) * pagination.limit + 1}–{Math.min(pagination.page * pagination.limit, pagination.total)} of {pagination.total} items
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className={`inline-flex items-center gap-1 px-3 py-2 rounded-lg border text-sm font-medium transition ${
                      theme === 'dark' 
                        ? 'border-gray-600 bg-gray-800 text-white hover:bg-gray-700 disabled:opacity-50' 
                        : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50 disabled:opacity-50'
                    } disabled:cursor-not-allowed`}
                  >
                    <ChevronLeft className="w-4 h-4" />
                    Previous
                  </button>
                  <span className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'} px-2`}>
                    Page {pagination.page} {pagination.pages > 0 ? `of ${pagination.pages}` : ''}
                  </span>
                  <button
                    onClick={() => setPage((p) => (pagination.pages > 0 ? Math.min(pagination.pages, p + 1) : p + 1))}
                    disabled={page >= pagination.pages}
                    className={`inline-flex items-center gap-1 px-3 py-2 rounded-lg border text-sm font-medium transition ${
                      theme === 'dark' 
                        ? 'border-gray-600 bg-gray-800 text-white hover:bg-gray-700 disabled:opacity-50' 
                        : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50 disabled:opacity-50'
                    } disabled:cursor-not-allowed`}
                  >
                    Next
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className={`p-6 text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>No inventory items found</div>
        )}
      </div>
    </div>
  );
};

export default AdminInventory;
