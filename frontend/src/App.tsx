import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout, AuthLayout } from './components/layout/Layout';
import { AdminLayout } from './components/admin/AdminLayout';
import { AuthProvider } from './contexts/AuthContext';
import { CartProvider } from './contexts/CartContext';
import { WishlistProvider } from './contexts/WishlistContext';
import { SubscriptionProvider } from './contexts/SubscriptionContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { FontLoader } from './components/ui/FontLoader';
import { Toaster } from 'react-hot-toast';
import GoogleOAuthProvider from './providers/GoogleOAuthProvider';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { CategoryProvider } from './contexts/CategoryContext';
import { LocaleProvider } from './contexts/LocaleContext';
import { ProtectedRoute } from './components/routing/ProtectedRoute';
import ErrorBoundary from './components/common/ErrorBoundary';
import SupportWidget from './components/support/SupportWidget';

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLIC_KEY);

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
const FAQ = lazy(() => import('./pages/FAQ'));
const Wishlist = lazy(() => import('./pages/Wishlist'));
const Subscriptions = lazy(() => import('./pages/Subscriptions'));
const TermsAndConditions = lazy(() => import('./pages/TermsAndConditions'));
const PrivacyPolicy = lazy(() => import('./pages/PrivacyPolicy'));
const EmailVerification = lazy(() => import('./pages/EmailVerification'));
const ResetPassword = lazy(() => import('./pages/ResetPassword'));

// Lazy load admin pages
const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'));
const AdminProducts = lazy(() => import('./pages/admin/AdminProducts'));
const AdminUsers = lazy(() => import('./pages/admin/AdminUsers'));
const AdminOrders = lazy(() => import('./pages/admin/AdminOrders'));
const AdminRegister = lazy(() => import('./pages/admin/AdminRegister'));
const AdminOrderDetail = lazy(() => import('./pages/admin/AdminOrderDetail'));
const AdminProductDetail = lazy(() => import('./pages/admin/AdminProductDetail'));
const AdminUserDetail = lazy(() => import('./pages/admin/AdminUserDetail'));
const AdminVariants = lazy(() => import('./pages/admin/AdminVariants'));
const AdminNewUser = lazy(() => import('./pages/admin/AdminNewUser'));
const AdminUserEdit = lazy(() => import('./pages/admin/AdminUserEdit'));
const AdminNewProduct = lazy(() => import('./pages/admin/AdminNewProduct'));
const AdminProductEdit = lazy(() => import('./pages/admin/AdminProductEdit'));

// New Inventory Admin Pages
const AdminInventory = lazy(() => import('./pages/admin/AdminInventory'));
const AdminInventoryAdjustments = lazy(() => import('./pages/admin/AdminInventoryAdjustments'));
const AdminWarehouseLocations = lazy(() => import('./pages/admin/AdminWarehouseLocations'));
const AdminWarehouseLocationForm = lazy(() => import('./pages/admin/AdminWarehouseLocationForm'));
const AdminInventoryAdjustmentForm = lazy(() => import('./pages/admin/AdminInventoryAdjustmentForm'));
const AdminStockAdjustments = lazy(() => import('./pages/admin/AdminStockAdjustments'));
const AdminInventoryItemForm = lazy(() => import('./pages/admin/AdminInventoryItemForm'));
const AdminShippingMethods = lazy(() => import('./pages/admin/AdminShippingMethods'));
const AdminShippingMethodForm = lazy(() => import('./pages/admin/AdminShippingMethodForm'));
const TaxRatesAdmin = lazy(() => import('./pages/admin/TaxRates'));
const TrackOrder = lazy(() => import('./pages/TrackOrder'));
const TrackOrderSearch = lazy(() => import('./components/account/TrackOrder'));
const Support = lazy(() => import('./pages/Support'));

// Lazy load supplier pages
const SupplierDashboard = lazy(() => import('./components/dashboard/SupplierDashboard'));

