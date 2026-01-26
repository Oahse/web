import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeftIcon, PlusIcon, CalendarIcon, UserIcon, PackageIcon } from 'lucide-react';
import { usePaginatedApi, useApi } from '../../hooks/useAsync';
import { AdminAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { ResponsiveTable } from '../../components/ui/ResponsiveTable';
import { Pagination } from '../../components/ui/Pagination';

interface StockAdjustment {
  id: string;
  inventory_id: string;
  quantity_change: number;
  reason: string;
  notes?: string;
  adjusted_by?: {
    id: string;
    firstname: string;
    lastname: string;
    email: string;
  };
  created_at: string;
}

interface InventoryItem {
  id: string;
  variant_id: string;
  location_id: string;
  quantity: number;
  quantity_available: number;
  low_stock_threshold: number;
  variant?: {
    id: string;
    name: string;
    sku: string;
    product?: {
      id: string;
      name: string;
    };
  };
  location?: {
    id: string;
    name: string;
  };
}

export const AdminInventoryAdjustments = () => {
  const { inventoryId } = useParams<{ inventoryId: string }>();
  const [inventoryItem, setInventoryItem] = useState<InventoryItem | null>(null);

  const {
    loading: inventoryLoading,
    error: inventoryError,
    execute: fetchInventoryItem,
  } = useApi<{ data: InventoryItem }>();

  const apiCall = useCallback((page: number, limit: number) => {
    if (!inventoryId) return Promise.resolve({ data: [] });
    return AdminAPI.getStockAdjustments(inventoryId, { page, limit });
  }, [inventoryId]);

  const {
    data: adjustments,
    loading: adjustmentsLoading,
    error: adjustmentsError,
    execute: fetchAdjustments,
    page: currentPage,
    limit: itemsPerPage,
    totalPages,
    total: totalAdjustments,
    goToPage,
  } = usePaginatedApi(
    apiCall,
    1,
    10,
    { showErrorToast: false, autoFetch: true }
  );

  useEffect(() => {
    if (inventoryId) {
      // Fetch inventory item details
      fetchInventoryItem(AdminAPI.getInventoryItem, inventoryId).then((result) => {
        if (result?.data) {
          setInventoryItem(result.data);
        }
      });
    }
  }, [inventoryId, fetchInventoryItem]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatQuantityChange = (change: number) => {
    return change > 0 ? `+${change}` : change.toString();
  };

  if (inventoryError || adjustmentsError) {
    return (
      <div className="p-4 sm:p-6">
        <ErrorMessage
          error={inventoryError || adjustmentsError}
          onRetry={() => {
            if (inventoryId) {
              fetchInventoryItem(AdminAPI.getInventoryItem, inventoryId);
              fetchAdjustments();
            }
          }}
          onDismiss={() => {}}
        />
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 max-w-full">
      {/* Header */}
      <div className="mb-6 flex flex-col space-y-4 lg:flex-row lg:items-center lg:justify-between lg:space-y-0">
        <div className="flex items-center space-x-4">
          <Link
            to="/admin/inventory"
            className="flex items-center text-copy-light hover:text-main transition-colors"
          >
            <ArrowLeftIcon size={20} className="mr-2" />
            Back to Inventory
          </Link>
        </div>
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <Link
            to={`/admin/inventory/adjustments/new?inventory_id=${inventoryId}`}
            className="inline-flex items-center justify-center bg-primary hover:bg-primary-dark text-white px-3 py-2 sm:px-4 rounded-md transition-colors text-sm"
          >
            <PlusIcon size={16} className="mr-2" />
            New Adjustment
          </Link>
        </div>
      </div>

      {/* Inventory Item Info */}
      {inventoryItem && (
        <div className="bg-surface rounded-lg shadow-sm p-4 sm:p-6 mb-6 border border-border-light">
          <h2 className="text-lg font-semibold text-main mb-4">Inventory Item Details</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium text-copy-light">Product</label>
              <p className="text-main font-medium">
                {inventoryItem.variant?.product?.name || 'Unknown Product'}
              </p>
              <p className="text-sm text-copy-light">
                {inventoryItem.variant?.name || 'Default Variant'}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-copy-light">SKU</label>
              <p className="text-main font-mono text-sm">
                {inventoryItem.variant?.sku || '—'}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-copy-light">Location</label>
              <p className="text-main">
                {inventoryItem.location?.name || 'Unknown Location'}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-copy-light">Current Stock</label>
              <p className="text-main font-semibold text-lg">
                {inventoryItem.quantity_available || inventoryItem.quantity}
              </p>
              <p className="text-sm text-copy-light">
                Threshold: {inventoryItem.low_stock_threshold}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Stock Adjustments Table */}
      <div className="bg-surface rounded-lg shadow-sm border border-border-light overflow-hidden">
        <div className="p-4 sm:p-6 border-b border-border-light">
          <h2 className="text-lg font-semibold text-main">Stock Adjustment History</h2>
          <p className="text-sm text-copy-light mt-1">
            All stock adjustments for this inventory item
          </p>
        </div>

        <div className="overflow-x-auto">
          <ResponsiveTable
            data={adjustments || []}
            loading={inventoryLoading || adjustmentsLoading}
            keyExtractor={(item) => item.id}
            emptyMessage="No stock adjustments found"
            columns={[
              {
                key: 'date',
                label: 'Date',
                mobileLabel: 'Date',
                render: (item) => (
                  <div className="flex items-center text-sm">
                    <CalendarIcon size={16} className="mr-2 text-copy-light" />
                    {formatDate(item.created_at)}
                  </div>
                ),
              },
              {
                key: 'change',
                label: 'Quantity Change',
                mobileLabel: 'Change',
                render: (item) => (
                  <span
                    className={`font-semibold ${
                      item.quantity_change > 0
                        ? 'text-success'
                        : item.quantity_change < 0
                        ? 'text-warning'
                        : 'text-copy'
                    }`}
                  >
                    {formatQuantityChange(item.quantity_change)}
                  </span>
                ),
              },
              {
                key: 'reason',
                label: 'Reason',
                render: (item) => (
                  <span className="text-sm text-main capitalize">
                    {item.reason.replace(/_/g, ' ')}
                  </span>
                ),
              },
              {
                key: 'notes',
                label: 'Notes',
                hideOnMobile: true,
                render: (item) => (
                  <span className="text-sm text-copy-light">
                    {item.notes || '—'}
                  </span>
                ),
              },
              {
                key: 'adjusted_by',
                label: 'Adjusted By',
                hideOnMobile: true,
                render: (item) => (
                  <div className="flex items-center text-sm">
                    <UserIcon size={16} className="mr-2 text-copy-light" />
                    {item.adjusted_by
                      ? `${item.adjusted_by.firstname} ${item.adjusted_by.lastname}`
                      : 'System'}
                  </div>
                ),
              },
            ]}
          />
        </div>
      </div>

      {/* Pagination */}
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        totalItems={totalAdjustments || adjustments.length}
        itemsPerPage={itemsPerPage}
        onPageChange={goToPage}
        showingStart={(currentPage - 1) * itemsPerPage + 1}
        showingEnd={Math.min(currentPage * itemsPerPage, totalAdjustments || adjustments.length)}
        itemName="adjustments"
        className="mt-6"
      />

      {/* Summary Stats */}
      {adjustments.length > 0 && (
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-surface rounded-lg p-4 border border-border-light">
            <div className="flex items-center">
              <PackageIcon size={20} className="text-success mr-2" />
              <div>
                <p className="text-sm text-copy-light">Total Increases</p>
                <p className="text-lg font-semibold text-success">
                  +{adjustments
                    .filter((adj) => adj.quantity_change > 0)
                    .reduce((sum, adj) => sum + adj.quantity_change, 0)}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-surface rounded-lg p-4 border border-border-light">
            <div className="flex items-center">
              <PackageIcon size={20} className="text-warning mr-2" />
              <div>
                <p className="text-sm text-copy-light">Total Decreases</p>
                <p className="text-lg font-semibold text-warning">
                  {adjustments
                    .filter((adj) => adj.quantity_change < 0)
                    .reduce((sum, adj) => sum + adj.quantity_change, 0)}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-surface rounded-lg p-4 border border-border-light">
            <div className="flex items-center">
              <PackageIcon size={20} className="text-main mr-2" />
              <div>
                <p className="text-sm text-copy-light">Net Change</p>
                <p className="text-lg font-semibold text-main">
                  {formatQuantityChange(
                    adjustments.reduce((sum, adj) => sum + adj.quantity_change, 0)
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};