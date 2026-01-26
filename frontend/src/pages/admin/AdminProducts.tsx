import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { PlusIcon, SearchIcon, FilterIcon, EditIcon, TrashIcon, ChevronDownIcon, EyeIcon, MoreHorizontalIcon } from 'lucide-react';
import { usePaginatedApi } from '../../hooks/useAsync';
import { AdminAPI } from '../../apis';
import { useCategories } from '../../contexts/CategoryContext';
import ErrorMessage from '../../components/common/ErrorMessage';
import { ResponsiveTable } from '../../components/ui/ResponsiveTable';
import { Pagination } from '../../components/ui/Pagination';
import { PLACEHOLDER_IMAGES } from '../../utils/placeholderImage';

export const AdminProducts = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [submittedSearchTerm, setSubmittedSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [showMoreFilters, setShowMoreFilters] = useState(false);
  const [status, setStatus] = useState('all');
  const [supplier, setSupplier] = useState('');

  const apiCall = useCallback((page: number, limit: number) => {
    return AdminAPI.getAllProducts({
      search: submittedSearchTerm || undefined,
      category: filterCategory !== 'all' ? filterCategory : undefined,
      status: status !== 'all' ? status : undefined,
      supplier: supplier || undefined,
      page,
      limit,
    });
  }, [submittedSearchTerm, filterCategory, status, supplier]);

  // API calls
  const {
    data: products,
    loading: productsLoading,
    error: productsError,
    execute: fetchProducts,
    page: currentPage,
    limit: itemsPerPage,
    totalPages,
    total: totalProducts,
    goToPage,
  } = usePaginatedApi(
    apiCall,
    1,
    10,
    { showErrorToast: false, autoFetch: true }
  );

  const { categories: categoriesData } = useCategories();

  const categories = categoriesData ? [
    { id: 'all', name: 'All Categories' },
    ...(categoriesData as any[]).map((cat: any) => ({ id: cat.name, name: cat.name }))
  ] : [];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedSearchTerm(searchTerm);
    goToPage(1); // Reset to first page when searching
  };

  if (productsError) {
    return (
      <div className="p-6">
        <ErrorMessage
          error={productsError}
          onRetry={() => fetchProducts()}
          onDismiss={() => {}}
        />
      </div>
    );
  }

  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalProducts || products.length);

  return <div>
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between">
        <h1 className="text-2xl font-bold text-main mb-2 md:mb-0">Products</h1>
        <Link to="/admin/products/new" className="inline-flex items-center bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-md transition-colors">
          <PlusIcon size={18} className="mr-2" />
          Add Product
        </Link>
      </div>
      {/* Filters and search */}
      <div className="bg-surface rounded-lg shadow-sm p-4 mb-6 border border-border-light">
        <form onSubmit={handleSearch}>
          <div className="flex flex-col md:flex-row md:items-center space-y-3 md:space-y-0 md:space-x-4">
            <div className="flex-grow">
              <div className="relative">
                <input 
                  type="text" 
                  placeholder="Search products..." 
                  className="w-full pl-10 pr-4 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" 
                  value={searchTerm} 
                  onChange={e => setSearchTerm(e.target.value)} 
                />
                <SearchIcon size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-copy-lighter" />
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="relative">
                <select value={filterCategory} onChange={e => setFilterCategory(e.target.value)} className="appearance-none pl-3 pr-10 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy">
                  {categories.map(category => <option key={category.id} value={category.id}>
                      {category.name}
                    </option>)}
                </select>
                <ChevronDownIcon size={16} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-copy-light pointer-events-none" />
              </div>
              <button type="button" onClick={() => setShowMoreFilters(!showMoreFilters)} className="flex items-center px-3 py-2 border border-border rounded-md hover:bg-surface-hover text-copy">
                <FilterIcon size={18} className="mr-2" />
                More Filters
              </button>
              <button type="submit" className="flex items-center px-3 py-2 bg-primary text-white rounded-md hover:bg-primary-dark">
                <SearchIcon size={18} className="mr-2" />
                Search
              </button>
            </div>
          </div>
        </form>
        {showMoreFilters && (
          <div className="mt-4 pt-4 border-t border-border-light">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-copy-light mb-1 block">Status</label>
                <select value={status} onChange={e => setStatus(e.target.value)} className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy">
                  <option value="all">All Statuses</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="pending">Pending</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-copy-light mb-1 block">Supplier</label>
                <input type="text" placeholder="Supplier ID or name" className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" value={supplier} onChange={e => setSupplier(e.target.value)} />
              </div>
            </div>
          </div>
        )}
      </div>
      {/* Products table */}
      <div className="bg-surface rounded-lg shadow-sm border border-border-light overflow-hidden">
        <ResponsiveTable
          data={products || []}
          loading={productsLoading}
          keyExtractor={(product) => product.id}
          emptyMessage="No products found"
          onRowClick={(product) => navigate(`/admin/products/${product.id}`)}
          columns={[
            {
              key: 'product',
              label: 'Product',
              mobileLabel: 'Product',
              render: (product) => {
                const primaryVariant = product.primary_variant || product.variants?.[0];
                const imageUrl = primaryVariant?.primary_image?.url || 
                               primaryVariant?.images?.[0]?.url || 
                               PLACEHOLDER_IMAGES.small;
                return (
                  <div className="flex items-center">
                    <div className="relative w-12 h-12 mr-3 flex-shrink-0">
                      <img 
                        src={imageUrl} 
                        alt={product.name} 
                        className="w-full h-full rounded-md object-cover border border-border-light" 
                        onError={(e) => {
                          e.currentTarget.src = PLACEHOLDER_IMAGES.small;
                        }}
                        onLoad={(e) => {
                          // Remove any loading state if needed
                          e.currentTarget.classList.remove('opacity-50');
                        }}
                        style={{ 
                          backgroundColor: '#f3f4f6',
                          minHeight: '48px',
                          minWidth: '48px'
                        }}
                      />
                      {/* Loading overlay */}
                      {!imageUrl.startsWith('data:') && (
                        <div className="absolute inset-0 bg-surface-hover animate-pulse rounded-md opacity-0 transition-opacity duration-200" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-main truncate">{product.name}</p>
                      <p className="text-xs text-copy-light truncate">
                        {product.short_description && product.short_description.length > 50 
                          ? `${product.short_description.substring(0, 50)}...` 
                          : product.short_description || `ID: ${product.id.substring(0, 8)}...`}
                      </p>
                    </div>
                  </div>
                );
              },
            },
            {
              key: 'sku',
              label: 'SKU',
              hideOnMobile: true,
              render: (product) => {
                const primaryVariant = product.primary_variant || product.variants?.[0];
                return (
                  <span className="text-copy-light font-mono text-sm">
                    {primaryVariant?.sku || 'N/A'}
                  </span>
                );
              },
            },
            {
              key: 'category',
              label: 'Category',
              render: (product) => (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-surface-hover text-copy">
                  {product.category?.name || 'Uncategorized'}
                </span>
              ),
            },
            {
              key: 'price',
              label: 'Price',
              render: (product) => {
                const primaryVariant = product.primary_variant || product.variants?.[0];
                if (!primaryVariant) {
                  return <span className="text-copy-light">N/A</span>;
                }
                
                const hasDiscount = primaryVariant.sale_price && primaryVariant.sale_price < primaryVariant.base_price;
                
                return (
                  <div className="text-right">
                    {hasDiscount ? (
                      <div>
                        <span className="font-medium text-success">
                          ${primaryVariant.sale_price.toFixed(2)}
                        </span>
                        <div className="text-xs text-copy-light line-through">
                          ${primaryVariant.base_price.toFixed(2)}
                        </div>
                      </div>
                    ) : (
                      <span className="font-medium text-main">
                        ${primaryVariant.base_price?.toFixed(2) || '0.00'}
                      </span>
                    )}
                    {product.min_price !== product.max_price && (
                      <div className="text-xs text-copy-light">
                        ${product.min_price?.toFixed(2)} - ${product.max_price?.toFixed(2)}
                      </div>
                    )}
                  </div>
                );
              },
            },
            {
              key: 'stock',
              label: 'Stock',
              render: (product) => {
                const totalStock = product.total_stock || 0;
                return (
                  <div className="text-center">
                    <span className={`font-medium ${
                      totalStock === 0 ? 'text-error' : 
                      totalStock <= 10 ? 'text-warning' : 
                      'text-success'
                    }`}>
                      {totalStock}
                    </span>
                    <div className="text-xs text-copy-light">units</div>
                  </div>
                );
              },
            },
            {
              key: 'status',
              label: 'Status',
              render: (product) => {
                const stockStatus = product.stock_status || 'unknown';
                const isActive = product.is_active && product.product_status === 'active';
                
                let status, colorClass;
                
                if (!isActive) {
                  status = 'Inactive';
                  colorClass = 'bg-gray-100 text-gray-600';
                } else {
                  switch (stockStatus) {
                    case 'in_stock':
                      status = 'In Stock';
                      colorClass = 'bg-success/10 text-success';
                      break;
                    case 'low_stock':
                      status = 'Low Stock';
                      colorClass = 'bg-warning/10 text-warning';
                      break;
                    case 'out_of_stock':
                      status = 'Out of Stock';
                      colorClass = 'bg-error/10 text-error';
                      break;
                    default:
                      status = 'Unknown';
                      colorClass = 'bg-gray-100 text-gray-600';
                  }
                }
                
                return (
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${colorClass}`}>
                    {status}
                  </span>
                );
              },
            },
            {
              key: 'variants',
              label: 'Variants',
              hideOnMobile: true,
              render: (product) => (
                <div className="text-center">
                  <Link 
                    to={`/admin/products/${product.id}/variants`} 
                    className="inline-flex items-center px-2 py-1 text-xs bg-primary/10 text-primary rounded-md hover:bg-primary/20 transition-colors"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {product.variants?.length || 0} variant{(product.variants?.length || 0) !== 1 ? 's' : ''}
                  </Link>
                </div>
              ),
            },
            {
              key: 'actions',
              label: 'Actions',
              render: (product) => (
                <div className="flex items-center justify-end space-x-2">
                  <Link 
                    to={`/admin/products/${product.id}`} 
                    className="p-1 text-copy-light hover:text-main" 
                    title="View"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <EyeIcon size={18} />
                  </Link>
                  <Link 
                    to={`/admin/products/${product.id}/edit`} 
                    className="p-1 text-copy-light hover:text-primary" 
                    title="Edit"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <EditIcon size={18} />
                  </Link>
                  <button 
                    className="p-1 text-copy-light hover:text-error" 
                    title="Delete"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <TrashIcon size={18} />
                  </button>
                </div>
              ),
            },
          ]}
        />
      </div>
      {/* Pagination */}
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        totalItems={totalProducts || products.length}
        itemsPerPage={itemsPerPage}
        onPageChange={goToPage}
        showingStart={startIndex + 1}
        showingEnd={endIndex}
        itemName="products"
        className="mt-6"
      />
    </div>;
};