import { createLazyRoute, withSuspense } from './lib/lazyLoading';
import { PageSkeleton, ProductListSkeleton, DashboardSkeleton } from './components/routing/skeletons';

export const OptimizedRoutes = {
  // Critical routes - preload immediately
  Home: withSuspense(
    createLazyRoute(() => import('./pages/Home').then(m => ({ default: m.Home })), true),
    <PageSkeleton />
  ),
  
  ProductList: withSuspense(
    createLazyRoute(() => import('./pages/ProductList').then(m => ({ default: m.ProductList })), true),
    <ProductListSkeleton />
  ),
  
  ProductDetails: withSuspense(
    createLazyRoute(() => import('./pages/ProductDetails').then(m => ({ default: m.ProductDetails })), true),
    <PageSkeleton />
  ),

  // Important routes - preload after initial load
  Cart: withSuspense(
    createLazyRoute(() => import('./pages/Cart').then(m => ({ default: m.Cart })), false),
    <PageSkeleton />
  ),
  
  Login: withSuspense(
    createLazyRoute(() => import('./pages/Login').then(m => ({ default: m.Login })), false),
    <PageSkeleton />
  ),
  
  Register: withSuspense(
    createLazyRoute(() => import('./pages/Register').then(m => ({ default: m.Register })), false),
    <PageSkeleton />
  ),

  // Admin routes - lazy load only when needed
  AdminDashboard: withSuspense(
    createLazyRoute(() => import('./pages/admin/AdminDashboard').then(m => ({ default: m.AdminDashboard })), false),
    <DashboardSkeleton />
  ),
  
  AdminProducts: withSuspense(
    createLazyRoute(() => import('./pages/admin/AdminProducts').then(m => ({ default: m.AdminProducts })), false),
    <ProductListSkeleton />
  ),
  
  AdminUsers: withSuspense(
    createLazyRoute(() => import('./pages/admin/AdminUsers').then(m => ({ default: m.AdminUsers })), false),
    <DashboardSkeleton />
  ),
  
  AdminOrders: withSuspense(
    createLazyRoute(() => import('./pages/admin/AdminOrders').then(m => ({ default: m.AdminOrders })), false),
    <DashboardSkeleton />
  ),
  
  AdminAnalytics: withSuspense(
    createLazyRoute(() => import('./pages/admin/AdminAnalytics').then(m => ({ default: m.AdminAnalytics })), false),
    <DashboardSkeleton />
  ),

  // Secondary routes - lazy load
  Account: withSuspense(
    createLazyRoute(() => import('./pages/Account').then(m => ({ default: m.Account })), false),
    <PageSkeleton />
  ),
  
  Checkout: withSuspense(
    createLazyRoute(() => import('./pages/Checkout').then(m => ({ default: m.Checkout })), false),
    <PageSkeleton />
  ),
  
  About: withSuspense(
    createLazyRoute(() => import('./pages/About').then(m => ({ default: m.About })), false),
    <PageSkeleton />
  ),
  
  Contact: withSuspense(
    createLazyRoute(() => import('./pages/Contact').then(m => ({ default: m.Contact })), false),
    <PageSkeleton />
  ),
  
  FAQ: withSuspense(
    createLazyRoute(() => import('./pages/FAQ').then(m => ({ default: m.FAQ })), false),
    <PageSkeleton />
  ),
  
  Blog: withSuspense(
    createLazyRoute(() => import('./pages/Blog').then(m => ({ default: m.Blog })), false),
    <PageSkeleton />
  ),
  
  BlogPost: withSuspense(
    createLazyRoute(() => import('./pages/BlogPost').then(m => ({ default: m.BlogPost })), false),
    <PageSkeleton />
  ),
  
  ForgotPassword: withSuspense(
    createLazyRoute(() => import('./pages/ForgotPassword').then(m => ({ default: m.ForgotPassword })), false),
    <PageSkeleton />
  ),
  
  Subscription: withSuspense(
    createLazyRoute(() => import('./pages/Subscription').then(m => ({ default: m.Subscription })), false),
    <PageSkeleton />
  ),
  
  TermsAndConditions: withSuspense(
    createLazyRoute(() => import('./pages/TermsAndConditions').then(m => ({ default: m.TermsAndConditions })), false),
    <PageSkeleton />
  ),
  
  PrivacyPolicy: withSuspense(
    createLazyRoute(() => import('./pages/PrivacyPolicy').then(m => ({ default: m.PrivacyPolicy })), false),
    <PageSkeleton />
  ),
  
  AdminRegister: withSuspense(
    createLazyRoute(() => import('./pages/admin/AdminRegister').then(m => ({ default: m.AdminRegister })), false),
    <PageSkeleton />
  )
};