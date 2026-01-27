import React, { useState, useCallback, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { SearchIcon, FilterIcon, EditIcon, TrashIcon, PlusIcon, TruckIcon } from 'lucide-react';
import { useApi } from '../../hooks/useAsync';
import { AdminAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { ResponsiveTable } from '../../components/ui/ResponsiveTable';
import { DeleteShippingMethodModal } from '../../components/admin/DeleteShippingMethodModal';
import { toast } from 'react-hot-toast';
import { useLocale } from '../../contexts/LocaleContext';

interface ShippingMethod {
  id: string;
  name: string;
  description: string;
  price: number;
  estimated_days: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const AdminShippingMethods = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [submittedSearchTerm, setSubmittedSearchTerm] = useState('');
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [shippingMethods, setShippingMethods] = useState<ShippingMethod[]>([]);
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    method: ShippingMethod | null;
  }>({
    isOpen: false,
    method: null,
  });
  const { formatCurrency } = useLocale();

  const { data, loading, error, execute } = useApi<{ data: ShippingMethod[] }>();

  const fetchShippingMethods = useCallback(async () => {
    const result = await execute(AdminAPI.getShippingMethods);
    if (result?.data) {
      setShippingMethods(result.data);
    }
  }, [execute]);

  useEffect(() => {
    fetchShippingMethods();
  }, [fetchShippingMethods]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedSearchTerm(searchTerm);
  };

  const handleDeleteShippingMethod = async (method: ShippingMethod) => {
    setDeleteModal({
      isOpen: true,
      method: method,
    });
  };

  const confirmDeleteShippingMethod = async () => {
    if (!deleteModal.method) return;

    const { id, name } = deleteModal.method;
    setLoadingAction(id);
    
    try {
      await AdminAPI.deleteShippingMethod(id);
      toast.success(`Shipping method "${name}" deleted successfully!`);
      await fetchShippingMethods();
      setDeleteModal({ isOpen: false, method: null });
    } catch (error) {
      console.error('Failed to delete shipping method:', error);
      toast.error('Failed to delete shipping method. Please try again.');
    } finally {
      setLoadingAction(null);
    }
  };

  const closeDeleteModal = () => {
    if (loadingAction) return; // Prevent closing while deleting
    setDeleteModal({ isOpen: false, method: null });
  };

  const filteredMethods = shippingMethods?.filter(method =>
    method.name.toLowerCase().includes(submittedSearchTerm.toLowerCase()) ||
    method.description.toLowerCase().includes(submittedSearchTerm.toLowerCase())
  ) || [];

  if (error) {
    return <ErrorMessage error={error} onRetry={fetchShippingMethods} onDismiss={() => {}} />;
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between">
        <h1 className="text-2xl font-bold text-main mb-2 md:mb-0">Shipping Methods</h1>
        <Link 
          to="/admin/shipping-methods/new" 
          className="inline-flex items-center bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-md transition-colors"
        >
          <PlusIcon size={18} className="mr-2" />
          Add Shipping Method
        </Link>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 bg-surface p-4 rounded-lg border border-border-light">
        <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <SearchIcon size={20} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-copy-lighter" />
              <input
                type="text"
                placeholder="Search shipping methods..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-border rounded-md focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-copy"
              />
            </div>
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark transition-colors flex items-center"
          >
            <SearchIcon size={18} className="mr-2" />
            Search
          </button>
        </form>
      </div>

      {/* Desktop Table */}
      <div className="hidden md:block">
        <div className="overflow-x-auto">
          <table className="w-full bg-surface rounded-lg border border-border-light">
            <thead className="bg-surface-hover">
              <tr>
                <th className="py-3 px-4 text-left font-medium text-main">Method</th>
                <th className="py-3 px-4 text-left font-medium text-main">Price</th>
                <th className="py-3 px-4 text-left font-medium text-main">Estimated Days</th>
                <th className="py-3 px-4 text-left font-medium text-main">Status</th>
                <th className="py-3 px-4 text-left font-medium text-main">Created</th>
                <th className="py-3 px-4 text-right font-medium text-main">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center">
                    <div className="flex justify-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                  </td>
                </tr>
              ) : filteredMethods.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-copy-light">
                    No shipping methods found
                  </td>
                </tr>
              ) : (
                filteredMethods.map((method: ShippingMethod) => (
                  <tr key={method.id} className="border-t border-border-light hover:bg-surface-hover">
                    <td className="py-3 px-4">
                      <div className="flex items-center">
                        <TruckIcon size={20} className="text-primary mr-3" />
                        <div>
                          <div className="font-medium text-main">{method.name}</div>
                          <div className="text-sm text-copy-light">{method.description}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-medium text-primary">
                        {formatCurrency(method.price)}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-copy">
                        {method.estimated_days} {method.estimated_days === 1 ? 'day' : 'days'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        method.is_active
                          ? 'bg-success/10 text-success'
                          : 'bg-error/10 text-error'
                      }`}>
                        {method.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-copy-light">
                      {new Date(method.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <Link 
                          to={`/admin/shipping-methods/edit/${method.id}`} 
                          className="p-1 text-copy-light hover:text-primary" 
                          title="Edit"
                        >
                          <EditIcon size={18} />
                        </Link>
                        <button
                          onClick={() => handleDeleteShippingMethod(method)}
                          disabled={loadingAction === method.id}
                          className="p-1 text-copy-light hover:text-error disabled:opacity-50"
                          title="Delete"
                        >
                          {loadingAction === method.id ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-error"></div>
                          ) : (
                            <TrashIcon size={18} />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden space-y-4">
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : filteredMethods.length === 0 ? (
          <div className="text-center py-8 text-copy-light">
            No shipping methods found
          </div>
        ) : (
          filteredMethods.map((method) => (
            <div key={method.id} className="bg-surface border border-border-light rounded-lg p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center">
                  <TruckIcon size={20} className="text-primary mr-3" />
                  <div>
                    <h3 className="font-medium text-main">{method.name}</h3>
                    <p className="text-sm text-copy-light">{method.description}</p>
                  </div>
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  method.is_active
                    ? 'bg-success/10 text-success'
                    : 'bg-error/10 text-error'
                }`}>
                  {method.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                <div>
                  <span className="text-copy-light">Price:</span>
                  <div className="font-medium text-primary">{formatCurrency(method.price)}</div>
                </div>
                <div>
                  <span className="text-copy-light">Delivery:</span>
                  <div className="text-copy">
                    {method.estimated_days} {method.estimated_days === 1 ? 'day' : 'days'}
                  </div>
                </div>
              </div>
              
              <div className="text-xs text-copy-light mb-3">
                Created: {new Date(method.created_at).toLocaleDateString()}
              </div>
              
              <div className="flex space-x-2 pt-2">
                <Link 
                  to={`/admin/shipping-methods/edit/${method.id}`} 
                  className="flex-1 text-center py-2 px-3 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/90"
                >
                  Edit
                </Link>
                <button
                  onClick={() => handleDeleteShippingMethod(method)}
                  disabled={loadingAction === method.id}
                  className="flex-1 text-center py-2 px-3 bg-error text-white rounded-md text-sm font-medium hover:bg-error/90 disabled:opacity-50"
                >
                  {loadingAction === method.id ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <DeleteShippingMethodModal
        isOpen={deleteModal.isOpen}
        onClose={closeDeleteModal}
        onConfirm={confirmDeleteShippingMethod}
        method={deleteModal.method}
        loading={loadingAction === deleteModal.method?.id}
      />
    </div>
  );
};
export default AdminShippingMethods;