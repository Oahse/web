import React, { useState, useRef, useEffect } from 'react';

export const LazyImage = ({
  src,
  alt,
  className = '',
  placeholder,
  blurDataURL,
  width,
  height,
  priority = false,
  onLoad,
  onError,
  sizes,
  srcSet,
  loading = 'lazy',
  decoding = 'async'
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isError, setIsError] = useState(false);
  const [isInView, setIsInView] = useState(priority);
  const imgRef = useRef(null);
  const observerRef = useRef();

  useEffect(() => {
    if (priority || isInView) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true);
            observerRef.current?.disconnect();
          }
        });
      },
      {
        threshold: 0.1,
        rootMargin: '50px'
      }
    );

    if (imgRef.current) {
      observerRef.current.observe(imgRef.current);
    }

    return () => {
      observerRef.current?.disconnect();
    };
  }, [priority, isInView]);

  const handleLoad = () => {
    setIsLoaded(true);
    onLoad?.();
  };

  const handleError = () => {
    setIsError(true);
    onError?.();
  };

  const getOptimizedSrc = (originalSrc, format) => {
    if (!format) return originalSrc;
    
    if (originalSrc.includes('jsdelivr.net') || originalSrc.includes('cloudinary.com')) {
      const url = new URL(originalSrc);
      url.searchParams.set('format', format);
      return url.toString();
    }
    
    return originalSrc;
  };

  const generateSrcSet = () => {
    if (srcSet) return srcSet;
    
    const widths = [320, 640, 768, 1024, 1280, 1536];
    return widths
      .map(w => `${getOptimizedSrc(src)}?w=${w} ${w}w`)
      .join(', ');
  };

  if (isError) {
    return (
      <div 
        className={`${className} bg-gray-200 flex items-center justify-center`}
        style={{ width, height }}
      >
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
    );
  }

  return (
    <div className={`relative overflow-hidden ${className}`} style={{ width, height }}>
      {blurDataURL && !isLoaded && (
        <img
          src={blurDataURL}
          alt=""
          className="absolute inset-0 w-full h-full object-cover filter blur-sm scale-110"
          aria-hidden="true"
        />
      )}
      
      {!blurDataURL && !isLoaded && (
        <div 
          className="absolute inset-0 bg-gray-200 animate-pulse"
          style={{ backgroundColor: placeholder || 'var(--color-surface-hover)' }}
        />
      )}

      {(isInView || priority) && (
        <picture>
          <source
            srcSet={generateSrcSet().replace(/\.(jpg|jpeg|png)/g, '.webp')}
            sizes={sizes || '(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw'}
            type="image/webp"
          />
          
          <source
            srcSet={generateSrcSet().replace(/\.(jpg|jpeg|png)/g, '.avif')}
            sizes={sizes || '(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw'}
            type="image/avif"
          />
          
          <img
            ref={imgRef}
            src={src}
            alt={alt}
            className={`w-full h-full object-cover transition-opacity duration-300 ${
              isLoaded ? 'opacity-100' : 'opacity-0'
            }`}
            onLoad={handleLoad}
            onError={handleError}
            loading={loading}
            decoding={decoding}
            srcSet={generateSrcSet()}
            sizes={sizes || '(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw'}
            width={width}
            height={height}
          />
        </picture>
      )}
    </div>
  );
};