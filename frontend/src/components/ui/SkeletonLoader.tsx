import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
  width?: string | number;
  height?: string | number;
  lines?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'text',
  width,
  height,
  lines = 1
}) => {
  const baseClasses = 'animate-pulse bg-gray-200 dark:bg-gray-700';
  
  const variantClasses = {
    text: 'h-4 rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-md',
    rounded: 'rounded-lg'
  };

  const style = {
    width: width || (variant === 'text' ? '100%' : undefined),
    height: height || (variant === 'text' ? '1rem' : undefined)
  };

  if (variant === 'text' && lines > 1) {
    return (
      <div className={`space-y-2 ${className}`}>
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={index}
            className={`${baseClasses} ${variantClasses[variant]}`}
            style={{
              width: index === lines - 1 ? '70%' : '100%',
              height: height || '1rem'
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
    />
  );
};

// Page Skeleton Components
export const PageSkeleton: React.FC = () => (
  <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
    <div className="animate-pulse">
      {/* Header Skeleton */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded" />
              <div className="w-32 h-6 bg-gray-200 dark:bg-gray-700 rounded" />
            </div>
            <div className="flex items-center space-x-4">
              <div className="w-20 h-8 bg-gray-200 dark:bg-gray-700 rounded" />
              <div className="w-24 h-8 bg-gray-200 dark:bg-gray-700 rounded" />
            </div>
          </div>
        </div>
      </div>

      {/* Content Skeleton */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
                <div className="space-y-4">
                  <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full" />
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  </div>
);

// Product List Skeleton
export const ProductListSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {Array.from({ length: 8 }).map((_, index) => (
        <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
          <div className="h-48 bg-gray-200 dark:bg-gray-700" />
          <div className="p-4 space-y-3">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
          </div>
        </div>
      ))}
    </div>
  </div>
);

// Product Detail Skeleton
export const ProductDetailSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div>
        <div className="h-96 bg-gray-200 dark:bg-gray-700 rounded-lg" />
        <div className="grid grid-cols-4 gap-2 mt-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-20 bg-gray-200 dark:bg-gray-700 rounded" />
          ))}
        </div>
      </div>
      <div className="space-y-4">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full" />
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
        <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-full" />
        <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-full" />
      </div>
    </div>
  </div>
);

// Cart Skeleton
export const CartSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="space-y-4">
      {Array.from({ length: 3 }).map((_, index) => (
        <div key={index} className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-gray-200 dark:bg-gray-700 rounded" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
            </div>
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-16" />
          </div>
        </div>
      ))}
    </div>
    <div className="mt-8 bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
      <div className="space-y-4">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
        <div className="space-y-2">
          <div className="flex justify-between">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20" />
          </div>
          <div className="flex justify-between">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20" />
          </div>
        </div>
        <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded" />
      </div>
    </div>
  </div>
);

// Checkout Skeleton
export const CheckoutSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div className="lg:col-span-2 space-y-6">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4" />
            <div className="space-y-4">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full" />
              <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-full" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
              <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-full" />
            </div>
          </div>
        ))}
      </div>
      <div className="space-y-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4" />
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20" />
              </div>
              <div className="flex justify-between">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20" />
              </div>
            </div>
            <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded" />
          </div>
        </div>
      </div>
    </div>
  </div>
);

// Account Skeleton
export const AccountSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div className="md:col-span-1">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
          <div className="space-y-4">
            <div className="w-16 h-16 bg-gray-200 dark:bg-gray-700 rounded-full mx-auto" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mx-auto" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mx-auto" />
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, index) => (
                <div key={index} className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full" />
              ))}
            </div>
          </div>
        </div>
      </div>
      <div className="md:col-span-3">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
          <div className="space-y-6">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="border-b border-gray-200 dark:border-gray-700 pb-4">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mt-2" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// Admin Dashboard Skeleton
export const AdminDashboardSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
            </div>
          </div>
        ))}
      </div>

      {/* Recent Orders */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4" />
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, index) => (
                <div key={index} className="border-b border-gray-200 dark:border-gray-700 pb-3">
                  <div className="flex items-center space-x-4">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20" />
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16" />
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4" />
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="h-10 bg-gray-200 dark:bg-gray-700 rounded" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// Admin Table Skeleton
export const AdminTableSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-64" />
          <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-32" />
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              {Array.from({ length: 5 }).map((_, index) => (
                <th key={index} className="px-4 py-3">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20" />
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {Array.from({ length: 10 }).map((_, index) => (
              <tr key={index}>
                {Array.from({ length: 5 }).map((_, colIndex) => (
                  <td key={colIndex} className="px-4 py-3">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

export default Skeleton;
