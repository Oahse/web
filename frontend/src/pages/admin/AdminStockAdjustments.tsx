import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';
import { StockAdjustmentResponse } from '../../types'; // Assuming StockAdjustmentResponse type exists
import { useParams } from 'react-router-dom';
import { Input } from '../../components/forms/Input';
import { Select } from '../../components/forms/Select';

export const AdminStockAdjustments = () => {
  const { inventoryId } = useParams<{ inventoryId?: string }>(); // Optional: if viewing adjustments for a specific item
  const [adjustments, setAdjustments] = useState<StockAdjustmentResponse[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    userId: '',
    reason: '',
    dateFrom: '',
    dateTo: '',
  });

  const { data: fetchedAdjustments, loading, error, execute: fetchAdjustments } = useApi<{
    total: number;
    page: number;
    limit: number;
    data: StockAdjustmentResponse[];
  }>();

  const loadAdjustments = useCallback(async () => {
    // AdminAPI.getStockAdjustments will be implemented later, assuming it can take inventoryId or global filters
    await fetchAdjustments(() => AdminAPI.getStockAdjustments({
      inventory_id: inventoryId || undefined, // Filter by specific inventory item if provided
      page: currentPage,
      limit: 10,
      user_id: filters.userId || undefined,
      reason: filters.reason || undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
    }));
  }, [currentPage, filters, inventoryId, fetchAdjustments]);

  useEffect(() => {
    loadAdjustments();
  }, [loadAdjustments]);

  useEffect(() => {
    if (fetchedAdjustments) {
      setAdjustments(fetchedAdjustments.data);
      setTotalPages(Math.ceil(fetchedAdjustments.total / fetchedAdjustments.limit));
    }
  }, [fetchedAdjustments]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleFilterChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value,
    }));
    setCurrentPage(1); // Reset to first page on new filter
  }, []);

  if (loading && !fetchedAdjustments) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorMessage error={error} onRetry={loadAdjustments} onDismiss={() => {}} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-main mb-6">Stock Adjustments {inventoryId ? `for Inventory Item ${inventoryId}` : ''}</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Only show User ID filter if not already filtered by inventory item */}
        {!inventoryId && (
            <Input
            label="Adjusted By User ID"
            name="userId"
            value={filters.userId}
            onChange={handleFilterChange}
            placeholder="Filter by User ID"
            />
        )}
        <Input
          label="Reason"
          name="reason"
          value={filters.reason}
          onChange={handleFilterChange}
          placeholder="Filter by Reason"
        />
        <Input
          label="Date From"
          name="dateFrom"
          type="date"
          value={filters.dateFrom}
          onChange={handleFilterChange}
        />
        <Input
          label="Date To"
          name="dateTo"
          type="date"
          value={filters.dateTo}
          onChange={handleFilterChange}
        />
      </div>

      {!adjustments || adjustments.length === 0 ? (
        <div className="text-center text-copy-light p-8">No stock adjustments found.</div>
      ) : (
        <div className="overflow-x-auto bg-surface rounded-lg shadow-sm">
          <table className="table w-full">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Inventory ID</th>
                <th>Change</th>
                <th>Reason</th>
                <th>Adjusted By</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {adjustments.map((adjustment) => (
                <tr key={adjustment.id}>
                  <td>{new Date(adjustment.created_at).toLocaleString()}</td>
                  <td>{adjustment.inventory_id}</td>
                  <td>{adjustment.quantity_change > 0 ? `+${adjustment.quantity_change}` : adjustment.quantity_change}</td>
                  <td>{adjustment.reason}</td>
                  <td>{adjustment.adjusted_by_user_id || 'N/A'}</td> {/* Display user name if available */}
                  <td>{adjustment.notes || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex justify-center mt-4">
          <div className="join">
            <button className="join-item btn" onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>«</button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button key={page} className={`join-item btn ${currentPage === page ? 'btn-active' : ''}`} onClick={() => handlePageChange(page)}>{page}</button>
            ))}
            <button className="join-item btn" onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages}>»</button>
          </div>
        </div>
      )}
    </div>
  );
};
