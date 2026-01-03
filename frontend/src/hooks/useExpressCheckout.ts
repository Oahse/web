/**
 * Checkout Hook - Optimized for performance and responsiveness
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useCart } from '../contexts/CartContext';
import { AuthAPI } from '../apis/auth';
import { CartAPI } from '../apis/cart';
import { OrdersAPI } from '../apis/orders';
import { TokenManager } from '../apis/client';
import { toast } from 'react-hot-toast';

interface ExpressCheckoutData {
  address: any;
  payment: any;
  shipping: any;
  total: number;
  stockValidated: boolean;
}

interface UseExpressCheckoutReturn {
  canUseExpress: boolean;
  expressData: ExpressCheckoutData | null;
  loading: boolean;
  handleExpressCheckout: () => Promise<void>;
  refreshEligibility: () => Promise<void>;
}

export const useExpressCheckout = (
  onSuccess: (orderId: string) => void,
  onFallback: () => void
): UseExpressCheckoutReturn => {
  const { user } = useAuth();
  const { cart, clearCart } = useCart();
  
  const [canUseExpress, setCanUseExpress] = useState(false);
  const [expressData, setExpressData] = useState<ExpressCheckoutData | null>(null);
  const [loading, setLoading] = useState(false);
  const [checkoutInProgress, setCheckoutInProgress] = useState(false);

  // Cache for user preferences to avoid repeated API calls
  const [cachedPreferences, setCachedPreferences] = useState<{
    addresses?: any[];
    paymentMethods?: any[];
    shippingMethods?: any[];
    timestamp?: number;
  }>({});

  const CACHE_DURATION = 10 * 60 * 1000; // 10 minutes - increased cache duration

  const calculateTotal = useCallback((cart: any, shippingMethod: any) => {
    const subtotal = cart?.subtotal || 0;
    const shipping = shippingMethod?.price || 0;
    const tax = cart?.tax_amount || 0;
    return subtotal + shipping + tax;
  }, []);

  const loadUserPreferences = useCallback(async (useCache = true) => {
    const now = Date.now();
    
    // Use cache if available and not expired
    if (useCache && cachedPreferences.timestamp && 
        (now - cachedPreferences.timestamp) < CACHE_DURATION &&
        cachedPreferences.addresses && cachedPreferences.paymentMethods && cachedPreferences.shippingMethods) {
      return cachedPreferences;
    }

    try {
      // Load preferences in parallel for better performance
      const [addressesRes, paymentMethodsRes] = await Promise.all([
        AuthAPI.getAddresses(),
        AuthAPI.getPaymentMethods()
      ]);

      // Get shipping methods from database using the first available address
      let shippingMethods: any[] = [];
      const defaultAddress = addressesRes.data?.find((addr: any) => addr.is_default) || addressesRes.data?.[0];
      
      if (defaultAddress) {
        try {
          const accessToken = TokenManager.getToken();
          if (accessToken) {
            const shippingRes = await CartAPI.getShippingOptions(defaultAddress, accessToken);
            shippingMethods = Array.isArray(shippingRes.data?.shipping_options) ? shippingRes.data.shipping_options : [];
          }
        } catch (shippingError) {
          console.error('Failed to load shipping options for express checkout:', shippingError);
          // Continue with empty array - express checkout will be disabled
        }
      }

      const preferences = {
        addresses: addressesRes.data || [],
        paymentMethods: paymentMethodsRes.data || [],
        shippingMethods: shippingMethods,
        timestamp: now
      };

      setCachedPreferences(preferences);
      return preferences;
    } catch (error) {
      console.error('Failed to load user preferences:', error);
      return null;
    }
  }, [cachedPreferences, user]);

  const checkExpressEligibility = useCallback(async () => {
    if (!user || !cart?.items?.length) {
      setCanUseExpress(false);
      setExpressData(null);
      return;
    }

    setLoading(true);
    try {
      // Load user preferences and validate stock in parallel
      const [preferences, stockCheckRes] = await Promise.all([
        loadUserPreferences(),
        CartAPI.checkBulkStock((cart?.items || []).map((item: any) => ({
          variant_id: item.variant_id || item.variant?.id,
          quantity: item.quantity
        })))
      ]);

      if (!preferences) {
        setCanUseExpress(false);
        return;
      }

      // Check stock availability first - if not available, no Checkout
      const stockCheck = stockCheckRes.data;
      if (!stockCheck?.all_available) {
        setCanUseExpress(false);
        setExpressData(null);
        return;
      }

      // Find default/preferred options
      const defaultAddress = preferences.addresses?.find((addr: any) => addr.is_default) || preferences.addresses?.[0];
      const defaultPayment = preferences.paymentMethods?.find((pm: any) => pm.is_default) || preferences.paymentMethods?.[0];
      // Select the cheapest shipping method for express checkout (usually the first one since they're ordered by price)
      const cheapestShipping = preferences.shippingMethods?.[0];

      if (defaultAddress && defaultPayment && cheapestShipping) {
        const expressCheckoutData: ExpressCheckoutData = {
          address: defaultAddress,
          payment: defaultPayment,
          shipping: cheapestShipping,
          total: calculateTotal(cart, cheapestShipping),
          stockValidated: true
        };

        setExpressData(expressCheckoutData);
        setCanUseExpress(true);
      } else {
        setCanUseExpress(false);
        setExpressData(null);
      }
    } catch (error) {
      console.error('Failed to check express eligibility:', error);
      setCanUseExpress(false);
      setExpressData(null);
    } finally {
      setLoading(false);
    }
  }, [user, cart, loadUserPreferences, calculateTotal]);

  const handleExpressCheckout = useCallback(async () => {
    if (!expressData || checkoutInProgress) return;

    setCheckoutInProgress(true);
    setLoading(true);

    try {
      // Final stock validation before checkout
      const stockCheck = await CartAPI.checkBulkStock((cart?.items || []).map((item: any) => ({
        variant_id: item.variant_id || item.variant?.id,
        quantity: item.quantity
      })));

      if (!stockCheck.data?.all_available) {
        const unavailableItems = stockCheck.data?.items?.filter((item: any) => !item.available) || [];
        toast.error(`${unavailableItems.length} item(s) are no longer available. Please review your cart.`);
        onFallback();
        return;
      }

      // Generate idempotency key to prevent duplicate orders
      const idempotencyKey = `express_${(user as any)?.id || 'anonymous'}_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;

      const checkoutRequest = {
        shipping_address_id: expressData.address?.id,
        shipping_method_id: expressData.shipping?.id,
        payment_method_id: expressData.payment?.id,
        notes: 'Checkout order',
        express_checkout: true,
        idempotency_key: idempotencyKey
      };

      // Add idempotency header
      const response = await OrdersAPI.checkout(checkoutRequest);

      if (response?.success && response?.data) {
        toast.success('Order placed successfully! 🎉', {
          duration: 4000,
          icon: '🎉'
        });
        
        // Clear cart and cache
        await clearCart();
        setCachedPreferences({}); // Clear cache to force refresh next time
        
        onSuccess(response.data?.id || response.data);
      } else {
        throw new Error(response?.message || 'Failed to place order');
      }
    } catch (error) {
      console.error('Checkout failed:', error);
      
      // Handle specific error types with user-friendly messages
      const errorDetail = (error as any)?.response?.data?.detail;
      if (typeof errorDetail === 'object' && errorDetail?.error_type === 'STOCK_UNAVAILABLE') {
        const stockIssues = errorDetail.stock_issues || [];
        toast.error(`${stockIssues.length} item(s) are out of stock. Please review your cart.`);
      } else if ((error as any)?.response?.status === 409) {
        toast.error('This order has already been placed. Please check your order history.');
      } else if ((error as any)?.response?.status === 429) {
        toast.error('Too many requests. Please wait a moment and try again.');
      } else {
        toast.error('Checkout failed. Please try regular checkout.');
      }
      
      onFallback();
    } finally {
      setLoading(false);
      setCheckoutInProgress(false);
    }
  }, [expressData, checkoutInProgress, cart, user, clearCart, onSuccess, onFallback]);

  const refreshEligibility = useCallback(async () => {
    // Force refresh by clearing cache
    setCachedPreferences({});
    await checkExpressEligibility();
  }, [checkExpressEligibility]);

  // Check eligibility when dependencies change
  useEffect(() => {
    checkExpressEligibility();
  }, [checkExpressEligibility]);

  // Refresh eligibility when cart items change (debounced)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      checkExpressEligibility();
    }, 500); // 500ms debounce

    return () => clearTimeout(timeoutId);
  }, [cart?.items?.length, checkExpressEligibility]); // Use length to avoid deep comparison

  return {
    canUseExpress,
    expressData,
    loading,
    handleExpressCheckout,
    refreshEligibility
  };
};

export default useExpressCheckout;