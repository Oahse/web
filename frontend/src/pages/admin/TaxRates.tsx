import React, { useEffect, useState } from 'react';
import { Loader, AlertCircle, PlusIcon, EditIcon, TrashIcon, ChevronLeft, ChevronRight, SearchIcon, DownloadIcon } from 'lucide-react';
import AdminAPI from '../../api/admin';
import toast from 'react-hot-toast';
import { useTheme } from '../../store/ThemeContext';

const LIMIT = 10;

interface PaginationInfo {
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

interface TaxRate {
  id: string;
  country_code: string;
  country_name: string;
  province_code?: string;
  province_name?: string;
  tax_rate: number;
  tax_percentage: number;
  tax_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export const AdminTaxRates = () => {
  const [taxRates, setTaxRates] = useState<TaxRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState<PaginationInfo>({ 
    page: 1, 
    per_page: LIMIT, 
    total: 0, 
    pages: 0 
  });
  const [searchQuery, setSearchQuery] = useState('');
  const { theme } = useTheme();

  useEffect(() => {
    const fetchTaxRates = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await AdminAPI.getTaxRates({
          page,
          per_page: LIMIT,
          search: searchQuery || undefined
        });
        
        if (response?.success && response?.data) {
          const data = response.data;
          setTaxRates(data.data || []);
          if (data.pagination) {
            setPagination({
              page: data.pagination.page || page,
              per_page: data.pagination.per_page || LIMIT,
              total: data.pagination.total || 0,
              pages: data.pagination.pages || 0,
            });
          }
        } else {
          throw new Error(response?.message || 'Failed to load tax rates');
        }
      } catch (err: any) {
        const message = err?.response?.data?.message || err?.message || 'Failed to load tax rates';
        setError(message);
        toast.error(message);
      } finally {
        setLoading(false);
      }
    };

    fetchTaxRates();
  }, [page, searchQuery]);

  const handleDeleteTaxRate = async (rateId: string) => {
    try {
      await AdminAPI.deleteTaxRate(rateId);
      toast.success('Tax rate deleted successfully');
      // Refresh the list
      const response = await AdminAPI.getTaxRates({
          page,
          per_page: LIMIT,
          search: searchQuery || undefined
        });
      if (response?.success && response?.data) {
        setTaxRates(response.data.data || []);
      }
    } catch (error: any) {
      toast.error('Failed to delete tax rate');
    }
  };

  const handleDownloadTaxRates = async (format: 'csv' | 'excel' | 'pdf' = 'csv') => {
    try {
      await AdminAPI.downloadProducts(format);
      toast.success(`Tax rates downloaded as ${format.toUpperCase()}`);
    } catch (error: any) {
      toast.error('Failed to download tax rates');
    }
  };

  const formatPercentage = (rate: number) => {
    return `${rate.toFixed(2)}%`;
  };

  const statusBadge = (isActive: boolean) => {
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
        isActive 
          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      }`}>
        {isActive ? 'Active' : 'Inactive'}
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
    <div className={`space-y-6 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Tax Rates Management</h1>
          <p className={`mt-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>Manage tax rates by country and region</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleDownloadTaxRates('csv')}
            className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <DownloadIcon size={20} />
            Download CSV
          </button>
          <button className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <PlusIcon size={20} />
            Add Tax Rate
          </button>
        </div>
      </div>

      {/* Search */}
      <div className={`p-4 rounded-lg border ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
        <div className="flex-1">
          <div className="relative">
            <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search tax rates..."
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
          <h2 className="text-xl font-bold">All Tax Rates</h2>
        </div>

        {taxRates.length > 0 ? (
          <>
            {/* Desktop table */}
            <div className="overflow-x-auto hidden md:block">
              <table className="w-full">
                <thead className={`${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'} border-b ${theme === 'dark' ? 'border-gray-600' : 'border-gray-200'}`}>
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold">Rate ID</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold">Country</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold">Province</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold">Tax Rate</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold">Tax Name</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold">Status</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {taxRates.map((taxRate: any) => (
                    <tr key={taxRate.id} className={`border-b ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} hover:${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'}`}>
                      <td className="px-6 py-4 text-sm font-mono text-blue-600">{String(taxRate.id).slice(0, 8)}</td>
                      <td className={`px-6 py-4 text-sm ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{taxRate.country_name} ({taxRate.country_code})</td>
                      <td className={`px-6 py-4 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                        {taxRate.province_name ? `${taxRate.province_name} (${taxRate.province_code})` : '-'}
                      </td>
                      <td className={`px-6 py-4 text-sm font-mono ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                        {formatPercentage(taxRate.tax_rate)}
                      </td>
                      <td className={`px-6 py-4 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>{taxRate.tax_name || 'General Tax'}</td>
                      <td className="px-6 py-4 text-sm">{statusBadge(taxRate.is_active)}</td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex gap-2">
                          <button className="inline-flex items-center gap-1 px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                            <EditIcon size={16} />
                          </button>
                          <button
                            onClick={() => handleDeleteTaxRate(taxRate.id)}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                          >
                            <TrashIcon size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className={`md:hidden divide-y ${theme === 'dark' ? 'divide-gray-700' : 'divide-gray-200'}`}>
              {taxRates.map((taxRate: any) => (
                <div
                  key={taxRate.id}
                  className={`p-4 flex flex-col gap-2 ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} ${theme === 'dark' ? 'hover:bg-gray-700' : 'hover:bg-gray-50'} transition`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-mono text-blue-600">{String(taxRate.id).slice(0, 8)}</span>
                    {statusBadge(taxRate.is_active)}
                  </div>
                  <div className={`font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                    {taxRate.country_name} ({taxRate.country_code})
                  </div>
                  <div className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                    {taxRate.province_name ? `${taxRate.province_name} (${taxRate.province_code})` : '-'}
                  </div>
                  <div className={`text-sm font-mono ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                    {formatPercentage(taxRate.tax_rate)}
                  </div>
                  <div className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>{taxRate.tax_name || 'General Tax'}</div>
                  <div className="flex gap-2 mt-2">
                    <button className="inline-flex items-center gap-1 px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                      <EditIcon size={16} />
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteTaxRate(taxRate.id)}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                    >
                      <TrashIcon size={16} />
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {(pagination.pages > 1 || taxRates.length === LIMIT) && (
              <div className={`px-6 py-4 border-t ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} flex flex-wrap items-center justify-between gap-4`}>
                <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                  Showing {(pagination.page - 1) * pagination.per_page + 1}–{Math.min(pagination.page * pagination.per_page, pagination.total || taxRates.length)} of {pagination.total || taxRates.length} tax rates
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
                    disabled={taxRates.length < LIMIT}
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
          <div className={`p-6 text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>No tax rates found</div>
        )}
      </div>
    </div>
  );
};

export default AdminTaxRates;
