import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { SearchIcon, FilterIcon, EditIcon, TrashIcon, MoreHorizontalIcon, PlusIcon, EyeIcon } from 'lucide-react';
import { usePaginatedApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { ResponsiveTable } from '../../components/ui/ResponsiveTable';

export const AdminVariants = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [submittedSearchTerm, setSubmittedSearchTerm] = useState('');
  const [showMoreFilters, setShowMoreFilters] = useState(false);
  const [productId, setProductId] = useState('');

  const apiCall = useCallback((page: number, limit: number) => {
    return AdminAPI.getAllVariants({
      search: submittedSearchTerm || undefined,
      product_id: productId || undefined,
      page,
      limit,
    });
  }, [submittedSearchTerm, productId]);

  const {
    data: variants,
    loading: variantsLoading,
    error: variantsError,
    execute: fetchVariants,
    page: currentPage,
    limit: itemsPerPage,
    totalPages,
    goToPage,
  } = usePaginatedApi(
    apiCall,
    1,
    10,
    { showErrorToast: false, autoFetch: true }
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedSearchTerm(searchTerm);
    goToPage(1); // Reset to first page when searching
  };

  if (variantsError) {
    return (
      <div className="p-6">
        <ErrorMessage
          error={variantsError}
          onRetry={() => fetchVariants()}
          onDismiss={() => {}}
        />
      </div>
    );
  }

  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, variants.length);

  return (
    <div>
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between">
        <h1 className="text-2xl font-bold text-main mb-2 md:mb-0">Product Variants</h1>
        <Link to="/admin/products/new-variant" className="inline-flex items-center bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-md transition-colors">
          <PlusIcon size={18} className="mr-2" />
          Add Variant
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
                  placeholder="Search variants by SKU or name..." 
                  className="w-full pl-10 pr-4 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" 
                  value={searchTerm} 
                  onChange={e => setSearchTerm(e.target.value)} 
                />
                <SearchIcon size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-copy-lighter" />
              </div>
            </div>
            <div className="flex items-center space-x-3">
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
                <label className="text-sm text-copy-light mb-1 block">Product ID</label>
                <input type="text" placeholder="Product ID" className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" value={productId} onChange={e => setProductId(e.target.value)} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Variants table */}
      <div className="bg-surface rounded-lg shadow-sm border border-border-light overflow-hidden">
        <ResponsiveTable
          data={variants}
          loading={variantsLoading}
          keyExtractor={(variant) => variant.id}
          emptyMessage="No product variants found"
          columns={[
            {
              key: 'variant',
              label: 'Variant',
              mobileLabel: 'Variant',
              render: (variant) => (
                <div className="flex items-center">
                  <img 
                    src={variant.primary_image?.url || 'https://via.placeholder.com/100'} 
                    alt={variant.name} 
                    className="w-10 h-10 rounded-md object-cover mr-3" 
                  />
                  <div>
                    <p className="font-medium text-main">{variant.name}</p>
                    <p className="text-xs text-copy-light">SKU: {variant.sku}</p>
                  </div>
                </div>
              ),
            },
            {
              key: 'product',
              label: 'Product',
              render: (variant) => (
                <Link 
                  to={`/admin/products/${variant.product_id}`}
                  className="text-primary hover:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  {variant.product_name || 'N/A'}
                </Link>
              ),
            },
            {
              key: 'sku',
              label: 'SKU',
              hideOnMobile: true,
              render: (variant) => <span className="text-copy-light">{variant.sku}</span>,
            },
            {
              key: 'price',
              label: 'Price',
              render: (variant) => variant.sale_price ? (
                <div>
                  <span className="font-medium text-main">${variant.sale_price.toFixed(2)}</span>
                  <span className="text-xs text-copy-light line-through ml-2">${variant.base_price.toFixed(2)}</span>
                </div>
              ) : (
                <span className="font-medium text-main">${variant.base_price.toFixed(2)}</span>
              ),
            },
            {
              key: 'stock',
              label: 'Stock',
              render: (variant) => <span className="text-copy-light">{variant.stock}</span>,
            },
            {
              key: 'status',
              label: 'Status',
              render: (variant) => (
                <span className={`px-2 py-1 rounded-full text-xs ${
                  variant.is_active && variant.stock > 0 ? 'bg-success/10 text-success' :
                  variant.stock <= 0 ? 'bg-error/10 text-error' :
                  'bg-warning/10 text-warning'
                }`}>
                  {variant.is_active && variant.stock > 0 ? 'Active' : variant.stock <= 0 ? 'Out of Stock' : 'Inactive'}
                </span>
              ),
            },
            {
              key: 'actions',
              label: 'Actions',
              render: (variant) => (
                <div className="flex items-center justify-end space-x-2">
                  <Link 
                    to={`/admin/products/${variant.product_id}`}
                    className="p-1 text-copy-light hover:text-main" 
                    title="View Product"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <EyeIcon size={18} />
                  </Link>
                  <Link 
                    to={`/admin/products/${variant.product_id}/variants/${variant.id}/edit`} 
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
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-copy-light">
            Showing <span className="font-medium">{startIndex + 1}</span> to{' '}
            <span className="font-medium">{Math.min(endIndex, variants.length)}</span> of{' '}
            <span className="font-medium">{variants.length}</span> variants
          </p>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-3 py-1 border border-border rounded-md text-sm text-copy-light bg-background disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            
            <div className="flex items-center gap-1">
              {[...Array(totalPages)].map((_, pageNum) => (
                <button
                  key={pageNum + 1}
                  onClick={() => goToPage(pageNum + 1)}
                  className={`px-3 py-1 text-sm rounded-md ${
                    currentPage === pageNum + 1
                      ? 'bg-primary text-white'
                      : 'border border-border text-copy hover:bg-surface-hover'
                  }`}
                >
                  {pageNum + 1}
                </button>
              ))}
            </div>
            
            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border border-border rounded-md text-sm text-copy-light bg-background disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
