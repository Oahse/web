import React from 'react';
import { Skeleton } from './Skeleton';

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
      {/* Image Skeleton - Smaller aspect ratio */}
      <div className="relative aspect-[4/3]">
        <div className={combineThemeClasses(
          themeClasses.background.elevated,
          'absolute inset-0 bg-gradient-to-r animate-shimmer bg-[length:200%_100%]'
        )}></div>
        
        {/* Sale Badge Skeleton */}
        <div className="absolute top-1.5 left-1.5">
          <Skeleton className={combineThemeClasses(themeClasses.background.surface, 'w-8 h-4 rounded')} />
        </div>
        
        {/* Quick Actions Skeleton */}
        <div className="absolute top-1.5 right-1.5 flex flex-col gap-1">
          <Skeleton className={combineThemeClasses(themeClasses.background.surface, 'w-6 h-6 rounded-full')} />
          <Skeleton className={combineThemeClasses(themeClasses.background.surface, 'w-6 h-6 rounded-full')} />
        </div>
      </div>

      {/* Content Skeleton - More compact */}
      <div className="p-2 sm:p-3 space-y-2 flex-1 flex flex-col">
        {/* Title Skeleton */}
        <div className="space-y-1 flex-1">
          <Skeleton className={combineThemeClasses(themeClasses.background.surface, 'w-full h-3')} />
          <Skeleton className={combineThemeClasses(themeClasses.background.surface, 'w-3/4 h-3')} />
        </div>
        
        {/* Price Skeleton */}
        <div className="flex items-center gap-1.5">
          <Skeleton className={combineThemeClasses(themeClasses.background.surface, 'w-12 h-4')} />
          <Skeleton className={combineThemeClasses(themeClasses.background.surface, 'w-8 h-3')} />
        </div>

        {/* Rating Skeleton */}
        <div className="flex items-center gap-1">
          <div className="flex gap-0.5">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className={combineThemeClasses(themeClasses.background.surface, 'w-2.5 h-2.5')} />
            ))}
          </div>
          <Skeleton className={combineThemeClasses(themeClasses.background.surface, 'w-8 h-2.5')} />
        </div>

        {/* Button Skeleton */}
        <Skeleton className={combineThemeClasses(themeClasses.background.surface, 'w-full h-7 sm:h-8 rounded-md')} />

        {/* Stock Info Skeleton */}
        <div className="text-center">
          <Skeleton className={combineThemeClasses(themeClasses.background.surface, 'w-16 h-2.5 mx-auto')} />
        </div>
      </div>
    </div>
  );
};