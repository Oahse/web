import { useEffect, Suspense, lazy } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../store/AuthContext';
import AccountLayout from '../components/account/AccountLayout';
import { ProtectedRoute } from '../components/ProtectedRoute';

// Account Skeleton for loading states
const AccountSkeleton = () => (
  <div className="animate-pulse space-y-4">
    <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
    <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
  </div>
);

// Lazy load account components
const Dashboard = lazy(() => import('../components/account/Dashboard'));
const Profile = lazy(() => import('../components/account/Profile'));
const Orders = lazy(() => import('../components/account/Orders'));
const OrderDetail = lazy(() => import('../components/account/OrderDetail'));
const TrackOrder = lazy(() => import('../components/account/TrackOrder'));
const ShipmentTracking = lazy(() => import('../components/shipping/ShipmentTracking'));
const Wishlist = lazy(() => import('../components/account/Wishlist'));
const WishlistEdit = lazy(() => import('../pages/WishlistEdit'));
const Addresses = lazy(() => import('../components/account/Addresses'));
const MySubscriptions = lazy(() => import('../components/account/MySubscriptions').then(module => ({ default: module.MySubscriptions })));
const SubscriptionEdit = lazy(() => import('../pages/SubscriptionEdit'));
const SubscriptionOrders = lazy(() => import('../components/account/SubscriptionOrders').then(module => ({ default: module.SubscriptionOrders })));
const PaymentMethods = lazy(() => import('../components/account/PaymentMethods').then(module => ({ default: module.PaymentMethods })));

// Loading Spinner
const LoadingSpinner = () => (
  <div className="flex items-center justify-center h-64">
    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
  </div>
);

// Main Account Component
export const Account = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAdmin, isSupplier } = useAuth();

  useEffect(() => {
    if (!user) {
      navigate('/login');
    }
  }, [user, navigate]);

  if (!user) {
    return <LoadingSpinner />;
  }

  return (
    <AccountLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/orders" element={<Orders />} />
        <Route path="/orders/:orderId" element={<OrderDetail />} />
        <Route path="/tracking" element={<TrackOrder />} />
        <Route path="/tracking/:shipmentId" element={<ShipmentTracking />} />
        <Route path="/wishlist" element={<Wishlist />} />
        <Route path="/wishlist/:wishlistId/edit" element={<WishlistEdit />} />
        <Route path="/addresses" element={<Addresses />} />
        <Route path="/payment-methods" element={<PaymentMethods />} />
        <Route path="/subscriptions" element={<MySubscriptions /> } />
        <Route path="/subscriptions/:subscriptionId/edit" element={<SubscriptionEdit />} />
        <Route path="/subscriptions/:subscriptionId/orders" element={<SubscriptionOrders />} />
        
        {/* Redirect root to dashboard */}
        <Route path="*" element={<Dashboard />} />
      </Routes>
    </AccountLayout>
  );
};

export default Account;
