import React, { useState } from 'react';
import { CheckIcon, ImageIcon } from 'lucide-react';
import { themeClasses, combineThemeClasses } from '../../utils/themeClasses';
import { formatCurrency } from '../../utils/locale-config';

interface Variant {
  id: string;
  name: string;
  price: number;
  sale_price?: number;
  stock: number;
  sku?: string;
  images?: Array<{ url: string; is_primary?: boolean }>;
  primary_image?: { url: string };
  attributes?: { [key: string]: string };
}

interface VariantSelectorProps {
  variants: Variant[];
  selectedVariantId?: string;
  onVariantSelect: (variant: Variant) => void;
  currency?: string;
  showImages?: boolean;
  showStock?: boolean;
  showSku?: boolean;
  layout?: 'grid' | 'list';
  size?: 'sm' | 'md' | 'lg';
}

export const VariantSelector: React.FC<VariantSelectorProps> = ({
  variants,
  selectedVariantId,
  onVariantSelect,
  currency = 'USD',
  showImages = true,
  showStock = true,
  showSku = false,
  layout = 'grid',
  size = 'md'
}) => {
  const [imageErrors, setImageErrors] = useState<Set<string>>(new Set());
  const [loadedImages, setLoadedImages] = useState<Set<string>>(new Set());

  const sizeClasses = {
    sm: {
      container: 'gap-2',
      image: 'w-12 h-12',
      text: 'text-sm',
      price: 'text-sm',
      padding: 'p-2'
    },
    md: {
      container: 'gap-3',
      image: 'w-16 h-16',
      text: 'text-base',
      price: 'text-base',
      padding: 'p-3'
    },
    lg: {
      container: 'gap-4',
      image: 'w-20 h-20',
      text: 'text-lg',
      price: 'text-lg',
      padding: 'p-4'
    }
  };

  const currentSize = sizeClasses[size];

  const getPrimaryImage = (variant: Variant) => {
    if (imageErrors.has(variant.id)) return null;
    
    // Check for primary image in images array
    if (variant.images && variant.images.length > 0) {
      const primaryImage = variant.images.find(img => img.is_primary);
      if (primaryImage?.url) return primaryImage.url;
      if (variant.images[0]?.url) return variant.images[0].url;
    }
    
    // Fallback to primary_image field
    if (variant.primary_image?.url) return variant.primary_image.url;
    
    return null;
  };

  const handleImageError = (variantId: string) => {
    setImageErrors(prev => new Set([...prev, variantId]));
  };

  const handleImageLoad = (variantId: string) => {
    setLoadedImages(prev => new Set([...prev, variantId]));
  };

  const isOutOfStock = (variant: Variant) => variant.stock <= 0;
  const isLowStock = (variant: Variant) => variant.stock > 0 && variant.stock < 10;
  const isOnSale = (variant: Variant) => variant.sale_price && variant.sale_price < variant.price;

  const getDisplayPrice = (variant: Variant) => {
    if (isOnSale(variant)) {
      return {
        current: variant.sale_price!,
        original: variant.price,
        discount: Math.round(((variant.price - variant.sale_price!) / variant.price) * 100)
      };
    }
    return { current: variant.price };
  };

  if (layout === 'list') {
    return (
      <div className={combineThemeClasses('space-y-2', currentSize.container)}>
        {variants.map((variant) => {
          const isSelected = selectedVariantId === variant.id;
          const imageUrl = showImages ? getPrimaryImage(variant) : null;
          const priceInfo = getDisplayPrice(variant);
          const outOfStock = isOutOfStock(variant);
          const lowStock = isLowStock(variant);

          return (
            <button
              key={variant.id}
              onClick={() => !outOfStock && onVariantSelect(variant)}
              disabled={outOfStock}
              className={combineThemeClasses(
                'w-full flex items-center space-x-3 rounded-lg border-2 transition-all duration-200',
                currentSize.padding,
                isSelected 
                  ? 'border-primary bg-primary/5' 
                  : combineThemeClasses(themeClasses.border.light, 'hover:border-primary/50'),
                outOfStock 
                  ? 'opacity-50 cursor-not-allowed' 
                  : 'cursor-pointer hover:shadow-md'
              )}
            >
              {/* Variant Image */}
              {showImages && (
                <div className={combineThemeClasses('flex-shrink-0 relative', currentSize.image)}>
                  {imageUrl ? (
                    <div className="relative w-full h-full rounded-md overflow-hidden bg-gray-100">
                      {!loadedImages.has(variant.id) && (
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className={combineThemeClasses(themeClasses.loading.spinner, 'w-4 h-4')}></div>
                        </div>
                      )}
                      <img
                        src={imageUrl}
                        alt={variant.name}
                        className={`w-full h-full object-cover transition-opacity duration-300 ${
                          loadedImages.has(variant.id) ? 'opacity-100' : 'opacity-0'
                        }`}
                        onError={() => handleImageError(variant.id)}
                        onLoad={() => handleImageLoad(variant.id)}
                        loading="lazy"
                      />
                    </div>
                  ) : (
                    <div className={combineThemeClasses(
                      'w-full h-full rounded-md flex items-center justify-center border-2 border-dashed',
                      themeClasses.border.light,
                      themeClasses.background.elevated
                    )}>
                      <ImageIcon className={combineThemeClasses(themeClasses.text.muted, 'w-6 h-6')} />
                    </div>
                  )}
                  
                  {/* Stock Badge */}
                  {showStock && (outOfStock || lowStock) && (
                    <div className={combineThemeClasses(
                      'absolute -top-1 -right-1 px-1.5 py-0.5 rounded-full text-xs font-medium',
                      outOfStock 
                        ? 'bg-red-100 text-red-800' 
                        : 'bg-orange-100 text-orange-800'
                    )}>
                      {outOfStock ? 'Out' : 'Low'}
                    </div>
                  )}
                </div>
              )}

              {/* Variant Info */}
              <div className="flex-1 min-w-0 text-left">
                <div className="flex items-center justify-between mb-1">
                  <h4 className={combineThemeClasses(
                    themeClasses.text.heading,
                    'font-medium truncate',
                    currentSize.text
                  )}>
                    {variant.name}
                  </h4>
                  {isSelected && (
                    <CheckIcon className="w-5 h-5 text-primary flex-shrink-0" />
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className={combineThemeClasses(
                      themeClasses.text.heading,
                      'font-semibold',
                      currentSize.price
                    )}>
                      {formatCurrency(priceInfo.current, currency)}
                    </span>
                    {priceInfo.original && (
                      <span className={combineThemeClasses(
                        themeClasses.text.muted,
                        'line-through text-sm'
                      )}>
                        {formatCurrency(priceInfo.original, currency)}
                      </span>
                    )}
                    {priceInfo.discount && (
                      <span className="px-1.5 py-0.5 bg-red-100 text-red-800 text-xs rounded-full font-medium">
                        -{priceInfo.discount}%
                      </span>
                    )}
                  </div>

                  {showStock && !outOfStock && (
                    <span className={combineThemeClasses(
                      themeClasses.text.muted,
                      'text-xs',
                      lowStock ? 'text-orange-600' : ''
                    )}>
                      {variant.stock} in stock
                    </span>
                  )}
                </div>

                {showSku && variant.sku && (
                  <p className={combineThemeClasses(themeClasses.text.muted, 'text-xs mt-1')}>
                    SKU: {variant.sku}
                  </p>
                )}

                {/* Variant Attributes */}
                {variant.attributes && Object.keys(variant.attributes).length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {Object.entries(variant.attributes).map(([key, value]) => (
                      <span
                        key={key}
                        className={combineThemeClasses(
                          'px-2 py-0.5 rounded-full text-xs',
                          themeClasses.background.elevated,
                          themeClasses.text.secondary
                        )}
                      >
                        {key}: {value}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>
    );
  }

  // Grid layout
  return (
    <div className={combineThemeClasses(
      'grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4',
      currentSize.container
    )}>
      {variants.map((variant) => {
        const isSelected = selectedVariantId === variant.id;
        const imageUrl = showImages ? getPrimaryImage(variant) : null;
        const priceInfo = getDisplayPrice(variant);
        const outOfStock = isOutOfStock(variant);
        const lowStock = isLowStock(variant);

        return (
          <button
            key={variant.id}
            onClick={() => !outOfStock && onVariantSelect(variant)}
            disabled={outOfStock}
            className={combineThemeClasses(
              'relative flex flex-col rounded-lg border-2 transition-all duration-200',
              currentSize.padding,
              isSelected 
                ? 'border-primary bg-primary/5' 
                : combineThemeClasses(themeClasses.border.light, 'hover:border-primary/50'),
              outOfStock 
                ? 'opacity-50 cursor-not-allowed' 
                : 'cursor-pointer hover:shadow-md'
            )}
          >
            {/* Selection Indicator */}
            {isSelected && (
              <div className="absolute top-2 right-2 w-6 h-6 bg-primary rounded-full flex items-center justify-center z-10">
                <CheckIcon className="w-4 h-4 text-white" />
              </div>
            )}

            {/* Variant Image */}
            {showImages && (
              <div className={combineThemeClasses('relative mb-3', currentSize.image, 'mx-auto')}>
                {imageUrl ? (
                  <div className="relative w-full h-full rounded-md overflow-hidden bg-gray-100">
                    {!loadedImages.has(variant.id) && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className={combineThemeClasses(themeClasses.loading.spinner, 'w-4 h-4')}></div>
                      </div>
                    )}
                    <img
                      src={imageUrl}
                      alt={variant.name}
                      className={`w-full h-full object-cover transition-opacity duration-300 ${
                        loadedImages.has(variant.id) ? 'opacity-100' : 'opacity-0'
                      }`}
                      onError={() => handleImageError(variant.id)}
                      onLoad={() => handleImageLoad(variant.id)}
                      loading="lazy"
                    />
                  </div>
                ) : (
                  <div className={combineThemeClasses(
                    'w-full h-full rounded-md flex items-center justify-center border-2 border-dashed',
                    themeClasses.border.light,
                    themeClasses.background.elevated
                  )}>
                    <ImageIcon className={combineThemeClasses(themeClasses.text.muted, 'w-8 h-8')} />
                  </div>
                )}

                {/* Stock Badge */}
                {showStock && (outOfStock || lowStock) && (
                  <div className={combineThemeClasses(
                    'absolute -top-1 -right-1 px-1.5 py-0.5 rounded-full text-xs font-medium',
                    outOfStock 
                      ? 'bg-red-100 text-red-800' 
                      : 'bg-orange-100 text-orange-800'
                  )}>
                    {outOfStock ? 'Out' : 'Low'}
                  </div>
                )}
              </div>
            )}

            {/* Variant Info */}
            <div className="text-center space-y-1">
              <h4 className={combineThemeClasses(
                themeClasses.text.heading,
                'font-medium line-clamp-2',
                currentSize.text
              )}>
                {variant.name}
              </h4>

              <div className="space-y-1">
                <div className="flex items-center justify-center space-x-1">
                  <span className={combineThemeClasses(
                    themeClasses.text.heading,
                    'font-semibold',
                    currentSize.price
                  )}>
                    {formatCurrency(priceInfo.current, currency)}
                  </span>
                  {priceInfo.original && (
                    <span className={combineThemeClasses(
                      themeClasses.text.muted,
                      'line-through text-xs'
                    )}>
                      {formatCurrency(priceInfo.original, currency)}
                    </span>
                  )}
                </div>

                {priceInfo.discount && (
                  <div className="px-1.5 py-0.5 bg-red-100 text-red-800 text-xs rounded-full font-medium inline-block">
                    -{priceInfo.discount}%
                  </div>
                )}

                {showStock && !outOfStock && (
                  <p className={combineThemeClasses(
                    themeClasses.text.muted,
                    'text-xs',
                    lowStock ? 'text-orange-600' : ''
                  )}>
                    {variant.stock} in stock
                  </p>
                )}

                {showSku && variant.sku && (
                  <p className={combineThemeClasses(themeClasses.text.muted, 'text-xs')}>
                    {variant.sku}
                  </p>
                )}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
};