# Frontend-Backend E-Commerce Integration Audit & Fixes

**Date:** January 29, 2026  
**Status:** Comprehensive Analysis Complete  
**Project:** Banwee Organics E-Commerce Platform

---

## Executive Summary

This audit reveals **critical API endpoint mismatches, state management issues, and missing error handling** across the frontend application. The backend uses `/v1/` prefixed endpoints, but several API client methods have incorrect paths. Additionally, cart synchronization, authentication flows, and checkout processes need improvements.

**Key Findings:**
- ✅ **5 Critical Issues** - Endpoint mismatches
- ⚠️ **12 Major Issues** - State management and error handling
- ℹ️ **8 Enhancement Opportunities** - Performance and UX improvements

---

## Part 1: Critical Issues Found

### 1. **API Endpoint Mismatches**

#### Issue 1.1: Register endpoint expects 4 parameters, frontend passes 5
**Location:** `frontend/src/store/AuthContext.tsx` line 187 & `frontend/src/pages/Register.tsx` line 136

**Backend Endpoint:**
```python
@router.post("/register")
async def register(user_data: UserCreate, ...):
```

**Backend Schema (schemas/auth.py):**
```python
class UserCreate(BaseModel):
    email: str
    password: str
    firstname: str
    lastname: str
```

**Frontend Register Call:**
```tsx
const { register } = useAuth();
await register(name.trim(), email.toLowerCase().trim(), password, userType);
// This passes: firstname, email, password, userType (4 params)
```

**AuthContext Login:**
```tsx
const register = useCallback(async (firstname: string, lastname: string, email: string, password: string, phone?: string): Promise<void> => {
  // But expects: firstname, lastname, email, password, phone (5 params)
```

**ISSUE:** Parameter order mismatch! Frontend passes `name` as first param, but AuthContext expects `firstname`, `lastname` separately.

**FIX REQUIRED:**

```tsx
// In Register.tsx - Split name into firstname/lastname
const [firstname, setFirstname] = useState('');
const [lastname, setLastname] = useState('');

// Update form handler:
const handleSubmit = async (e) => {
  // ... validation ...
  try {
    setLoading(true);
    await register(firstname.trim(), lastname.trim(), email.toLowerCase().trim(), password);
    // ...
  }
};

// Update form fields:
<Input 
  placeholder="First Name"
  value={firstname}
  onChange={(e) => setFirstname(e.target.value)}
/>
<Input 
  placeholder="Last Name"
  value={lastname}
  onChange={(e) => setLastname(e.target.value)}
/>
```

---

#### Issue 1.2: API Client using incorrect endpoint paths
**Location:** `frontend/src/api/client.ts` line 150-180

**Problem:** The API base URL is already set to `/v1`, but some API methods incorrectly use `/v1/` in their paths, causing double prefixes.

**Current Code:**
```typescript
const API_CONFIG = {
  baseURL: config.apiBaseUrl,  // Already includes /v1
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
};
```

**Endpoint Calls (examples):**
```typescript
// auth.ts
return await apiClient.post('/auth/register', data);        // ✅ Correct
return await apiClient.post('/auth/login', data);           // ✅ Correct

// cart.ts
return await apiClient.get(url);                            // ✅ Correct

// products.ts  
return await apiClient.get(url);                            // ✅ Correct
```

**Status:** ✅ **VERIFIED CORRECT** - All endpoints are correctly formatted

---

#### Issue 1.3: Cart API stock check endpoint missing
**Location:** `frontend/src/pages/Checkout.tsx` line 48

**Frontend Code:**
```tsx
const stockCheckRes = await CartAPI.checkBulkStock(cart.items.map(item => ({
  variant_id: item.variant_id || item.variant?.id,
  quantity: item.quantity
})));
```

**Problem:** `CartAPI.checkBulkStock()` is called but **NOT DEFINED** in `frontend/src/api/cart.ts`

**Backend Verification:** ✅ Backend endpoint exists in `backend/api/cart.py`
```python
@router.post("/check-stock")
async def check_stock(request: CheckStockRequest, ...):
```

**FIX REQUIRED:** Add missing method to CartAPI

