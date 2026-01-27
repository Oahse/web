import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../hooks/useAsync';
import { AdminAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';
import { WarehouseLocationCreate, WarehouseLocationUpdate, WarehouseLocationResponse } from '../../types';
import { useNavigate, useParams } from 'react-router-dom';
import { Input } from '../../components/forms/Input';
import { Textarea } from '../../components/forms/Textarea';
import { SkeletonForm } from '../../components/ui/SkeletonForm';

export const AdminWarehouseLocationForm = () => {
  const { locationId } = useParams<{ locationId?: string }>();
  const navigate = useNavigate();
  const [formData, setFormData] = useState<WarehouseLocationCreate | WarehouseLocationUpdate>({
    name: '',
    address: '',
    description: '',
  });
  const [isEditMode, setIsEditMode] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // API hooks for fetching and submitting
  const { data: fetchedLocation, loading, error, execute: fetchLocation } = useApi<WarehouseLocationResponse>();
  const { execute: submitLocation } = useApi<WarehouseLocationResponse>();

  useEffect(() => {
    if (locationId) {
      setIsEditMode(true);
      fetchLocation(() => AdminAPI.getWarehouseLocationById(locationId));
    } else {
      setIsEditMode(false);
    }
  }, [locationId, fetchLocation]);

  useEffect(() => {
    if (fetchedLocation) {
      setFormData({
        name: fetchedLocation.data.name,
        address: fetchedLocation.data.address || '',
        description: fetchedLocation.data.description || '',
      });
    }
  }, [fetchedLocation]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      let response: any;
      if (isEditMode && locationId) {
        response = await submitLocation(() => AdminAPI.updateWarehouseLocation(locationId, formData));
        toast.success('Warehouse location updated successfully!');
      } else {
        response = await submitLocation(() => AdminAPI.createWarehouseLocation(formData));
        toast.success('Warehouse location created successfully!');
      }
      navigate('/admin/inventory/locations'); // Redirect to location list
    } catch (err: any) {
      toast.error(`Failed to ${isEditMode ? 'update' : 'create'} location: ${err.message || 'Unknown error'}`);
    } finally {
      setSubmitting(false);
    }
  }, [isEditMode, locationId, formData, navigate, submitLocation]);

  if (loading) {
    return <SkeletonForm fields={4} />;
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorMessage error={error} onRetry={() => fetchLocation(() => AdminAPI.getWarehouseLocationById(locationId!))} onDismiss={() => {}} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-main mb-2">{isEditMode ? 'Edit' : 'Create'} Warehouse Location</h1>
        <p className="text-copy-lighter">
          {isEditMode ? 'Update the warehouse location details below.' : 'Add a new warehouse location to manage inventory across different sites.'}
        </p>
      </div>
      
      <form onSubmit={handleSubmit} className="bg-surface rounded-lg shadow-sm p-6 border border-border-light max-w-2xl">
        <div className="space-y-6 mb-6">
          <Input
            label="Location Name *"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="e.g., Main Warehouse, Distribution Center"
            required
          />
          <Input
            label="Address"
            name="address"
            value={formData.address || ''}
            onChange={handleChange}
            placeholder="Full address of the warehouse location"
          />
          <Textarea
            label="Description"
            name="description"
            value={formData.description || ''}
            onChange={handleChange}
            rows={4}
            placeholder="Optional description of the warehouse location, its purpose, or special notes..."
          />
        </div>

        <div className="flex items-center justify-between pt-6 border-t border-border-light">
          <button
            type="button"
            className="px-4 py-2 text-copy-lighter hover:text-copy border border-border rounded-md hover:bg-surface-hover transition-colors"
            onClick={() => navigate('/admin/inventory/locations')}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-6 py-2 bg-primary text-white rounded-md hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
            disabled={submitting}
          >
            {submitting ? (
              <>
                <div className="inline-block w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                {isEditMode ? 'Updating...' : 'Creating...'}
              </>
            ) : (
              isEditMode ? 'Update Location' : 'Create Location'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
export default AdminWarehouseLocationForm;