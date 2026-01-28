import React, { useEffect } from 'react';
import { useApi } from '../../hooks/useAsync';
import { apiClient, ProductsAPI } from '../../apis';
import { getBestPrice } from '../../utils/price-utils';

/**
 * @typedef {object} OrderItemDetailsProps
 * @property {string} productId
 * @property {number} quantity
 * @property {number} price
 */

export const OrderItemDetails = ({ productId, quantity, price }) => {
  const { data: product, loading, error, execute } = useApi();

  useEffect(() => {
    if (productId) {
      execute(() => ProductsAPI.getProduct(productId));
    }
  }, [productId, execute]);

  if (loading) {
    return <div className="flex items-center space-x-4">
      <div className="w-16 h-16 bg-gray-200 rounded animate-pulse"></div>
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse"></div>
        <div className="h-3 bg-gray-200 rounded w-1/4 animate-pulse"></div>
      </div>
      <div className="h-4 bg-gray-200 rounded w-12 animate-pulse"></div>
    </div>;
  }

  if (error) {
    return <div className="text-error text-sm">Error loading product</div>;
  }

  if (!product) {
    return null;
  }

  const variant = product.variants?.[0];
  const image = variant?.images?.[0];

  return (
    <div className="flex items-center space-x-4">
      {image ? (
        <img src={image.url} alt={image.alt_text || product.name} className="w-16 h-16 object-cover rounded" />
      ) : (
        <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center">
          <span className="text-xs text-gray-500">No Image</span>
        </div>
      )}
      <div className="flex-1">
        <h3 className="font-medium text-main dark:text-white">
          {product.name}
        </h3>
        {variant?.name && (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Variant: {variant.name}
          </p>
        )}
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Quantity: {quantity} × ${(() => {
            const unitPrice = price / quantity;
            const variantPrice = getBestPrice(variant || {});
            // Use the order item price if available, otherwise fall back to variant price
            const displayPrice = unitPrice > 0 ? unitPrice : variantPrice;
            return displayPrice.toFixed(2);
          })()}
        </p>
      </div>
      <p className="font-medium text-main dark:text-white">
        ${price.toFixed(2)}
      </p>
    </div>
  );
};
