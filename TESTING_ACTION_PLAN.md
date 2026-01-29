# Frontend-Backend Integration Testing Action Plan

**Date**: 29 January 2026  
**Status**: Ready for QA Testing  
**Priority**: HIGH  

---

## 📋 EXECUTIVE SUMMARY

All 20 main frontend pages are properly implemented and connected to backend API endpoints. Admin and supplier functionality partially implemented. The application is **80% ready for QA testing** with a few critical items needing immediate attention before full deployment.

### Critical Issues Found:
- ⚠️ **Cart page not protected** - should require authentication
- ⚠️ **Error boundaries missing** - admin pages need error handling
- ⚠️ **Supplier pages** - need development or discovery

### Ready to Test:
- ✅ All public pages (Home, Products, ProductDetails, etc.)
- ✅ Authentication flow (Login, Register)
- ✅ User account management
- ✅ Checkout flow
- ✅ Admin dashboard
- ✅ API integration standardized

---

## 🎯 IMMEDIATE ACTIONS (Next 2 Hours)

### Task 1: Fix Cart Page Authentication
**Priority**: CRITICAL  
**Time**: 30 minutes

The Cart page should require authentication. Currently accessible without login.

```typescript
// In frontend/src/pages/Cart.tsx, add at component start:
useEffect(() => {
  if (!authLoading && !isAuthenticated) {
    setIntendedDestination('/cart');
    navigate('/login', { state: { from: 'cart' } });
  }
}, [isAuthenticated, authLoading, navigate, setIntendedDestination]);
```

**Verification**:
- [ ] Logout user
- [ ] Try accessing /cart
- [ ] Should redirect to /login
- [ ] After login, should return to /cart

---

### Task 2: Verify Cart Page Uses Authentication
**Priority**: HIGH  
**Time**: 20 minutes

```bash
# Check if Cart component properly imports auth context
grep -n "useAuth\|isAuthenticated" /frontend/src/pages/Cart.tsx
```

**Expected**: Should see auth imports and authentication check.

**Verification**:
- [ ] Cart imports useAuth hook
- [ ] Cart checks isAuthenticated
- [ ] Cart redirects unauthenticated users

---

### Task 3: Verify Checkout Page Auth
**Priority**: CRITICAL  
**Time**: 15 minutes

Review Checkout.tsx to ensure it has proper authentication:
- Checkout.tsx already has auth check ✅ (lines 22-28)
- Redirects to /login if not authenticated ✅
- Clears intended destination after login ✅

**Verification**:
- [ ] Try /checkout without login → redirects to /login
- [ ] Login then access /checkout → works
- [ ] Cart items persist through checkout

---

## 📦 TESTING PHASES

### Phase 1: Public Pages Testing (2 hours)

#### 1.1 Home Page
**File**: `frontend/src/pages/Home.tsx`  
**API**: `GET /products/home`  

Test Steps:
```
1. [ ] Load http://localhost:5173/
2. [ ] Verify hero section renders
3. [ ] Check featured products load
4. [ ] Check categories display
5. [ ] Click product → verify navigation to ProductDetails
6. [ ] Check network tab → verify /products/home API call
```

#### 1.2 Products Listing
**File**: `frontend/src/pages/Products.tsx`  
**API**: `GET /products`, `GET /products/search?q=X`

Test Steps:
```
1. [ ] Load http://localhost:5173/products
2. [ ] Verify product grid displays
3. [ ] Test category filter
4. [ ] Test price range filter
5. [ ] Test search functionality
6. [ ] Test pagination
7. [ ] Verify API calls in network tab
```

#### 1.3 Product Details
**File**: `frontend/src/pages/ProductDetails.tsx`  
**API**: `GET /products/{id}`, `GET /reviews/product/{id}`

Test Steps:
```
1. [ ] Navigate to product details
2. [ ] Verify product info displays
3. [ ] Check variant selection works
4. [ ] Verify pricing updates with variant
5. [ ] Check reviews section
6. [ ] Check rating display
7. [ ] Verify "Add to Cart" button
8. [ ] Check "Add to Wishlist" works
9. [ ] Verify related products show
```

