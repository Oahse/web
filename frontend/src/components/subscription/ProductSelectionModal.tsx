import React, { useState, useEffect } from 'react';
import { XIcon, SearchIcon, PlusIcon, MinusIcon, ShoppingBagIcon } from 'lucide-react';
import { themeClasses, combineThemeClasses, getButtonClasses } from '../../utils/themeClasses';
import { ProductsAPI } from '../../api/products';
import { SubscriptionProductCard } from './SubscriptionProductCard';
import { VariantSelector } from './VariantSelector';
import { toast } from 'react-hot-toast';

interface Product {
  id: string;
  name: string;
  price: number;
  images?: Array<{ url: string; is_primary?: boolean }>;
  primary_image?: { url: string };
  variants?: Array<{
    id: string;
    name: string;
    price: number;
    sale_price?: number;
    stock: number;
    sku?: string;
    images?: Array<{ url: string; is_primary?: boolean }>;
    primary_image?: { url: string };
    attributes?: { [key: string]: string };
  }>;
}

interface ProductSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProductsSelected: (selectedVariantIds: string[]) => void;
  title?: string;
  selectedProducts?: Set<string>;
  currency?: string;
}

export const ProductSelectionModal: React.FC<ProductSelectionModalProps> = ({
  isOpen,
  onClose,
  onProductsSelected,
  title = 'Select Products',
  selectedProducts = new Set(),
  currency = 'USD'
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVariants, setSelectedVariants] = useState<Set<string>>(new Set(selectedProducts));
  const [expandedProducts, setExpandedProducts] = useState<Set<string>>(new Set());
  const [selectedVariantsByProduct, setSelectedVariantsByProduct] = useState<{ [productId: string]: string }>({});

  useEffect(() => {
    if (isOpen) {
      loadProducts();
    }
  }, [isOpen, searchQuery]);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const response = await ProductsAPI.getProducts({
        q: searchQuery,
        page: 1,
        limit: 20,
        availability: true
      });
      setProducts(response.data.data || []);
    } catch (error) {
      console.error('Failed to load products:', error);
      toast.error('Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  const toggleProductExpansion = (productId: string) => {
    setExpandedProducts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(productId)) {
        newSet.delete(productId);
      } else {
        newSet.add(productId);
      }
      return newSet;
    });
  };

  const handleVariantSelect = (productId: string, variant: any) => {
    setSelectedVariantsByProduct(prev => ({
      ...prev,
      [productId]: variant.id
    }));

    // Add to selected variants
    setSelectedVariants(prev => {
      const newSet = new Set(prev);
      // Remove any previously selected variant from this product
      const product = products.find(p => p.id === productId);
      if (product?.variants) {
        product.variants.forEach(v => newSet.delete(v.id));
      }
      // Add the new variant
      newSet.add(variant.id);
      return newSet;
    });
  };

  const toggleVariantSelection = (variantId: string) => {
    setSelectedVariants(prev => {
      const newSet = new Set(prev);
      if (newSet.has(variantId)) {
        newSet.delete(variantId);
        // Also remove from selectedVariantsByProduct
        const productId = products.find(p => 
          p.variants?.some(v => v.id === variantId)
        )?.id;
        if (productId) {
          setSelectedVariantsByProduct(prev => {
            const newMap = { ...prev };
            delete newMap[productId];
            return newMap;
          });
        }
      } else {
        newSet.add(variantId);
      }
      return newSet;
    });
  };

  const handleConfirm = () => {
    onProductsSelected(Array.from(selectedVariants));
    onClose();
  };

  const getSelectedVariantForProduct = (product: Product) => {
    const selectedVariantId = selectedVariantsByProduct[product.id];
    return product.variants?.find(v => v.id === selectedVariantId);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className={combineThemeClasses(
        themeClasses.background.surface,
        'rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col'
      )}>
        {/* Header */}
        <div className={combineThemeClasses(
          'flex items-center justify-between p-6 border-b',
          themeClasses.border.light
        )}>
          <h2 className={combineThemeClasses(themeClasses.text.heading, 'text-xl font-semibold')}>
            {title}
          </h2>
          <button
            onClick={onClose}
            className={combineThemeClasses(
              'p-2 rounded-lg transition-colors duration-200',
              themeClasses.text.muted
            )}
          >
            <XIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Search */}
        <div className="p-6 pb-4">
          <div className="relative">
            <SearchIcon className={combineThemeClasses(
              'absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5',
              themeClasses.text.muted
            )} />
            <input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={combineThemeClasses(
                themeClasses.input.base,
                themeClasses.input.default,
                'pl-10 w-full'
              )}
            />
          </div>
        </div>

        {/* Selected Count */}
        {selectedVariants.size > 0 && (
          <div className={combineThemeClasses(
            'px-6 pb-4 flex items-center justify-between',
            themeClasses.background.elevated,
            'border-b',
            themeClasses.border.light
          )}>
            <div className="flex items-center space-x-2">
              <ShoppingBagIcon className={combineThemeClasses(themeClasses.text.primary, 'w-5 h-5')} />
              <span className={combineThemeClasses(themeClasses.text.primary, 'font-medium')}>
                {selectedVariants.size} product{selectedVariants.size !== 1 ? 's' : ''} selected
              </span>
            </div>
            <button
              onClick={() => {
                setSelectedVariants(new Set());
                setSelectedVariantsByProduct({});
              }}
              className={combineThemeClasses(
                themeClasses.text.secondary,
                'text-sm hover:text-red-600 transition-colors duration-200'
              )}
            >
              Clear all
            </button>
          </div>
        )}

        {/* Products List */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className={combineThemeClasses(themeClasses.loading.spinner, 'w-8 h-8')}></div>
            </div>
          ) : products.length === 0 ? (
            <div className="text-center py-12">
              <p className={themeClasses.text.secondary}>
                {searchQuery ? 'No products found matching your search.' : 'No products available.'}
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {products.map((product) => (
                <div key={product.id} className={combineThemeClasses(
                  themeClasses.card.base,
                  'overflow-hidden'
                )}>
                  {/* Product Header */}
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {product.primary_image?.url || product.images?.[0]?.url ? (
                          <img
                            src={product.primary_image?.url || product.images?.[0]?.url}
                            alt={product.name}
                            className="w-12 h-12 rounded-lg object-cover"
                          />
                        ) : (
                          <div className={combineThemeClasses(
                            'w-12 h-12 rounded-lg flex items-center justify-center border-2 border-dashed',
                            themeClasses.border.light,
                            themeClasses.background.elevated
                          )}>
                            <ShoppingBagIcon className={combineThemeClasses(themeClasses.text.muted, 'w-6 h-6')} />
                          </div>
                        )}
                        <div>
                          <h3 className={combineThemeClasses(themeClasses.text.heading, 'font-medium')}>
                            {product.name}
                          </h3>
                          <p className={combineThemeClasses(themeClasses.text.secondary, 'text-sm')}>
                            {product.variants?.length || 0} variant{(product.variants?.length || 0) !== 1 ? 's' : ''}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        {product.variants && product.variants.length > 1 && (
                          <button
                            onClick={() => toggleProductExpansion(product.id)}
                            className={combineThemeClasses(
                              getButtonClasses('outline'),
                              'text-sm'
                            )}
                          >
                            {expandedProducts.has(product.id) ? 'Hide Variants' : 'Show Variants'}
                          </button>
                        )}
                        
                        {product.variants && product.variants.length === 1 && (
                          <button
                            onClick={() => toggleVariantSelection(product.variants![0].id)}
                            className={combineThemeClasses(
                              selectedVariants.has(product.variants![0].id) 
                                ? getButtonClasses('primary')
                                : getButtonClasses('outline'),
                              'text-sm'
                            )}
                          >
                            {selectedVariants.has(product.variants![0].id) ? (
                              <>
                                <MinusIcon className="w-4 h-4 mr-1" />
                                Remove
                              </>
                            ) : (
                              <>
                                <PlusIcon className="w-4 h-4 mr-1" />
                                Add
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Variants */}
                  {product.variants && product.variants.length > 1 && expandedProducts.has(product.id) && (
                    <div className={combineThemeClasses(
                      'border-t p-4',
                      themeClasses.border.light,
                      themeClasses.background.elevated
                    )}>
                      <VariantSelector
                        variants={product.variants}
                        selectedVariantId={selectedVariantsByProduct[product.id]}
                        onVariantSelect={(variant) => handleVariantSelect(product.id, variant)}
                        currency={currency}
                        showImages={true}
                        showStock={true}
                        showSku={true}
                        layout="grid"
                        size="sm"
                      />
                      
                      {selectedVariantsByProduct[product.id] && (
                        <div className="mt-4 flex justify-end">
                          <button
                            onClick={() => toggleVariantSelection(selectedVariantsByProduct[product.id])}
                            className={combineThemeClasses(
                              selectedVariants.has(selectedVariantsByProduct[product.id])
                                ? getButtonClasses('primary')
                                : getButtonClasses('outline'),
                              'text-sm'
                            )}
                          >
                            {selectedVariants.has(selectedVariantsByProduct[product.id]) ? (
                              <>
                                <MinusIcon className="w-4 h-4 mr-1" />
                                Remove from Selection
                              </>
                            ) : (
                              <>
                                <PlusIcon className="w-4 h-4 mr-1" />
                                Add to Selection
                              </>
                            )}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className={combineThemeClasses(
          'flex items-center justify-between p-6 border-t',
          themeClasses.border.light,
          themeClasses.background.elevated
        )}>
          <span className={combineThemeClasses(themeClasses.text.secondary, 'text-sm')}>
            {selectedVariants.size} product{selectedVariants.size !== 1 ? 's' : ''} selected
          </span>
          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className={combineThemeClasses(getButtonClasses('outline'))}
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={selectedVariants.size === 0}
              className={combineThemeClasses(
                getButtonClasses('primary'),
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              Add {selectedVariants.size} Product{selectedVariants.size !== 1 ? 's' : ''}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};