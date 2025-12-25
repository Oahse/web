import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';
import { InventoryUpdate, InventoryResponse } from '../../types';
import { useNavigate, useParams } from 'react-router-dom';
import { Input } from '../../components/forms/Input';

export const AdminInventoryItemForm = () => {
  const { inventoryId } = useParams<{ inventoryId: string }>(); // inventoryId is required for editing
  const navigate = useNavigate();
  const [formData, setFormData] = useState<InventoryUpdate>({
    quantity: undefined,
    low_stock_threshold: undefined,
  });
  const [submitting, setSubmitting] = useState(false);

  // API hooks for fetching and submitting
  const { data: fetchedInventoryItem, loading, error, execute: fetchInventoryItem } = useApi<InventoryResponse>();
  const { execute: submitInventoryItem } = useApi<InventoryResponse>();

  useEffect(() => {
    if (inventoryId) {
      fetchInventoryItem(() => AdminAPI.getInventoryItem(inventoryId));
    }
  }, [inventoryId, fetchInventoryItem]);

  useEffect(() => {
    if (fetchedInventoryItem) {
      setFormData({
        quantity: fetchedInventoryItem.data.quantity,
        low_stock_threshold: fetchedInventoryItem.data.low_stock_threshold,
      });
    }
  }, [fetchedInventoryItem]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: parseInt(value), // Convert to number for quantity and threshold
    }));
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (!inventoryId) {
        toast.error('Inventory item ID is missing.');
        return;
      }
      await submitInventoryItem(() => AdminAPI.updateInventoryItem(inventoryId, formData));
      toast.success('Inventory item updated successfully!');
      navigate('/admin/inventory'); // Redirect to inventory list
    } catch (err: any) {
      toast.error(`Failed to update inventory item: ${err.message || 'Unknown error'}`);
    } finally {
      setSubmitting(false);
    }
  }, [inventoryId, formData, navigate, submitInventoryItem]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorMessage error={error} onRetry={() => fetchInventoryItem(() => AdminAPI.getInventoryItem(inventoryId))} onDismiss={() => {}} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-main mb-6">Edit Inventory Item</h1>
      <form onSubmit={handleSubmit} className="bg-surface rounded-lg shadow-sm p-6 border border-border-light">
        <div className="grid grid-cols-1 gap-4 mb-6">
          <Input
            label="Quantity"
            name="quantity"
            type="number"
            value={formData.quantity}
            onChange={handleChange}
            required
          />
          <Input
            label="Low Stock Threshold"
            name="low_stock_threshold"
            type="number"
            value={formData.low_stock_threshold}
            onChange={handleChange}
            required
          />
        </div>

        <div className="mt-6 text-right">
          <button
            type="button"
            className="btn btn-secondary mr-2"
            onClick={() => navigate('/admin/inventory')}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
          >
            {submitting ? <LoadingSpinner size="sm" /> : 'Update Inventory'}
          </button>
        </div>
      </form>
    </div>
  );
};
