import { useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeftIcon, EditIcon, TrashIcon, PackageIcon, TrendingUpIcon, UsersIcon } from 'lucide-react';
import { useApi } from '../../hooks/useApi';
import { ProductsAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';

export const AdminProductDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: apiResponse, loading, error, execute } = useApi();

  useEffect(() => {
    // Don't fetch if id is 'new' or 'edit' (reserved routes)
    if (id && id !== 'new' && id !== 'edit') {
      execute(ProductsAPI.getProduct, id);
    }
  }, [id, execute]);

  // Redirect if trying to access reserved routes
  if (id === 'new' || id === 'edit') {
    return (
      <div className="p-6">
        <div className="bg-warning/10 border border-warning text-warning p-4 rounded-md">
          <p>This page is under construction. Please use the product list to manage products.</p>
          <button
            onClick={() => navigate('/admin/products')}
            className="mt-4 px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark"
          >
            Back to Products
          </button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorMessage 
          error={error} 
          onRetry={() => id && execute(ProductsAPI.getProduct, id)}
          onDismiss={() => navigate('/admin/products')}
        />
      </div>
    );
  }

  if (loading || !apiResponse) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-surface-hover rounded w-1/3 mb-6"></div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-surface rounded-lg p-6 border border-border-light">
                <div className="h-6 bg-surface-hover rounded w-1/4 mb-4"></div>
                <div className="space-y-3">
                  <div className="h-4 bg-surface-hover rounded"></div>
                  <div className="h-4 bg-surface-hover rounded w-5/6"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Extract the actual product data from the API response
  const product = apiResponse?.data || apiResponse;

  const totalStock = Array.isArray(product.variants)
    ? product.variants.reduce((sum: number, variant: any) => sum + (variant.stock || 0), 0)
    : 0;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={() => navigate('/admin/products')}
            className="mr-4 p-2 hover:bg-surface-hover rounded-md"
          >
            <ArrowLeftIcon size={20} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-main">{product.name}</h1>
            <p className="text-sm text-copy-light">Product ID: {product.id}</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            to={`/admin/products/${product.id}/edit`}
            className="flex items-center px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark"
          >
            <EditIcon size={18} className="mr-2" />
            Edit Product
          </Link>
          <button className="flex items-center px-4 py-2 border border-error text-error rounded-md hover:bg-error/10">
            <TrashIcon size={18} className="mr-2" />
            Delete
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Product Information */}
          <div className="bg-surface rounded-lg p-6 border border-border-light">
            <h2 className="text-lg font-semibold text-main mb-4">Product Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-copy-light mb-1">Name</p>
                <p className="text-copy font-medium">{product.name}</p>
              </div>
              <div>
                <p className="text-sm text-copy-light mb-1">Category</p>
                <p className="text-copy font-medium">{product.category?.name || 'Uncategorized'}</p>
              </div>
              <div>
                <p className="text-sm text-copy-light mb-1">Supplier</p>
                <p className="text-copy font-medium">
                  {product.supplier 
                    ? (typeof product.supplier === 'string' 
                        ? product.supplier 
                        : `${product.supplier.firstname || ''} ${product.supplier.lastname || ''}`.trim() || product.supplier.email || 'N/A')
                    : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-sm text-copy-light mb-1">Rating</p>
                <p className="text-copy font-medium">{product.rating?.toFixed(1) || 'N/A'} ({product.review_count || 0} reviews)</p>
              </div>
              <div className="col-span-2">
                <p className="text-sm text-copy-light mb-1">Description</p>
                <p className="text-copy">{product.description || 'No description available'}</p>
              </div>
            </div>
          </div>

          {/* Variants */}
          <div className="bg-surface rounded-lg p-6 border border-border-light">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-main">Variants ({product.variants?.length || 0})</h2>
              <Link
                to={`/admin/products/${product.id}/variants`}
                className="text-sm text-primary hover:underline"
              >
                Manage Variants
              </Link>
            </div>
            <div className="space-y-3">
              {product.variants?.map((variant: any) => (
                <div key={variant.id} className="flex items-center justify-between p-4 border border-border-light rounded-md">
                  <div className="flex items-center space-x-4">
                    <img
                      src={variant.images?.[0]?.url || 'https://via.placeholder.com/100'}
                      alt={variant.name}
                      className="w-16 h-16 rounded-md object-cover"
                    />
                    <div>
                      <p className="font-medium text-main">{variant.name}</p>
                      <p className="text-sm text-copy-light">SKU: {variant.sku}</p>
                      {variant.attributes && (
                        <p className="text-xs text-copy-light mt-1">
                          {Object.entries(variant.attributes).map(([key, value]) => `${key}: ${value}`).join(', ')}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-main">
                      ${variant.sale_price ? variant.sale_price.toFixed(2) : variant.base_price.toFixed(2)}
                    </p>
                    {variant.sale_price && (
                      <p className="text-sm text-copy-light line-through">
                        ${variant.base_price.toFixed(2)}
                      </p>
                    )}
                    <p className={`text-sm mt-1 ${variant.stock > 10 ? 'text-success' : variant.stock > 0 ? 'text-warning' : 'text-error'}`}>
                      Stock: {variant.stock}
                    </p>
                  </div>
                </div>
              ))}
              {(!product.variants || product.variants.length === 0) && (
                <p className="text-center text-copy-light py-4">No variants available</p>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="bg-surface rounded-lg p-6 border border-border-light">
            <h2 className="text-lg font-semibold text-main mb-4">Quick Stats</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <PackageIcon size={20} className="text-primary mr-2" />
                  <span className="text-sm text-copy-light">Total Stock</span>
                </div>
                <span className="font-medium text-main">{totalStock}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <TrendingUpIcon size={20} className="text-success mr-2" />
                  <span className="text-sm text-copy-light">Total Sales</span>
                </div>
                <span className="font-medium text-main">N/A</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <UsersIcon size={20} className="text-info mr-2" />
                  <span className="text-sm text-copy-light">Views</span>
                </div>
                <span className="font-medium text-main">N/A</span>
              </div>
            </div>
          </div>

          {/* Status */}
          <div className="bg-surface rounded-lg p-6 border border-border-light">
            <h2 className="text-lg font-semibold text-main mb-4">Status</h2>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-copy-light mb-1">Availability</p>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  totalStock === 0 ? 'bg-error/10 text-error' :
                  totalStock < 10 ? 'bg-warning/10 text-warning' :
                  'bg-success/10 text-success'
                }`}>
                  {totalStock === 0 ? 'Out of Stock' : totalStock < 10 ? 'Low Stock' : 'In Stock'}
                </span>
              </div>
              <div>
                <p className="text-sm text-copy-light mb-1">Created</p>
                <p className="text-copy text-sm">
                  {product.created_at ? new Date(product.created_at).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="bg-surface rounded-lg p-6 border border-border-light">
            <h2 className="text-lg font-semibold text-main mb-4">Actions</h2>
            <div className="space-y-2">
              <Link
                to={`/product/${product.id}`}
                className="block w-full text-center px-4 py-2 border border-border rounded-md hover:bg-surface-hover text-copy"
              >
                View as Customer
              </Link>
              <button className="w-full px-4 py-2 border border-border rounded-md hover:bg-surface-hover text-copy">
                Duplicate Product
              </button>
              <button className="w-full px-4 py-2 border border-border rounded-md hover:bg-surface-hover text-copy">
                Archive Product
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
