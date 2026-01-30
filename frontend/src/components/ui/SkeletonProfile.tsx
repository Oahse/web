import React from 'react';
import { Skeleton, SkeletonText, SkeletonRectangle } from './Skeleton';

export const SkeletonProfile = ({
  className = '',
  animation = 'shimmer'
}) => {
  return (
    <div className={`p-3 space-y-3 ${className}`} role="status" aria-label="Loading profile...">
      {/* Profile Header Skeleton */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Skeleton variant="circular" width="64px" height="64px" animation={animation} className="" />
            <div className="ml-3 space-y-2">
              <SkeletonText width="150px" height="20px" animation={animation} />
              <SkeletonText width="200px" height="16px" animation={animation} />
              <div className="flex items-center space-x-2">
                <SkeletonRectangle width="80px" height="20px" rounded="full" animation={animation} className="" />
                <SkeletonText width="60px" height="14px" animation={animation} />
              </div>
            </div>
          </div>
          <SkeletonRectangle width="80px" height="32px" rounded="md" animation={animation} className="" />
        </div>
      </div>

      {/* Profile Information Skeleton */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
        <SkeletonText width="150px" height="18px" animation={animation} className="mb-3" />
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* Form Fields Skeleton */}
          {Array.from({ length: 8 }).map((_, index) => (
            <div key={index}>
              <SkeletonText width="80px" height="14px" animation={animation} className="mb-1" />
              <SkeletonRectangle width="100%" height="32px" rounded="md" animation={animation} className="" />
            </div>
          ))}
        </div>

        {/* Form Actions Skeleton */}
        <div className="mt-4 flex justify-end space-x-2">
          <SkeletonRectangle width="60px" height="32px" rounded="md" animation={animation} className="" />
          <SkeletonRectangle width="100px" height="32px" rounded="md" animation={animation} className="" />
        </div>
      </div>

      {/* Account Information Skeleton */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
        <SkeletonText width="140px" height="18px" animation={animation} className="mb-3" />
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700 last:border-b-0">
              <SkeletonText width="100px" height="14px" animation={animation} />
              <SkeletonText width="80px" height="14px" animation={animation} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
