import React, { useEffect, useState, useMemo } from 'react';
import { Loader, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import AdminAPI from '@/api/admin';
import toast from 'react-hot-toast';

const LIMIT = 10;

export const AdminShipping = () => {
  const [methods, setMethods] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    const fetchMethods = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await AdminAPI.getShippingMethods();
        const data = response?.data?.data || response?.data;
        setMethods(Array.isArray(data) ? data : data?.items || []);
      } catch (err: any) {
        const message = err?.response?.data?.message || 'Failed to load shipping methods';
        setError(message);
        toast.error(message);
      } finally {
        setLoading(false);
      }
    };

    fetchMethods();
  }, []);

  const total = methods.length;
  const pages = Math.max(1, Math.ceil(total / LIMIT));
  const paginatedMethods = useMemo(() => {
    const start = (page - 1) * LIMIT;
    return methods.slice(start, start + LIMIT);
  }, [methods, page]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader className="w-12 h-12 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-copy">Shipping Management</h1>
        <p className="text-copy-light mt-2">Manage shipping methods and rates</p>
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
          <h2 className="text-xl font-bold text-copy">Shipping Methods</h2>
        </div>

        {paginatedMethods.length > 0 ? (
          <>
            {/* Desktop table */}
            <div className="overflow-x-auto hidden md:block">
              <table className="w-full">
                <thead className="bg-surface-dark border-b border-border-light">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Method</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Carrier</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Base Rate</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Delivery Time</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Active</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedMethods.map((method) => (
                    <tr key={method.id} className="border-b border-border-light hover:bg-surface-light">
                      <td className="px-6 py-4 text-sm text-copy font-semibold">{method.name || 'N/A'}</td>
                      <td className="px-6 py-4 text-sm text-copy-light">{method.carrier_name || 'N/A'}</td>
                      <td className="px-6 py-4 text-sm font-semibold">${(method.base_rate || 0).toFixed(2)}</td>
                      <td className="px-6 py-4 text-sm text-copy-light">{method.estimated_delivery_days ?? '-'} days</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          method.is_active ? 'bg-success/20 text-success' : 'bg-warning/20 text-warning'
                        }`}>
                          {method.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="md:hidden divide-y divide-border-light">
              {paginatedMethods.map((method) => (
                <div
                  key={method.id}
                  className="p-4 flex flex-col gap-2 bg-surface hover:bg-surface-light transition"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-copy">{method.name || 'N/A'}</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      method.is_active ? 'bg-success/20 text-success' : 'bg-warning/20 text-warning'
                    }`}>
                      {method.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="text-sm text-copy-light">{method.carrier_name || 'N/A'}</div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-copy-light">{method.estimated_delivery_days ?? '-'} days</span>
                    <span className="font-semibold">${(method.base_rate || 0).toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>

            {pages > 1 && (
              <div className="px-6 py-4 border-t border-border-light flex flex-wrap items-center justify-between gap-4">
                <p className="text-sm text-copy-light">
                  Showing {(page - 1) * LIMIT + 1}–{Math.min(page * LIMIT, total)} of {total} methods
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
                    Page {page} of {pages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(pages, p + 1))}
                    disabled={page >= pages}
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
          <div className="p-6 text-center text-copy-light">No shipping methods found</div>
        )}
      </div>
    </div>
  );
};

export default AdminShipping;
