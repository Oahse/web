# Frontend Fix Implementation Guide

## Quick Reference

### Files to Update Immediately (Critical Fixes)

1. **`frontend/src/api/cart.ts`** - Add missing `checkBulkStock` method
2. **`frontend/src/api/products.ts`** - Add missing `getRecommendedProducts` method  
3. **`frontend/src/pages/Register.tsx`** - Fix parameter order
4. **`frontend/src/pages/Checkout.tsx`** - Fix response handling and validation

### Corrected Files Provided

- `frontend/src/api/cart.CORRECTED.ts` - Full corrected version
- `frontend/src/api/products.CORRECTED.ts` - Full corrected version
- `frontend/src/pages/Register.CORRECTED.tsx` - Full corrected version
- `frontend/src/pages/Checkout.CORRECTED.tsx` - Full corrected version

---

## Implementation Steps

### Step 1: Update Cart API

**File:** `frontend/src/api/cart.ts`

Add this method to the `CartAPI` class:

```typescript
/**
 * Check stock availability for multiple variants
 * ACCESS: Public - No authentication required
 * Issue 1.3 Fix
 */
static async checkBulkStock(items: Array<{ variant_id: string; quantity: number }>) {
  return await apiClient.post('/cart/check-stock', { items });
}
```

Also add this method for better checkout support:

```typescript
/**
 * Validate cart for checkout
 * ACCESS: Authenticated - Requires user login
 */
static async validateCart() {
  return await apiClient.post('/cart/validate', {});
}

/**
 * Get shipping methods available for cart
 * ACCESS: Public - No authentication required
 */
static async getShippingMethods(country?: string, province?: string) {
  const params = new URLSearchParams();
  if (country) params.append('country', country);
  if (province) params.append('province', province);
  
  const queryString = params.toString();
  const url = queryString ? `/cart/shipping-methods?${queryString}` : '/cart/shipping-methods';
  
  return await apiClient.get(url);
}
```

---

### Step 2: Update Products API

**File:** `frontend/src/api/products.ts`

Add these methods to the `ProductsAPI` class:

```typescript
/**
 * Get recommended/related products for a specific product
 * ACCESS: Public - No authentication required
 * Issue 1.5 Fix
 */
static async getRecommendedProducts(productId: string, limit = 4) {
  return await apiClient.get(`/products/${productId}/recommended?limit=${limit}`);
}

/**
 * Get categories
 * ACCESS: Public - No authentication required
 */
static async getCategories(params?: any) {
  const queryParams = new URLSearchParams();
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.sort) queryParams.append('sort', params.sort);

  const url = `/products/categories${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  return await apiClient.get(url);
}

/**
 * Get single category
 * ACCESS: Public - No authentication required
 */
static async getCategory(categoryId: string) {
  return await apiClient.get(`/products/categories/${categoryId}`);
}
```

Also add the `CategoriesAPI` class export:

```typescript
/**
 * Categories API endpoints
 */
export class CategoriesAPI {
  static async getCategories(params?: any) {
    return ProductsAPI.getCategories(params);
  }

  static async getCategory(categoryId: string) {
    return ProductsAPI.getCategory(categoryId);
  }
}
```

---

### Step 3: Fix Register Component

**File:** `frontend/src/pages/Register.tsx`

Key changes:

1. Split name into firstname and lastname:
```typescript
// OLD (REMOVE):
const [name, setName] = useState('');

// NEW:
const [firstname, setFirstname] = useState('');
const [lastname, setLastname] = useState('');
```

2. Update form inputs:
```tsx
{/* First Name Input */}
<div>
  <label className="block text-sm font-medium text-copy mb-2">First Name *</label>
  <Input
    type="text"
    placeholder="Enter your first name"
    value={firstname}
    onChange={(e) => setFirstname(e.target.value)}
    disabled={loading}
    required
  />
</div>

{/* Last Name Input */}
<div>
  <label className="block text-sm font-medium text-copy mb-2">Last Name *</label>
  <Input
    type="text"
    placeholder="Enter your last name"
    value={lastname}
    onChange={(e) => setLastname(e.target.value)}
    disabled={loading}
    required
  />
