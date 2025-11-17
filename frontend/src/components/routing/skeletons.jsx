import React from 'react';
import { Skeleton } from '../ui/Skeleton';

// Enhanced loading components with skeletons
export const PageSkeleton = () => (
  <div className="min-h-screen bg-background p-4">
    <div className="max-w-7xl mx-auto">
      <Skeleton variant="rectangular" width="100%" height={60} className="mb-6" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          <Skeleton variant="rectangular" width="100%" height={400} className="mb-4" />
          <Skeleton variant="text" width="80%" height={24} className="mb-2" />
          <Skeleton variant="text" width="60%" height={20} className="mb-2" />
          <Skeleton variant="text" width="90%" height={20} />
        </div>
        <div>
          <Skeleton variant="rectangular" width="100%" height={200} className="mb-4" />
          <Skeleton variant="text" width="100%" height={20} className="mb-2" />
          <Skeleton variant="text" width="80%" height={20} />
        </div>
      </div>
    </div>
  </div>
);

export const ProductListSkeleton = () => (
  <div className="min-h-screen bg-background p-4">
    <div className="max-w-7xl mx-auto">
      <Skeleton variant="text" width={300} height={32} className="mb-6" />
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm p-4">
            <Skeleton variant="rectangular" width="100%" height={200} className="mb-4" />
            <Skeleton variant="text" width="100%" height={20} className="mb-2" />
            <Skeleton variant="text" width="60%" height={16} className="mb-2" />
            <Skeleton variant="text" width="40%" height={20} />
          </div>
        ))}
      </div>
    </div>
  </div>
);

export const DashboardSkeleton = () => (
  <div className="min-h-screen bg-background p-4">
    <div className="max-w-7xl mx-auto">
      <Skeleton variant="text" width={200} height={32} className="mb-6" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm p-6">
            <Skeleton variant="text" width="80%" height={16} className="mb-2" />
            <Skeleton variant="text" width="60%" height={24} />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Skeleton variant="rectangular" width="100%" height={300} />
        <Skeleton variant="rectangular" width="100%" height={300} />
      </div>
    </div>
  </div>
);

// Route preloader utility
export const preloadRoutes = () => {
  // Preload critical routes after initial render
  setTimeout(() => {
    import('../../pages/Cart');
    import('../../pages/Login');
    import('../../pages/Register');
  }, 2000);
  
  // Preload admin routes when user hovers over admin links
  const preloadAdminRoutes = () => {
    import('../../pages/admin/AdminDashboard');
    import('../../pages/admin/AdminProducts');
    import('../../pages/admin/AdminUsers');
  };
  
  // Add hover listeners for admin navigation
  const adminLinks = document.querySelectorAll('[href*="/admin"]');
  adminLinks.forEach(link => {
    link.addEventListener('mouseenter', preloadAdminRoutes, { once: true });
  });
};