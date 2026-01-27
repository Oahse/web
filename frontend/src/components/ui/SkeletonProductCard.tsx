import React from 'react';
import { Skeleton } from './Skeleton';
import { themeClasses, combineThemeClasses } from '../../lib/themeClasses';

export const SkeletonProductCard: React.FC = () => {
  return (
    <div className={combineThemeClasses(
      themeClasses.card.base,
      themeClasses.border.default,
      'overflow-hidden animate-pulse h-full flex flex-col'
    )}>
      {/* Image Skeleton - Responsive aspect ratio */}
      <div className="relative aspect-[4/3]">
        <div className={combineThemeClasses(
          themeClasses.background.elevated,
          themeClasses.loading.shimmer,
          'absolute inset-0'
        )}></div>
        
        {/* Sale Badge Skeleton - Responsive */}
        <div className="absolute top-1 left-1 sm:top-1.5 sm:left-1.5">
          <Skeleton 
            width="1.5rem" 
            height="0.75rem" 
            className="sm:w-8 sm:h-4 rounded"
          />
        </div>
        
        {/* Quick Actions Skeleton - Responsive */}
        <div className="absolute top-1 right-1 sm:top-1.5 sm:right-1.5 flex flex-col gap-1">
          <Skeleton 
            width="1.25rem" 
            height="1.25rem" 
            variant="circular"
            className="sm:w-6 sm:h-6"
          />
          <Skeleton 
            width="1.25rem" 
            height="1.25rem" 
            variant="circular"
            className="sm:w-6 sm:h-6"
          />
        </div>
      </div>

      {/* Content Skeleton - Responsive padding */}
      <div className="p-2 sm:p-3 space-y-1.5 sm:space-y-2 flex-1 flex flex-col">
        {/* Title Skeleton - Responsive */}
        <div className="space-y-1 flex-1">
          <Skeleton 
            width="100%" 
            height="0.75rem" 
            className="sm:h-3.5"
          />
          <Skeleton 
            width="75%" 
            height="0.75rem" 
            className="sm:h-3.5"
          />
        </div>
        
        {/* Price Skeleton - Responsive */}
        <div className="flex items-center gap-1 sm:gap-1.5">
          <Skeleton 
            width="3rem" 
            height="1rem" 
            className="sm:w-16 sm:h-5"
          />
          <Skeleton 
            width="2rem" 
            height="0.75rem" 
            className="sm:w-10 sm:h-3.5"
          />
        </div>

        {/* Rating Skeleton - Responsive */}
        <div className="flex items-center gap-1">
          <div className="flex gap-0.5">
            {[...Array(5)].map((_, i) => (
              <Skeleton 
                key={i} 
                width="0.625rem" 
                height="0.625rem" 
                variant="circular"
                className="sm:w-3 sm:h-3"
              />
            ))}
          </div>
          <Skeleton 
            width="2rem" 
            height="0.625rem" 
            className="sm:w-10 sm:h-3"
          />
        </div>

        {/* Button Skeleton - Responsive */}
        <Skeleton 
          width="100%" 
          height="1.5rem" 
          className="sm:h-8 rounded-md"
        />

        {/* Stock Info Skeleton - Responsive */}
        <div className="text-center">
          <Skeleton 
            width="3rem" 
            height="0.625rem" 
            className="sm:w-16 sm:h-3 mx-auto"
          />
        </div>
      </div>
    </div>
  );
};