import React, { Suspense, lazy } from 'react';
import { NotificationProvider } from './contexts/NotificationContext';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout, AuthLayout } from './components/layout/Layout';
import { AdminLayout } from './components/admin/AdminLayout';
import { AuthProvider } from './contexts/AuthContext';
import { CartProvider } from './contexts/CartContext';
import { WishlistProvider } from './contexts/WishlistContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { FontLoader } from './components/ui/FontLoader';
import { Toaster, toast } from 'react-hot-toast';
import { XIcon } from 'lucide-react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { CategoryProvider } from './contexts/CategoryContext';
import { LocaleProvider } from './contexts/LocaleContext';
import { ProtectedRoute } from './components/routing/ProtectedRoute';
// import { initPerformanceMonitoring } from './utils/performance';
import ErrorBoundary from './components/common/ErrorBoundary';
import { OfflineIndicator } from './components/common/OfflineIndicator';

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLIC_KEY);

// Lazy load pages for better performance
const Home = lazy(() => import('./pages/Home').then((module) => ({ default: module.Home })));
const ProductList = lazy(() =>
  import('./pages/ProductList').then((module) => ({ default: module.ProductList }))
);
const ProductDetails = lazy(() =>
  import('./pages/ProductDetails').then((module) => ({ default: module.ProductDetails }))
);
const Cart = lazy(() => import('./pages/Cart').then((module) => ({ default: module.Cart })));
const Checkout = lazy(() => import('./pages/Checkout').then((module) => ({ default: module.Checkout })));
const Account = lazy(() => import('./pages/Account').then((module) => ({ default: module.Account })));
const Login = lazy(() => import('./pages/Login').then((module) => ({ default: module.Login })));
const ForgotPassword = lazy(() =>
  import('./pages/ForgotPassword').then((module) => ({ default: module.ForgotPassword }))
);
const Register = lazy(() => import('./pages/Register').then((module) => ({ default: module.Register })));
const About = lazy(() => import('./pages/About').then((module) => ({ default: module.About })));
const Contact = lazy(() => import('./pages/Contact').then((module) => ({ default: module.Contact })));
const FAQ = lazy(() => import('./pages/FAQ').then((module) => ({ default: module.FAQ })));
// Blog feature disabled
// const Blog = lazy(() => import('./pages/Blog').then((module) => ({ default: module.Blog })));
// const BlogPost = lazy(() => import('./pages/BlogPost').then((module) => ({ default: module.BlogPost })));
const Wishlist = lazy(() => import('./pages/Wishlist').then((module) => ({ default: module.Wishlist })));
const Subscription = lazy(() =>
  import('./pages/Subscription').then((module) => ({ default: module.Subscription }))
);
const TermsAndConditions = lazy(() =>
  import('./pages/TermsAndConditions').then((module) => ({ default: module.TermsAndConditions }))
);
const PrivacyPolicy = lazy(() =>
  import('./pages/PrivacyPolicy').then((module) => ({ default: module.PrivacyPolicy }))
);
const EmailVerification = lazy(() =>
  import('./pages/EmailVerification').then((module) => ({ default: module.EmailVerification }))
);
const ResetPassword = lazy(() =>
  import('./pages/ResetPassword').then((module) => ({ default: module.ResetPassword }))
);
// Lazy load admin pages
const AdminDashboard = lazy(() =>
  import('./pages/admin/AdminDashboard').then((module) => ({ default: module.AdminDashboard }))
);
const AdminProducts = lazy(() =>
  import('./pages/admin/AdminProducts').then((module) => ({ default: module.AdminProducts }))
);
const AdminUsers = lazy(() =>
  import('./pages/admin/AdminUsers').then((module) => ({ default: module.AdminUsers }))
);
const AdminOrders = lazy(() =>
  import('./pages/admin/AdminOrders').then((module) => ({ default: module.AdminOrders }))
);
const AdminAnalytics = lazy(() =>
  import('./pages/admin/AdminAnalytics').then((module) => ({ default: module.AdminAnalytics }))
);
const AdminNotifications = lazy(() =>
  import('./pages/admin/AdminNotifications').then((module) => ({ default: module.AdminNotifications }))
);
const AdminRegister = lazy(() =>
  import('./pages/admin/AdminRegister').then((module) => ({ default: module.AdminRegister }))
);
const AdminOrderDetail = lazy(() =>
  import('./pages/admin/AdminOrderDetail').then((module) => ({ default: module.AdminOrderDetail }))
);
const AdminProductDetail = lazy(() =>
  import('./pages/admin/AdminProductDetail').then((module) => ({ default: module.AdminProductDetail }))
);
const AdminUserDetail = lazy(() =>
  import('./pages/admin/AdminUserDetail').then((module) => ({ default: module.AdminUserDetail }))
);
const AdminVariants = lazy(() =>
  import('./pages/admin/AdminVariants').then((module) => ({ default: module.AdminVariants }))
);
const AdminNewUser = lazy(() =>
  import('./pages/admin/AdminNewUser').then((module) => ({ default: module.AdminNewUser }))
);
const AdminNewProduct = lazy(() =>
  import('./pages/admin/AdminNewProduct').then((module) => ({ default: module.AdminNewProduct }))
);

