/**
 * Smart Checkout Form - Intelligent form with auto-completion, real-time validation,
 * and progressive disclosure to reduce friction
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useCart } from '../../contexts/CartContext';
import { OrdersAPI } from '../../apis/orders';
import { AuthAPI } from '../../apis/auth';
import { toast } from 'react-hot-toast';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { debounce } from 'lodash';

interface SmartCheckoutFormProps {
  onSuccess: (orderId: string) => void;
}

export const SmartCheckoutForm: React.FC<SmartCheckoutFormProps> = ({ onSuccess }) => {
  const { user } = useAuth();
  const { cart, clearCart } = useCart();
  
  // Form state
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    shipping_address_id: '',
    shipping_method_id: '',
    payment_method_id: '',
    notes: ''
  });
  
  // Data state
  const [addresses, setAddresses] = useState([]);
  const [shippingMethods, setShippingMethods] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  const [realTimeValidation, setRealTimeValidation] = useState({});
  const [orderSummary, setOrderSummary] = useState(null);
  const [processingPayment, setProcessingPayment] = useState(false);

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

  // Load initial data
  useEffect(() => {
    loadCheckoutData();
  }, []);

  // Real-time validation
  const debouncedValidation = useCallback(
    debounce(async (data) => {
      try {
        const response = await OrdersAPI.validateCheckout(data);
        setRealTimeValidation(response.data || {});
      } catch (error) {
        console.error('Real-time validation failed:', error);
      }
    }, 500),
    []
  );

  useEffect(() => {
    if (formData.shipping_address_id && formData.shipping_method_id) {
      debouncedValidation(formData);
    }
  }, [formData, debouncedValidation]);

  const loadCheckoutData = async () => {
    setLoading(true);
    try {
      const [addressesRes, shippingRes, paymentsRes] = await Promise.all([
        AuthAPI.getAddresses(),
        AuthAPI.getShippingMethods(),
        AuthAPI.getPaymentMethods()
      ]);

      setAddresses(addressesRes.data || []);
      setShippingMethods(shippingRes.data || []);
      setPaymentMethods(paymentsRes.data || []);

      // Auto-select defaults
      const defaultAddress = addressesRes.data?.find(addr => addr.is_default) || addressesRes.data?.[0];
      const standardShipping = shippingRes.data?.find(sm => sm.name.toLowerCase().includes('standard')) || shippingRes.data?.[0];
      const defaultPayment = paymentsRes.data?.find(pm => pm.is_default) || paymentsRes.data?.[0];

      setFormData(prev => ({
        ...prev,
        shipping_address_id: prev.shipping_address_id || defaultAddress?.id || '',
        shipping_method_id: prev.shipping_method_id || standardShipping?.id || '',
        payment_method_id: prev.payment_method_id || defaultPayment?.id || ''
      }));

    } catch (error) {
      console.error('Failed to load checkout data:', error);
      toast.error('Failed to load checkout options');
    } finally {
      setLoading(false);
    }
  };

  const updateOrderSummary = useCallback(() => {
    if (!cart || !formData.shipping_method_id) return;

    const selectedShipping = shippingMethods.find(sm => sm.id === formData.shipping_method_id);
    if (!selectedShipping) return;

    const subtotal = cart.subtotal || 0;
    const shipping = selectedShipping.price || 0;
    const tax = calculateTax(subtotal, shipping);
    const total = subtotal + shipping + tax;

    setOrderSummary({
      subtotal,
      shipping,
      tax,
      total,
      items: cart.items?.length || 0
    });
  }, [cart, formData.shipping_method_id, shippingMethods]);

  useEffect(() => {
    updateOrderSummary();
  }, [updateOrderSummary]);

  const calculateTax = (subtotal, shipping) => {
    // Simple tax calculation - in real app, this would be based on address
    const taxRate = 0.08; // 8%
    return (subtotal + shipping) * taxRate;
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
    try {
      const response = await OrdersAPI.checkout(formData);

      if (response?.success && response?.data) {
        toast.success('Order placed successfully! 🎉');
        
        // Clear saved form data
        localStorage.removeItem('checkout_form_data');
        
        await clearCart();
        onSuccess(response.data.id);
      } else {
        throw new Error('Failed to place order');
      }
    } catch (error) {
      console.error('Checkout failed:', error);
      const errorMessage = error?.response?.data?.message || error?.message || 'Failed to place order';
      toast.error(errorMessage);
    } finally {
      setProcessingPayment(false);
    }
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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading checkout options...</span>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.number} className="flex items-center">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                currentStep >= step.number
                  ? 'bg-blue-600 border-blue-600 text-white'
                  : 'border-gray-300 text-gray-400'
              }`}>
                {currentStep > step.number ? (
                  <CheckCircleIcon className="w-6 h-6" />
                ) : (
                  <span className="text-lg">{step.icon}</span>
                )}
              </div>
              <div className="ml-3">
                <div className={`text-sm font-medium ${
                  currentStep >= step.number ? 'text-blue-600' : 'text-gray-400'
                }`}>
                  Step {step.number}
                </div>
                <div className={`text-xs ${
                  currentStep >= step.number ? 'text-gray-900' : 'text-gray-400'
                }`}>
                  {step.title}
                </div>
              </div>
              {index < steps.length - 1 && (
                <div className={`flex-1 h-0.5 mx-4 ${
                  currentStep > step.number ? 'bg-blue-600' : 'bg-gray-200'
                }`} />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Form */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            {/* Step 1: Shipping Address */}
            {currentStep === 1 && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Shipping Address</h3>
                <div className="space-y-4">
                  {addresses.map((address) => (
                    <label
                      key={address.id}
                      className={`block p-4 border rounded-lg cursor-pointer transition-colors ${
                        formData.shipping_address_id === address.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="shipping_address"
                        value={address.id}
                        checked={formData.shipping_address_id === address.id}
                        onChange={(e) => setFormData(prev => ({ ...prev, shipping_address_id: e.target.value }))}
                        className="sr-only"
                      />
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-medium text-gray-900">
                            {address.street}
                          </div>
                          <div className="text-sm text-gray-600">
                            {address.city}, {address.state} {address.post_code}
                          </div>
                          <div className="text-sm text-gray-600">
                            {address.country}
                          </div>
                        </div>
                        {address.is_default && (
                          <span className="bg-green-100 text-green-800 text-xs font-medium px-2 py-1 rounded">
                            Default
                          </span>
                        )}
                      </div>
                    </label>
                  ))}
                  
                  {addresses.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <p>No addresses found. Please add an address to continue.</p>
                      <Button
                        onClick={() => {/* Navigate to add address */}}
                        className="mt-4"
                        variant="outline"
                      >
                        Add Address
                      </Button>
                    </div>
                  )}
                </div>
                
                {validationErrors.shipping_address_id && (
                  <div className="mt-2 text-sm text-red-600 flex items-center">
                    <ExclamationTriangleIcon className="w-4 h-4 mr-1" />
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
                  {shippingMethods.map((method) => (
                    <label
                      key={method.id}
                      className={`block p-4 border rounded-lg cursor-pointer transition-colors ${
                        formData.shipping_method_id === method.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
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
                          <div className="font-medium text-gray-900">
                            {method.name}
                          </div>
                          <div className="text-sm text-gray-600">
                            {method.estimated_days} business days
                          </div>
                        </div>
                        <div className="text-lg font-semibold text-gray-900">
                          ${method.price.toFixed(2)}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
                
                {validationErrors.shipping_method_id && (
                  <div className="mt-2 text-sm text-red-600 flex items-center">
                    <ExclamationTriangleIcon className="w-4 h-4 mr-1" />
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
                  {paymentMethods.map((method) => (
                    <label
                      key={method.id}
                      className={`block p-4 border rounded-lg cursor-pointer transition-colors ${
                        formData.payment_method_id === method.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="payment_method"
                        value={method.id}
                        checked={formData.payment_method_id === method.id}
                        onChange={(e) => setFormData(prev => ({ ...prev, payment_method_id: e.target.value }))}
                        className="sr-only"
                      />
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-6 bg-gray-100 rounded flex items-center justify-center text-xs font-bold">
                            {method.brand?.toUpperCase()}
                          </div>
                          <div>
                            <div className="font-medium text-gray-900">
                              •••• •••• •••• {method.last_four}
                            </div>
                            <div className="text-sm text-gray-600">
                              Expires {method.expiry_month}/{method.expiry_year}
                            </div>
                          </div>
                        </div>
                        {method.is_default && (
                          <span className="bg-green-100 text-green-800 text-xs font-medium px-2 py-1 rounded">
                            Default
                          </span>
                        )}
                      </div>
                    </label>
                  ))}
                  
                  {paymentMethods.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <p>No payment methods found. Please add a payment method to continue.</p>
                      <Button
                        onClick={() => {/* Navigate to add payment method */}}
                        className="mt-4"
                        variant="outline"
                      >
                        Add Payment Method
                      </Button>
                    </div>
                  )}
                </div>
                
                {validationErrors.payment_method_id && (
                  <div className="mt-2 text-sm text-red-600 flex items-center">
                    <ExclamationTriangleIcon className="w-4 h-4 mr-1" />
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
                    <div key={item.id} className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
                      <img
                        src={item.product?.image_url || '/placeholder-product.jpg'}
                        alt={item.product?.name}
                        className="w-16 h-16 object-cover rounded"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{item.product?.name}</div>
                        <div className="text-sm text-gray-600">Quantity: {item.quantity}</div>
                      </div>
                      <div className="text-lg font-semibold text-gray-900">
                        ${(item.quantity * item.price_per_unit).toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Order notes */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Order Notes (Optional)
                  </label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                    placeholder="Any special instructions for your order..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                  />
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t">
              <Button
                onClick={handlePrevious}
                variant="outline"
                disabled={currentStep === 1}
              >
                Previous
              </Button>
              
              {currentStep < 4 ? (
                <Button
                  onClick={handleNext}
                  disabled={!formData.shipping_address_id && currentStep === 1 ||
                           !formData.shipping_method_id && currentStep === 2 ||
                           !formData.payment_method_id && currentStep === 3}
                >
                  Next
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  loading={processingPayment}
                  className="bg-green-600 hover:bg-green-700"
                  size="lg"
                >
                  {processingPayment ? 'Processing...' : `Place Order - $${orderSummary?.total?.toFixed(2) || '0.00'}`}
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Order Summary Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border p-6 sticky top-6">
            <h3 className="text-lg font-semibold mb-4">Order Summary</h3>
            
            {orderSummary && (
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Subtotal ({orderSummary.items} items)</span>
                  <span>${orderSummary.subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Shipping</span>
                  <span>${orderSummary.shipping.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Tax</span>
                  <span>${orderSummary.tax.toFixed(2)}</span>
                </div>
                <div className="border-t pt-3">
                  <div className="flex justify-between text-lg font-semibold">
                    <span>Total</span>
                    <span>${orderSummary.total.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Real-time validation status */}
            {realTimeValidation && Object.keys(realTimeValidation).length > 0 && (
              <div className="mt-6 p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center text-sm text-green-800">
                  <CheckCircleIcon className="w-4 h-4 mr-2" />
                  Order validated and ready to place
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SmartCheckoutForm;