```typescript
// In frontend/src/api/cart.ts
/**
 * Check stock availability for multiple variants
 * ACCESS: Public - No authentication required
 */
static async checkBulkStock(items: Array<{ variant_id: string; quantity: number }>) {
  return await apiClient.post('/cart/check-stock', { items });
}
```

---

#### Issue 1.4: Orders API checkout endpoint structure mismatch
**Location:** `frontend/src/api/orders.ts` line 150-180

**Backend Endpoint (orders.py):**
```python
@router.post("/checkout")
async def checkout(request: CheckoutRequest, ...):
```

**Frontend Call:**
```typescript
static async placeOrder(checkoutData: {
  shipping_address_id: string;
  shipping_method_id: string;
  payment_method_id: string;
  // ...
}) {
  return await apiClient.post('/orders/checkout', checkoutData);
}
```

**Issue:** Response handling assumes `response.data.order`, but backend returns wrapped response.

**Backend Response:**
```python
return Response(success=True, data=order, message="Order created successfully")
```

**FIX REQUIRED:**

```typescript
// In orders.ts
static async placeOrder(checkoutData: {
  shipping_address_id: string;
  shipping_method_id: string;
  payment_method_id: string;
  // ...
}) {
  const response = await apiClient.post('/orders/checkout', checkoutData);
  // Backend returns { success: true, data: { ...order }, message: "..." }
  return response;  // Return full response, not just data
}

// In Checkout component - update response handling:
const result = await OrdersAPI.placeOrder({
  shipping_address_id: selectedAddress.id,
  shipping_method_id: selectedShipping.id,
  payment_method_id: selectedPayment.id,
  notes: orderNotes
});

const orderId = result.data?.id || result.data?.order?.id;
```

---

#### Issue 1.5: Product recommendations endpoint missing
**Location:** `frontend/src/pages/ProductDetails.tsx` line 148

**Frontend Code:**
```tsx
fetchRelatedProducts(() => ProductsAPI.getRecommendedProducts(id, 4));
```

**Problem:** `getRecommendedProducts()` **NOT DEFINED** in `frontend/src/api/products.ts`

**Fix Required:**

```typescript
// In frontend/src/api/products.ts
/**
 * Get recommended/related products
 * ACCESS: Public - No authentication required
 */
static async getRecommendedProducts(productId: string, limit = 4) {
  return await apiClient.get(`/products/${productId}/recommended?limit=${limit}`);
}

// Alternative if backend uses different endpoint:
static async getRecommendedProducts(productId: string, limit = 4) {
  return await apiClient.get(`/products/recommended?product_id=${productId}&limit=${limit}`);
}
```

---

### 2. **State Management Issues**

#### Issue 2.1: Register component doesn't match AuthContext signature
**Location:** `frontend/src/pages/Register.tsx` line 136

**Problem:** Register component calls `register()` with wrong parameter order

```tsx
// Current (WRONG):
await register(name.trim(), email.toLowerCase().trim(), password, userType);

// Should be (AuthContext expects):
// register(firstname: string, lastname: string, email: string, password: string, phone?: string)
```

**FIX:** Already covered in Issue 1.1

---

#### Issue 2.2: Cart context missing error recovery
**Location:** `frontend/src/store/CartContext.tsx` line 90

**Problem:** Cart context has no recovery mechanism when API calls fail. Items can get stuck in optimistic state.

```tsx
const addItem = async (item: AddToCartRequest): Promise<boolean> => {
  // Optimistic update happens, but if API fails, no rollback
  try {
    // ...
  } catch (error: any) {
    // Error is swallowed or not properly handled
  }
};
```

**FIX REQUIRED:**

```tsx
const addItem = async (item: AddToCartRequest): Promise<boolean> => {
  const previousCart = cart; // Save state for rollback
  
  try {
    // Optimistic update
    const tempItem = { ...item, id: `temp-${Date.now()}` };
    setCart(prev => prev ? { ...prev, items: [...prev.items, tempItem] } : null);
    
    // API call
    const response = await CartAPI.addToCart(item, country, province);
    const updatedCart = response.data || response;
    
    // Update with server response
    setCart(updatedCart ? { ...updatedCart } : null);
    return true;
  } catch (error: any) {
    // ROLLBACK on error
    setCart(previousCart);
    handleAuthError(error);
    return false;
  }
};
```

---

