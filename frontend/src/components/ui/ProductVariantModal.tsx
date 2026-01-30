import React, { useState, useEffect } from 'react';
import { XIcon, SearchIcon, PackageIcon, PlusIcon, CheckIcon } from 'lucide-react';
import { useLocale } from '../../store/LocaleContext';
import ProductsAPI from '../../api/products';
import { toast } from 'react-hot-toast';
import { Product } from '../../types';

interface ProductVariantModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectionChange: (selectedVariants: string[]) => void;
  selectedVariants?: string[];
  multiSelect?: boolean;
  title?: string;
  showOnlyAvailable?: boolean;
}

export const ProductVariantModal: React.FC<ProductVariantModalProps> = ({
  isOpen,
  onClose,
  onSelectionChange,
  selectedVariants = [],
  multiSelect = true,
  title = 'Select Products & Variants',
  showOnlyAvailable = false
}) => {
  const { formatCurrency: formatCurrencyLocale, locale } = useLocale();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set(selectedVariants));
  const [expandedProducts, setExpandedProducts] = useState<Set<string>>(new Set());
  
  // Default currency - in a real app this might come from user preferences or a currency context
  const currency = 'USD';

  useEffect(() => {
    if (isOpen) {
      loadProducts();
    }
  }, [isOpen, searchQuery]);

  useEffect(() => {
    setSelected(new Set(selectedVariants));
  }, [selectedVariants]);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const response = await ProductsAPI.getProducts({ 
        q: searchQuery,
        page: 1,
        limit: 50 
      });
      
      const products = response.data?.data || response.data || [];
      setProducts(Array.isArray(products) ? products : []);
    } catch (error) {
      console.error('Failed to load products:', error);
      toast.error('Failed to load products');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleVariantToggle = (variantId: string) => {
    const newSelected = new Set(selected);
    
    if (multiSelect) {
      if (newSelected.has(variantId)) {
        newSelected.delete(variantId);
      } else {
        newSelected.add(variantId);
      }
    } else {
      // Single select mode
      newSelected.clear();
      newSelected.add(variantId);
    }
    
    setSelected(newSelected);
    onSelectionChange(Array.from(newSelected));
  };

  const toggleProductExpansion = (productId: string) => {
    const newExpanded = new Set(expandedProducts);
    if (newExpanded.has(productId)) {
      newExpanded.delete(productId);
    } else {
      newExpanded.add(productId);
    }
    setExpandedProducts(newExpanded);
  };

  const getVariantAvailability = (variant: any) => {
    if (!showOnlyAvailable) return null;
    
    const inventory = variant.inventory;
    if (!inventory) return null;
    
    const isAvailable = inventory.quantity_available > 0;
    return isAvailable;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 w-full max-w-4xl max-h-[90vh] flex flex-col rounded-lg shadow-xl">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">{title}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <XIcon size={24} />
            </button>
          </div>
          
          {/* Search */}
          <div className="relative">
            <SearchIcon size={20} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search products by name..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          {/* Selected Summary */}
          {selected.size > 0 && (
            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                    {selected.size}
                  </div>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {selected.size} variant{selected.size !== 1 ? 's' : ''} selected
                  </span>
                </div>
                <button
                  onClick={() => {
                    setSelected(new Set());
                    onSelectionChange([]);
                  }}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Clear all
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
              <span className="ml-3 text-gray-600 dark:text-gray-400">Loading products...</span>
            </div>
          ) : products.length === 0 ? (
            <div className="text-center py-12">
              <PackageIcon size={48} className="text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400 mb-2">
                {searchQuery ? 'No products found matching your search.' : 'No products available.'}
              </p>
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="text-primary hover:underline text-sm"
                >
                  Clear search
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {products.map((product) => (
                <div key={product.id} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  {/* Product Header */}
                  <div 
                    className="p-4 bg-gray-50 dark:bg-gray-800 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    onClick={() => toggleProductExpansion(product.id)}
                  >
                    <div className="flex items-center gap-3">
                      {product.images && product.images.length > 0 ? (
                        <img
                          src={product.images[0].url}
                          alt={product.name}
                          className="w-12 h-12 rounded-lg object-cover border border-gray-300 dark:border-gray-600 flex-shrink-0"
                        />
                      ) : (
                        <div className="w-12 h-12 rounded-lg bg-gray-200 dark:bg-gray-600 flex items-center justify-center flex-shrink-0">
                          <PackageIcon className="w-6 h-6 text-gray-400" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-gray-900 dark:text-white truncate">
                          {product.name}
                        </h3>
                        {product.description && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 truncate mt-1">
                            {product.description}
                          </p>
                        )}
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {formatCurrencyLocale(product.price || product.min_price || 0, currency)}
                          </span>
                          {product.min_price !== product.max_price && product.max_price && (
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                              - {formatCurrencyLocale(product.max_price, currency)}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {product.variants && product.variants.length > 0 && (
                          <span className="text-sm text-gray-500 dark:text-gray-400">
                            {product.variants.length} variant{product.variants.length !== 1 ? 's' : ''}
                          </span>
                        )}
                        <div className={`transform transition-transform ${expandedProducts.has(product.id) ? 'rotate-180' : ''}`}>
                          <PlusIcon size={20} className="text-gray-400" />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Variants */}
                  {expandedProducts.has(product.id) && product.variants && product.variants.length > 0 && (
                    <div className="p-4 space-y-2">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        Available Variants:
                      </p>
                      {product.variants.map((variant: any) => {
                        const isSelected = selected.has(variant.id);
                        const isAvailable = getVariantAvailability(variant);
                        
                        return (
                          <label
                            key={variant.id}
                            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                              isSelected 
                                ? 'border-primary bg-primary/5 dark:bg-primary/10' 
                                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                            } ${showOnlyAvailable && isAvailable === false ? 'opacity-50 cursor-not-allowed' : ''}`}
                          >
                            <input
                              type={multiSelect ? 'checkbox' : 'radio'}
                              checked={isSelected}
                              onChange={() => handleVariantToggle(variant.id)}
                              disabled={showOnlyAvailable && isAvailable === false}
                              className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
                            />
                            
                            {/* Variant Image */}
                            {variant.images?.[0]?.url ? (
                              <img
                                src={variant.images[0].url}
                                alt={variant.name}
                                className="w-10 h-10 rounded object-cover border border-gray-300 dark:border-gray-600 flex-shrink-0"
                              />
                            ) : (
                              <div className="w-10 h-10 rounded bg-gray-200 dark:bg-gray-600 flex items-center justify-center flex-shrink-0">
                                <PackageIcon className="w-5 h-5 text-gray-400" />
                              </div>
                            )}

                            {/* Variant Info */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-gray-900 dark:text-white text-sm">
                                  {variant.name || "Default Variant"}
                                </span>
                                {variant.sku && (
                                  <span className="text-xs text-gray-500 dark:text-gray-400">
                                    SKU: {variant.sku}
                                  </span>
                                )}
                              </div>
                              {showOnlyAvailable && variant.inventory && (
                                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                  Stock: {variant.inventory.quantity_available || 0}
                                </div>
                              )}
                            </div>

                            {/* Price and Selection */}
                            <div className="flex items-center gap-3">
                              <span className="font-medium text-gray-900 dark:text-white text-sm">
                                {formatCurrencyLocale(
                                  variant.current_price || variant.base_price || variant.price || 0,
                                  currency
                                )}
                              </span>
                              {isSelected && (
                                <div className="w-5 h-5 bg-primary text-white rounded-full flex items-center justify-center">
                                  <CheckIcon size={12} />
                                </div>
                              )}
                            </div>
                          </label>
                        );
                      })}
                    </div>
                  )}

                  {/* No variants case */}
                  {expandedProducts.has(product.id) && (!product.variants || product.variants.length === 0) && (
                    <div className="p-4">
                      <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-600 cursor-pointer hover:border-gray-300 dark:hover:border-gray-500 transition-colors">
                        <input
                          type={multiSelect ? 'checkbox' : 'radio'}
                          checked={selected.has(product.id)}
                          onChange={() => handleVariantToggle(product.id)}
                          className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
                        />
                        <div className="flex-1">
                          <span className="font-medium text-gray-900 dark:text-white text-sm">
                            Default Variant
                          </span>
                        </div>
                        <span className="font-medium text-gray-900 dark:text-white text-sm">
                          {formatCurrencyLocale(product.price || 0, currency)}
                        </span>
                        {selected.has(product.id) && (
                          <div className="w-5 h-5 bg-primary text-white rounded-full flex items-center justify-center">
                            <CheckIcon size={12} />
                          </div>
                        )}
                      </label>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={selected.size === 0}
            >
              {multiSelect 
                ? `Select ${selected.size} variant${selected.size !== 1 ? 's' : ''}`
                : selected.size > 0 ? 'Select Variant' : 'Select a Variant'
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductVariantModal;
