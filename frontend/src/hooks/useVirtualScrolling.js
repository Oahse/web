import { useState, useRef, useEffect } from 'react';

export const useVirtualScrolling = ({
  itemHeight,
  totalItems,
  overscan = 3,
  containerRef,
}) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [containerHeight, setContainerHeight] = useState(0);

  const handleScroll = () => {
    if (containerRef.current) {
      setScrollTop(containerRef.current.scrollTop);
    }
  };

  const handleResize = () => {
    if (containerRef.current) {
      setContainerHeight(containerRef.current.offsetHeight);
    }
  };

  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      handleResize();
      container.addEventListener('scroll', handleScroll);
      window.addEventListener('resize', handleResize);

      return () => {
        container.removeEventListener('scroll', handleScroll);
        window.removeEventListener('resize', handleResize);
      };
    }
  }, [containerRef]);

  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    totalItems - 1,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );

  const visibleItems = Array.from({ length: totalItems })
    .map((_, index) => index)
    .slice(startIndex, endIndex + 1);

  const totalHeight = totalItems * itemHeight;
  const offset = startIndex * itemHeight;

  return {
    visibleItems,
    totalHeight,
    offset,
    startIndex,
    endIndex,
  };
};