</div>
```

3. Update validation in handleSubmit:
```typescript
const handleSubmit = async (e) => {
  e.preventDefault();

  // Validate firstname
  const firstnameValidation = validation.name(firstname);
  if (!firstnameValidation.valid) {
    toast.error(`First name: ${firstnameValidation.message}`);
    return;
  }

  // Validate lastname
  const lastnameValidation = validation.name(lastname);
  if (!lastnameValidation.valid) {
    toast.error(`Last name: ${lastnameValidation.message}`);
    return;
  }

  // ... other validations ...

  try {
    setLoading(true);
    // FIXED: Pass parameters in correct order
    await register(
      firstname.trim(),
      lastname.trim(),
      email.toLowerCase().trim(),
      password
    );
    // ...
  }
};
```

---

### Step 4: Fix Checkout Component

**File:** `frontend/src/pages/Checkout.tsx`

1. Fix response handling in stock validation:
```typescript
useEffect(() => {
  const validateStock = async () => {
    if (!cart?.items || cart.items.length === 0) {
      setStockValidation({ valid: true, issues: [] });
      return;
    }

    try {
      const stockCheckRes = await CartAPI.checkBulkStock(cart.items.map(item => ({
        variant_id: item.variant_id || item.variant?.id,
        quantity: item.quantity
      })));

      // FIXED: Handle wrapped response structure
      const stockCheckData = stockCheckRes.data || stockCheckRes;
      const stockCheck = stockCheckData?.data || stockCheckData;
      
      const stockIssues = stockCheck?.items?.filter((item: any) => !item.available) || [];
      
      // ... rest of validation
    } catch (error) {
      console.error('Stock validation failed:', error);
      setStockValidation({ valid: false, issues: [] });
    }
  };

  if (!authLoading && isAuthenticated && cart?.items) {
    validateStock();
    const interval = setInterval(validateStock, 300000);
    return () => clearInterval(interval);
  }
}, [cart?.items, authLoading, isAuthenticated]);
```

2. Add comprehensive validation function:
```typescript
const validateCheckout = (): boolean => {
  if (!stockValidation.valid && stockValidation.issues.length > 0) {
    toast.error('Please resolve stock issues. Check items in your cart.');
    return false;
  }

  if (!selectedAddress) {
    toast.error('Please select a shipping address');
    return false;
  }

  if (!selectedShipping) {
    toast.error('Please select a shipping method');
    return false;
  }

  if (!selectedPayment) {
    toast.error('Please select a payment method');
    return false;
  }

  if (!cart?.items || cart.items.length === 0) {
    toast.error('Your cart is empty');
    return false;
  }

  return true;
};
```

3. Update checkout handler:
```typescript
const handleCheckoutSubmit = async () => {
  if (!validateCheckout()) {
    return;
  }

  setLoading(true);
  try {
    const result = await OrdersAPI.placeOrder({
      shipping_address_id: selectedAddress.id,
      shipping_method_id: selectedShipping.id,
      payment_method_id: selectedPayment.id,
      notes: orderNotes || undefined
    });

    // FIXED: Handle response properly
    const orderId = result.data?.id || result.data?.order_id;
    
    if (!orderId) {
      throw new Error('Order ID not found in response');
    }

    await clearCart();
    toast.success('Order placed successfully!');
    
    navigate(`/account/orders/${orderId}`, {
      replace: true,
      state: { fromCheckout: true }
    });
    
  } catch (error: any) {
    console.error('Checkout error:', error);
    const errorMessage = error?.response?.data?.message || 
                        error?.message || 
                        'Failed to place order. Please try again.';
    toast.error(errorMessage);
    setLoading(false);
  }
};
```

---

### Step 5: Update Login Page Redirect Logic

**File:** `frontend/src/pages/Login.tsx`

Replace the `getRedirectPath` function:

```typescript
const getRedirectPath = useCallback((user: any) => {
  // Priority 1: Back to previous page
  if (location.state?.from?.pathname && location.state.from.pathname !== '/login') {
    return location.state.from.pathname + (location.state.from.search || '');
  }
  
  // Priority 2: Intended destination
  if (intendedDestination && (intendedDestination as any).path !== '/login') {
    return (intendedDestination as any).path;
  }
  
  // Priority 3: Redirect param
  const params = new URLSearchParams(location.search);
  const redirect = params.get('redirect');
  if (redirect) {
    try {
      return decodeURIComponent(redirect);
    } catch (e) {
      console.error('Failed to decode redirect URL:', e);
    }
  }
  
  // Priority 4: Role-based defaults
  if (user?.role === 'Admin') return '/admin';
  if (user?.role === 'Supplier') return '/account/products';
  
  // Default
  return '/';
}, [location.state, location.search, intendedDestination]);
```

---

## Testing Checklist

- [ ] User can register with firstname and lastname
- [ ] Registration stores data correctly in backend
- [ ] User can login with email/password
- [ ] Cart shows proper errors when items out of stock
- [ ] Checkout validates all required fields
- [ ] Order is created with correct data
- [ ] Response handling works for all API calls
- [ ] Token refresh works when token expires
- [ ] Redirect after login works correctly
- [ ] Product details loads with recommended products
- [ ] Featured products on home page load properly

---

## Backend Verification Needed

Confirm these endpoints exist in backend:

- [ ] `POST /v1/cart/check-stock` - Stock validation
- [ ] `GET /v1/products/{id}/recommended` - Related products
- [ ] `POST /v1/orders/checkout` - Order creation (verify response format)
- [ ] `POST /v1/cart/validate` - Cart validation

---

## Additional Improvements (Non-Critical)

1. **Add loading states to buttons** (Issue 19)
2. **Add checkout progress indicator** (Issue 20)
3. **Add empty states to all pages** (Issue 5.1)
4. **Add request deduplication cache** (Issue 17)
5. **Improve error recovery in CartContext** (Issue 2.2)
6. **Add auth state checking to Wishlist** (Issue 2.3)

---

## Support

For each issue, refer to the main audit document:
`/Users/oscaroguledo/Documents/banwee/FRONTEND_BACKEND_INTEGRATION_AUDIT.md`

Issues are referenced by number (e.g., Issue 1.3, Issue 4.2, etc.)

