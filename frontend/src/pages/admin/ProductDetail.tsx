import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader, AlertCircle, ArrowLeft, Package, DollarSign, Tag, User, Image as ImageIcon, Warehouse, RefreshCw } from 'lucide-react';
import AdminAPI from '@/api/admin';
import toast from 'react-hot-toast';

export const AdminProductDetail = () => {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProduct = async () => {
      if (!productId) return;
      
      try {
        setLoading(true);
        setError(null);
        const response = await AdminAPI.getProductById(productId);
        
        // Handle different response structures
        const productData = response?.data?.data || response?.data || response;
        
        if (!productData) {
          throw new Error('No product data received');
        }
        
        setProduct(productData);
      } catch (err: any) {
        console.error('Product fetch error:', err);
        const message = err?.response?.data?.message || err?.message || 'Failed to load product details';
        setError(message);
        toast.error(message);
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [productId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader className="w-12 h-12 text-primary animate-spin" />
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => navigate('/admin/products')}
          className="inline-flex items-center gap-2 text-copy-light hover:text-copy transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Products
        </button>
        
        {error && (
          <div className="bg-destructive/10 border border-destructive rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-destructive">Error</p>
              <p className="text-destructive/80 text-sm">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="mt-2 inline-flex items-center gap-2 px-3 py-1 bg-destructive text-white rounded text-sm hover:bg-destructive/90 transition-colors"
              >
                <RefreshCw className="w-3 h-3" />
                Retry
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/admin/products')}
            className="inline-flex items-center gap-2 text-copy-light hover:text-copy transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Products
          </button>
          <div>
            <h1 className="text-3xl font-bold text-copy">{product.name}</h1>
            <p className="text-copy-light mt-1">Product ID: {String(product.id).slice(0, 8)}...</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
            product.product_status === 'active' ? 'bg-success/20 text-success' : 
            product.product_status === 'inactive' ? 'bg-warning/20 text-warning' :
            'bg-gray-20 text-gray'
          }`}>
            {product.product_status?.charAt(0).toUpperCase() + product.product_status?.slice(1) || 'Unknown'}
          </span>
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
            product.availability_status === 'available' ? 'bg-success/20 text-success' : 
            product.availability_status === 'out_of_stock' ? 'bg-destructive/20 text-destructive' :
            'bg-warning/20 text-warning'
          }`}>
            {product.availability_status?.replace('_', ' ').charAt(0).toUpperCase() + product.availability_status?.replace('_', ' ').slice(1) || 'Unknown'}
          </span>
        </div>
      </div>

      {/* Product Information */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Info */}
          <div className="bg-surface rounded-lg border border-border-light p-6">
            <h2 className="text-xl font-bold text-copy mb-4 flex items-center gap-2">
              <Package className="w-5 h-5" />
              Product Information
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-copy-light">Name</label>
                <p className="text-copy font-medium">{product.name}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-copy-light">Slug</label>
                <p className="text-copy font-mono text-sm">{product.slug}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-copy-light">SKU</label>
                <p className="text-copy">{product.variants?.[0]?.sku || 'N/A'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-copy-light">Rating</label>
                <p className="text-copy">⭐ {product.rating_average || 0} ({product.rating_count || 0} reviews)</p>
              </div>
            </div>
            
            {product.description && (
              <div className="mt-4">
                <label className="text-sm font-medium text-copy-light">Description</label>
                <p className="text-copy mt-1">{product.description}</p>
              </div>
            )}
            
            {product.short_description && (
              <div className="mt-4">
                <label className="text-sm font-medium text-copy-light">Short Description</label>
                <p className="text-copy mt-1">{product.short_description}</p>
              </div>
            )}
          </div>

          {/* Category & Supplier */}
          <div className="bg-surface rounded-lg border border-border-light p-6">
            <h2 className="text-xl font-bold text-copy mb-4 flex items-center gap-2">
              <Tag className="w-5 h-5" />
              Category & Supplier
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-copy-light">Category</label>
                {product.category ? (
                  <div className="mt-1">
                    <p className="text-copy font-medium">{product.category.name}</p>
                    {product.category.description && (
                      <p className="text-copy-light text-sm">{product.category.description}</p>
                    )}
                  </div>
                ) : (
                  <p className="text-copy-light">No category assigned</p>
                )}
              </div>
              
              <div>
                <label className="text-sm font-medium text-copy-light">Supplier</label>
                {product.supplier ? (
                  <div className="mt-1">
                    <p className="text-copy font-medium">{product.supplier.name}</p>
                    <p className="text-copy-light text-sm">{product.supplier.email}</p>
                    {product.supplier.phone && (
                      <p className="text-copy-light text-sm">{product.supplier.phone}</p>
                    )}
                  </div>
                ) : (
                  <p className="text-copy-light">No supplier assigned</p>
                )}
              </div>
            </div>
          </div>

          {/* Variants */}
          <div className="bg-surface rounded-lg border border-border-light p-6">
            <h2 className="text-xl font-bold text-copy mb-4 flex items-center gap-2">
              <Package className="w-5 h-5" />
              Product Variants ({product.variants?.length || 0})
            </h2>
            
            {product.variants && product.variants.length > 0 ? (
              <div className="space-y-4">
                {product.variants.map((variant: any, index: number) => (
                  <div key={variant.id} className="border border-border-light rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold text-copy">{variant.name}</h3>
                        <p className="text-copy-light text-sm font-mono">SKU: {variant.sku}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-copy">
                          ${variant.current_price?.toFixed(2) || variant.base_price?.toFixed(2)}
                        </p>
                        {variant.sale_price && variant.sale_price < variant.base_price && (
                          <p className="text-sm text-copy-light line-through">
                            ${variant.base_price?.toFixed(2)}
                          </p>
                        )}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <label className="text-copy-light">Stock</label>
                        <p className={`font-medium ${
                          variant.stock > 0 ? 'text-success' : 'text-destructive'
                        }`}>
                          {variant.stock || 0} units
                        </p>
                      </div>
                      <div>
                        <label className="text-copy-light">Status</label>
                        <p className="font-medium">
                          {variant.is_active ? 'Active' : 'Inactive'}
                        </p>
                      </div>
                      <div>
                        <label className="text-copy-light">Attributes</label>
                        <p className="font-medium">
                          {variant.attributes ? Object.entries(variant.attributes).map(([k, v]) => 
                            `${k}: ${v}`).join(', ') : 'None'}
                        </p>
                      </div>
                    </div>
                    
                    {/* Inventory Details */}
                    {variant.inventory && (
                      <div className="mt-3 pt-3 border-t border-border-light">
                        <div className="flex items-center gap-2 text-sm text-copy-light mb-2">
                          <Warehouse className="w-4 h-4" />
                          Inventory Details
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                          <div>
                            <span className="text-copy-light">Available:</span>
                            <span className="ml-1 font-medium">{variant.inventory.quantity_available}</span>
                          </div>
                          <div>
                            <span className="text-copy-light">Total:</span>
                            <span className="ml-1 font-medium">{variant.inventory.quantity}</span>
                          </div>
                          <div>
                            <span className="text-copy-light">Reorder Level:</span>
                            <span className="ml-1 font-medium">{variant.inventory.reorder_level || 'N/A'}</span>
                          </div>
                          <div>
                            <span className="text-copy-light">Location:</span>
                            <span className="ml-1 font-medium">{variant.inventory.warehouse_location || 'N/A'}</span>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Images */}
                    {variant.images && variant.images.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-border-light">
                        <div className="flex items-center gap-2 text-sm text-copy-light mb-2">
                          <ImageIcon className="w-4 h-4" />
                          Images ({variant.images.length})
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {variant.images.map((image: any) => (
                            <div key={image.id} className="relative group">
                              <img
                                src={image.url}
                                alt={image.alt_text || variant.name}
                                className="w-16 h-16 object-cover rounded border border-border-light"
                              />
                              {image.is_primary && (
                                <span className="absolute top-0 right-0 bg-primary text-white text-xs px-1 rounded-bl">
                                  Primary
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-copy-light">No variants found</p>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Pricing */}
          <div className="bg-surface rounded-lg border border-border-light p-6">
            <h2 className="text-xl font-bold text-copy mb-4 flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              Pricing
            </h2>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-copy-light">Min Price:</span>
                <span className="font-semibold">${product.min_price?.toFixed(2) || '0.00'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-copy-light">Max Price:</span>
                <span className="font-semibold">${product.max_price?.toFixed(2) || '0.00'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-copy-light">Price Range:</span>
                <span className="font-semibold">
                  ${product.price_range?.min?.toFixed(2) || '0.00'} - 
                  ${product.price_range?.max?.toFixed(2) || '0.00'}
                </span>
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div className="bg-surface rounded-lg border border-border-light p-6">
            <h2 className="text-xl font-bold text-copy mb-4">Metrics</h2>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-copy-light">Views:</span>
                <span className="font-semibold">{product.view_count || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-copy-light">Purchases:</span>
                <span className="font-semibold">{product.purchase_count || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-copy-light">Reviews:</span>
                <span className="font-semibold">{product.review_count || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-copy-light">In Stock:</span>
                <span className={`font-semibold ${product.in_stock ? 'text-success' : 'text-destructive'}`}>
                  {product.in_stock ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>

          {/* Tags */}
          {product.tags && product.tags.length > 0 && (
            <div className="bg-surface rounded-lg border border-border-light p-6">
              <h2 className="text-xl font-bold text-copy mb-4">Tags</h2>
              <div className="flex flex-wrap gap-2">
                {product.tags.map((tag: string, index: number) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-primary/10 text-primary rounded-md text-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminProductDetail;