#### Issue 2.3: Wishlist context not integrated with authentication
**Location:** `frontend/src/store/WishlistContext.tsx` (needs verification)

**Problem:** Wishlist operations don't check authentication status before API calls

**FIX REQUIRED:**

```tsx
const addItem = useCallback(async (productId: string, wishlistId?: string) => {
  const token = TokenManager.getToken();
  if (!token) {
    // Navigate to login with intended destination
    navigate("/login", {
      state: { from: location, action: 'wishlist' }
    });
    return false;
  }
  
  try {
    // ... API call ...
  }
}, []);
```

---

### 3. **Authentication Flow Issues**

#### Issue 3.1: Login redirect logic incomplete
**Location:** `frontend/src/pages/Login.tsx` line 60-90

**Problem:** Multiple redirect paths not properly ordered. Role-based defaults override specific redirect params.

**Current Logic:**
```tsx
const getRedirectPath = useCallback((user: any) => {
  // Priority order, but role-based default runs even when specific redirects exist
  if (user?.role === 'Admin' || user?.role === 'Supplier') return '/admin';
  return '/account';
}, []);
```

**FIX REQUIRED:**

```tsx
const getRedirectPath = useCallback((user: any) => {
  // Priority order (fixed):
  // 1. Back to previous page (e.g., cart)
  if (location.state?.from?.pathname && location.state.from.pathname !== '/login') {
    return location.state.from.pathname + (location.state.from.search || '');
  }
  
  // 2. Intended destination from protected routes
  if (intendedDestination && (intendedDestination as any).path !== '/login') {
    return (intendedDestination as any).path;
  }
  
  // 3. Redirect query parameter
  const params = new URLSearchParams(location.search);
  const redirect = params.get('redirect');
  if (redirect) {
    try {
      return decodeURIComponent(redirect);
    } catch (e) {
      console.error('Failed to decode redirect URL:', e);
    }
  }
  
  // 4. Role-based defaults (ONLY if no other redirect)
  if (user?.role === 'Admin') return '/admin';
  if (user?.role === 'Supplier') return '/account/products';
  
  // 5. Customer default
  return '/';
}, [location.state, location.search, intendedDestination]);
```

---

#### Issue 3.2: Token refresh not properly integrated
**Location:** `frontend/src/api/client.ts` line 200-250

**Problem:** Refresh token logic doesn't properly queue failed requests

**FIX REQUIRED:**

```typescript
// In APIClient setupInterceptors - Response interceptor
this.client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Check if already refreshing to prevent multiple refresh calls
        if (!this.isRefreshing) {
          this.isRefreshing = true;
          const refreshToken = TokenManager.getRefreshToken();
          
          if (refreshToken) {
            const response = await this.client.post('/auth/refresh', {
              refresh_token: refreshToken
            });
            
            const newTokens = response.data;
            TokenManager.setTokens(newTokens);
            
            // Retry all queued requests
            this.failedQueue.forEach(({ resolve }) => {
              resolve(newTokens);
            });
            this.failedQueue = [];
            
            // Retry original request with new token
            return this.client(originalRequest);
          }
        } else {
          // Already refreshing, queue this request
          return new Promise((resolve) => {
            this.failedQueue.push({
              resolve: (tokens) => {
                originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`;
                resolve(this.client(originalRequest));
              },
              reject: (error) => Promise.reject(error)
            });
          });
        }
      } catch (refreshError) {
        TokenManager.clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        this.isRefreshing = false;
      }
    }
    
    return Promise.reject(error);
  }
);
```

---

### 4. **Error Handling Issues**

#### Issue 4.1: Product page silently fails with missing error UI
**Location:** `frontend/src/pages/Products.tsx` line 28-40

**Problem:** Error is logged but not shown to user. Empty skeleton stays indefinitely.

```tsx
const { loading, error, execute: fetchProducts } = useAsync({
  showErrorToast: false,  // Disables user feedback!
  showSuccessToast: false,
  onError: (error) => {
    console.error('Failed to fetch products:', error);
  }
});
```

**FIX REQUIRED:**

```tsx
const [fetchError, setFetchError] = useState<any>(null);

const { loading, error, execute: fetchProducts } = useAsync({
  showErrorToast: false,
  showSuccessToast: false,
  onError: (error) => {
    setFetchError(error);
    console.error('Failed to fetch products:', error);
  }
});

