import { useRef } from 'react';

export const useImagePreloader = () => {
  const preloadedImages = useRef(new Set());

  const preloadImage = (src) => {
    if (preloadedImages.current.has(src)) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        preloadedImages.current.add(src);
        resolve();
      };
      img.onerror = reject;
      img.src = src;
    });
  };

  const preloadImages = (srcs) => {
    return Promise.all(srcs.map(preloadImage));
  };

  return { preloadImage, preloadImages };
};
