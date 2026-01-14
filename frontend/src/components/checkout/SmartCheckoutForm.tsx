/**
 * Smart Checkout Form - Intelligent form with auto-completion, real-time validation,
 * and progressive disclosure to reduce friction
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useCart } from '../../contexts/CartContext';
import { useLocale } from '../../contexts/LocaleContext';
import { OrdersAPI } from '../../apis/orders';
import { AuthAPI } from '../../apis/auth';
import { CartAPI } from '../../apis/cart';
import { TokenManager } from '../../apis/client';
import { toast } from 'react-hot-toast';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { CheckCircle, AlertTriangle } from 'lucide-react';
import { useStripe, useElements, PaymentElement } from '@stripe/react-stripe-js';
import AddAddressForm from '../forms/AddAddressForm';
import { 
  handlePriceDiscrepancies, 
  validatePrices, 
  formatCurrency,
  addMoney 
} from '../../lib/price-validation';

// Simple debounce function
const debounce = (func: Function, wait: number) => {
  let timeout: NodeJS.Timeout;
  return function executedFunction(...args: any[]) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

interface SmartCheckoutFormProps {
  onSuccess: (orderId: string) => void;
}

export const SmartCheckoutForm: React.FC<SmartCheckoutFormProps> = ({ onSuccess }) => {
  const { user } = useAuth();
  const { cart, clearCart } = useCart();
  const { formatCurrency } = useLocale();

  const stripe = useStripe();
  const elements = useElements();
  
  // Form state
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<any>({
    shipping_address_id: null,
    shipping_method_id: null,
    payment_method_id: null,
    notes: ''
  });
  
  // Data state - Initialize with empty arrays to prevent map errors
  const [addresses, setAddresses] = useState<any[]>([]);
  const [shippingMethods, setShippingMethods] = useState<any[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<any[]>([]);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [validationErrors, setValidationErrors] = useState<any>({});
  const [realTimeValidation, setRealTimeValidation] = useState<any>({});
  const [orderSummary, setOrderSummary] = useState<any>(null);
  const [processingPayment, setProcessingPayment] = useState(false);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [showNewCardForm, setShowNewCardForm] = useState(false);
  const [isProcessingStripePayment, setIsProcessingStripePayment] = useState(false);
  const [showAddAddressForm, setShowAddAddressForm] = useState(false);

  const fetchPaymentIntentClientSecret = useCallback(async () => {
    if (!cart?.id || !user?.id) {
      toast.error('Cart or user information missing for payment intent creation.');
      return;
    }

    try {
      setIsProcessingStripePayment(true);
      const response = await OrdersAPI.createPaymentIntent({
        cart_id: cart.id,
        user_id: user.id,
        amount: orderSummary?.total || cart.total_amount,
        currency: cart.currency || 'usd', // Assuming cart has a currency
      });
      if (response?.data?.client_secret) {
        setClientSecret(response.data.client_secret);
      } else {
        toast.error('Failed to get payment intent client secret.');
      }
    } catch (error) {
      console.error('Error fetching payment intent client secret:', error);
      toast.error('Failed to initialize payment. Please try again.');
    } finally {
      setIsProcessingStripePayment(false);
    }
  }, [cart, user, orderSummary]);

  // Auto-save form data to localStorage
  useEffect(() => {
    const savedData = localStorage.getItem('checkout_form_data');
    if (savedData) {
      try {
        const parsed = JSON.parse(savedData);
        setFormData(prev => ({ ...prev, ...parsed }));
      } catch (error) {
        console.error('Failed to parse saved form data:', error);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('checkout_form_data', JSON.stringify(formData));
  }, [formData]);

  // Load shipping methods when address changes
  const loadShippingMethods = useCallback(async (addressId: string) => {
    if (!addressId) {
      setShippingMethods([]);
      return;
    }

    try {
      const accessToken = TokenManager.getToken();
      if (!accessToken) {
        console.error('No access token available');
        return;
      }

      const selectedAddress = addresses.find(addr => addr.id === addressId);
      if (!selectedAddress) {
        console.error('Selected address not found');
        return;
      }

      const response = await CartAPI.getShippingOptions(selectedAddress, accessToken);
      const shippingMethodsData = Array.isArray(response.data?.shipping_options) ? response.data.shipping_options : [];
      setShippingMethods(shippingMethodsData);

      // Auto-select the first shipping method if none is selected
      if (shippingMethodsData.length > 0 && !formData.shipping_method_id) {
        const firstShipping = shippingMethodsData[0];
        setFormData(prev => ({ ...prev, shipping_method_id: firstShipping?.id || '' }));
      }
    } catch (error) {
      console.error('Failed to load shipping methods:', error);
      setShippingMethods([]);
    }
  }, [addresses, formData.shipping_method_id]);

  // Load shipping methods when address selection changes
  useEffect(() => {
    if (formData.shipping_address_id) {
      loadShippingMethods(formData.shipping_address_id);
    }
  }, [formData.shipping_address_id, loadShippingMethods]);

  // Load initial data
  useEffect(() => {
    loadCheckoutData();
  }, []);

  // Real-time validation
  const debouncedValidation = useCallback(
    debounce(async (data) => {
      try {
        // Validate that all required fields are present and not empty
        // Skip validation if any required field is missing or empty
        if (!data.shipping_address_id || 
            !data.shipping_method_id || 
            !data.payment_method_id ||
            data.shipping_address_id === '' ||
            data.shipping_method_id === '' ||
            data.payment_method_id === '') {
          // Clear validation state when fields are incomplete
          setRealTimeValidation({});
          return;
        }
        
        const response = await OrdersAPI.validateCheckout(data);
        setRealTimeValidation(response.data || {});
      } catch (error) {
        console.error('Real-time validation failed:', error);
        // Only show validation errors if all required fields were provided
        if (data.shipping_address_id && 
            data.shipping_method_id && 
            data.payment_method_id &&
            data.shipping_address_id !== '' &&
            data.shipping_method_id !== '' &&
            data.payment_method_id !== '') {
          setRealTimeValidation({ 
            can_proceed: false, 
            validation_errors: ['Validation failed. Please check your selections.'] 
          });
        }
      }
    }, 500),
    []
  );

  useEffect(() => {
    // Only validate if all required fields have valid non-empty values
    if (formData.shipping_address_id && 
        formData.shipping_method_id && 
        formData.payment_method_id &&
        formData.shipping_address_id !== '' &&
        formData.shipping_method_id !== '' &&
        formData.payment_method_id !== '') {
      debouncedValidation(formData);
    } else {
      // Clear validation state when fields are incomplete
      setRealTimeValidation({});
    }
  }, [formData, debouncedValidation]);

  const loadCheckoutData = async () => {
    setLoading(true);
    try {
      // Fetch addresses and payment methods in parallel
      const [addressesRes, paymentsRes] = await Promise.all([
        AuthAPI.getAddresses(),
        AuthAPI.getPaymentMethods()
      ]);

      const defaultAddress = addressesRes.data?.find((addr: any) => addr.is_default) || addressesRes.data?.[0];

      let shippingMethodsRes = { data: { shipping_options: [] } };
      if (defaultAddress) {
        try {
          // Get access token from TokenManager
          const accessToken = TokenManager.getToken();
          
          if (accessToken) {
            // Fetch shipping methods using the default address
            shippingMethodsRes = await CartAPI.getShippingOptions(defaultAddress, accessToken);
          }
        } catch (shippingError) {
          console.error('Failed to load shipping options:', shippingError);
          // Continue with empty shipping methods array
        }
      }
      
      // Ensure we always have arrays - extract shipping_options from the response
      const addressesData = Array.isArray(addressesRes.data) ? addressesRes.data : [];
      const shippingMethodsData = Array.isArray(shippingMethodsRes.data?.shipping_options) ? shippingMethodsRes.data.shipping_options : [];
      const paymentMethodsData = Array.isArray(paymentsRes.data) ? paymentsRes.data : [];
      
      setAddresses(addressesData);
      setShippingMethods(shippingMethodsData);
      setPaymentMethods(paymentMethodsData);

      // Auto-select defaults - use first available options, not hardcoded names
      const firstShipping = shippingMethodsData[0];
      const defaultPayment = paymentMethodsData.find((pm: any) => pm.is_default) || paymentMethodsData[0];

      setFormData((prev: any) => ({
        ...prev,
        shipping_address_id: prev.shipping_address_id || defaultAddress?.id || '',
        shipping_method_id: prev.shipping_method_id || firstShipping?.id || '',
        payment_method_id: prev.payment_method_id || defaultPayment?.id || ''
      }));

    } catch (error) {
      console.error('Failed to load checkout data:', error);
      toast.error('Failed to load checkout options');
      // Set empty arrays as fallback
      setAddresses([]);
      setShippingMethods([]);
      setPaymentMethods([]);
    } finally {
      setLoading(false);
    }
  };

  const updateOrderSummary = useCallback(async () => {
    if (!cart || !formData.shipping_method_id) return;

    const safeShippingMethods = Array.isArray(shippingMethods) ? shippingMethods : [];
    const selectedShipping = safeShippingMethods.find(sm => sm.id === formData.shipping_method_id);
    if (!selectedShipping) return;

    const subtotal = cart.subtotal || 0;
    const shipping = selectedShipping.price || 0;
    
    // Get selected shipping address for tax calculation
    const selectedAddress = addresses.find(addr => addr.id === formData.shipping_address_id);
    const tax = await calculateTax(subtotal, shipping, selectedAddress);
    
    // Use safe money operations to avoid floating point errors
    const total = addMoney(addMoney(subtotal, shipping), tax);

    setOrderSummary({
      subtotal,
      shipping,
      tax,
      total,
      items: cart.items?.length || 0
    });
  }, [cart, formData.shipping_method_id, formData.shipping_address_id, shippingMethods, addresses]);

  useEffect(() => {
    updateOrderSummary();
  }, [updateOrderSummary]);

  const calculateTax = async (subtotal, shipping, shippingAddress) => {
    try {
      // Get tax rate from backend based on shipping address
      if (!shippingAddress) return 0;
      
      const response = await OrdersAPI.calculateTax({
        subtotal,
        shipping,
        shipping_address_id: shippingAddress.id
      });
      
      return response.data?.tax_amount || 0;
    } catch (error) {
      console.error('Failed to calculate tax:', error);
      // Fallback to 0 tax if calculation fails
      return 0;
    }
  };

  const validateStep = (step) => {
    const errors = {};
    
    switch (step) {
      case 1: // Shipping Address
        if (!formData.shipping_address_id) {
          errors.shipping_address_id = 'Please select a shipping address';
        }
        break;
      case 2: // Shipping Method
        if (!formData.shipping_method_id) {
          errors.shipping_method_id = 'Please select a shipping method';
        }
        break;
      case 3: // Payment Method
        if (!formData.payment_method_id) {
          errors.payment_method_id = 'Please select a payment method';
        }
        break;
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 4));
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(3)) return;

    setProcessingPayment(true);
    setIsProcessingStripePayment(true); // Indicate Stripe processing is active
    
    try {
      // Final validation before checkout
      const finalValidation = await OrdersAPI.validateCheckout(formData);
      
      if (!finalValidation.data?.can_proceed) {
        toast.error('Checkout validation failed. Please review your cart.');
        setCurrentStep(1); // Go back to review cart
        setIsProcessingStripePayment(false);
        return;
      }

      // Check for price discrepancies
      if (finalValidation.data?.price_discrepancies) {
        handlePriceDiscrepancies(
          finalValidation.data.price_discrepancies,
          () => {
            // Refresh cart and order summary on price updates
            updateOrderSummary();
          }
        );
        
        // If there are critical price errors, block checkout
        const hasErrors = finalValidation.data.price_discrepancies.some(d => d.severity === 'error');
        if (hasErrors) {
          setIsProcessingStripePayment(false);
          return;
        }
      }

      // Validate frontend vs backend totals
      const backendTotal = finalValidation.data?.estimated_totals?.total_amount || 0;
      const frontendTotal = orderSummary?.total || 0;
      
      if (!validatePrices(frontendTotal, backendTotal)) {
        toast.error(
          `Price mismatch detected. Frontend: ${formatCurrency(frontendTotal)}, Backend: ${formatCurrency(backendTotal)}. Please refresh and try again.`,
          { duration: 8000 }
        );
        setIsProcessingStripePayment(false);
        return;
      }
      
      let finalPaymentMethodId = formData.payment_method_id;

      // Handle new card payment via Stripe
      if (showNewCardForm && stripe && elements && clientSecret) {
        const { error: submitError } = await elements.submit();
        if (submitError) {
          toast.error(submitError.message || 'Failed to submit payment details.');
          setIsProcessingStripePayment(false);
          return;
        }

        const { paymentIntent, error: confirmError } = await stripe.confirmPayment({
          elements,
          clientSecret,
          confirmParams: {
            return_url: `${window.location.origin}/checkout`, // URL to redirect after successful payment
          },
          redirect: 'if_required'
        });
        
        if (confirmError) {
          toast.error(confirmError.message || 'Payment confirmation failed.');
          setIsProcessingStripePayment(false);
          return;
        }

        if (paymentIntent?.status === 'succeeded' && paymentIntent.payment_method) {
          finalPaymentMethodId = paymentIntent.payment_method as string;
          // Optionally, save the new payment method to user's profile
          // await AuthAPI.addPaymentMethod({ payment_method_id: finalPaymentMethodId });
        } else {
          toast.error('Payment not successful. Please try again.');
          setIsProcessingStripePayment(false);
          return;
        }
      } else if (!finalPaymentMethodId) {
        toast.error('Please select a payment method or add a new card.');
        setIsProcessingStripePayment(false);
        return;
      }
      
      // Generate idempotency key to prevent duplicate orders
      const idempotencyKey = `checkout_${user?.id}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Add idempotency key and calculated total for validation
      const checkoutData = {
        ...formData,
        payment_method_id: finalPaymentMethodId, // Use the new payment method ID if applicable
        idempotency_key: idempotencyKey,
        frontend_calculated_total: orderSummary?.total || 0
      };
      
      // Attempt checkout with retry logic for transient failures
      let lastError = null;
      const maxRetries = 3;
      
      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          toast.loading(`Processing order... (Attempt ${attempt}/${maxRetries})`, { 
            id: 'checkout-loading',
            duration: 60000 // 60 second timeout
          });
          
          const response = await OrdersAPI.checkout(checkoutData);
          
          toast.dismiss('checkout-loading');
          
          if (response?.success && response?.data) {
            // Clear form data from localStorage on success
            localStorage.removeItem('checkout_form_data');
            
            // Clear cart
            await clearCart();
            
            toast.success('Order placed successfully! 🎉');
            onSuccess(response.data.id);
            return;
          } else {
            throw new Error(response?.message || 'Checkout failed');
          }
          
        } catch (error) {
          lastError = error;
          toast.dismiss('checkout-loading');
          
          // Check if it's a retryable error
          const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
          const isRetryable = 
            errorMessage.includes('timeout') ||
            errorMessage.includes('temporarily unavailable') ||
            errorMessage.includes('high demand') ||
            errorMessage.includes('Lock conflict') ||
            error.response?.status === 408 || // Request timeout
            error.response?.status === 429 || // Rate limit
            error.response?.status === 503;   // Service unavailable
          
          if (!isRetryable || attempt === maxRetries) {
            // Non-retryable error or final attempt
            break;
          }
          
          // Wait before retry with exponential backoff
          const waitTime = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
          toast.loading(`Retrying in ${waitTime / 1000} seconds...`, { 
            id: 'retry-wait',
            duration: waitTime 
          });
          
          await new Promise(resolve => setTimeout(resolve, waitTime));
          toast.dismiss('retry-wait');
        }
      }
      
      // All retries failed - handle the error
      const errorMessage = lastError?.response?.data?.detail || lastError?.message || 'Checkout failed';
      
      // Handle specific error types with appropriate user guidance
      if (errorMessage.includes('Cart validation failed')) {
        toast.error('Your cart has been updated. Please review and try again.');
        setCurrentStep(1); // Go back to cart review
      } else if (errorMessage.includes('Price mismatch') || errorMessage.includes('price')) {
        toast.error('Prices have been updated. Please review your order.');
        // Reload order summary
        updateOrderSummary();
      } else if (errorMessage.includes('Insufficient stock')) {
        toast.error('Some items are no longer available. Please update your cart.');
        setCurrentStep(1);
      } else if (errorMessage.includes('Payment')) {
        toast.error(`Payment failed: ${errorMessage}`);
        setCurrentStep(3); // Stay on payment step
      } else if (errorMessage.includes('high demand') || errorMessage.includes('temporarily unavailable')) {
        toast.error('Service is experiencing high demand. Please try again in a moment.');
      } else {
        toast.error(`Checkout failed: ${errorMessage}`);
      }
      
    } catch (error) {
      console.error('Checkout error:', error);
      toast.error('An unexpected error occurred. Please try again.');
    } finally {
      setProcessingPayment(false);
      setIsProcessingStripePayment(false); // Reset Stripe processing state
    }
  };

  const handleAddressAdded = (newAddress: any) => {
    setAddresses(prev => [...prev, newAddress]);
    setFormData(prev => ({ ...prev, shipping_address_id: newAddress.id }));
    setShowAddAddressForm(false);
    toast.success('Address added and selected!');
  };

  const steps = [
    { number: 1, title: 'Shipping Address', icon: '📍' },
    { number: 2, title: 'Shipping Method', icon: '🚚' },
    { number: 3, title: 'Payment Method', icon: '💳' },
    { number: 4, title: 'Review Order', icon: '✅' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="ml-3 text-copy-light">Loading checkout options...</span>
      </div>
    );
  }

  // Safety check to ensure arrays are properly initialized
  const safeAddresses = Array.isArray(addresses) ? addresses : [];
  const safeShippingMethods = Array.isArray(shippingMethods) ? shippingMethods : [];
  const safePaymentMethods = Array.isArray(paymentMethods) ? paymentMethods : [];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Steps */}
      <div className="mb-6 lg:mb-8">
        <div className="flex items-center justify-between overflow-x-auto pb-2">
          {steps.map((step, index) => (
            <div key={step.number} className="flex items-center min-w-0 flex-shrink-0">
              <div className={`flex items-center justify-center w-8 h-8 lg:w-10 lg:h-10 rounded-full border-2 ${
                currentStep >= step.number
                  ? 'bg-primary border-primary text-copy-inverse'
                  : 'border text-copy-lighter'
              }`}>
                {currentStep > step.number ? (
                  <CheckCircle className="w-4 h-4 lg:w-6 lg:h-6" />
                ) : (
                  <span className="text-sm lg:text-lg">{step.icon}</span>
                )}
              </div>
              <div className="ml-2 lg:ml-3 hidden sm:block">
                <div className={`text-xs lg:text-sm font-medium ${
                  currentStep >= step.number ? 'text-primary' : 'text-copy-lighter'
                }`}>
                  Step {step.number}
                </div>
                <div className={`text-xs ${
                  currentStep >= step.number ? 'text-copy' : 'text-copy-lighter'
                }`}>
                  {step.title}
                </div>
              </div>
              {index < steps.length - 1 && (
                <div className={`flex-1 h-0.5 mx-2 lg:mx-4 min-w-4 lg:min-w-8 ${
                  currentStep > step.number ? 'bg-primary' : 'bg-border-light'
                }`} />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-8">
        {/* Main Form */}
        <div className="lg:col-span-2">
          <div className="bg-surface rounded-lg shadow-sm border border-border p-4 lg:p-6">
            {/* Step 1: Shipping Address */}
            {currentStep === 1 && (
              <div>
                <h3 className="text-lg font-semibold mb-4 text-copy">Shipping Address</h3>
                <div className="space-y-4">
                  {safeAddresses.map((address) => (
                    <label
                      key={address.id}
                      className={`block p-4 border border-border rounded-lg cursor-pointer transition-colors ${
                        formData.shipping_address_id === address.id
                          ? 'border-primary bg-primary/10'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <input
                        type="radio"
                        name="shipping_address"
                        value={address.id}
                        checked={formData.shipping_address_id === address.id}
                        onChange={(e) => {
                          setFormData(prev => ({ ...prev, shipping_address_id: e.target.value }));
                          // Clear shipping method selection when address changes
                          setFormData(prev => ({ ...prev, shipping_method_id: '' }));
                        }}
                        className="sr-only"
                      />
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-medium text-copy">
                            {address.street}
                          </div>
                          <div className="text-sm text-copy-light">
                            {address.city}, {address.state} {address.post_code}
                          </div>
                          <div className="text-sm text-copy-light">
                            {address.country}
                          </div>
                        </div>
                        {address.is_default && (
                          <span className="bg-success/20 text-success text-xs font-medium px-2 py-1 rounded">
                            Default
                          </span>
                        )}
                      </div>
                    </label>
                  ))}
                  
                  {(!Array.isArray(addresses) || safeAddresses.length === 0) && (
                    <div className="text-center py-8 text-copy-light">
                      <div className="bg-surface rounded-lg p-6 border border-border">
                        <div className="text-copy-light mb-4">
                          <svg className="w-12 h-12 mx-auto mb-3 text-copy-lighter" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          <p className="text-copy">No addresses found</p>
                          <p className="text-copy-light text-sm">Please add an address to continue with your order.</p>
                        </div>
                        <Button
                          onClick={() => setShowAddAddressForm(true)}
                          className="mt-4"
                          variant="outline"
                        >
                          Add Address
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
                
                {validationErrors.shipping_address_id && (
                  <div className="mt-2 text-sm text-error flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-1" />
                    {validationErrors.shipping_address_id}
                  </div>
                )}
              </div>
            )}

            {/* Step 2: Shipping Method */}
            {currentStep === 2 && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Shipping Method</h3>
                <div className="space-y-3">
                  {safeShippingMethods.length > 0 ? (
                    safeShippingMethods.map((method) => (
                      <label
                        key={method.id}
                        className={`block p-4 border rounded-lg cursor-pointer transition-colors ${
                          formData.shipping_method_id === method.id
                            ? 'border-primary bg-primary/10'
                            : 'border hover:border-strong'
                        }`}
                      >
                        <input
                          type="radio"
                          name="shipping_method"
                          value={method.id}
                          checked={formData.shipping_method_id === method.id}
                          onChange={(e) => setFormData(prev => ({ ...prev, shipping_method_id: e.target.value }))}
                          className="sr-only"
                        />
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-copy">
                              {method.name}
                            </div>
                            <div className="text-sm text-copy-light">
                              {method.delivery_days || method.estimated_days} business days
                            </div>
                          </div>
                          <div className="text-lg font-semibold text-copy">
                            {formatCurrency(method.price)}
                          </div>
                        </div>
                      </label>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <div className="bg-surface rounded-lg p-6 border border-border">
                        <div className="text-copy-light mb-4">
                          <svg className="w-12 h-12 mx-auto mb-3 text-copy-lighter" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                          </svg>
                          <p className="text-copy">No shipping methods available</p>
                          <p className="text-copy-light text-sm">Please select a shipping address first or try refreshing the page.</p>
                        </div>
                        <Button
                          onClick={() => setCurrentStep(1)}
                          variant="outline"
                        >
                          Go Back to Address
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
                
                {validationErrors.shipping_method_id && (
                  <div className="mt-2 text-sm text-error flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-1" />
                    {validationErrors.shipping_method_id}
                  </div>
                )}
              </div>
            )}

            {/* Step 3: Payment Method */}
            {currentStep === 3 && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Payment Method</h3>
                <div className="space-y-3">
                  {safePaymentMethods.map((method) => (
                    <label
                      key={method.id}
                      className={`block p-4 border rounded-lg cursor-pointer transition-colors ${
                        formData.payment_method_id === method.id && !showNewCardForm
                          ? 'border-primary bg-primary/10'
                          : 'border hover:border-strong'
                      }`}
                    >
                      <input
                        type="radio"
                        name="payment_method"
                        value={method.id}
                        checked={formData.payment_method_id === method.id && !showNewCardForm}
                        onChange={(e) => {
                          setFormData(prev => ({ ...prev, payment_method_id: e.target.value }));
                          setShowNewCardForm(false);
                        }}
                        className="sr-only"
                      />
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-6 bg-surface-active rounded flex items-center justify-center text-xs font-bold">
                            {method.brand?.toUpperCase()}
                          </div>
                          <div>
                            <div className="font-medium text-copy">
                              •••• •••• •••• {method.last_four}
                            </div>
                            <div className="text-sm text-copy-light">
                              Expires {method.expiry_month}/{method.expiry_year}
                            </div>
                          </div>
                        </div>
                        {method.is_default && (
                          <span className="bg-success/20 text-success text-xs font-medium px-2 py-1 rounded">
                            Default
                          </span>
                        )}
                      </div>
                    </label>
                  ))}
                  
                  {/* Option to add a new card */}
                  <label
                    className={`block p-4 border rounded-lg cursor-pointer transition-colors ${
                      showNewCardForm
                        ? 'border-primary bg-primary/10'
                        : 'border hover:border-strong'
                    }`}
                  >
                    <input
                      type="radio"
                      name="payment_method"
                      value="new_card"
                      checked={showNewCardForm}
                      onChange={() => {
                        setShowNewCardForm(true);
                        setFormData(prev => ({ ...prev, payment_method_id: null })); // Clear selected payment method
                        if (!clientSecret) {
                          fetchPaymentIntentClientSecret();
                        }
                      }}
                      className="sr-only"
                    />
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-6 bg-surface-active rounded flex items-center justify-center text-xs font-bold">
                        NEW
                      </div>
                      <div className="font-medium text-copy">Use a new card</div>
                    </div>
                  </label>

                  {/* Stripe Payment Element for new card input */}
                  {showNewCardForm && clientSecret && (
                    <div className="mt-4 p-4 border rounded-lg">
                      <PaymentElement options={{ layout: "tabs" }} />
                    </div>
                  )}

                  {safePaymentMethods.length === 0 && !showNewCardForm && (
                    <div className="text-center py-8">
                      <div className="bg-surface rounded-lg p-6 border border-border">
                        <div className="text-copy-light mb-4">
                          <svg className="w-12 h-12 mx-auto mb-3 text-copy-lighter" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                          </svg>
                          <p className="text-copy">No payment methods found</p>
                          <p className="text-copy-light text-sm">Please add a payment method to continue with your order.</p>
                        </div>
                        <Button
                          onClick={() => {
                            setShowNewCardForm(true);
                            setFormData(prev => ({ ...prev, payment_method_id: null }));
                            if (!clientSecret) {
                              fetchPaymentIntentClientSecret();
                            }
                          }}
                          className="mt-4"
                          variant="outline"
                        >
                          Add New Card
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
                
                {validationErrors.payment_method_id && (
                  <div className="mt-2 text-sm text-error flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-1" />
                    {validationErrors.payment_method_id}
                  </div>
                )}
              </div>
            )}

            {/* Step 4: Review Order */}
            {currentStep === 4 && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Review Your Order</h3>
                
                {/* Order items */}
                <div className="space-y-4 mb-6">
                  {cart?.items?.map((item) => (
                    <div key={item.id} className="flex items-center space-x-4 p-4 bg-surface-hover rounded-lg">
                      <img
                        src={item.product?.image_url || '/placeholder-product.jpg'}
                        alt={item.product?.name}
                        className="w-16 h-16 object-cover rounded"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-copy">{item.product?.name}</div>
                        <div className="text-sm text-copy-light">Quantity: {item.quantity}</div>
                      </div>
                      <div className="text-lg font-semibold text-copy">
                        {formatCurrency(item.quantity * item.price_per_unit)}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Order notes */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-copy mb-2">
                    Order Notes (Optional)
                  </label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                    placeholder="Any special instructions for your order..."
                    className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    rows={3}
                  />
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-between mt-6 lg:mt-8 pt-4 lg:pt-6 border-t gap-4 sm:gap-0">
              <Button
                onClick={handlePrevious}
                variant="outline"
                disabled={currentStep === 1}
                className="w-full sm:w-auto order-2 sm:order-1"
              >
                Previous
              </Button>
              
              {currentStep < 4 ? (
                <Button
                  onClick={handleNext}
                  disabled={!formData.shipping_address_id && currentStep === 1 ||
                           !formData.shipping_method_id && currentStep === 2 ||
                           !formData.payment_method_id && currentStep === 3}
                  className="w-full sm:w-auto order-1 sm:order-2"
                >
                  Next
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  isLoading={processingPayment}
                  className="bg-success hover:bg-success-dark w-full sm:w-auto order-1 sm:order-2"
                  size="lg"
                >
                  {processingPayment ? 'Processing...' : `Place Order - ${formatCurrency(orderSummary?.total || 0)}`}
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Order Summary Sidebar */}
        <div className="lg:col-span-1 order-first lg:order-last">
          <div className="bg-surface rounded-lg shadow-sm border border-border p-4 lg:p-6 lg:sticky lg:top-6">
            <h3 className="text-lg font-semibold mb-4 text-copy">Order Summary</h3>
            
            {orderSummary && (
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-copy-light">Subtotal ({orderSummary.items} items)</span>
                  <span className="text-copy">{formatCurrency(orderSummary.subtotal)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-copy-light">Shipping</span>
                  <span className="text-copy">{formatCurrency(orderSummary.shipping)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-copy-light">Tax</span>
                  <span className="text-copy">{formatCurrency(orderSummary.tax)}</span>
                </div>
                <div className="border-t border-border pt-3">
                  <div className="flex justify-between text-lg font-semibold">
                    <span className="text-copy">Total</span>
                    <span className="text-primary">{formatCurrency(orderSummary.total)}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Real-time validation status */}
            {realTimeValidation && Object.keys(realTimeValidation).length > 0 && (
              <div className="mt-6 p-3 bg-success/10 border border-success/30 rounded-lg">
                <div className="flex items-center text-sm text-success">
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Order validated and ready to place
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Address Modal */}
      {showAddAddressForm && (
        <AddAddressForm
          isModal={true}
          onSuccess={handleAddressAdded}
          onCancel={() => setShowAddAddressForm(false)}
        />
      )}
    </div>
  );
};

export default SmartCheckoutForm;