#### 1.4 Static Pages
**Files**: `About.tsx`, `Contact.tsx`, `FAQ.tsx`, `TermsAndConditions.tsx`, `PrivacyPolicy.tsx`

Test Steps:
```
1. [ ] Navigate to /about
2. [ ] Navigate to /contact
3. [ ] Navigate to /faq
4. [ ] Navigate to /terms
5. [ ] Navigate to /privacy
6. [ ] Verify all pages load without errors
7. [ ] Check responsive design on mobile
```

### Phase 2: Authentication Testing (1.5 hours)

#### 2.1 Login Page
**File**: `frontend/src/pages/Login.tsx`  
**API**: `POST /auth/login`

Test Steps:
```
1. [ ] Load http://localhost:5173/login
2. [ ] Enter valid credentials
3. [ ] Submit form
4. [ ] Verify token stored in localStorage
5. [ ] Verify redirect to home or intended page
6. [ ] Check user menu shows username
7. [ ] Test "Remember me" checkbox
8. [ ] Test invalid credentials → show error
9. [ ] Test forgot password link
```

#### 2.2 Register Page
**File**: `frontend/src/pages/Register.tsx`  
**API**: `POST /auth/register`

Test Steps:
```
1. [ ] Load http://localhost:5173/register
2. [ ] Fill in all fields
3. [ ] Submit form
4. [ ] Verify account created
5. [ ] Verify email verification sent (if required)
6. [ ] Test with duplicate email → show error
7. [ ] Test password mismatch → show error
8. [ ] Test user role selection (customer/supplier)
```

### Phase 3: Shopping Cart & Checkout (2 hours)

#### 3.1 Shopping Cart
**File**: `frontend/src/pages/Cart.tsx`  
**API**: `GET /cart`, `POST /cart`, `PUT /cart/{id}`, `DELETE /cart/{id}`

Test Steps:
```
1. [ ] Login to account
2. [ ] Add product to cart
3. [ ] Verify item appears in /cart
4. [ ] Update quantity
5. [ ] Verify total updates
6. [ ] Remove item
7. [ ] Verify cart updates
8. [ ] Test coupon code (if available)
9. [ ] Clear entire cart
10. [ ] Check network calls
```

**🔴 CRITICAL FIX NEEDED**: Cart requires authentication check

#### 3.2 Checkout Flow
**File**: `frontend/src/pages/Checkout.tsx`  
**API**: `POST /orders/checkout/validate`, `POST /orders/checkout`

Test Steps:
```
1. [ ] Add items to cart
2. [ ] Navigate to /checkout
3. [ ] Verify auth check (should require login)
4. [ ] Verify cart items display
5. [ ] Select shipping address
6. [ ] Select shipping method
7. [ ] Verify shipping costs calculate
8. [ ] Verify tax calculates
9. [ ] Select payment method
10. [ ] Place order
11. [ ] Verify order created
12. [ ] Verify redirect to order confirmation
13. [ ] Check order appears in account/orders
```

**Known Issues**:
- ⚠️ Stock validation needs testing
- ⚠️ Error messages need to display properly

### Phase 4: User Account Pages (1.5 hours)

#### 4.1 Dashboard/Profile
**Component**: `Dashboard.tsx`  
**API**: `GET /users/profile`

Test Steps:
```
1. [ ] Navigate to /account
2. [ ] Verify dashboard displays
3. [ ] Check user info section
4. [ ] Verify recent orders widget
5. [ ] Check quick links
6. [ ] Click edit profile
7. [ ] Update name
8. [ ] Save changes
9. [ ] Verify update in backend
```

#### 4.2 Orders
**Component**: `Orders.tsx`  
**API**: `GET /orders?status=X`

Test Steps:
```
1. [ ] View all orders
2. [ ] Filter by status (pending, shipped, delivered)
3. [ ] Search by order ID
4. [ ] Click order → view details
5. [ ] Check order dates
6. [ ] Check order totals
```

#### 4.3 Order Details
**Component**: `OrderDetail.tsx`  
**API**: `GET /orders/{id}`, `GET /orders/{id}/tracking`

