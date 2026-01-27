import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../hooks/useAsync';
import { AdminAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';
import { StockAdjustmentCreate, Product, WarehouseLocationResponse } from '../../types';
import { useNavigate } from 'react-router-dom';
import { Input } from '../../components/forms/Input';
import { Select } from '../../components/forms/Select';
import { Textarea } from '../../components/forms/Textarea';
import { SkeletonForm } from '../../components/ui/SkeletonForm';

interface ProductVariant {
  id: string;
  product_id: string;
  name: string;
  sku: string;
  base_price: number;
  sale_price?: number;
  is_active: boolean;
}

export const AdminInventoryAdjustmentForm = () => {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState<StockAdjustmentCreate>({
    variant_id: '',
    location_id: '',
    quantity_change: 0,
    reason: '',
    notes: '',
    product_id: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [locations, setLocations] = useState<WarehouseLocationResponse[]>([]);
  const [productVariants, setProductVariants] = useState<ProductVariant[]>([]);

  // API hooks
  const { data: fetchedProducts, loading: loadingProducts, error: productsError, execute: fetchProducts } = useApi<{ data: Product[] }>();
  const { data: fetchedLocations, loading: loadingLocations, error: locationsError, execute: fetchLocations } = useApi<any>();
  const { data: fetchedVariants, loading: loadingVariants, error: variantsError, execute: fetchVariants } = useApi<any>();
  const { execute: submitAdjustment } = useApi();

  // Function to fetch all products by making multiple paginated requests
  const fetchAllProducts = useCallback(async () => {
    try {
      let allProducts: Product[] = [];
      let page = 1;
      let hasMore = true;
      
      while (hasMore) {
        const response = await AdminAPI.getAllProducts({ limit: 100, page });
        // The response structure is { data: { data: [...products...], pagination: {...} } }
        const productsData = response.data?.data || response.data || [];
        
        // Ensure we have an array
        if (Array.isArray(productsData)) {
          allProducts = [...allProducts, ...productsData];
          // If we got less than 100 products, we've reached the end
          hasMore = productsData.length === 100;
        } else {
          // If it's not an array, we might have a different response structure
          console.warn('Unexpected response structure:', response);
          hasMore = false;
        }
        
        page++;
      }
      
      return { data: allProducts };
    } catch (error) {
      console.error('Error fetching products:', error);
      throw error;
    }
  }, []);

  useEffect(() => {
    fetchProducts(fetchAllProducts);
    fetchLocations(AdminAPI.getWarehouseLocations);
  }, [fetchProducts, fetchLocations, fetchAllProducts]);

  useEffect(() => {
    if (fetchedProducts) {
      setProducts(fetchedProducts.data || []);
    }
  }, [fetchedProducts]);

  useEffect(() => {
    if (fetchedLocations) {
      // Handle both direct array and wrapped response formats
      const locationsData = Array.isArray(fetchedLocations) ? fetchedLocations : fetchedLocations.data;
      setLocations(locationsData || []);
    }
  }, [fetchedLocations]);

  // Fetch variants when a product is selected
  useEffect(() => {
    if (formData.product_id) {
      fetchVariants(() => AdminAPI.getAllVariants({ product_id: formData.product_id }));
    } else {
      setProductVariants([]);
    }
  }, [formData.product_id, fetchVariants]);

  useEffect(() => {
    if (fetchedVariants) {
      // Handle the same nested structure as products: response.data.data
      const variantsData = fetchedVariants.data?.data || fetchedVariants.data || [];
      setProductVariants(Array.isArray(variantsData) ? variantsData : []);
    }
  }, [fetchedVariants]);

  useEffect(() => {
    if (productsError) {
      toast.error('Failed to load products');
    }
  }, [productsError]);

  useEffect(() => {
    if (locationsError) {
      toast.error('Failed to load warehouse locations');
    }
  }, [locationsError]);

  useEffect(() => {
    if (variantsError) {
      toast.error('Failed to load product variants');
    }
  }, [variantsError]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    // Handle numeric inputs
    if (name === 'quantity_change') {
      setFormData(prev => ({
        ...prev,
        [name]: parseInt(value) || 0,
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value,
      }));
    }

    // Reset variant selection when product changes
    if (name === 'product_id') {
      setFormData(prev => ({
        ...prev,
        variant_id: '',
      }));
    }
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      // Validation
      if (!formData.variant_id) {
        toast.error('Please select a product variant.');
        return;
      }
      if (!formData.location_id) {
        toast.error('Please select a location.');
        return;
      }
      if (formData.quantity_change === 0) {
        toast.error('Please enter a quantity change (positive or negative).');
        return;
      }
      if (!formData.reason.trim()) {
        toast.error('Please provide a reason for the adjustment.');
        return;
      }

      // Create adjustment data without product_id (backend doesn't need it)
      const adjustmentData = {
        variant_id: formData.variant_id,
        location_id: formData.location_id,
        quantity_change: formData.quantity_change,
        reason: formData.reason.trim(),
        notes: formData.notes?.trim() || undefined,
      };

      await submitAdjustment(() => AdminAPI.adjustStock(adjustmentData));
      toast.success('Stock adjusted successfully!');
      navigate('/admin/inventory');
    } catch (err: any) {
      console.error('Stock adjustment error:', err);
      toast.error(`Failed to adjust stock: ${err.message || 'Unknown error'}`);
    } finally {
      setSubmitting(false);
    }
  }, [formData, navigate, submitAdjustment]);

  const productOptions = Array.isArray(products) ? products.map(p => ({ value: p.id, label: p.name })) : [];
  const locationOptions = Array.isArray(locations) ? locations.map(l => ({ value: l.id, label: l.name })) : [];
  const variantOptions = Array.isArray(productVariants) ? productVariants.map(v => ({ 
    value: v.id, 
    label: `${v.name} (${v.sku})` 
  })) : [];

  if (loadingProducts || loadingLocations) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-main mb-2">Adjust Inventory Stock</h1>
          <p className="text-copy-lighter">Make adjustments to product inventory levels across different warehouse locations.</p>
        </div>
        <SkeletonForm fields={6} layout="grid" className="bg-surface rounded-lg shadow-sm p-6 border border-border-light" />
      </div>
    );
  }

  if (productsError || locationsError) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-main mb-2">Adjust Inventory Stock</h1>
          <p className="text-copy-lighter">Make adjustments to product inventory levels across different warehouse locations.</p>
        </div>
        <ErrorMessage
          error={productsError || locationsError}
          onRetry={() => { 
            fetchProducts(fetchAllProducts); 
            fetchLocations(AdminAPI.getWarehouseLocations); 
          }}
          onDismiss={() => {}}
        />
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-main mb-2">Adjust Inventory Stock</h1>
        <p className="text-copy-lighter">Make adjustments to product inventory levels across different warehouse locations.</p>
      </div>
      
      {/* Show helpful message if no data is available */}
      {!loadingProducts && !loadingLocations && products.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <p className="text-yellow-800">
            No products found. Please ensure you have products created before making inventory adjustments.
          </p>
        </div>
      )}
      
      {!loadingProducts && !loadingLocations && locations.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <p className="text-yellow-800">
            No warehouse locations found. Please create warehouse locations before making inventory adjustments.
          </p>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="bg-surface rounded-lg shadow-sm p-6 border border-border-light max-w-4xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="md:col-span-2">
            <Select
              label="Product *"
              name="product_id"
              value={formData.product_id}
              onChange={handleChange}
              options={[{ value: '', label: 'Select a product...' }, ...productOptions]}
              required
            />
          </div>
          
          <Select
            label="Product Variant *"
            name="variant_id"
            value={formData.variant_id}
            onChange={handleChange}
            options={[
              { 
                value: '', 
                label: formData.product_id ? 
                  (loadingVariants ? 'Loading variants...' : 
                   (variantOptions.length > 0 ? 'Select a variant...' : 'No variants found')) : 
                  'Select a product first' 
              }, 
              ...variantOptions
            ]}
            disabled={!formData.product_id || loadingVariants}
            required
          />
          
          <Select
            label="Warehouse Location *"
            name="location_id"
            value={formData.location_id}
            onChange={handleChange}
            options={[{ value: '', label: 'Select a location...' }, ...locationOptions]}
            required
          />
          
          <Input
            label="Quantity Change *"
            name="quantity_change"
            type="number"
            value={formData.quantity_change}
            onChange={handleChange}
            placeholder="Enter positive or negative number"
            helperText="Use positive numbers to increase stock, negative to decrease"
            required
          />
          
          <Input
            label="Reason for Adjustment *"
            name="reason"
            value={formData.reason}
            onChange={handleChange}
            placeholder="e.g., Damaged goods, Restock, Inventory correction"
            required
          />
          
          <div className="md:col-span-2">
            <Textarea
              label="Additional Notes"
              name="notes"
              value={formData.notes || ''}
              onChange={handleChange}
              rows={3}
              placeholder="Optional additional details about this adjustment..."
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-6 border-t border-border-light">
          <button
            type="button"
            className="px-4 py-2 text-copy-lighter hover:text-copy border border-border rounded-md hover:bg-surface-hover transition-colors"
            onClick={() => navigate('/admin/inventory')}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-6 py-2 bg-primary text-white rounded-md hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
            disabled={submitting || products.length === 0 || locations.length === 0}
          >
            {submitting ? (
              <>
                <div className="inline-block w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Processing...
              </>
            ) : (
              'Submit Adjustment'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
export default AdminInventoryAdjustmentForm;