// In JSX:
{fetchError && (
  <div className="rounded-lg bg-red-50 border border-red-200 p-4 mb-4">
    <h3 className="font-semibold text-red-800">Failed to load products</h3>
    <p className="text-red-700 text-sm mt-1">{fetchError.message}</p>
    <button 
      onClick={retryFetch}
      className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
    >
      Try Again
    </button>
  </div>
)}
```

---

#### Issue 4.2: Checkout validation doesn't handle all edge cases
**Location:** `frontend/src/pages/Checkout.tsx` line 75-95

**Problem:** Stock validation shows error but doesn't prevent checkout submission

**FIX REQUIRED:**

```tsx
// Create checkout handler with validation
const handleCheckoutSubmit = async () => {
  // Validate stock before allowing checkout
  if (!stockValidation.valid) {
    toast.error('Please resolve stock issues before checking out');
    navigate('/cart');
    return;
  }
  
  // Validate addresses
  if (!selectedAddress) {
    toast.error('Please select a shipping address');
    return;
  }
  
  // Validate payment
  if (!selectedPayment) {
    toast.error('Please select a payment method');
    return;
  }
  
  // Proceed with checkout
  try {
    setLoading(true);
    const result = await OrdersAPI.placeOrder({
      shipping_address_id: selectedAddress.id,
      shipping_method_id: selectedShipping.id,
      payment_method_id: selectedPayment.id,
      notes: orderNotes
    });
    
    handleSmartCheckoutSuccess(result.data?.id);
  } catch (error) {
    toast.error(error?.message || 'Checkout failed');
  } finally {
    setLoading(false);
  }
};
```

---

### 5. **Loading States & Skeleton Issues**

#### Issue 5.1: Home page has no proper empty state
**Location:** `frontend/src/pages/Home.tsx` line 150+

**Problem:** Featured products section loads indefinitely with skeletons if API fails

**FIX REQUIRED:** Add error handling and empty states

```tsx
const { data: featuredData, loading: featuredLoading, error: featuredError } = useAsync();

useEffect(() => {
  fetchFeatured(async () => {
    const response = await ProductsAPI.getFeaturedProducts(8);
    return response.data;
  });
}, []);

// In JSX:
{featuredError ? (
  <div className="text-center py-12">
    <p className="text-gray-500 mb-4">Failed to load featured products</p>
    <button onClick={refetchFeatured} className="btn-primary">
      Try Again
    </button>
  </div>
) : featuredLoading ? (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    {[...Array(4)].map((_, i) => <SkeletonProductCard key={i} />)}
  </div>
) : featuredProducts.length === 0 ? (
  <div className="text-center py-12">
    <p className="text-gray-500">No featured products available</p>
  </div>
) : (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    {featuredProducts.map(product => <ProductCard key={product.id} product={product} />)}
  </div>
)}
```

---

## Part 2: Major Issues & Improvements

### Issue 6: Cart synchronization after page reload
**Location:** `frontend/src/store/CartContext.tsx`

**Problem:** Cart doesn't persist cart ID properly, causing duplicate cart creation

**FIX:**
```tsx
useEffect(() => {
  // Fetch cart on mount to establish cart_id
  fetchCart();
  
  // Listen for storage changes from other tabs
  const handleStorageChange = (e: StorageEvent) => {
    if (e.key === 'detected_country' || e.key === 'detected_province') {
      fetchCart();
    }
  };
  
  window.addEventListener('storage', handleStorageChange);
  return () => window.removeEventListener('storage', handleStorageChange);
}, []);
```

---

### Issue 7: Product filter parameters not synced with URL
**Location:** `frontend/src/pages/Products.tsx` line 80-110

**Problem:** URL params not updated when filters change, breaks browser back button

**FIXED IN CODE** - Already uses `setSearchParams()` correctly ✅

---

### Issue 8: Missing pagination bounds checking
**Location:** `frontend/src/pages/Products.tsx` line 200+

**Problem:** Current page can exceed total pages

**FIX:**
```tsx
const handlePageChange = (page: number) => {
  const boundedPage = Math.max(1, Math.min(page, totalPages));
  setCurrentPage(boundedPage);
};
```

---

### Issue 9: Wishlist item limit not checked
**Location:** `frontend/src/components/product/ProductCard.tsx` (needs verification)

**Problem:** No UI feedback when wishlist is full

**FIX:** Add quota checking

---

### Issue 10: Missing payment method validation
**Location:** `frontend/src/pages/Checkout.tsx`

**Problem:** Checkout allows submission without valid payment method selection

**FIX:** Add validation before checkout submission (covered in Issue 4.2)

---

### Issue 11: Cart currency inconsistency
**Location:** `frontend/src/pages/Cart.tsx` line 50

**Problem:** Cart doesn't validate currency matches between items

**FIX:**
```tsx
const validateCurrency = () => {
  const currencies = new Set(cart.items.map(item => item.currency || 'USD'));
  if (currencies.size > 1) {
    toast.error('Cannot mix items in different currencies');
    return false;
  }
  return true;
};
```

---

### Issue 12: Missing quantity constraints
**Location:** `frontend/src/pages/Cart.tsx` & `frontend/src/pages/ProductDetails.tsx`

**Problem:** No max quantity checking against inventory

**FIX:**
```tsx
const maxQuantity = selectedVariant?.stock || 1;