const AdminSettings = lazy(() =>
  import('./pages/admin/AdminSettings').then((module) => ({ default: module.AdminSettings }))
);
const Notifications = lazy(() =>
  import('./pages/account/Notifications').then((module) => ({ default: module.Notifications }))
);
const TrackOrder = lazy(() =>
  import('./pages/TrackOrder').then((module) => ({ default: module.TrackOrder }))
);
const TrackOrderSearch = lazy(() =>
  import('./components/account/TrackOrder').then((module) => ({ default: module.default }))
);

// Lazy load supplier pages
const SupplierDashboard = lazy(() =>
  import('./components/dashboard/SupplierDashboard').then((module) => ({ default: module.SupplierDashboard }))
);

// Loading component
const PageLoading: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen bg-background">
    <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
  </div>
);

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || ''}>
        <AuthProvider>
          <ThemeProvider>
            <LocaleProvider>
              <CartProvider>
                <WishlistProvider>
                  <NotificationProvider>
                    <WebSocketProvider autoConnect={false}>
                      <CategoryProvider>
                      <FontLoader />
                      <OfflineIndicator />
                      <Toaster
                        position="top-right"
                        toastOptions={{
                          success: {
                            style: {
                              background: 'var(--color-success)',
                              color: 'var(--color-copy-inverse)',
                            },
                          },
                          error: {
                            duration: Infinity,
                            style: {
                              background: 'var(--color-error)',
                              color: 'var(--color-copy-inverse)',
                            }
                          },
                          loading: {
                            style: {
                              background: 'var(--color-surface-elevated)',
                              color: 'var(--color-copy)',
                            },
                          },
                          blank: {
                            style: {
                              background: 'var(--color-surface)',
                              color: 'var(--color-copy)',
                            },
                          },
                        }}
                      />
                      <BrowserRouter>
                        <Elements stripe={stripePromise}>
                          <Suspense fallback={<PageLoading />}>
                            <Routes>
                              <Route
                                path="/admin"
                                element={
                                  <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                    <AdminLayout>
                                      <AdminDashboard />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route
                                path="/admin/products"
                                element={
                                  <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                    <AdminLayout>
                                      <AdminProducts />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route
                                path="/admin/products/new"
                                element={
                                  <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                    <AdminLayout>
                                      <AdminNewProduct />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route
                                path="/admin/products/:id"
                                element={
                                  <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                    <AdminLayout>
                                      <AdminProductDetail />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route
                                path="/admin/users"
                                element={
                                  <ProtectedRoute requiredRole={['Admin']}>
                                    <AdminLayout>
                                      <AdminUsers />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route
                                path="/admin/users/new"
                                element={
                                  <ProtectedRoute requiredRole={['Admin']}>
                                    <AdminLayout>
                                      <AdminNewUser />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route
                                path="/admin/users/:id"
                                element={
                                  <ProtectedRoute requiredRole={['Admin']}>
                                    <AdminLayout>
                                      <AdminUserDetail />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route
                                path="/admin/orders"
                                element={
                                  <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                    <AdminLayout>
                                      <AdminOrders />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route
                                path="/admin/orders/:id"
                                element={
                                  <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                    <AdminLayout>
                                      <AdminOrderDetail />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route
                                path="/admin/variants"
                                element={
                                  <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                    <AdminLayout>
                                      <AdminVariants />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />

                              <Route
                                path="/admin/analytics"
                                element={
                                  <ProtectedRoute requiredRole={['Admin']}>
                                    <AdminLayout>
                                      <AdminAnalytics />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route
                                path="/admin/notifications"
                                element={
                                  <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                    <AdminLayout>
                                      <AdminNotifications />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route
                                path="/admin/settings"
                                element={
                                  <ProtectedRoute requiredRole={['Admin']}>
                                    <AdminLayout>
                                      <AdminSettings />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route path="/admin/register" element={<AuthLayout><AdminRegister /></AuthLayout>} />
                              <Route path="/admin/login" element={<AuthLayout><Login /></AuthLayout>} />

                              {/* Supplier Routes */}
                              <Route
                                path="/supplier"
                                element={
                                  <ProtectedRoute requiredRole={['Supplier']}>
                                    <Layout>
                                      <SupplierDashboard />
                                    </Layout>
                                  </ProtectedRoute>
                                }
                              />

                              <Route path="/" element={<Layout><Home /></Layout>} />

                              <Route path="/products" element={<Layout><ProductList /></Layout>} />
                              <Route path="/product/:id" element={<Layout><ProductDetails /></Layout>} />
                              <Route path="/cart" element={<Layout><Cart /></Layout>} />
                              <Route path="/checkout" element={<ProtectedRoute><Layout><Checkout /></Layout></ProtectedRoute>} />
                              <Route path="/account/*" element={<ProtectedRoute><Layout><Account /></Layout></ProtectedRoute>} />
                              <Route path="/account/notifications" element={<ProtectedRoute><Layout><Notifications /></Layout></ProtectedRoute>} />
                              <Route path="/account/track-order" element={<ProtectedRoute><Layout><TrackOrderSearch /></Layout></ProtectedRoute>} />
                              <Route path="/track-order/:orderId" element={<ProtectedRoute><Layout><TrackOrder /></Layout></ProtectedRoute>} />
                              <Route
                                path="/login"
                                element={
                                  <Layout>
                                    <Login />
                                  </Layout>
                                }
                              />
                              <Route
                                path="/forgot-password"
                                element={
                                  <Layout>
                                    <ForgotPassword />
                                  </Layout>
                                }
                              />
                              <Route path="/register" element={<Layout><Register /></Layout>} />
                              <Route path="/about" element={<Layout><About /></Layout>} />
                              <Route path="/contact" element={<Layout><Contact /></Layout>} />
                              <Route path="/faq" element={<Layout><FAQ /></Layout>} />
                              {/* Blog routes disabled */}
                              {/* <Route path="/blog" element={<Layout><Blog /></Layout>} /> */}
                              {/* <Route path="/blog/:id" element={<Layout><BlogPost /></Layout>} /> */}
                              <Route path="/account/wishlist" element={<ProtectedRoute><Layout><Wishlist /></Layout></ProtectedRoute>} />
                              <Route
                                path="/subscription"
                                element={
                                  <Layout>
                                    <Subscription />
                                  </Layout>
                                }
                              />
                              <Route
                                path="/terms"
                                element={
                                  <Layout>
                                    <TermsAndConditions />
                                  </Layout>
                                }
                              />
                              <Route
                                path="/privacy"
                                element={
                                  <Layout>
                                    <PrivacyPolicy />
                                  </Layout>
                                }
                              />
                              <Route path="/verify-email" element={<Layout><EmailVerification /></Layout>} />
                              <Route path="/reset-password" element={<Layout><ResetPassword /></Layout>} />
                            </Routes>
                          </Suspense>
                        </Elements>
                      </BrowserRouter>
                      </CategoryProvider>
                    </WebSocketProvider>
                  </NotificationProvider>
                </WishlistProvider>
              </CartProvider>
            </LocaleProvider>
          </ThemeProvider>
        </AuthProvider>
      </GoogleOAuthProvider>
    </ErrorBoundary>
  );
}