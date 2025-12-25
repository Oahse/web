import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorMessage from '../../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';
import { InventoryResponse, WarehouseLocationResponse, Product } from '../../types'; // Assuming types exist
import { Link } from 'react-router-dom';
import { Input } from '../../components/forms/Input';
import { Select } from '../../components/forms/Select';

export const AdminInventory = () => {
  const [inventoryItems, setInventoryItems] = useState<InventoryResponse[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    productId: '',
    locationId: '',
    lowStock: 'all', // 'all', 'true', 'false'
  });
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const [products, setProducts] = useState<Product[]>([]);
  const [locations, setLocations] = useState<WarehouseLocationResponse[]>([]);

  // API hooks
  const { data: fetchedInventory, loading: loadingInventory, error: inventoryError, execute: fetchInventory } = useApi<{
    total: number;
    page: number;
    limit: number;
    data: InventoryResponse[];
  }>();
  const { data: fetchedProducts, execute: fetchProducts } = useApi<{ data: Product[] }>();
  const { data: fetchedLocations, execute: fetchLocations } = useApi<WarehouseLocationResponse[]>();


  const loadInventory = useCallback(async () => {
    await fetchInventory(() => AdminAPI.getInventoryItems({
      page: currentPage,
      limit: 10,
      product_id: filters.productId || undefined,
      location_id: filters.locationId || undefined,
      low_stock: filters.lowStock === 'true' ? true : filters.lowStock === 'false' ? false : undefined,
    }));
  }, [currentPage, filters, fetchInventory]);

  const loadProductsAndLocations = useCallback(async () => {
    // Assuming AdminAPI has getAllProducts (with minimal data) and getWarehouseLocations
    await fetchProducts(() => AdminAPI.getAllProducts({ limit: 9999 })); // Fetch all products for filter dropdown
    await fetchLocations(AdminAPI.getWarehouseLocations);
  }, [fetchProducts, fetchLocations]);

  useEffect(() => {
    loadInventory();
  }, [loadInventory]);

  useEffect(() => {
    loadProductsAndLocations();
  }, [loadProductsAndLocations]);

  useEffect(() => {
    if (fetchedInventory) {
      setInventoryItems(fetchedInventory.data);
      setTotalPages(Math.ceil(fetchedInventory.total / fetchedInventory.limit));
    }
  }, [fetchedInventory]);

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

  const productOptions = products.map(p => ({ value: p.id, label: p.name }));
  const locationOptions = locations.map(l => ({ value: l.id, label: l.name }));

  if (loadingInventory || loadingProducts || loadingLocations) {
    return <LoadingSpinner />;
  }

  if (inventoryError) {
    return (
      <div className="p-6">
        <ErrorMessage error={inventoryError} onRetry={loadInventory} onDismiss={() => {}} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-main mb-6">Inventory Management</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Select
          label="Filter by Product"
          name="productId"
          value={filters.productId}
          onChange={handleFilterChange}
          options={[{ value: '', label: 'All Products' }, ...productOptions]}
        />
        <Select
          label="Filter by Location"
          name="locationId"
          value={filters.locationId}
          onChange={handleFilterChange}
          options={[{ value: '', label: 'All Locations' }, ...locationOptions]}
        />
        <Select
          label="Low Stock Status"
          name="lowStock"
          value={filters.lowStock}
          onChange={handleFilterChange}
          options={[
            { value: 'all', label: 'All' },
            { value: 'true', label: 'Low Stock' },
            { value: 'false', label: 'Sufficient Stock' },
          ]}
        />
      </div>

      <div className="flex justify-end mb-4">
        <Link to="/admin/inventory/adjustments/new" className="btn btn-primary mr-2">
          Adjust Stock
        </Link>
        <Link to="/admin/inventory/locations" className="btn btn-secondary">
          Manage Locations
        </Link>
      </div>

      {!inventoryItems || inventoryItems.length === 0 ? (
        <div className="text-center text-copy-light p-8">No inventory items found.</div>
      ) : (
        <div className="overflow-x-auto bg-surface rounded-lg shadow-sm">
          <table className="table w-full">
            <thead>
              <tr>
                <th>Product Name</th>
                <th>Variant Name</th>
                <th>SKU</th>
                <th>Location</th>
                <th>Quantity</th>
                <th>Threshold</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {inventoryItems.map((item) => (
                <tr key={item.id}>
                  <td>{item.variant?.product?.name || 'N/A'}</td>
                  <td>{item.variant?.name || 'N/A'}</td>
                  <td>{item.variant?.sku || 'N/A'}</td>
                  <td>{item.location?.name || 'N/A'}</td>
                  <td>{item.quantity}</td>
                  <td>{item.low_stock_threshold}</td>
                  <td>
                    <span className={`badge ${item.quantity <= item.low_stock_threshold ? 'badge-warning' : 'badge-success'}`}>
                      {item.quantity <= item.low_stock_threshold ? 'Low Stock' : 'In Stock'}
                    </span>
                  </td>
                  <td>
                    <Link to={`/admin/inventory/${item.id}/adjustments`} className="btn btn-sm btn-info mr-2">
                      View Adjustments
                    </Link>
                    <Link to={`/admin/inventory/edit/${item.id}`} className="btn btn-sm btn-secondary" disabled={loadingAction === item.id}>
                      Edit
                    </Link>
                  </td>
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