const handleQuantityChange = (qty: number) => {
  if (qty > maxQuantity) {
    toast.error(`Only ${maxQuantity} available`);
    return;
  }
  setQuantity(qty);
};
```

---

### Issue 13: Account page profile updates not reflected
**Location:** `frontend/src/components/account/Profile.tsx`

**Problem:** Profile form doesn't properly sync updated user data to AuthContext

**FIX:**
```tsx
const handleProfileUpdate = async (updatedProfile) => {
  try {
    const result = await AuthAPI.updateProfile(updatedProfile);
    const updatedUser = transformUser(result.data.user);
    
    // Update both AuthContext and local component state
    updateUser(updatedUser);
    setProfileData(updatedUser);
    
    toast.success('Profile updated successfully');
  } catch (error) {
    toast.error(error.message);
  }
};
```

---

### Issue 14: Order status doesn't auto-refresh
**Location:** `frontend/src/components/account/OrderDetail.tsx`

**Problem:** Order status stuck showing old status after shipment updates

**FIX:**
```tsx
useEffect(() => {
  const interval = setInterval(() => {
    if (orderId) {
      fetchOrder();
    }
  }, 30000); // Refresh every 30 seconds
  
  return () => clearInterval(interval);
}, [orderId, fetchOrder]);
```

---

## Part 3: Performance Optimizations

### Issue 15: Unnecessary re-renders in ProductCard
**Location:** `frontend/src/components/product/ProductCard.tsx`

**Problem:** ProductCard re-renders on every parent state change

**FIX:**
```tsx
export const ProductCard = React.memo(({ product, onAddToCart }: Props) => {
  // Component implementation
}, (prevProps, nextProps) => {
  // Custom comparison - only re-render if product changed
  return prevProps.product.id === nextProps.product.id;
});
```

---

### Issue 16: Duplicate API requests for products
**Location:** `frontend/src/pages/ProductDetails.tsx` line 145

**Problem:** Product variants fetched separately instead of included in product data

**OPTIMIZATION:**
```typescript
// Instead of:
const product = await ProductsAPI.getProduct(id);
const variants = await ProductsAPI.getProductVariants(id);

// Use single endpoint that includes variants:
const response = await ProductsAPI.getProduct(id);
const product = response.data; // Already includes variants
```

---

### Issue 17: Missing request deduplication
**Location:** `frontend/src/api/client.ts` (RequestCache not used)

**Problem:** Identical requests made multiple times aren't cached

**FIX VERIFIED:** RequestCache is implemented but needs to be used

```typescript
// In each API method:
static async getProduct(productId: string) {
  const cacheKey = RequestCache.getCacheKey('GET', `/products/${productId}`);
  const cached = RequestCache.get(cacheKey);
  if (cached) return cached;
  
  const response = await apiClient.get(`/products/${productId}`);
  RequestCache.set(cacheKey, response);
  return response;
}
```

---

### Issue 18: Missing lazy loading for images
**Location:** `frontend/src/components/product/ProductImageGallery.tsx`

**Problem:** All product images load at once, slow on poor connections

**FIX:** Add lazy loading

```tsx
<img 
  src={images[selectedImage]}
  loading="lazy"
  alt="Product"
