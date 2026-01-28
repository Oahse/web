/**
 * Smart Checkout Form - Comprehensive checkout with backend-only pricing
 * Features real-time validation, price verification, and secure order processing
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../store/AuthContext';
import { useCart } from '../../store/CartContext';
import { useLocale } from '../../store/LocaleContext';
import { useShipping } from '../../hooks/useShipping';
import { OrdersAPI } from '../../api/orders';
import { AuthAPI } from '../../api/auth';
import { CartAPI } from '../../api/cart';
import { TokenManager } from '../../api/client';
import { PaymentsAPI } from '../../api/payments';
import { toast } from 'react-hot-toast';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { CheckCircle, AlertTriangle, CreditCard, Truck, MapPin } from 'lucide-react';
import AddAddressForm from '../forms/AddAddressForm';

// Debounce utility
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

interface CheckoutPricing {
  subtotal: number;
  shipping: {
    method_id: string;
    method_name: string;
    cost: number;
  };
  tax: {
    rate: number;
    amount: number;
    location: string;
  };
  discount?: {
    code: string;
    type: string;
    value: number;
    amount: number;
  };
  total: number;
  currency: string;
  calculated_at: string;
}

export const SmartCheckoutForm: React.FC<SmartCheckoutFormProps> = ({ onSuccess }) => {
  const { user } = useAuth();
  const { cart, clearCart, refreshCart } = useCart();
  const { formatCurrency, currency, countryCode } = useLocale();
  const { 
    shippingMethods, 
    loading: shippingLoading, 
    error: shippingError,
    loadShippingMethods,
    getCheapestMethod 
  } = useShipping({ autoLoad: true });
  
  // Form state
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<any>({
    shipping_address_id: null,
    shipping_method_id: null,
    payment_method_id: null,
    discount_code: '',
    notes: ''
  });
  
  // Data state
  const [addresses, setAddresses] = useState<any[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<any[]>([]);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [validationErrors, setValidationErrors] = useState<any>({});
  const [realTimeValidation, setRealTimeValidation] = useState<any>({});
  const [processingPayment, setProcessingPayment] = useState(false);
  const [showAddAddressForm, setShowAddAddressForm] = useState(false);
  const [pricingData, setPricingData] = useState<CheckoutPricing | null>(null);
  const [priceValidationErrors, setPriceValidationErrors] = useState<string[]>([]);

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

  // Auto-select cheapest shipping method when available
  useEffect(() => {
    if (shippingMethods.length > 0 && !formData.shipping_method_id) {
      const cheapestMethod = getCheapestMethod();
      if (cheapestMethod) {
        setFormData(prev => ({ ...prev, shipping_method_id: cheapestMethod.id }));
      }
    }
  }, [shippingMethods, formData.shipping_method_id, getCheapestMethod]);

  // Load initial data
  useEffect(() => {
    loadCheckoutData();
  }, []);

  // Real-time validation with comprehensive pricing
  const debouncedValidation = useCallback(
    debounce(async (data) => {
      try {
        // Skip validation if required fields are missing
        if (!data.shipping_address_id || 
            !data.shipping_method_id || 
            !data.payment_method_id) {
          setRealTimeValidation({});
          setPricingData(null);
          return;
        }
        
        console.log('=== CHECKOUT VALIDATION REQUEST ===');
        console.log('Validating checkout with data:', {
          shipping_address_id: data.shipping_address_id,
          shipping_method_id: data.shipping_method_id,
          payment_method_id: data.payment_method_id,
          discount_code: data.discount_code,
          notes: data.notes
        });
        
        const response = await OrdersAPI.validateCheckout({
          shipping_address_id: data.shipping_address_id,
          shipping_method_id: data.shipping_method_id,
          payment_method_id: data.payment_method_id,
          discount_code: data.discount_code || undefined,
          notes: data.notes,
          currency: currency,
          country_code: countryCode
        });
        
        console.log('=== CHECKOUT VALIDATION RESPONSE ===');
        console.log('Validation response:', response);
        
        if (response.success && response.data) {
          setRealTimeValidation(response.data);
          
          // Extract pricing information
          if (response.data.pricing) {
            setPricingData(response.data.pricing);
            setPriceValidationErrors([]);
          }
          
          // Handle validation warnings
          if (response.data.warnings && response.data.warnings.length > 0) {
            const priceWarnings = response.data.warnings
              .filter(w => w.type === 'price_mismatch')
              .map(w => w.message);
            setPriceValidationErrors(priceWarnings);
          }
        } else {
          console.error('Validation failed:', response);
          const errorMessages = response.data?.errors || [response.message || 'Validation failed'];
          setRealTimeValidation({ 
            can_proceed: false, 
            errors: errorMessages
          });
          setPricingData(null);
        }
      } catch (error: any) {
        console.error('Real-time validation failed:', error);
        setRealTimeValidation({ 
          can_proceed: false, 
          errors: ['Validation service temporarily unavailable'] 
        });
        setPricingData(null);
      }
    }, 1000),
    [currency, countryCode]
  );

  // Trigger validation when form data changes
  useEffect(() => {
    debouncedValidation(formData);
  }, [formData, debouncedValidation]);

  const loadCheckoutData = async () => {
    setLoading(true);
    try {
      // Load addresses and payment methods in parallel
      const [addressesRes, paymentMethodsRes] = await Promise.all([
        AuthAPI.getUserAddresses(),
        PaymentsAPI.getPaymentMethods()
      ]);

      if (addressesRes.success) {
        setAddresses(addressesRes.data || []);
        // Auto-select default address
        const defaultAddress = addressesRes.data?.find(addr => addr.is_default);
        if (defaultAddress && !formData.shipping_address_id) {
          setFormData(prev => ({ ...prev, shipping_address_id: defaultAddress.id }));
        }
      }

      if (paymentMethodsRes.success) {
        setPaymentMethods(paymentMethodsRes.data || []);
        // Auto-select default payment method
        const defaultPayment = paymentMethodsRes.data?.find(pm => pm.is_default);
        if (defaultPayment && !formData.payment_method_id) {
          setFormData(prev => ({ ...prev, payment_method_id: defaultPayment.id }));
        }
      }
    } catch (error) {
      console.error('Failed to load checkout data:', error);
      toast.error('Failed to load checkout information');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!realTimeValidation.can_proceed) {
      toast.error('Please resolve validation errors before proceeding');
      return;
    }

    setProcessingPayment(true);
    
    try {
      console.log('=== PLACING ORDER ===');
      console.log('Order data:', formData);
      console.log('Pricing data:', pricingData);
      
      const orderResponse = await OrdersAPI.placeOrder({
        shipping_address_id: formData.shipping_address_id,
        shipping_method_id: formData.shipping_method_id,
        payment_method_id: formData.payment_method_id,
        discount_code: formData.discount_code || undefined,
        notes: formData.notes,
        currency: currency,
        country_code: countryCode,
        // Include pricing data for verification
        frontend_calculated_total: pricingData?.total
      });

      if (orderResponse.success) {
        // Clear cart and form data
        await clearCart();
        localStorage.removeItem('checkout_form_data');
        
        toast.success('Order placed successfully!');
        onSuccess(orderResponse.data.id);
      } else {
        throw new Error(orderResponse.message || 'Failed to place order');
      }
    } catch (error: any) {
      console.error('Order placement failed:', error);
      
      // Handle specific error types
      if (error.response?.data?.errors) {
        const errors = error.response.data.errors;
        const errorMessages = errors.map(err => err.message).join(', ');
        toast.error(`Order failed: ${errorMessages}`);
      } else {
        toast.error(error.message || 'Failed to place order. Please try again.');
      }
    } finally {
      setProcessingPayment(false);
    }
  };

  const updateFormData = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Render pricing summary
  const renderPricingSummary = () => {
    if (!pricingData) {
      return (
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-gray-500">Select shipping and payment methods to see pricing</p>
        </div>
      );
    }

    return (
      <div className="bg-white border rounded-lg p-4 space-y-3">
        <h3 className="font-semibold text-lg">Order Summary</h3>
        
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span>Subtotal:</span>
            <span>{formatCurrency(pricingData.subtotal)}</span>
          </div>
          
          <div className="flex justify-between">
            <span>Shipping ({pricingData.shipping.method_name}):</span>
            <span>{formatCurrency(pricingData.shipping.cost)}</span>
          </div>
          
          <div className="flex justify-between">
            <span>Tax ({(pricingData.tax.rate * 100).toFixed(2)}%):</span>
            <span>{formatCurrency(pricingData.tax.amount)}</span>
          </div>
          
          {pricingData.discount && (
            <div className="flex justify-between text-green-600">
              <span>Discount ({pricingData.discount.code}):</span>
              <span>-{formatCurrency(pricingData.discount.amount)}</span>
            </div>
          )}
          
          <hr className="my-2" />
          
          <div className="flex justify-between font-semibold text-lg">
            <span>Total:</span>
            <span>{formatCurrency(pricingData.total)}</span>
          </div>
        </div>
        
        {priceValidationErrors.length > 0 && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <div className="flex items-center">
              <AlertTriangle className="h-4 w-4 text-yellow-600 mr-2" />
              <span className="text-sm font-medium text-yellow-800">Price Verification</span>
            </div>
            {priceValidationErrors.map((error, index) => (
              <p key={index} className="text-sm text-yellow-700 mt-1">{error}</p>
            ))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading checkout...</span>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Form */}
        <div className="lg:col-span-2">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Shipping Address Section */}
            <div className="bg-white border rounded-lg p-6">
              <div className="flex items-center mb-4">
                <MapPin className="h-5 w-5 text-blue-600 mr-2" />
                <h2 className="text-lg font-semibold">Shipping Address</h2>
              </div>
              
              {addresses.length > 0 ? (
                <div className="space-y-3">
                  {addresses.map((address) => (
                    <label key={address.id} className="flex items-start space-x-3 p-3 border rounded cursor-pointer hover:bg-gray-50">
                      <input
                        type="radio"
                        name="shipping_address"
                        value={address.id}
                        checked={formData.shipping_address_id === address.id}
                        onChange={(e) => updateFormData('shipping_address_id', e.target.value)}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <div className="font-medium">{address.street}</div>
                        <div className="text-sm text-gray-600">
                          {address.city}, {address.state} {address.post_code}
                        </div>
                        <div className="text-sm text-gray-600">{address.country}</div>
                      </div>
                    </label>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowAddAddressForm(true)}
                    className="w-full"
                  >
                    Add New Address
                  </Button>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-gray-600 mb-4">No addresses found</p>
                  <Button
                    type="button"
                    onClick={() => setShowAddAddressForm(true)}
                  >
                    Add Address
                  </Button>
                </div>
              )}
            </div>

            {/* Shipping Method Section */}
            <div className="bg-white border rounded-lg p-6">
              <div className="flex items-center mb-4">
                <Truck className="h-5 w-5 text-blue-600 mr-2" />
                <h2 className="text-lg font-semibold">Shipping Method</h2>
              </div>
              
              {shippingLoading ? (
                <div className="animate-pulse space-y-3">
                  <div className="h-16 bg-gray-200 rounded"></div>
                  <div className="h-16 bg-gray-200 rounded"></div>
                </div>
              ) : shippingMethods.length > 0 ? (
                <div className="space-y-3">
                  {shippingMethods.map((method) => (
                    <label key={method.id} className="flex items-center justify-between p-3 border rounded cursor-pointer hover:bg-gray-50">
                      <div className="flex items-center space-x-3">
                        <input
                          type="radio"
                          name="shipping_method"
                          value={method.id}
                          checked={formData.shipping_method_id === method.id}
                          onChange={(e) => updateFormData('shipping_method_id', e.target.value)}
                        />
                        <div>
                          <div className="font-medium">{method.name}</div>
                          <div className="text-sm text-gray-600">{method.description}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium">{formatCurrency(method.price)}</div>
                        <div className="text-sm text-gray-600">{method.estimated_days} days</div>
                      </div>
                    </label>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No shipping methods available</p>
              )}
            </div>

            {/* Payment Method Section */}
            <div className="bg-white border rounded-lg p-6">
              <div className="flex items-center mb-4">
                <CreditCard className="h-5 w-5 text-blue-600 mr-2" />
                <h2 className="text-lg font-semibold">Payment Method</h2>
              </div>
              
              {paymentMethods.length > 0 ? (
                <div className="space-y-3">
                  {paymentMethods.map((method) => (
                    <label key={method.id} className="flex items-center space-x-3 p-3 border rounded cursor-pointer hover:bg-gray-50">
                      <input
                        type="radio"
                        name="payment_method"
                        value={method.id}
                        checked={formData.payment_method_id === method.id}
                        onChange={(e) => updateFormData('payment_method_id', e.target.value)}
                      />
                      <div className="flex-1">
                        <div className="font-medium">
                          {method.type === 'credit_card' ? 'Credit Card' : method.type}
                        </div>
                        <div className="text-sm text-gray-600">
                          **** **** **** {method.last_four}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No payment methods available</p>
              )}
            </div>

            {/* Discount Code Section */}
            <div className="bg-white border rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Discount Code</h2>
              <Input
                type="text"
                placeholder="Enter discount code"
                value={formData.discount_code}
                onChange={(e) => updateFormData('discount_code', e.target.value)}
              />
            </div>

            {/* Order Notes */}
            <div className="bg-white border rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Order Notes (Optional)</h2>
              <textarea
                className="w-full p-3 border rounded-lg resize-none"
                rows={3}
                placeholder="Special instructions for your order..."
                value={formData.notes}
                onChange={(e) => updateFormData('notes', e.target.value)}
              />
            </div>

            {/* Validation Errors */}
            {realTimeValidation.errors && realTimeValidation.errors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center mb-2">
                  <AlertTriangle className="h-4 w-4 text-red-600 mr-2" />
                  <span className="font-medium text-red-800">Please fix the following issues:</span>
                </div>
                <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
                  {realTimeValidation.errors.map((error, index) => (
                    <li key={index}>{typeof error === 'string' ? error : error.message}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={!realTimeValidation.can_proceed || processingPayment}
              className="w-full py-3 text-lg"
            >
              {processingPayment ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Processing Order...
                </>
              ) : (
                `Place Order ${pricingData ? formatCurrency(pricingData.total) : ''}`
              )}
            </Button>
          </form>
        </div>

        {/* Order Summary Sidebar */}
        <div className="lg:col-span-1">
          <div className="sticky top-6">
            {renderPricingSummary()}
            
            {/* Validation Status */}
            {realTimeValidation.can_proceed !== undefined && (
              <div className={`mt-4 p-3 rounded-lg ${
                realTimeValidation.can_proceed 
                  ? 'bg-green-50 border border-green-200' 
                  : 'bg-red-50 border border-red-200'
              }`}>
                <div className="flex items-center">
                  {realTimeValidation.can_proceed ? (
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-red-600 mr-2" />
                  )}
                  <span className={`text-sm font-medium ${
                    realTimeValidation.can_proceed ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {realTimeValidation.can_proceed ? 'Ready to place order' : 'Cannot proceed'}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Address Modal */}
      {showAddAddressForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <AddAddressForm
              onSuccess={() => {
                setShowAddAddressForm(false);
                loadCheckoutData();
              }}
              onCancel={() => setShowAddAddressForm(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartCheckoutForm;
