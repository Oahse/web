import React, { useState, useCallback, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { SearchIcon, FilterIcon, EditIcon, TrashIcon, PlusIcon, EyeIcon, ArrowLeftIcon, CheckIcon, XIcon } from 'lucide-react';
import { usePaginatedApi } from '../../hooks/useAsync';
import { AdminAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { ResponsiveTable } from '../../components/ui/ResponsiveTable';
import { Pagination } from '../../components/ui/Pagination';
import { PLACEHOLDER_IMAGES } from '../../utils/placeholderImage';
import { toast } from 'react-hot-toast';

export const AdminVariants = () => {
  const { id: productIdFromRoute } = useParams<{ id: string }>();
  const [searchTerm, setSearchTerm] = useState('');
  const [submittedSearchTerm, setSubmittedSearchTerm] = useState('');
  const [showMoreFilters, setShowMoreFilters] = useState(false);
  const [productId, setProductId] = useState('');
  const [editingStock, setEditingStock] = useState<{ [key: string]: string }>({});
  const [updatingStock, setUpdatingStock] = useState<{ [key: string]: boolean }>({});

  // If we have a product ID from the route, use it and hide the filter
  const isProductSpecific = !!productIdFromRoute;
  const effectiveProductId = productIdFromRoute || productId;

  useEffect(() => {
    if (productIdFromRoute) {
      setProductId(productIdFromRoute);
    }
  }, [productIdFromRoute]);

  const apiCall = useCallback((page: number, limit: number) => {
    return AdminAPI.getAllVariants({
      search: submittedSearchTerm || undefined,
      product_id: effectiveProductId || undefined,
      page,
      limit,
    });
  }, [submittedSearchTerm, effectiveProductId]);

  const {
    data: variants,
    loading: variantsLoading,
    error: variantsError,
    execute: fetchVariants,
    page: currentPage,
    limit: itemsPerPage,
    totalPages,
    total: totalVariants,
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

  const handleStockEdit = (variantId: string, currentStock: number) => {
    setEditingStock(prev => ({ ...prev, [variantId]: currentStock.toString() }));
  };

  const handleStockCancel = (variantId: string) => {
    setEditingStock(prev => {
      const newState = { ...prev };
      delete newState[variantId];
      return newState;
    });
  };

  const handleStockSave = async (variantId: string) => {
    const newStock = editingStock[variantId];
    if (!newStock || isNaN(parseInt(newStock))) {
      toast.error('Please enter a valid stock number');
      return;
    }

    setUpdatingStock(prev => ({ ...prev, [variantId]: true }));
    
    try {
      // This would need to be implemented in the AdminAPI
      await AdminAPI.updateVariantStock(variantId, parseInt(newStock));
      toast.success('Stock updated successfully');
      
      // Remove from editing state
      setEditingStock(prev => {
        const newState = { ...prev };
        delete newState[variantId];
        return newState;
      });
      
      // Refresh the data
      fetchVariants();
    } catch (error: any) {
      console.error('Error updating stock:', error);
      toast.error(error?.message || 'Failed to update stock');
    } finally {
      setUpdatingStock(prev => ({ ...prev, [variantId]: false }));
    }
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
  const endIndex = Math.min(startIndex + itemsPerPage, totalVariants || variants.length);

  return (
    <div>
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between">
        <div className="flex items-center mb-2 md:mb-0">
          {isProductSpecific && (
            <Link
              to={`/admin/products/${productIdFromRoute}`}
              className="mr-4 p-2 hover:bg-surface-hover rounded-md"
            >
              <ArrowLeftIcon size={20} />
            </Link>
          )}
          <h1 className="text-2xl font-bold text-main">
            {isProductSpecific ? 'Product Variants' : 'All Product Variants'}
          </h1>
        </div>
        <Link to="/admin/variants/new" className="inline-flex items-center bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-md transition-colors">
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
              {!isProductSpecific && (
                <button type="button" onClick={() => setShowMoreFilters(!showMoreFilters)} className="flex items-center px-3 py-2 border border-border rounded-md hover:bg-surface-hover text-copy">
                  <FilterIcon size={18} className="mr-2" />
                  More Filters
                </button>
              )}
              <button type="submit" className="flex items-center px-3 py-2 bg-primary text-white rounded-md hover:bg-primary-dark">
                <SearchIcon size={18} className="mr-2" />
                Search
              </button>
            </div>
          </div>
        </form>
        {showMoreFilters && !isProductSpecific && (
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
          data={variants || []}
          loading={variantsLoading}
          keyExtractor={(variant) => variant.id}
          emptyMessage="No product variants found"
          columns={[
            {
              key: 'variant',
              label: 'Variant',
              mobileLabel: 'Variant',
              render: (variant) => {
                const imageUrl = variant.primary_image?.url || 
                               variant.images?.[0]?.url || 
                               PLACEHOLDER_IMAGES.small;
                return (
                  <div className="flex items-center">
                    <div className="relative w-10 h-10 mr-3 flex-shrink-0">
                      <img 
                        src={imageUrl} 
                        alt={variant.name} 
                        className="w-full h-full rounded-md object-cover border border-border-light" 
                        onError={(e) => {
                          e.currentTarget.src = PLACEHOLDER_IMAGES.small;
                        }}
                        onLoad={(e) => {
                          e.currentTarget.classList.remove('opacity-50');
                        }}
                        style={{ 
                          backgroundColor: '#f3f4f6',
                          minHeight: '40px',
                          minWidth: '40px'
                        }}
                      />
                      {!imageUrl.startsWith('data:') && (
                        <div className="absolute inset-0 bg-surface-hover animate-pulse rounded-md opacity-0 transition-opacity duration-200" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-main truncate">{variant.name}</p>
                      <p className="text-xs text-copy-light truncate">SKU: {variant.sku}</p>
                    </div>
                  </div>
                );
              },
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
              render: (variant) => {
                const isEditing = editingStock[variant.id] !== undefined;
                const isUpdating = updatingStock[variant.id];
                
                if (isEditing) {
                  return (
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        value={editingStock[variant.id]}
                        onChange={(e) => setEditingStock(prev => ({ ...prev, [variant.id]: e.target.value }))}
                        className="w-20 px-2 py-1 border border-border rounded text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                        disabled={isUpdating}
                      />
                      <button
                        onClick={() => handleStockSave(variant.id)}
                        disabled={isUpdating}
                        className="p-1 text-success hover:bg-success/10 rounded disabled:opacity-50"
                        title="Save"
                      >
                        <CheckIcon size={14} />
                      </button>
                      <button
                        onClick={() => handleStockCancel(variant.id)}
                        disabled={isUpdating}
                        className="p-1 text-error hover:bg-error/10 rounded disabled:opacity-50"
                        title="Cancel"
                      >
                        <XIcon size={14} />
                      </button>
                    </div>
                  );
                }
                
                return (
                  <button
                    onClick={() => handleStockEdit(variant.id, variant.stock)}
                    className="text-copy-light hover:text-primary hover:bg-surface-hover px-2 py-1 rounded transition-colors"
                    title="Click to edit stock"
                  >
                    {variant.stock}
                  </button>
                );
              },
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
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        totalItems={totalVariants || variants.length}
        itemsPerPage={itemsPerPage}
        onPageChange={goToPage}
        showingStart={startIndex + 1}
        showingEnd={Math.min(endIndex, totalVariants || variants.length)}
        itemName="variants"
        className="mt-6"
      />
    </div>
  );
};
