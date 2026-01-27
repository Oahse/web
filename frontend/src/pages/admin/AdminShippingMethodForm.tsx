import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeftIcon } from 'lucide-react';
import { AdminAPI } from '../../apis';
import { toast } from 'react-hot-toast';
import { Input } from '../../components/forms/Input';
import { Checkbox } from '../../components/forms/Checkbox';

interface ShippingMethodFormData {
  name: string;
  description: string;
  price: number;
  estimated_days: number;
  is_active: boolean;
}

export const AdminShippingMethodForm = () => {
  const navigate = useNavigate();
  const { methodId } = useParams<{ methodId: string }>();
  const isEditing = Boolean(methodId);

  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(isEditing);
  const [formData, setFormData] = useState<ShippingMethodFormData>({
    name: '',
    description: '',
    price: 0,
    estimated_days: 1,
    is_active: true,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Load existing shipping method data if editing
  useEffect(() => {
    if (isEditing && methodId) {
      loadShippingMethod();
    }
  }, [isEditing, methodId]);

  const loadShippingMethod = async () => {
    try {
      setInitialLoading(true);
      const response = await AdminAPI.getShippingMethod(methodId!);
      const method = response.data;
      
      setFormData({
        name: method.name,
        description: method.description,
        price: method.price,
        estimated_days: method.estimated_days,
        is_active: method.is_active,
      });
    } catch (error) {
      console.error('Failed to load shipping method:', error);
      toast.error('Failed to load shipping method');
      navigate('/admin/shipping-methods');
    } finally {
      setInitialLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (formData.price < 0) {
      newErrors.price = 'Price must be 0 or greater';
    }

    if (formData.estimated_days < 1) {
      newErrors.estimated_days = 'Estimated days must be at least 1';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);

      if (isEditing) {
        await AdminAPI.updateShippingMethod(methodId!, formData);
        toast.success('Shipping method updated successfully!');
      } else {
        await AdminAPI.createShippingMethod(formData);
        toast.success('Shipping method created successfully!');
      }

      navigate('/admin/shipping-methods');
    } catch (error: any) {
      console.error('Error saving shipping method:', error);
      toast.error(error?.message || 'Failed to save shipping method');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof ShippingMethodFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  if (initialLoading) {
    return (
      <div className="p-6">
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <button
        onClick={() => navigate('/admin/shipping-methods')}
        className="flex items-center text-copy-light hover:text-main mb-6"
      >
        <ArrowLeftIcon size={20} className="mr-2" />
        Back to Shipping Methods
      </button>

      <div className="max-w-2xl">
        <h1 className="text-2xl font-bold text-main mb-6">
          {isEditing ? 'Edit Shipping Method' : 'Create New Shipping Method'}
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="bg-surface p-6 rounded-lg border border-border-light">
            <h2 className="text-lg font-semibold text-main mb-4">Basic Information</h2>
            
            <div className="space-y-4">
              <Input
                label="Method Name"
                id="name"
                type="text"
                placeholder="e.g., Standard Shipping"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                error={errors.name}
                required
              />

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-main mb-1">
                  Description
                </label>
                <textarea
                  id="description"
                  rows={3}
                  placeholder="e.g., Standard delivery within 3-5 business days"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-copy ${
                    errors.description ? 'border-error' : 'border-border'
                  }`}
                  required
                />
                {errors.description && (
                  <p className="mt-1 text-sm text-error">{errors.description}</p>
                )}
              </div>
            </div>
          </div>

          <div className="bg-surface p-6 rounded-lg border border-border-light">
            <h2 className="text-lg font-semibold text-main mb-4">Pricing & Delivery</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Price ($)"
                id="price"
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                value={formData.price}
                onChange={(e) => handleInputChange('price', parseFloat(e.target.value) || 0)}
                error={errors.price}
                required
              />

              <Input
                label="Estimated Delivery Days"
                id="estimated_days"
                type="number"
                min="1"
                placeholder="1"
                value={formData.estimated_days}
                onChange={(e) => handleInputChange('estimated_days', parseInt(e.target.value) || 1)}
                error={errors.estimated_days}
                required
              />
            </div>
          </div>

          <div className="bg-surface p-6 rounded-lg border border-border-light">
            <h2 className="text-lg font-semibold text-main mb-4">Status</h2>
            
            <Checkbox
              label="Active"
              id="is_active"
              checked={formData.is_active}
              onChange={() => handleInputChange('is_active', !formData.is_active)}
              error={null}
              className="text-sm text-copy-light"
            />
            <p className="text-sm text-copy-light mt-1">
              Only active shipping methods will be available to customers
            </p>
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {isEditing ? 'Updating...' : 'Creating...'}
                </>
              ) : (
                isEditing ? 'Update Method' : 'Create Method'
              )}
            </button>
            
            <button
              type="button"
              onClick={() => navigate('/admin/shipping-methods')}
              className="px-6 py-2 border border-border text-copy hover:bg-surface-hover rounded-lg"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
export default AdminShippingMethodForm;