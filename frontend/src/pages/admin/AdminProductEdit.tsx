import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ProductEditForm } from '../../components/admin/products/ProductEditForm';
import { ArrowLeftIcon, SaveIcon } from 'lucide-react';
import { useApi } from '../../hooks/useApi';
import { ProductsAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { BarcodeDisplay } from '../../components/product/BarcodeDisplay';
import { toast } from 'react-hot-toast';

export const AdminProductEdit = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [selectedVariant, setSelectedVariant] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const { data: apiResponse, loading: fetchLoading, error, execute } = useApi();

  useEffect(() => {
    if (id) {
      execute(ProductsAPI.getProduct, id);
    }
  }, [id, execute]);

  const product = apiResponse?.data || apiResponse;

  useEffect(() => {
    if (product && product.variants && product.variants.length > 0 && !selectedVariant) {
      setSelectedVariant(product.variants[0]);
    }
  }, [product, selectedVariant]);

  const handleCodesGenerated = (codes: any) => {
    toast.success('Barcode and QR code generated successfully!');
    if (id) {
      execute(ProductsAPI.getProduct, id);
    }
  };

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

  if (fetchLoading || !product) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-surface-hover rounded w-1/3 mb-6"></div>
          <div className="space-y-6">
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
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center">
          <button
            onClick={() => navigate(`/admin/products/${id}`)}
            className="mr-4 p-2 hover:bg-surface-hover rounded-md"
          >
            <ArrowLeftIcon size={20} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-main break-words">Edit: {product.name}</h1>
            <p className="text-sm text-copy-light break-all">Product ID: {product.id}</p>
          </div>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-2 sm:space-y-0 sm:space-x-3">
          <button
            disabled={loading}
            className="flex items-center justify-center px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark disabled:opacity-50"
          >
            <SaveIcon size={18} className="mr-2" />
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {/* Edit Form Placeholder */}
        <div className="bg-surface rounded-lg p-6 border border-border-light">
          <h2 className="text-lg font-semibold text-main mb-4">Product Information</h2>
          <ProductEditForm
            product={product}
            onSubmit={async (data) => {
              setLoading(true);
              try {
                await ProductsAPI.updateProduct(product.id, data);
                toast.success('Product updated successfully!');
                navigate(`/admin/products/${product.id}`);
              } catch (error) {
                toast.error('Failed to update product.');
              } finally {
                setLoading(false);
              }
            }}
            loading={loading}
          />
        </div>

        {/* Variants with Code Management */}
        <div className="bg-surface rounded-lg p-6 border border-border-light">
          <h2 className="text-lg font-semibold text-main mb-4">Variant Code Management</h2>
          
          {product.variants && product.variants.length > 0 ? (
            <div className="space-y-6">
              {/* Variant Selector */}
              {product.variants.length > 1 && (
                <div>
                  <label className="block text-sm font-medium text-copy mb-2">
                    Select Variant to Manage
                  </label>
                  <select
                    value={selectedVariant?.id || ''}
                    onChange={(e) => {
                      const variant = product.variants.find((v: any) => v.id === e.target.value);
                      setSelectedVariant(variant);
                    }}
                    className="w-full sm:w-auto px-3 py-2 border border-border rounded-md"
                  >
                    {product.variants.map((variant: any) => (
                      <option key={variant.id} value={variant.id}>
                        {variant.name} ({variant.sku})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Selected Variant Codes */}
              {selectedVariant && (
                <div>
                  <BarcodeDisplay
                    variant={selectedVariant}
                    showBoth={true}
                    size="md"
                    onCodesGenerated={handleCodesGenerated}
                    canGenerate={true}
                  />
                </div>
              )}
            </div>
          ) : (
            <p className="text-center text-copy-light py-8">No variants available</p>
          )}
        </div>

        {/* All Variants Overview */}
        {product.variants && product.variants.length > 1 && (
          <div className="bg-surface rounded-lg p-6 border border-border-light">
            <h2 className="text-lg font-semibold text-main mb-4">All Variants Overview</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {product.variants.map((variant: any) => (
                <div 
                  key={variant.id} 
                  className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                    selectedVariant?.id === variant.id 
                      ? 'border-primary bg-primary/5' 
                      : 'border-border-light hover:border-primary/50'
                  }`}
                  onClick={() => setSelectedVariant(variant)}
                >
                  <div className="text-center">
                    <img
                      src={variant.images?.[0]?.url || '/placeholder-image.png'}
                      alt={variant.name}
                      className="w-16 h-16 rounded-md object-cover mx-auto mb-2"
                    />
                    <h3 className="font-medium text-main break-words">{variant.name}</h3>
                    <p className="text-xs text-copy-light break-all">SKU: {variant.sku}</p>
                    <div className="flex justify-center space-x-2 mt-2">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        variant.barcode 
                          ? 'bg-success/10 text-success' 
                          : 'bg-gray-100 text-gray-500'
                      }`}>
                        {variant.barcode ? 'Barcode ✓' : 'No Barcode'}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        variant.qr_code 
                          ? 'bg-success/10 text-success' 
                          : 'bg-gray-100 text-gray-500'
                      }`}>
                        {variant.qr_code ? 'QR ✓' : 'No QR'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminProductEdit;