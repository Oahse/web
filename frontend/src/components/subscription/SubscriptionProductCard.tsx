import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { MinusIcon, PlusIcon, PackageIcon } from 'lucide-react';
import { themeClasses, combineThemeClasses, getButtonClasses } from '../../utils/themeClasses';
import { useLocale } from '../../store/LocaleContext';
import { formatPriceWithFallback, getBestPrice } from '../../utils/price-utils';

interface SubscriptionProductCardProps {
  product: {
    id: string;
    product_id?: string;
    product_name?: string;
    name: string;
    price: number;
    currency?: string;
    quantity?: number;
    primary_image?: { url: string };
    images?: Array<{ url: string; is_primary?: boolean }>;
    variant_name?: string;
    variant_id?: string;
    stock?: number;
    sku?: string;
  };
  onRemove?: (productId: string) => void;
  onQuantityChange?: (productId: string, quantity: number) => void;
  showActions?: boolean;
  isRemoving?: boolean;
  viewMode?: 'grid' | 'list';
}

export const SubscriptionProductCard: React.FC<SubscriptionProductCardProps> = ({
  product,
  onRemove,
  onQuantityChange,
  showActions = true,
  isRemoving = false,
  viewMode = 'grid'
}) => {
  const [imageError, setImageError] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [quantity, setQuantity] = useState(product.quantity || 1);
  const { formatCurrency } = useLocale();

  const getPrimaryImage = () => {
    if (imageError) return null;
    
    // Check for primary image in images array
    if (product.images && product.images.length > 0) {
      const primaryImage = product.images.find(img => img.is_primary);
      if (primaryImage?.url) return primaryImage.url;
      if (product.images[0]?.url) return product.images[0].url;
    }
    
    // Fallback to primary_image field
    if (product.primary_image?.url) return product.primary_image.url;
    
    return null;
  };

  const handleImageError = () => {
    setImageError(true);
  };

  const handleImageLoad = () => {
    setImageLoaded(true);
  };

  const handleQuantityChange = (newQuantity: number) => {
    if (newQuantity < 1) return;
    setQuantity(newQuantity);
    onQuantityChange?.(product.id, newQuantity);
  };

  const productName = product.product_name || product.name;
  const productId = product.product_id || product.id;
  const imageUrl = getPrimaryImage();

  if (viewMode === 'list') {
    return (
      <div className={combineThemeClasses(
        themeClasses.card.base,
        'p-4 flex items-center space-x-4 hover:shadow-md transition-shadow duration-200'
      )}>
        {/* Product Image */}
        <div className="flex-shrink-0 w-16 h-16 sm:w-20 sm:h-20 relative">
          {imageUrl ? (
            <div className="relative w-full h-full rounded-lg overflow-hidden bg-gray-100">
              {!imageLoaded && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className={combineThemeClasses(themeClasses.loading.spinner, 'w-6 h-6')}></div>
                </div>
              )}
              <img
                src={imageUrl}
                alt={productName}
                className={`w-full h-full object-cover transition-opacity duration-300 ${
                  imageLoaded ? 'opacity-100' : 'opacity-0'
                }`}
                onError={handleImageError}
                onLoad={handleImageLoad}
                loading="lazy"
              />
            </div>
          ) : (
            <div className={combineThemeClasses(
              themeClasses.background.elevated,
              'w-full h-full rounded-lg flex items-center justify-center border-2 border-dashed',
              themeClasses.border.light
            )}>
              <PackageIcon className={combineThemeClasses(themeClasses.text.muted, 'w-6 h-6')} />
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="flex-1 min-w-0">
          <Link
            to={`/products/${productId}`}
            className={combineThemeClasses(
              themeClasses.text.heading,
              'font-medium hover:text-primary transition-colors duration-200 block truncate'
            )}
          >
            {productName}
          </Link>
          {product.variant_name && (
            <p className={combineThemeClasses(themeClasses.text.secondary, 'text-sm mt-1')}>
              Variant: {product.variant_name}
            </p>
          )}
          {product.sku && (
            <p className={combineThemeClasses(themeClasses.text.muted, 'text-xs mt-1')}>
              SKU: {product.sku}
            </p>
          )}
          <div className="flex items-center mt-2 space-x-4">
            <span className={combineThemeClasses(themeClasses.text.heading, 'font-semibold')}>
              {formatPriceWithFallback(product, product.currency, formatCurrency, 'Price not set')}
            </span>
            {product.stock !== undefined && (
              <span className={combineThemeClasses(
                themeClasses.text.muted,
                'text-xs',
                product.stock < 10 ? 'text-orange-600' : ''
              )}>
                Stock: {product.stock}
              </span>
            )}
          </div>
        </div>

        {/* Quantity & Actions */}
        {showActions && (
          <div className="flex items-center space-x-3">
            {onQuantityChange && (
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleQuantityChange(quantity - 1)}
                  disabled={quantity <= 1}
                  className={combineThemeClasses(
                    'p-1 rounded-md border transition-colors duration-200',
                    themeClasses.border.light,
                    'hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  <MinusIcon className="w-4 h-4" />
                </button>
                <span className={combineThemeClasses(themeClasses.text.primary, 'min-w-[2rem] text-center')}>
                  {quantity}
                </span>
                <button
                  onClick={() => handleQuantityChange(quantity + 1)}
                  className={combineThemeClasses(
                    'p-1 rounded-md border transition-colors duration-200',
                    themeClasses.border.light,
                    'hover:bg-gray-50'
                  )}
                >
                  <PlusIcon className="w-4 h-4" />
                </button>
              </div>
            )}
            
            {onRemove && (
              <button
                onClick={() => onRemove(product.id)}
                disabled={isRemoving}
                className={combineThemeClasses(
                  getButtonClasses('outline'),
                  'text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300',
                  'disabled:opacity-50 disabled:cursor-not-allowed text-sm px-3 py-1'
                )}
              >
                {isRemoving ? 'Removing...' : 'Remove'}
              </button>
            )}
          </div>
        )}
      </div>
    );
  }

  // Grid view
  return (
    <div className={combineThemeClasses(
      themeClasses.card.base,
      'group relative overflow-hidden hover:shadow-lg transition-all duration-300'
    )}>
      {/* Product Image */}
      <div className="relative aspect-square overflow-hidden bg-gray-100">
        {imageUrl ? (
          <>
            {!imageLoaded && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className={combineThemeClasses(themeClasses.loading.spinner, 'w-8 h-8')}></div>
              </div>
            )}
            <img
              src={imageUrl}
              alt={productName}
              className={`w-full h-full object-cover transition-all duration-500 group-hover:scale-105 ${
                imageLoaded ? 'opacity-100' : 'opacity-0'
              }`}
              onError={handleImageError}
              onLoad={handleImageLoad}
              loading="lazy"
            />
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center border-2 border-dashed border-gray-300">
            <div className="text-center">
              <PackageIcon className={combineThemeClasses(themeClasses.text.muted, 'w-12 h-12 mx-auto mb-2')} />
              <p className={combineThemeClasses(themeClasses.text.muted, 'text-sm')}>No Image</p>
            </div>
          </div>
        )}

        {/* Remove Button Overlay */}
        {showActions && onRemove && (
          <button
            onClick={() => onRemove(product.id)}
            disabled={isRemoving}
            className={combineThemeClasses(
              'absolute top-2 right-2 p-2 rounded-full shadow-lg transition-all duration-200',
              'bg-white/90 hover:bg-red-50 text-red-600 opacity-0 group-hover:opacity-100',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
            title="Remove from subscription"
          >
            <MinusIcon className="w-4 h-4" />
          </button>
        )}

        {/* Stock Badge */}
        {product.stock !== undefined && product.stock < 10 && (
          <div className="absolute top-2 left-2 px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
            {product.stock === 0 ? 'Out of Stock' : `${product.stock} left`}
          </div>
        )}
      </div>

      {/* Product Info */}
      <div className="p-4">
        <Link
          to={`/products/${productId}`}
          className={combineThemeClasses(
            themeClasses.text.heading,
            'font-medium hover:text-primary transition-colors duration-200 block mb-2 line-clamp-2'
          )}
        >
          {productName}
        </Link>

        {product.variant_name && (
          <p className={combineThemeClasses(themeClasses.text.secondary, 'text-sm mb-2')}>
            {product.variant_name}
          </p>
        )}

        {product.sku && (
          <p className={combineThemeClasses(themeClasses.text.muted, 'text-xs mb-3')}>
            SKU: {product.sku}
          </p>
        )}

        <div className="flex items-center justify-between">
          <span className={combineThemeClasses(themeClasses.text.heading, 'font-bold text-lg')}>
            {formatPriceWithFallback(product, product.currency, formatCurrency, 'Price not set')}
          </span>
          
          {showActions && onQuantityChange && (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleQuantityChange(quantity - 1)}
                disabled={quantity <= 1}
                className={combineThemeClasses(
                  'p-1 rounded-md border transition-colors duration-200',
                  themeClasses.border.light,
                  'hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                <MinusIcon className="w-3 h-3" />
              </button>
              <span className={combineThemeClasses(themeClasses.text.primary, 'min-w-[1.5rem] text-center text-sm')}>
                {quantity}
              </span>
              <button
                onClick={() => handleQuantityChange(quantity + 1)}
                className={combineThemeClasses(
                  'p-1 rounded-md border transition-colors duration-200',
                  themeClasses.border.light,
                  'hover:bg-gray-50'
                )}
              >
                <PlusIcon className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>

        {product.quantity && product.quantity > 1 && (
          <p className={combineThemeClasses(themeClasses.text.muted, 'text-xs mt-2')}>
            Quantity: {product.quantity}
          </p>
        )}
      </div>
    </div>
  );
};