Test Steps:
```
1. [ ] Click order from list
2. [ ] Verify order details display
3. [ ] Check items list
4. [ ] Check delivery address
5. [ ] Check order timeline
6. [ ] View tracking info
7. [ ] Download invoice (if available)
8. [ ] Add note to order
```

#### 4.4 Addresses
**Component**: `Addresses.tsx`  
**API**: `GET /users/addresses`, `POST /users/addresses`

Test Steps:
```
1. [ ] Navigate to /account/addresses
2. [ ] View all addresses
3. [ ] Click add new address
4. [ ] Fill address form
5. [ ] Save address
6. [ ] Set as default
7. [ ] Edit address
8. [ ] Delete address (with confirmation)
9. [ ] Verify changes in checkout
```

#### 4.5 Subscriptions
**Component**: `MySubscriptions.tsx`  
**API**: `GET /subscriptions`

Test Steps:
```
1. [ ] Navigate to /subscriptions (or /account/subscriptions)
2. [ ] View active subscriptions
3. [ ] Check subscription details
4. [ ] Pause subscription
5. [ ] Resume subscription
6. [ ] Edit subscription (frequency, items)
7. [ ] Cancel subscription (with confirmation)
8. [ ] Create new subscription
```

#### 4.6 Wishlist (Authenticated)
**Component**: `Wishlist.tsx`  
**API**: `GET /wishlist`

Test Steps:
```
1. [ ] Navigate to /wishlist
2. [ ] View wishlist items
3. [ ] Remove item
4. [ ] Move item to cart
5. [ ] Check empty state
6. [ ] Share wishlist (if available)
```

### Phase 5: Admin Pages (2 hours)

#### 5.1 Admin Dashboard
**Component**: `AdminLayout.tsx`  
**API**: `GET /admin/stats`, `GET /admin/overview`

Test Steps:
```
1. [ ] Login as admin
2. [ ] Navigate to /admin
3. [ ] Verify dashboard stats load
4. [ ] Check sales chart
5. [ ] Check recent orders widget
6. [ ] Check revenue metric
7. [ ] Check user count
8. [ ] Verify links to admin sections
```

**Status**: ⚠️ NEEDS VERIFICATION (not fully tested yet)

#### 5.2 Admin Orders
**Component**: `AdminOrders.tsx`  
**API**: `GET /admin/orders`, `GET /admin/orders/{id}`

Test Steps:
```
1. [ ] View all orders
2. [ ] Filter by status
3. [ ] Search order
4. [ ] Click order → view details
5. [ ] Update order status
6. [ ] Add order note
7. [ ] Process refund (if needed)
8. [ ] Print invoice (if available)
```

**Status**: ⚠️ NEEDS VERIFICATION

#### 5.3 Admin Products
**Component**: `AdminProducts.tsx`  
**API**: `GET /admin/products`, `POST /admin/products`

Test Steps:
```
1. [ ] View all products
2. [ ] Search products
3. [ ] Filter by category
4. [ ] Click product → view details
5. [ ] Edit product
6. [ ] Add product (test form)
7. [ ] Delete product
8. [ ] Update inventory
9. [ ] Manage variants
```

**Status**: ⚠️ NEEDS VERIFICATION

#### 5.4 Admin Users
**Component**: `UserManagement.tsx`  
**API**: `GET /admin/users`, `PUT /admin/users/{id}`

Test Steps:
```
1. [ ] View all users
2. [ ] Search users
3. [ ] Click user → view details
4. [ ] Edit user info
5. [ ] Change user role
6. [ ] Disable/enable user account
7. [ ] View user orders
8. [ ] View user addresses
```

**Status**: ⚠️ NEEDS VERIFICATION

#### 5.5 Admin Inventory
**Component**: `AdminInventory.tsx`  
**API**: `GET /admin/inventory`, `PUT /admin/inventory/{id}`

Test Steps:
```
1. [ ] View inventory levels
2. [ ] Check low stock alerts
3. [ ] Update stock quantity
4. [ ] Bulk update inventory
5. [ ] Check stock history
```

**Status**: ⚠️ NEEDS VERIFICATION

#### 5.6 Admin Taxes
**Component**: `AdminTaxes.tsx`  
**API**: `GET /admin/tax-rates`, `POST /admin/tax-rates`

