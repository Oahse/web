import React from 'react';
import { LazyImage } from './LazyImage';

export const ProductImage = ({
  src,
  alt,
  className,
  priority,
  sizes
}) => {
  return (
    <LazyImage
      src={src}
      alt={alt}
      className={className}
      priority={priority}
      sizes={sizes || '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw'}
      placeholder="var(--color-surface-hover)"
      loading={priority ? 'eager' : 'lazy'}
      decoding="async"
    />
  );
};
