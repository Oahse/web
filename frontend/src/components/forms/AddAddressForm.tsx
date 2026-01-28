import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { AuthAPI } from '../../api/auth';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { X } from 'lucide-react';

interface AddAddressFormProps {
  onSuccess?: (address: any) => void;
  onCancel?: () => void;
  isModal?: boolean;
}

export const AddAddressForm: React.FC<AddAddressFormProps> = ({
  onSuccess,
  onCancel,
  isModal = false
}) => {
  const [formData, setFormData] = useState({
    street: '',
    city: '',
    state: '',
    country: 'US',
    post_code: '',
    kind: 'shipping',
    is_default: false
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors: any = {};

    if (!formData.street.trim()) {
      newErrors.street = 'Street address is required';
    }
    if (!formData.city.trim()) {
      newErrors.city = 'City is required';
    }
    if (!formData.state.trim()) {
      newErrors.state = 'State is required';
    }
    if (!formData.country.trim()) {
      newErrors.country = 'Country is required';
    }
    if (!formData.post_code.trim()) {
      newErrors.post_code = 'Postal code is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const response = await AuthAPI.createAddress(formData);
      
      if (response.success) {
        toast.success('Address added successfully!');
        onSuccess?.(response.data);
      } else {
        toast.error(response.message || 'Failed to add address');
      }
    } catch (error: any) {
      console.error('Error adding address:', error);
      toast.error(error?.response?.data?.message || 'Failed to add address');
    } finally {
      setLoading(false);
    }
  };

  const formContent = (
    <form onSubmit={handleSubmit} className="space-y-4">
      {isModal && (
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-copy">Add New Address</h2>
          <button
            type="button"
            onClick={onCancel}
            className="text-copy-light hover:text-copy"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      )}

      <div>
        <label htmlFor="street" className="block text-sm font-medium text-copy mb-1">
          Street Address *
        </label>
        <Input
          id="street"
          name="street"
          type="text"
          value={formData.street}
          onChange={handleChange}
          placeholder="123 Main Street"
          error={errors.street}
          required
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="city" className="block text-sm font-medium text-copy mb-1">
            City *
          </label>
          <Input
            id="city"
            name="city"
            type="text"
            value={formData.city}
            onChange={handleChange}
            placeholder="New York"
            error={errors.city}
            required
          />
        </div>

        <div>
          <label htmlFor="state" className="block text-sm font-medium text-copy mb-1">
            State/Province *
          </label>
          <Input
            id="state"
            name="state"
            type="text"
            value={formData.state}
            onChange={handleChange}
            placeholder="NY"
            error={errors.state}
            required
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="post_code" className="block text-sm font-medium text-copy mb-1">
            Postal Code *
          </label>
          <Input
            id="post_code"
            name="post_code"
            type="text"
            value={formData.post_code}
            onChange={handleChange}
            placeholder="10001"
            error={errors.post_code}
            required
          />
        </div>

        <div>
          <label htmlFor="country" className="block text-sm font-medium text-copy mb-1">
            Country *
          </label>
          <select
            id="country"
            name="country"
            value={formData.country}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary bg-surface text-copy"
            required
          >
            <option value="US">United States</option>
            <option value="CA">Canada</option>
            <option value="GB">United Kingdom</option>
            <option value="AU">Australia</option>
            <option value="DE">Germany</option>
            <option value="FR">France</option>
            <option value="IT">Italy</option>
            <option value="ES">Spain</option>
            <option value="JP">Japan</option>
            <option value="KR">South Korea</option>
          </select>
          {errors.country && (
            <p className="mt-1 text-sm text-error">{errors.country}</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="kind" className="block text-sm font-medium text-copy mb-1">
          Address Type
        </label>
        <select
          id="kind"
          name="kind"
          value={formData.kind}
          onChange={handleChange}
          className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary bg-surface text-copy"
        >
          <option value="shipping">Shipping</option>
          <option value="billing">Billing</option>
        </select>
      </div>

      <div className="flex items-center">
        <input
          id="is_default"
          name="is_default"
          type="checkbox"
          checked={formData.is_default}
          onChange={handleChange}
          className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
        />
        <label htmlFor="is_default" className="ml-2 block text-sm text-copy">
          Set as default address
        </label>
      </div>

      <div className="flex items-center justify-end space-x-3 pt-4">
        {onCancel && (
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </Button>
        )}
        <Button
          type="submit"
          isLoading={loading}
          disabled={loading}
        >
          {loading ? 'Adding...' : 'Add Address'}
        </Button>
      </div>
    </form>
  );

  if (isModal) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-surface rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto p-6">
          {formContent}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface rounded-lg shadow-sm border border-border p-6">
      <h2 className="text-xl font-semibold text-copy mb-6">Add New Address</h2>
      {formContent}
    </div>
  );
};

export default AddAddressForm;