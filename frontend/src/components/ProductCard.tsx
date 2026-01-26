import React from 'react';
import CartButton from './CartButton';

export const ProductCard = ({ product }: { product: any }) => {
  const variant = product.variants?.[0] || product;
  const image = variant.primary_image?.url || variant.images?.[0]?.url || '/placeholder.jpg';
  const price = variant.current_price || variant.base_price;
  const salePrice = variant.sale_price;
  const isOnSale = salePrice && salePrice < price;
  const discount = isOnSale ? Math.round(((price - salePrice) / price) * 100) : 0;

  return (
    <div className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
      {/* Image */}
      <div className="relative aspect-square overflow-hidden rounded-t-lg">
        <img
          src={image}
          alt={product.name}
          className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
          onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
            const target = e.target as HTMLImageElement;
            target.src = '/placeholder.jpg';
          }}
        />
        {isOnSale && (
          <div className="absolute top-2 left-2 bg-red-500 text-white px-2 py-1 rounded text-xs font-medium">
            -{discount}%
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="product-title text-base truncate mb-2">
          {product.name}
        </h3>
        
        {/* Price */}
        <div className="flex items-center gap-2 mb-3">
          <span className="price text-lg">
            ${(isOnSale ? salePrice : price).toFixed(2)}
          </span>
          {isOnSale && (
            <span className="price text-sm text-gray-500 line-through">
              ${price.toFixed(2)}
            </span>
          )}
        </div>

        {/* Rating */}
        {product.rating_average > 0 && (
          <div className="flex items-center gap-1 mb-3 text-sm text-gray-600">
            <span>⭐</span>
            <span className="body-text">{product.rating_average.toFixed(1)}</span>
            <span className="body-text">({product.rating_count})</span>
          </div>
        )}

        {/* Add to Cart */}
        <CartButton
          variant={variant}
          className="w-full"
          size="sm"
          disabled={!variant.is_active || variant.stock === 0}
        />

        {/* Stock info */}
        {variant.stock <= 5 && variant.stock > 0 && (
          <p className="body-text text-xs text-orange-600 mt-2">
            Only {variant.stock} left!
          </p>
        )}
        {variant.stock === 0 && (
          <p className="body-text text-xs text-red-600 mt-2">Out of stock</p>
        )}
      </div>
    </div>
  );
};

export default ProductCard;