// Loading component
const PageLoading: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen bg-background">
    <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
  </div>
);

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <GoogleOAuthProvider>
        <AuthProvider>
          <ThemeProvider>
            <LocaleProvider>
              <CategoryProvider>
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
                      duration: Infinity, // Loading toasts should remain until dismissed by toast.success or toast.error
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
                  <CartProvider>
                    <SubscriptionProvider>
                      <WishlistProvider>
                        <SupportWidget />
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
                                path="/admin/products/:id/edit"
                                element={
                                  <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                    <AdminLayout>
                                      <AdminProductEdit />
                                    </AdminLayout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route
                                path="/admin/products/:id/variants"
                                element={
                                  <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                    <AdminLayout>
                                      <AdminVariants />
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
                                path="/admin/users/:id/edit"
                                element={
                                  <ProtectedRoute requiredRole={['Admin']}>
                                    <AdminLayout>
                                      <AdminUserEdit />
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

                              {/* Inventory Management Routes */}
                              <Route
                                  path="/admin/inventory"
                                  element={
                                      <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                          <AdminLayout>
                                              <AdminInventory />
                                          </AdminLayout>
                                      </ProtectedRoute>
                                  }
                              />
                              <Route
                                  path="/admin/inventory/:inventoryId/adjustments"
                                  element={
                                      <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                          <AdminLayout>
                                              <AdminInventoryAdjustments />
                                          </AdminLayout>
                                      </ProtectedRoute>
                                  }
                              />
                              <Route
                                  path="/admin/inventory/locations"
                                  element={
                                      <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                          <AdminLayout>
                                              <AdminWarehouseLocations />
                                          </AdminLayout>
                                      </ProtectedRoute>
                                  }
                              />
                              <Route
                                  path="/admin/inventory/locations/new"
                                  element={
                                      <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                          <AdminLayout>
                                              <AdminWarehouseLocationForm />
                                          </AdminLayout>
                                      </ProtectedRoute>
                                  }
                              />
                              <Route
                                  path="/admin/inventory/locations/edit/:locationId"
                                  element={
                                      <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                          <AdminLayout>
                                              <AdminWarehouseLocationForm />
                                          </AdminLayout>
                                      </ProtectedRoute>
                                  }
                              />
                              <Route
                                  path="/admin/inventory/adjustments/new"
                                  element={
                                      <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                          <AdminLayout>
                                              <AdminInventoryAdjustmentForm />
                                          </AdminLayout>
                                      </ProtectedRoute>
                                  }
                              />
                              <Route
                                  path="/admin/inventory/adjustments"
                                  element={
                                      <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                          <AdminLayout>
                                              <AdminStockAdjustments />
                                          </AdminLayout>
                                      </ProtectedRoute>
                                  }
                              />
                              <Route
                                  path="/admin/inventory/:inventoryId/adjustments"
                                  element={
                                      <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                          <AdminLayout>
                                              <AdminStockAdjustments />
                                          </AdminLayout>
                                      </ProtectedRoute>
                                  }
                              />
                              <Route
                                  path="/admin/inventory/edit/:inventoryId"
                                  element={
                                      <ProtectedRoute requiredRole={['Admin', 'Supplier']}>
                                          <AdminLayout>
                                              <AdminInventoryItemForm />
                                          </AdminLayout>
                                      </ProtectedRoute>
                                  }
                              />
                              {/* Shipping Methods Management Routes */}
                              <Route
                                  path="/admin/shipping-methods"
                                  element={
                                      <ProtectedRoute requiredRole={['Admin']}>
                                          <AdminLayout>
                                              <AdminShippingMethods />
                                          </AdminLayout>
                                      </ProtectedRoute>
                                  }
                              />
                              <Route
                                  path="/admin/shipping-methods/new"
                                  element={
                                      <ProtectedRoute requiredRole={['Admin']}>
                                          <AdminLayout>
                                              <AdminShippingMethodForm />
                                          </AdminLayout>
                                      </ProtectedRoute>
                                  }
                              />
                              <Route
                                  path="/admin/shipping-methods/edit/:methodId"
                                  element={
                                      <ProtectedRoute requiredRole={['Admin']}>
                                          <AdminLayout>
                                              <AdminShippingMethodForm />
                                          </AdminLayout>
                                      </ProtectedRoute>
                                  }
                              />
                              {/* Tax Rates Management Route */}
                              <Route
                                  path="/admin/tax-rates"
                                  element={
                                      <ProtectedRoute requiredRole={['Admin']}>
                                          <AdminLayout>
                                              <TaxRatesAdmin />
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

                              <Route path="/products" element={<Layout><Products /></Layout>} />
                              <Route path="/products/search" element={<Layout><Products /></Layout>} />
                              <Route path="/products/:id" element={<Layout><ProductDetails /></Layout>} />
                              <Route path="/cart" element={<Layout><Cart /></Layout>} />
                              <Route path="/checkout" element={<ProtectedRoute><Layout><Checkout /></Layout></ProtectedRoute>} />
                              <Route path="/account/*" element={<ProtectedRoute><Layout><Account /></Layout></ProtectedRoute>} />
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
                              <Route path="/support" element={<Layout><Support /></Layout>} />
                              <Route path="/faq" element={<Layout><FAQ /></Layout>} />
                              <Route path="/account/wishlist" element={<ProtectedRoute><Layout><Wishlist /></Layout></ProtectedRoute>} />
                              <Route
                                path="/subscriptions"
                                element={
                                  <ProtectedRoute>
                                    <Layout>
                                      <Subscriptions />
                                    </Layout>
                                  </ProtectedRoute>
                                }
                              />
                              <Route
                                path="/subscription/:subscriptionId/manage"
                                element={
                                  <ProtectedRoute>
                                    <Layout>
                                      <Subscriptions />
                                    </Layout>
                                  </ProtectedRoute>
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
                      </WishlistProvider>
                    </SubscriptionProvider>
                  </CartProvider>
                </BrowserRouter>
              </CategoryProvider>
            </LocaleProvider>
          </ThemeProvider>
        </AuthProvider>
      </GoogleOAuthProvider>
    </ErrorBoundary>
  );
}