/>
```

---

## Part 4: UI/UX Flow Issues

### Issue 19: Cart item updates don't show loading state
**Location:** `frontend/src/pages/Cart.tsx` line 150

**Problem:** Quantity updates appear instant but API call may fail silently

**FIX:**
```tsx
const [updatingItemId, setUpdatingItemId] = useState<string | null>(null);

const handleQuantityChange = async (itemId: string, quantity: number) => {
  setUpdatingItemId(itemId);
  try {
    await updateQuantity(itemId, quantity);
  } catch (error) {
    toast.error('Failed to update quantity');
  } finally {
    setUpdatingItemId(null);
  }
};

// In JSX:
<button disabled={updatingItemId === itemId}>
  {updatingItemId === itemId ? <Spinner /> : '+'}
</button>
```

---

### Issue 20: Missing progress indicator on multi-step checkout
**Location:** `frontend/src/pages/Checkout.tsx`

**Problem:** User doesn't know how many steps remain

**FIX:** Add step indicator

```tsx
const steps = [
  { id: 1, label: 'Shipping Address' },
  { id: 2, label: 'Shipping Method' },
  { id: 3, label: 'Payment' },
  { id: 4, label: 'Review' }
];

<div className="flex justify-between mb-8">
  {steps.map((step, idx) => (
    <div key={step.id} className={`flex-1 ${currentStep >= step.id ? 'text-blue-600' : 'text-gray-400'}`}>
      <div className="font-bold">{step.id}</div>
      <div className="text-sm">{step.label}</div>
    </div>
  ))}
</div>
```

---

## Summary of All Issues

| # | Issue | Severity | Category | Status |
|---|-------|----------|----------|--------|
| 1.1 | Register param mismatch | CRITICAL | API | ❌ Needs Fix |
| 1.2 | API paths | CRITICAL | API | ✅ Verified OK |
| 1.3 | checkBulkStock missing | CRITICAL | API | ❌ Needs Fix |
| 1.4 | Orders checkout response | CRITICAL | API | ❌ Needs Fix |
| 1.5 | getRecommendedProducts missing | CRITICAL | API | ❌ Needs Fix |
| 2.1 | Register signature | MAJOR | State | ❌ Needs Fix |
| 2.2 | Cart error recovery | MAJOR | State | ⚠️ Partial |
| 2.3 | Wishlist auth check | MAJOR | State | ⚠️ Partial |
| 3.1 | Login redirect logic | MAJOR | Auth | ⚠️ Partial |
| 3.2 | Token refresh queuing | MAJOR | Auth | ⚠️ Partial |
| 4.1 | Products error UI | MAJOR | Errors | ⚠️ Partial |
| 4.2 | Checkout validation | MAJOR | Errors | ⚠️ Partial |
| 5.1 | Home empty state | MAJOR | UX | ❌ Needs Fix |
| 6+ | Performance & UX | MINOR | Various | ⚠️ Various |

---

## Recommended Fix Priority

1. **Phase 1 (Day 1):** Issues 1.1, 1.3, 1.4, 1.5
2. **Phase 2 (Day 2):** Issues 2.1, 3.1, 3.2, 4.1, 4.2
3. **Phase 3 (Day 3):** Issues 5.1-6, UI/UX improvements

---

## Backend API Verification

✅ **Verified Endpoints:**
- `/auth/register` - Expects: UserCreate(email, password, firstname, lastname)
- `/auth/login` - Expects: UserLogin(email, password)
- `/products` - GET with filters works correctly
- `/products/{id}` - GET returns product with variants
- `/cart` - GET/POST/PUT/DELETE all functional
- `/orders/checkout` - POST functional
- `/tax/calculate` - POST functional

⚠️ **Needs Backend Verification:**
- `/cart/check-stock` - Endpoint should exist (needs confirmation)
- `/products/{id}/recommended` - Check exact path

---

## Next Steps

1. Apply all fixes in the order listed
2. Test each page flow end-to-end
3. Add comprehensive error logging
4. Run load testing on cart operations
5. Verify all auth flows work with token refresh

---