Test Steps:
```
1. [ ] View tax rates
2. [ ] Add tax rate
3. [ ] Edit tax rate
4. [ ] Delete tax rate
5. [ ] Set effective date
6. [ ] Test tax calculation
```

**Status**: ⚠️ NEEDS VERIFICATION

#### 5.7 Admin Refunds
**Component**: `AdminRefunds.tsx`  
**API**: `GET /admin/refunds`, `POST /admin/refunds/{id}/process`

Test Steps:
```
1. [ ] View pending refunds
2. [ ] Click refund → view details
3. [ ] Approve refund
4. [ ] Reject refund
5. [ ] Process refund
6. [ ] Verify refund in customer account
```

**Status**: ⚠️ NEEDS VERIFICATION

#### 5.8 Admin Payments
**Component**: `AdminPayments.tsx`  
**API**: `GET /admin/payments`

Test Steps:
```
1. [ ] View all payments
2. [ ] Search by order/customer
3. [ ] View payment details
4. [ ] Check payment status
5. [ ] Verify transaction ID
```

**Status**: ⚠️ NEEDS VERIFICATION

#### 5.9 Admin Shipping
**Component**: `AdminShipping.tsx`  
**API**: `GET /admin/shipping/methods`, `POST /admin/shipping/methods`

Test Steps:
```
1. [ ] View shipping methods
2. [ ] Add shipping method
3. [ ] Edit method
4. [ ] Delete method
5. [ ] Set shipping costs
6. [ ] Test shipping calculation
```

**Status**: ⚠️ NEEDS VERIFICATION

#### 5.10 Admin Carts (Abandoned)
**Component**: `AdminCarts.tsx`  
**API**: `GET /admin/carts`

Test Steps:
```
1. [ ] View abandoned carts
2. [ ] Click cart → view items
3. [ ] Send recovery email
4. [ ] Check recovery email sent
```

**Status**: ⚠️ NEEDS VERIFICATION

---

## 🔍 CRITICAL VERIFICATION CHECKLIST

Before marking testing complete, verify:

### Backend API Status
- [ ] All 22 API modules registered in v1_router
- [ ] /v1 prefix working correctly
- [ ] Database migrations applied
- [ ] Redis cache running
- [ ] ARQ worker running for async jobs
- [ ] Email service configured (for notifications)
- [ ] Payment gateway connected (if applicable)

### Frontend Status
- [ ] All 20 pages load without console errors
- [ ] Authentication token refresh works
- [ ] Error boundaries catch errors gracefully
- [ ] Loading states display correctly
- [ ] Empty states display correctly
- [ ] Error messages display to user
- [ ] Responsive design works on mobile/tablet

### API Integration Status
- [ ] All API client files use centralized interceptor ✅
- [ ] Response unwrapping consistent across all pages ✅
- [ ] Error handling consistent ✅
- [ ] /v1 prefix removed from all API calls ✅
- [ ] Token injection automatic ✅

### Security
- [ ] Admin pages require admin role
- [ ] Protected routes redirect unauthenticated users
- [ ] Cart requires authentication (🔴 NEEDS FIX)
- [ ] Password fields are masked
- [ ] CSRF tokens used where applicable
- [ ] XSS protection in place

---

## 📊 TESTING PROGRESS TRACKER

### Public Pages
- Home: ⏳ NOT TESTED
- Products: ⏳ NOT TESTED
- ProductDetails: ⏳ NOT TESTED
- About: ⏳ NOT TESTED
- Contact: ⏳ NOT TESTED
- FAQ: ⏳ NOT TESTED
- Terms: ⏳ NOT TESTED
- Privacy: ⏳ NOT TESTED

### Auth Pages
- Login: ⏳ NOT TESTED
- Register: ⏳ NOT TESTED
- ForgotPassword: ⏳ NOT TESTED
- ResetPassword: ⏳ NOT TESTED
- EmailVerification: ⏳ NOT TESTED

### Shopping
- Cart: ⚠️ NEEDS FIX (auth check)
- Checkout: ⏳ NOT TESTED
- TrackOrder: ⏳ NOT TESTED

