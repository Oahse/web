import React from 'react';
import { Skeleton, SkeletonText, SkeletonRectangle } from './Skeleton';

export const SkeletonAddresses = ({
  count = 3,
  className = '',
  animation = 'shimmer'
}) => {
  return (
    <div className={`space-y-4 ${className}`} role="status" aria-label="Loading addresses...">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1 space-y-3">
              {/* Address Type Badge */}
              <div className="flex items-center space-x-2">
                <SkeletonRectangle width="80px" height="20px" rounded="full" animation={animation} className="" />
                <SkeletonRectangle width="60px" height="20px" rounded="full" animation={animation} className="" />
              </div>
              
              {/* Address Lines */}
              <div className="space-y-2">
                <SkeletonText width="200px" animation={animation} />
                <SkeletonText width="180px" animation={animation} />
                <SkeletonText width="160px" animation={animation} />
                <SkeletonText width="140px" animation={animation} />
              </div>
              
              {/* Location Info */}
              <div className="flex items-center space-x-4 pt-2">
                <div className="flex items-center space-x-2">
                  <Skeleton variant="circular" width="16px" height="16px" animation={animation} className="" />
                  <SkeletonText width="100px" height="14px" animation={animation} />
                </div>
                <div className="flex items-center space-x-2">
                  <Skeleton variant="circular" width="16px" height="16px" animation={animation} className="" />
                  <SkeletonText width="80px" height="14px" animation={animation} />
                </div>
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="flex space-x-2 ml-4">
              <SkeletonRectangle width="32px" height="32px" rounded="md" animation={animation} className="" />
              <SkeletonRectangle width="32px" height="32px" rounded="md" animation={animation} className="" />
            </div>
          </div>
        </div>
      ))}
      
      {/* Add Address Button Skeleton */}
      <div className="flex justify-center pt-4">
        <SkeletonRectangle width="200px" height="40px" rounded="md" animation={animation} className="" />
      </div>
    </div>
  );
};
