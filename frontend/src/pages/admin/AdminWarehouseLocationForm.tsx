import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';
import { WarehouseLocationCreate, WarehouseLocationUpdate, WarehouseLocationResponse } from '../../types';
import { useNavigate, useParams } from 'react-router-dom';
import { Input } from '../../components/forms/Input';
import { Textarea } from '../../components/forms/Textarea';

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
    return <LoadingSpinner />;
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
      <h1 className="text-2xl font-bold text-main mb-6">{isEditMode ? 'Edit' : 'Create'} Warehouse Location</h1>
      <form onSubmit={handleSubmit} className="bg-surface rounded-lg shadow-sm p-6 border border-border-light">
        <div className="grid grid-cols-1 gap-4 mb-6">
          <Input
            label="Location Name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />
          <Input
            label="Address"
            name="address"
            value={formData.address || ''}
            onChange={handleChange}
          />
          <Textarea
            label="Description"
            name="description"
            value={formData.description || ''}
            onChange={handleChange}
            rows={4}
          />
        </div>

        <div className="mt-6 text-right">
          <button
            type="button"
            className="btn btn-secondary mr-2"
            onClick={() => navigate('/admin/inventory/locations')}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
          >
            {submitting ? <LoadingSpinner size="sm" /> : (isEditMode ? 'Update Location' : 'Create Location')}
          </button>
        </div>
      </form>
    </div>
  );
};