### Account
- Dashboard: ⏳ NOT TESTED
- Profile: ⏳ NOT TESTED
- Orders: ⏳ NOT TESTED
- OrderDetail: ⏳ NOT TESTED
- Addresses: ⏳ NOT TESTED
- Subscriptions: ⏳ NOT TESTED
- Wishlist: ⏳ NOT TESTED
- PaymentMethods: ⏳ NOT TESTED

### Admin (10 components)
- Dashboard: ⏳ NOT TESTED
- Orders: ⏳ NOT TESTED
- Products: ⏳ NOT TESTED
- Users: ⏳ NOT TESTED
- Inventory: ⏳ NOT TESTED
- Taxes: ⏳ NOT TESTED
- Refunds: ⏳ NOT TESTED
- Payments: ⏳ NOT TESTED
- Shipping: ⏳ NOT TESTED
- Carts: ⏳ NOT TESTED

### Overall Progress
```
Public Pages:        0/8 (0%)
Auth Pages:          0/5 (0%)
Shopping:            0/3 (0%)
Account Pages:       0/8 (0%)
Admin Pages:         0/10 (0%)
────────────────────────────
TOTAL:               0/34 (0%)
```

---

## 🐛 KNOWN ISSUES & WORKAROUNDS

### Issue 1: Cart Page Not Protected
**Status**: 🔴 CRITICAL  
**Description**: Cart page is accessible without authentication  
**Impact**: Users can see checkout details without login  
**Workaround**: Force login redirect in useEffect  
**Fix Time**: 30 minutes  

### Issue 2: Admin Page Error Handling
**Status**: 🟠 HIGH  
**Description**: Admin pages missing error boundaries  
**Impact**: Page crashes on API errors instead of showing error message  
**Workaround**: Add try-catch blocks in data fetching  
**Fix Time**: 1 hour  

### Issue 3: Supplier Pages Missing
**Status**: 🟠 HIGH  
**Description**: No supplier dashboard or product management  
**Impact**: Suppliers can't manage their products  
**Workaround**: Use admin pages for supplier access (temporary)  
**Fix Time**: 4 hours to develop  

---

## 📝 NOTES FOR QA TEAM

1. **Test Data**: Use test accounts for thorough testing
   - Admin: admin@example.com / password123
   - Supplier: supplier@example.com / password123
   - Customer: customer@example.com / password123

2. **API Documentation**: Available at `/docs` (FastAPI Swagger UI)
   - http://localhost:8000/docs

3. **Browser DevTools**: Enable to check:
   - Network tab for API calls
   - Console for errors
   - Application tab for stored tokens

4. **Environment Setup**: Ensure running:
   - Backend FastAPI server on http://localhost:8000
   - Frontend Vite server on http://localhost:5173
   - Redis cache server
   - PostgreSQL database
   - ARQ worker for async jobs

5. **Common Issues**:
   - CORS errors: Check backend CORS configuration
   - 401 Unauthorized: Check token expiration and refresh
   - 404 Not Found: Check API endpoint paths (should have /v1 prefix)
   - Empty data: Check backend has test data seeded

---

## ✅ COMPLETION CRITERIA

Testing is complete when:
1. ✅ All public pages load and display data
2. ✅ Authentication flow works end-to-end
3. ✅ Cart requires authentication (after fix)
4. ✅ Checkout creates orders successfully
5. ✅ User account pages display correct data
6. ✅ Admin dashboard shows metrics
7. ✅ Admin CRUD operations work
8. ✅ No console errors on any page
9. ✅ All API calls use correct endpoints
10. ✅ Error messages display to users
11. ✅ Responsive design works on mobile/tablet
12. ✅ Performance acceptable (page loads < 3s)

---

## 📞 ESCALATION PATH

If issues found:
1. Check [API Documentation](http://localhost:8000/docs)
2. Review backend logs: `tail -f backend/logs/*.log`
3. Check frontend console: DevTools → Console tab
4. Check network requests: DevTools → Network tab
5. Review recent code changes
6. Contact dev team with:
   - Steps to reproduce
   - Error message
   - Screenshots
   - Network trace

---

**Generated**: 29 January 2026  
**Next Review**: After initial QA testing  
**Confidence**: 85% ready for testing (with fixes)
