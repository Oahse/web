import React, { useEffect, useState } from 'react';
import { Loader, AlertCircle, Plus, Edit, Trash2, ChevronLeft, ChevronRight, MapPin } from 'lucide-react';
import AdminAPI from '@/api/admin';
import toast from 'react-hot-toast';

const LIMIT = 20;

interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

interface WarehouseLocation {
  id: string;
  name: string;
  code: string;
  address: string;
  city: string;
  state: string;
  country: string;
  postal_code: string;
  phone?: string;
  email?: string;
  manager_name?: string;
  is_active: boolean;
  total_capacity?: number;
  current_capacity?: number;
  created_at: string;
  updated_at?: string;
}

export const AdminInventoryLocations = () => {
  const [locations, setLocations] = useState<WarehouseLocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState<PaginationInfo>({ 
    page: 1, 
    limit: LIMIT, 
    total: 0, 
    pages: 0 
  });

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await AdminAPI.getWarehouseLocations();
        const data = response?.data || response;
        setLocations(Array.isArray(data) ? data : []);
      } catch (err: any) {
        const message = err?.response?.data?.message || 'Failed to load warehouse locations';
        setError(message);
        toast.error(message);
      } finally {
        setLoading(false);
      }
    };

    fetchLocations();
  }, []);

  const statusBadge = (isActive: boolean) => {
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
        isActive ? 'bg-success/20 text-success' : 'bg-destructive/20 text-destructive'
      }`}>
        {isActive ? 'Active' : 'Inactive'}
      </span>
    );
  };

  const capacityBadge = (current?: number, total?: number) => {
    if (current === undefined || total === undefined) {
      return <span className="text-sm text-copy-light">N/A</span>;
    }
    
    const percentage = (current / total) * 100;
    const colorClass = 
      percentage >= 90 ? 'text-destructive' :
      percentage >= 75 ? 'text-warning' :
      percentage >= 50 ? 'text-blue' :
      'text-success';
    
    return (
      <span className={`text-sm font-medium ${colorClass}`}>
        {current}/{total} ({percentage.toFixed(1)}%)
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
          <h1 className="text-3xl font-bold text-copy">Warehouse Locations</h1>
          <p className="text-copy-light mt-2">Manage warehouse and storage locations</p>
        </div>
        <button className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors">
          <Plus className="w-4 h-4" />
          Add Location
        </button>
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
          <h2 className="text-xl font-bold text-copy">All Locations ({locations.length})</h2>
        </div>

        {locations.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-surface-dark border-b border-border-light">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Location</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Address</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Contact</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Capacity</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Status</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Created</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {locations.map((location) => (
                    <tr key={location.id} className="border-b border-border-light hover:bg-surface-light">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-primary/10 rounded-lg">
                            <MapPin className="w-4 h-4 text-primary" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-copy">{location.name}</p>
                            <p className="text-xs text-copy-light">Code: {location.code}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          <p className="text-copy">{location.address}</p>
                          <p className="text-copy-light">
                            {location.city}, {location.state} {location.postal_code}
                          </p>
                          <p className="text-copy-light">{location.country}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          {location.manager_name && (
                            <p className="text-copy font-medium">{location.manager_name}</p>
                          )}
                          {location.phone && (
                            <p className="text-copy-light">{location.phone}</p>
                          )}
                          {location.email && (
                            <p className="text-copy-light">{location.email}</p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {capacityBadge(location.current_capacity, location.total_capacity)}
                      </td>
                      <td className="px-6 py-4">
                        {statusBadge(location.is_active)}
                      </td>
                      <td className="px-6 py-4 text-sm text-copy-light">
                        {new Date(location.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex items-center gap-2">
                          <button className="p-1 text-blue hover:bg-blue/10 rounded transition-colors">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button className="p-1 text-destructive hover:bg-destructive/10 rounded transition-colors">
                            <Trash2 className="w-4 h-4" />
                          </button>
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
                Showing {locations.length} warehouse locations
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
                  disabled={locations.length < LIMIT}
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
              <MapPin className="w-12 h-12 text-copy-light/50" />
              <p>No warehouse locations found</p>
              <button className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors">
                <Plus className="w-4 h-4" />
                Add Your First Location
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminInventoryLocations;
