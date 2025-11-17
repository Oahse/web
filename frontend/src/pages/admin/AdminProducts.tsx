import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { PlusIcon, SearchIcon, FilterIcon, EditIcon, TrashIcon, ChevronDownIcon, EyeIcon, MoreHorizontalIcon } from 'lucide-react';
import { usePaginatedApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import { useCategories } from '../../contexts/CategoryContext';
import ErrorMessage from '../../components/common/ErrorMessage';
import { ResponsiveTable } from '../../components/ui/ResponsiveTable';

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
  const endIndex = Math.min(startIndex + itemsPerPage, products.length);

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
          data={products}
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
                const primaryVariant = product.variants?.[0];
                return (
                  <div className="flex items-center">
                    <img 
                      src={primaryVariant?.images?.[0]?.url || 'https://via.placeholder.com/100'} 
                      alt={product.name} 
                      className="w-10 h-10 rounded-md object-cover mr-3" 
                    />
                    <div>
                      <p className="font-medium text-main">{product.name}</p>
                      <p className="text-xs text-copy-light">ID: {product.id}</p>
                    </div>
                  </div>
                );
              },
            },
            {
              key: 'sku',
              label: 'SKU',
              hideOnMobile: true,
              render: (product) => (
                <span className="text-copy-light">{product.variants?.[0]?.sku || 'N/A'}</span>
              ),
            },
            {
              key: 'category',
              label: 'Category',
              render: (product) => (
                <span className="text-copy-light">{product.category?.name || 'Uncategorized'}</span>
              ),
            },
            {
              key: 'price',
              label: 'Price',
              render: (product) => {
                const primaryVariant = product.variants?.[0];
                return primaryVariant?.sale_price ? (
                  <div>
                    <span className="font-medium text-main">
                      ${primaryVariant.sale_price.toFixed(2)}
                    </span>
                    <span className="text-xs text-copy-light line-through ml-2">
                      ${primaryVariant.base_price.toFixed(2)}
                    </span>
                  </div>
                ) : (
                  <span className="font-medium text-main">
                    ${primaryVariant?.base_price?.toFixed(2) || '0.00'}
                  </span>
                );
              },
            },
            {
              key: 'stock',
              label: 'Stock',
              render: (product) => {
                const totalStock = Array.isArray(product.variants)
                  ? product.variants.reduce((sum: number, variant: any) => sum + (variant.stock || 0), 0)
                  : 0;
                return <span className="text-copy-light">{totalStock}</span>;
              },
            },
            {
              key: 'status',
              label: 'Status',
              render: (product) => {
                const totalStock = Array.isArray(product.variants)
                  ? product.variants.reduce((sum: number, variant: any) => sum + (variant.stock || 0), 0)
                  : 0;
                const status = totalStock === 0 ? 'Out of Stock' : totalStock < 10 ? 'Low Stock' : 'Active';
                return (
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    status === 'Active' ? 'bg-success/10 text-success' :
                    status === 'Low Stock' ? 'bg-warning/10 text-warning' :
                    'bg-error/10 text-error'
                  }`}>
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
                <Link 
                  to={`/admin/products/${product.id}/variants`} 
                  className="text-primary hover:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  {product.variants?.length || 0}
                </Link>
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
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-copy-light">
            Showing <span className="font-medium">{startIndex + 1}</span> to{' '}
            <span className="font-medium">{endIndex}</span> of{' '}
            <span className="font-medium">{products.length}</span> products
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
    </div>;
};