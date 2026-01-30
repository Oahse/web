import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout, AuthLayout } from './components/layout/Layout';
import { AuthProvider } from './store/AuthContext';
import { CartProvider } from './store/CartContext';
import { WishlistProvider } from './store/WishlistContext';
import { SubscriptionProvider } from './store/SubscriptionContext';
import { CategoryProvider } from './store/CategoryContext';
import { LocaleProvider } from './store/LocaleContext';
import { ThemeProvider } from './store/ThemeContext';
import { FontLoader } from './components/ui/FontLoader';
import { Toaster } from 'react-hot-toast';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import ErrorBoundary from './components/ErrorBoundary';
import { ProtectedRoute } from './components/ProtectedRoute';
import { 
  Skeleton, 
  PageSkeleton, 
  ProductListSkeleton, 
  ProductDetailSkeleton, 
  CartSkeleton, 
  CheckoutSkeleton, 
  AccountSkeleton, 
  AdminDashboardSkeleton, 
  AdminTableSkeleton 
} from './components/ui/SkeletonLoader';
import { 
  AnimatedLoader, 
  PageTransitionLoader, 
  LoadingOverlay, 
  ProgressBar 
} from './components/ui/AnimatedLoader';
import './animations.css';

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLIC_KEY || '');

// Lazy load pages for better performance
const Home = lazy(() => import('./pages/Home'));
const Products = lazy(() => import('./pages/Products'));
const ProductDetails = lazy(() => import('./pages/ProductDetails'));
const Cart = lazy(() => import('./pages/Cart'));
const Checkout = lazy(() => import('./pages/Checkout'));
const Account = lazy(() => import('./pages/Account'));
const Login = lazy(() => import('./pages/Login'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const Register = lazy(() => import('./pages/Register'));
const About = lazy(() => import('./pages/About'));
const Contact = lazy(() => import('./pages/Contact'));
const TermsAndConditions = lazy(() => import('./pages/TermsAndConditions'));
const PrivacyPolicy = lazy(() => import('./pages/PrivacyPolicy'));
const EmailVerification = lazy(() => import('./pages/EmailVerification'));
const ResetPassword = lazy(() => import('./pages/ResetPassword'));
const TrackOrder = lazy(() => import('./pages/TrackOrder'));
const Support = lazy(() => import('./pages/Support'));
const FAQ = lazy(() => import('./pages/FAQ'));
const AdminLayout = lazy(() => import('./components/admin/AdminLayout'));
const AdminDashboardPage = lazy(() => import('./components/admin/Dashboard'));
const AdminOrders = lazy(() => import('./components/admin/Orders'));
const AdminOrderDetail = lazy(() => import('./pages/admin/OrderDetail'));
const AdminProducts = lazy(() => import('./pages/admin/Products'));
const AdminProductDetail = lazy(() => import('./pages/admin/ProductDetail'));
const AdminUsers = lazy(() => import('./components/admin/Users'));
const AdminTaxRates = lazy(() => import('./pages/admin/TaxRates'));
const AdminInventoryLocations = lazy(() => import('./pages/admin/InventoryLocations'));
const AdminInventoryAdjustments = lazy(() => import('./pages/admin/InventoryAdjustments'));
const AdminSubscriptions = lazy(() => import('./pages/admin/Subscriptions'));
const AdminInventory = lazy(() => import('./pages/admin/Inventory'));
const AdminShipping = lazy(() => import('./pages/admin/Shipping'));
const AdminShippingMethods = lazy(() => import('./pages/admin/ShippingMethods'));
const SupplierDashboard = lazy(() => import('./pages/admin/Dashboard'));

// Loading component
const PageLoading: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
    <div className="w-16 h-16 border-4 border-blue-600 dark:border-blue-400 border-t-transparent rounded-full animate-spin"></div>
  </div>
);

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ThemeProvider>
          <FontLoader />
          <Toaster
            position="top-right"
            toastOptions={{
              success: {
                duration: 3000,
                style: {
                  background: 'var(--color-success)',
                  color: 'var(--color-copy-inverse)',
                },
              },
              error: {
                duration: 5000,
                style: {
                  background: 'var(--color-error)',
                  color: 'var(--color-copy-inverse)',
                }
              },
              loading: {
                duration: Infinity,
                style: {
                  background: 'var(--color-surface-elevated)',
                  color: 'var(--color-copy)',
                },
              },
              blank: {
                duration: 2000,
                style: {
                  background: 'var(--color-surface)',
                  color: 'var(--color-copy)',
                },
              },
            }}
          />
          <BrowserRouter
            future={{
              v7_startTransition: true,
              v7_relativeSplatPath: true,
            }}
          >
            <CategoryProvider>
              <LocaleProvider>
                <CartProvider>
                  <SubscriptionProvider>
                    <WishlistProvider>
                      <Elements stripe={stripePromise}>
                        <Suspense fallback={<PageSkeleton />}>
                          <Routes>
                        <Route path="/" element={<Layout><Home /></Layout>} />
                        <Route path="/products" element={<Layout><Suspense fallback={<ProductListSkeleton />}><Products /></Suspense></Layout>} />
                        <Route path="/products/search" element={<Layout><Suspense fallback={<ProductListSkeleton />}><Products /></Suspense></Layout>} />
                        <Route path="/products/:id" element={<Layout><Suspense fallback={<ProductDetailSkeleton />}><ProductDetails /></Suspense></Layout>} />
                        <Route path="/cart" element={<ProtectedRoute><Layout><Suspense fallback={<CartSkeleton />}><Cart /></Suspense></Layout></ProtectedRoute>} />
                        <Route path="/checkout" element={<ProtectedRoute><Layout><Suspense fallback={<CheckoutSkeleton />}><Checkout /></Suspense></Layout></ProtectedRoute>} />
                        <Route path="/account/*" element={<ProtectedRoute><Layout><Suspense fallback={<AccountSkeleton />}><Account /></Suspense></Layout></ProtectedRoute>} />
                        <Route path="/track-order/:orderId" element={<ProtectedRoute><Layout><Suspense fallback={<PageSkeleton />}><TrackOrder /></Suspense></Layout></ProtectedRoute>} />
                        <Route path="/login" element={<Layout><Login /></Layout>} />
                        <Route path="/forgot-password" element={<Layout><ForgotPassword /></Layout>} />
                        <Route path="/register" element={<Layout><Register /></Layout>} />
                        <Route path="/about" element={<Layout><About /></Layout>} />
                        <Route path="/contact" element={<Layout><Contact /></Layout>} />
                        <Route path="/support" element={<Layout><Support /></Layout>} />
                        <Route path="/faq" element={<Layout><FAQ /></Layout>} />
                        <Route path="/terms" element={<Layout><TermsAndConditions /></Layout>} />
                        <Route path="/privacy" element={<Layout><PrivacyPolicy /></Layout>} />
                        <Route path="/verify-email" element={<Layout><EmailVerification /></Layout>} />
                        <Route path="/reset-password" element={<Layout><ResetPassword /></Layout>} />
                        <Route path="/admin" element={<ProtectedRoute><AdminLayout /></ProtectedRoute>}>
                          <Route index element={<Suspense fallback={<AdminDashboardSkeleton />}><AdminDashboardPage /></Suspense>} />
                          <Route path="orders" element={<Suspense fallback={<AdminTableSkeleton />}><AdminOrders /></Suspense>} />
                          <Route path="orders/:orderId" element={<Suspense fallback={<PageSkeleton />}><AdminOrderDetail /></Suspense>} />
                          <Route path="products" element={<Suspense fallback={<AdminTableSkeleton />}><AdminProducts /></Suspense>} />
                          <Route path="products/:productId" element={<Suspense fallback={<ProductDetailSkeleton />}><AdminProductDetail /></Suspense>} />
                          <Route path="users" element={<Suspense fallback={<AdminTableSkeleton />}><AdminUsers /></Suspense>} />
                          <Route path="tax-rates" element={<Suspense fallback={<AdminTableSkeleton />}><AdminTaxRates /></Suspense>} />
                          <Route path="inventory/locations" element={<Suspense fallback={<AdminTableSkeleton />}><AdminInventoryLocations /></Suspense>} />
                          <Route path="inventory/adjustments" element={<Suspense fallback={<AdminTableSkeleton />}><AdminInventoryAdjustments /></Suspense>} />
                          <Route path="subscriptions" element={<Suspense fallback={<AdminTableSkeleton />}><AdminSubscriptions /></Suspense>} />
                          <Route path="inventory" element={<Suspense fallback={<AdminTableSkeleton />}><AdminInventory /></Suspense>} />
                          <Route path="shipping" element={<Suspense fallback={<AdminTableSkeleton />}><AdminShipping /></Suspense>} />
                          <Route path="shipping-methods" element={<Suspense fallback={<AdminTableSkeleton />}><AdminShippingMethods /></Suspense>} />
                        </Route>
                        <Route path="/supplier/*" element={<ProtectedRoute><Suspense fallback={<AdminDashboardSkeleton />}><SupplierDashboard /></Suspense></ProtectedRoute>} />
                      </Routes>
                    </Suspense>
                  </Elements>
                </WishlistProvider>
              </SubscriptionProvider>
            </CartProvider>
            </LocaleProvider>
            </CategoryProvider>
          </BrowserRouter>
        </ThemeProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}