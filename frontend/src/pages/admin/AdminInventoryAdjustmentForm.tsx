import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';
import { StockAdjustmentCreate, Product, WarehouseLocationResponse, InventoryResponse } from '../../types';
import { useNavigate } from 'react-router-dom';
import { Input } from '../../components/forms/Input';
import { Select } from '../../components/forms/Select';
import { Textarea } from '../../components/forms/Textarea';

export const AdminInventoryAdjustmentForm = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<StockAdjustmentCreate>({
    variant_id: undefined,
    location_id: undefined,
    quantity_change: 0,
    reason: '',
    notes: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const [products, setProducts] = useState<Product[]>([]);
  const [locations, setLocations] = useState<WarehouseLocationResponse[]>([]);
  const [productVariants, setProductVariants] = useState<InventoryResponse['variant'][]>([]);

  // API hooks
  const { data: fetchedProducts, loading: loadingProducts, error: productsError, execute: fetchProducts } = useApi<{ data: Product[] }>();
  const { data: fetchedLocations, loading: loadingLocations, error: locationsError, execute: fetchLocations } = useApi<WarehouseLocationResponse[]>();
  const { data: fetchedVariants, loading: loadingVariants, error: variantsError, execute: fetchVariants } = useApi<InventoryResponse['variant'][]>();
  const { execute: submitAdjustment } = useApi<InventoryResponse>();


  useEffect(() => {
    fetchProducts(() => AdminAPI.getAllProducts({ limit: 9999 }));
    fetchLocations(AdminAPI.getWarehouseLocations);
  }, [fetchProducts, fetchLocations]);

  useEffect(() => {
    if (fetchedProducts) {
      setProducts(fetchedProducts.data);
    }
  }, [fetchedProducts]);

  useEffect(() => {
    if (fetchedLocations) {
      setLocations(fetchedLocations.data);
    }
  }, [fetchedLocations]);

  // Fetch variants when a product is selected
  useEffect(() => {
    if (formData.product_id) {
        // Find the product based on the selected variant's product_id
        // This is a simplification; ideally, we'd fetch variants directly for the selected product.
        // For now, let's assume we fetch all variants and filter.
        // AdminAPI.getAllVariants should ideally return variants with product_id.
        // Let's call AdminAPI.getAllVariants and then filter by product_id in the frontend
        fetchVariants(() => AdminAPI.getAllVariants({ product_id: formData.product_id }));
    } else {
        setProductVariants([]);
    }
  }, [formData.product_id, fetchVariants]);

  useEffect(() => {
    if (fetchedVariants) {
        setProductVariants(fetchedVariants.data);
    }
  }, [fetchedVariants]);


  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value === '' ? undefined : value, // Convert empty strings to undefined for UUIDs
    }));
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (!formData.variant_id || !formData.location_id || formData.quantity_change === 0 || !formData.reason) {
        toast.error('Please fill all required fields.');
        return;
      }
      await submitAdjustment(() => AdminAPI.adjustStock(formData));
      toast.success('Stock adjusted successfully!');
      navigate('/admin/inventory');
    } catch (err: any) {
      toast.error(`Failed to adjust stock: ${err.message || 'Unknown error'}`);
    } finally {
      setSubmitting(false);
    }
  }, [formData, navigate, submitAdjustment]);

  const productOptions = products.map(p => ({ value: p.id, label: p.name }));
  const locationOptions = locations.map(l => ({ value: l.id, label: l.name }));
  const variantOptions = productVariants
    .filter(v => v.product_id === formData.product_id) // Filter variants by selected product
    .map(v => ({ value: v.id, label: v.name }));


  if (loadingProducts || loadingLocations || loadingVariants) {
    return <LoadingSpinner />;
  }

  if (productsError || locationsError || variantsError) {
    return (
      <div className="p-6">
        <ErrorMessage
          error={productsError || locationsError || variantsError}
          onRetry={() => { fetchProducts(() => AdminAPI.getAllProducts({ limit: 9999 })); fetchLocations(AdminAPI.getWarehouseLocations); }}
          onDismiss={() => {}}
        />
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-main mb-6">Adjust Inventory Stock</h1>
      <form onSubmit={handleSubmit} className="bg-surface rounded-lg shadow-sm p-6 border border-border-light">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <Select
            label="Product"
            name="product_id"
            value={formData.product_id || ''}
            onChange={handleChange}
            options={[{ value: '', label: 'Select Product' }, ...productOptions]}
            required
          />
          <Select
            label="Product Variant"
            name="variant_id"
            value={formData.variant_id || ''}
            onChange={handleChange}
            options={[{ value: '', label: 'Select Variant' }, ...variantOptions]}
            disabled={!formData.product_id || variantOptions.length === 0}
            required
          />
          <Select
            label="Location"
            name="location_id"
            value={formData.location_id || ''}
            onChange={handleChange}
            options={[{ value: '', label: 'Select Location' }, ...locationOptions]}
            required
          />
          <Input
            label="Quantity Change"
            name="quantity_change"
            type="number"
            value={formData.quantity_change}
            onChange={handleChange}
            required
          />
          <Input
            label="Reason for Adjustment"
            name="reason"
            value={formData.reason}
            onChange={handleChange}
            required
          />
          <Textarea
            label="Notes"
            name="notes"
            value={formData.notes || ''}
            onChange={handleChange}
            rows={3}
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
            {submitting ? <LoadingSpinner size="sm" /> : 'Submit Adjustment'}
          </button>
        </div>
      </form>
    </div>
  );
};
