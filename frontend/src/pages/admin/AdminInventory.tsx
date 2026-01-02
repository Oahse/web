import React, { useState, useCallback, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { SearchIcon, FilterIcon, EditIcon, EyeIcon, PlusIcon, ChevronDownIcon, ChevronLeftIcon, ChevronRightIcon } from 'lucide-react';
import { usePaginatedApi, useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { ResponsiveTable } from '../../components/ui/ResponsiveTable';
import { PLACEHOLDER_IMAGES } from '../../utils/placeholderImage';

interface Product {
  id: string;
  name: string;
}

interface Location {
  id: string;
  name: string;
}

export const AdminInventory = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showMoreFilters, setShowMoreFilters] = useState(false);
  const [productId, setProductId] = useState('');
  const [locationId, setLocationId] = useState('');
  const [lowStock, setLowStock] = useState('all');
  const [products, setProducts] = useState<Product[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);

  // API hooks for fetching filter options
  const { execute: fetchProducts } = useApi<{ data: Product[] }>();
  const { execute: fetchLocations } = useApi<{ data: Location[] }>();

  const apiCall = useCallback((page: number, limit: number) => {
    return AdminAPI.getInventoryItems({
      page,
      limit,
      product_id: productId || undefined,
      location_id: locationId || undefined,
      low_stock: lowStock === 'true' ? true : lowStock === 'false' ? false : undefined,
      search: searchTerm || undefined,
    });
  }, [productId, locationId, lowStock, searchTerm]);

  const {
    data: inventoryItems,
    loading: inventoryLoading,
    error: inventoryError,
    execute: fetchInventory,
    page: currentPage,
    limit: itemsPerPage,
    totalPages,
    total,
    goToPage,
  } = usePaginatedApi(
    apiCall,
    1,
    10,
    { showErrorToast: false, autoFetch: true }
  );

  // Fetch products and locations for filter dropdowns
  useEffect(() => {
    const loadFilterOptions = async () => {
      try {
        // Fetch products
        const productsResult = await fetchProducts(AdminAPI.getAllProducts, { limit: 1000 });
        if (productsResult?.data) {
          const productList = Array.isArray(productsResult.data) ? productsResult.data : [];
          setProducts(productList.map(p => ({ id: p.id, name: p.name })));
        }

        // Fetch locations
        const locationsResult = await fetchLocations(AdminAPI.getWarehouseLocations);
        if (locationsResult?.data) {
          const locationList = Array.isArray(locationsResult.data) ? locationsResult.data : [];
          setLocations(locationList.map(l => ({ id: l.id, name: l.name })));
        }
      } catch (error) {
        console.error('Error loading filter options:', error);
      }
    };

    loadFilterOptions();
  }, [fetchProducts, fetchLocations]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    goToPage(1);
  };

  const handleFilterChange = () => {
    goToPage(1);
  };

  if (inventoryError) {
    return (
      <div className="p-4 sm:p-6">
        <ErrorMessage
          error={inventoryError}
          onRetry={() => fetchInventory()}
          onDismiss={() => {}}
        />
      </div>
    );
  }

  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, total || 0);

  // Generate page numbers for pagination
  const getPageNumbers = () => {
    const pages = [];
    const maxVisiblePages = 5;
    
    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      const start = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
      const end = Math.min(totalPages, start + maxVisiblePages - 1);
      
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
    }
    
    return pages;
  };

  return (
    <div className="p-4 sm:p-6 max-w-full">
      {/* Header */}
      <div className="mb-6 flex flex-col space-y-4 lg:flex-row lg:items-center lg:justify-between lg:space-y-0">
        <h1 className="text-xl sm:text-2xl font-bold text-main">Inventory Management</h1>
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <Link 
            to="/admin/inventory/adjustments/new" 
            className="inline-flex items-center justify-center bg-primary hover:bg-primary-dark text-white px-3 py-2 sm:px-4 rounded-md transition-colors text-sm"
          >
            <PlusIcon size={16} className="mr-2" />
            <span className="hidden sm:inline">Adjust Stock</span>
            <span className="sm:hidden">Adjust</span>
          </Link>
          <Link 
            to="/admin/inventory/locations" 
            className="inline-flex items-center justify-center bg-secondary hover:bg-secondary-dark text-white px-3 py-2 sm:px-4 rounded-md transition-colors text-sm"
          >
            <span className="hidden sm:inline">Manage Locations</span>
            <span className="sm:hidden">Locations</span>
          </Link>
        </div>
      </div>

      {/* Filters and search */}
      <div className="bg-surface rounded-lg shadow-sm p-4 mb-6 border border-border-light">
        <form onSubmit={handleSearch}>
          <div className="flex flex-col space-y-3 lg:flex-row lg:items-center lg:space-y-0 lg:space-x-4">
            <div className="flex-grow">
              <div className="relative">
                <input 
                  type="text" 
                  placeholder="Search inventory..." 
                  className="w-full pl-10 pr-4 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy text-sm" 
                  value={searchTerm} 
                  onChange={e => setSearchTerm(e.target.value)} 
                />
                <SearchIcon size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-copy-lighter" />
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
              <button 
                type="button" 
                onClick={() => setShowMoreFilters(!showMoreFilters)} 
                className="flex items-center justify-center px-3 py-2 border border-border rounded-md hover:bg-surface-hover text-copy text-sm"
              >
                <FilterIcon size={16} className="mr-2" />
                Filters
              </button>
              <button 
                type="submit" 
                className="flex items-center justify-center px-3 py-2 bg-primary text-white rounded-md hover:bg-primary-dark text-sm"
              >
                <SearchIcon size={16} className="mr-2" />
                Search
              </button>
            </div>
          </div>
        </form>
        
        {showMoreFilters && (
          <div className="mt-4 pt-4 border-t border-border-light">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="text-sm text-copy-light mb-1 block">Product</label>
                <div className="relative">
                  <select 
                    value={productId} 
                    onChange={e => {
                      setProductId(e.target.value);
                      handleFilterChange();
                    }}
                    className="appearance-none w-full pl-3 pr-10 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy text-sm"
                  >
                    <option value="">All Products</option>
                    {products.map(product => (
                      <option key={product.id} value={product.id}>
                        {product.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDownIcon size={16} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-copy-light pointer-events-none" />
                </div>
              </div>
              <div>
                <label className="text-sm text-copy-light mb-1 block">Location</label>
                <div className="relative">
                  <select 
                    value={locationId} 
                    onChange={e => {
                      setLocationId(e.target.value);
                      handleFilterChange();
                    }}
                    className="appearance-none w-full pl-3 pr-10 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy text-sm"
                  >
                    <option value="">All Locations</option>
                    {locations.map(location => (
                      <option key={location.id} value={location.id}>
                        {location.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDownIcon size={16} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-copy-light pointer-events-none" />
                </div>
              </div>
              <div className="sm:col-span-2 lg:col-span-1">
                <label className="text-sm text-copy-light mb-1 block">Stock Status</label>
                <div className="relative">
                  <select 
                    value={lowStock} 
                    onChange={e => {
                      setLowStock(e.target.value);
                      handleFilterChange();
                    }}
                    className="appearance-none w-full pl-3 pr-10 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy text-sm"
                  >
                    <option value="all">All Stock Levels</option>
                    <option value="true">Low Stock Only</option>
                    <option value="false">Sufficient Stock</option>
                  </select>
                  <ChevronDownIcon size={16} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-copy-light pointer-events-none" />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Inventory table */}
      <div className="bg-surface rounded-lg shadow-sm border border-border-light overflow-hidden">
        <div className="overflow-x-auto">
          <ResponsiveTable
            data={inventoryItems}
            loading={inventoryLoading}
            keyExtractor={(item) => item.id}
            emptyMessage="No inventory items found"
            columns={[
              {
                key: 'product',
                label: 'Product',
                mobileLabel: 'Product',
                render: (item) => (
                  <div className="flex items-center min-w-0">
                    <img 
                      src={item.variant?.primary_image?.url || item.variant?.images?.[0]?.url || PLACEHOLDER_IMAGES.small} 
                      alt={item.variant?.product?.name || 'Product'} 
                      className="w-8 h-8 sm:w-10 sm:h-10 rounded-md object-cover mr-2 sm:mr-3 flex-shrink-0"
                      onError={(e) => {
                        e.currentTarget.src = PLACEHOLDER_IMAGES.small;
                      }}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-main text-sm truncate">{item.variant?.product?.name || 'Product Name'}</p>
                      <p className="text-xs text-copy-light truncate">{item.variant?.name || 'Default Variant'}</p>
                    </div>
                  </div>
                ),
              },
              {
                key: 'sku',
                label: 'SKU',
                hideOnMobile: true,
                render: (item) => <span className="text-copy-light font-mono text-xs sm:text-sm">{item.variant?.sku || '—'}</span>,
              },
              {
                key: 'location',
                label: 'Location',
                render: (item) => <span className="text-copy-light text-sm">{item.location?.name || 'Default Location'}</span>,
              },
              {
                key: 'quantity',
                label: 'Qty',
                mobileLabel: 'Quantity',
                render: (item) => <span className="font-medium text-main text-sm">{item.quantity}</span>,
              },
              {
                key: 'threshold',
                label: 'Threshold',
                hideOnMobile: true,
                render: (item) => <span className="text-copy-light text-sm">{item.low_stock_threshold}</span>,
              },
              {
                key: 'status',
                label: 'Status',
                render: (item) => {
                  const isLowStock = item.quantity <= item.low_stock_threshold;
                  return (
                    <span className={`px-2 py-1 rounded-full text-xs whitespace-nowrap ${
                      isLowStock ? 'bg-warning/10 text-warning' : 'bg-success/10 text-success'
                    }`}>
                      {isLowStock ? 'Low Stock' : 'In Stock'}
                    </span>
                  );
                },
              },
              {
                key: 'actions',
                label: 'Actions',
                render: (item) => (
                  <div className="flex items-center justify-end space-x-1 sm:space-x-2">
                    <Link 
                      to={`/admin/inventory/${item.id}/adjustments`}
                      className="p-1 text-copy-light hover:text-main" 
                      title="View Adjustments"
                    >
                      <EyeIcon size={16} />
                    </Link>
                    <Link 
                      to={`/admin/inventory/edit/${item.id}`} 
                      className="p-1 text-copy-light hover:text-primary" 
                      title="Edit"
                    >
                      <EditIcon size={16} />
                    </Link>
                  </div>
                ),
              },
            ]}
          />
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex flex-col space-y-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <div className="text-sm text-copy-light text-center sm:text-left">
            Showing <span className="font-medium">{startIndex + 1}</span> to{' '}
            <span className="font-medium">{endIndex}</span> of{' '}
            <span className="font-medium">{total || 0}</span> items
          </div>
          
          <div className="flex items-center justify-center space-x-1 sm:space-x-2">
            {/* Previous button */}
            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="flex items-center px-2 py-1 sm:px-3 sm:py-1 border border-border rounded-md text-sm text-copy-light bg-background disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-hover"
            >
              <ChevronLeftIcon size={16} className="sm:mr-1" />
              <span className="hidden sm:inline">Previous</span>
            </button>
            
            {/* Page numbers */}
            <div className="flex items-center space-x-1">
              {getPageNumbers().map((pageNum) => (
                <button
                  key={pageNum}
                  onClick={() => goToPage(pageNum)}
                  className={`px-2 py-1 sm:px-3 sm:py-1 text-sm rounded-md min-w-[32px] ${
                    currentPage === pageNum
                      ? 'bg-primary text-white'
                      : 'border border-border text-copy hover:bg-surface-hover'
                  }`}
                >
                  {pageNum}
                </button>
              ))}
            </div>
            
            {/* Next button */}
            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="flex items-center px-2 py-1 sm:px-3 sm:py-1 border border-border rounded-md text-sm text-copy-light bg-background disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-hover"
            >
              <span className="hidden sm:inline">Next</span>
              <ChevronRightIcon size={16} className="sm:ml-1" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

