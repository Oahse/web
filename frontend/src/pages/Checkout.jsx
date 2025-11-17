import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { OrdersAPI } from '../apis/orders';
import { AuthAPI } from '../apis/auth';
import { CartAPI } from '../apis/cart';
import { toast } from 'react-hot-toast';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

const Checkout = () => {
  const navigate = useNavigate();
  const { cart, loading: cartLoading, clearCart } = useCart();
  const { isAuthenticated } = useAuth();

  // State management
  const [loading, setLoading] = useState(false);
  const [addresses, setAddresses] = useState([]);
  const [shippingMethods, setShippingMethods] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [checkoutData, setCheckoutData] = useState({
    shipping_address_id: '',
    shipping_method_id: '',
    payment_method_id: '',
    notes: ''
  });
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [newAddress, setNewAddress] = useState({
    street: '',
    city: '',
    state: '',
    country: '',
    post_code: '',
    kind: 'Shipping'
  });
  const [errors, setErrors] = useState({});
  const [processingPayment, setProcessingPayment] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      toast.error('Please login to checkout');
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  // Redirect if cart is empty
  useEffect(() => {
    if (!cartLoading && (!cart || !cart.items || cart.items.length === 0)) {
      toast.error('Your cart is empty');
      navigate('/cart');
    }
  }, [cart, cartLoading, navigate]);

  // Fetch checkout data
  useEffect(() => {
    const fetchCheckoutData = async () => {
      if (!isAuthenticated) return;

      try {
        setLoading(true);

        // Fetch addresses
        const addressResponse = await AuthAPI.getAddresses();
        if (addressResponse?.data) {
          setAddresses(addressResponse.data);
          // Auto-select first address if available
          if (addressResponse.data.length > 0 && !checkoutData.shipping_address_id) {
            setCheckoutData(prev => ({
              ...prev,
              shipping_address_id: addressResponse.data[0].id
            }));
          }
        }

        // Fetch shipping methods
        const shippingResponse = await CartAPI.getShippingOptions({});
        if (shippingResponse?.data) {
          setShippingMethods(shippingResponse.data);
          // Auto-select first shipping method if available
          if (shippingResponse.data.length > 0 && !checkoutData.shipping_method_id) {
            setCheckoutData(prev => ({
              ...prev,
              shipping_method_id: shippingResponse.data[0].id
            }));
          }
        }

        // Fetch payment methods
        const paymentResponse = await AuthAPI.getPaymentMethods();
        if (paymentResponse?.data) {
          setPaymentMethods(paymentResponse.data);
          // Auto-select first payment method if available
          if (paymentResponse.data.length > 0 && !checkoutData.payment_method_id) {
            setCheckoutData(prev => ({
              ...prev,
              payment_method_id: paymentResponse.data[0].id
            }));
          }
        }
      } catch (error) {
        console.error('Failed to fetch checkout data:', error);
        toast.error('Failed to load checkout information');
      } finally {
        setLoading(false);
      }
    };

    fetchCheckoutData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  // Validate address form
  const validateAddressForm = () => {
    const newErrors = {};

    if (!newAddress.street.trim()) {
      newErrors.street = 'Street address is required';
    }
    if (!newAddress.city.trim()) {
      newErrors.city = 'City is required';
    }
    if (!newAddress.state.trim()) {
      newErrors.state = 'State is required';
    }
    if (!newAddress.country.trim()) {
      newErrors.country = 'Country is required';
    }
    if (!newAddress.post_code.trim()) {
      newErrors.post_code = 'Postal code is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle add new address
  const handleAddAddress = async (e) => {
    e.preventDefault();

    if (!validateAddressForm()) {
      return;
    }

    try {
      setLoading(true);
      const response = await AuthAPI.createAddress(newAddress);
      
      if (response?.data) {
        setAddresses(prev => [...prev, response.data]);
        setCheckoutData(prev => ({
          ...prev,
          shipping_address_id: response.data.id
        }));
        setShowAddressForm(false);
        setNewAddress({
          street: '',
          city: '',
          state: '',
          country: '',
          post_code: '',
          kind: 'Shipping'
        });
        setErrors({});
        toast.success('Address added successfully');
      }
    } catch (error) {
      console.error('Failed to add address:', error);
      toast.error('Failed to add address');
    } finally {
      setLoading(false);
    }
  };

  // Validate checkout form
  const validateCheckout = () => {
    const newErrors = {};

    if (!checkoutData.shipping_address_id) {
      newErrors.shipping_address_id = 'Please select a shipping address';
    }
    if (!checkoutData.shipping_method_id) {
      newErrors.shipping_method_id = 'Please select a shipping method';
    }
    if (!checkoutData.payment_method_id) {
      newErrors.payment_method_id = 'Please select a payment method';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle place order
  const handlePlaceOrder = async () => {
    if (!validateCheckout()) {
      toast.error('Please complete all required fields');
      return;
    }

    try {
      setProcessingPayment(true);

      const response = await OrdersAPI.checkout(checkoutData);

      if (response?.success && response?.data) {
        toast.success('Order placed successfully!');
        
        // Clear cart
        await clearCart();
        
        // Navigate to order confirmation
        navigate(`/account/orders/${response.data.id}`);
      } else {
        throw new Error('Failed to place order');
      }
    } catch (error) {
      console.error('Failed to place order:', error);
      const errorMessage = error?.response?.data?.message || error?.message || 'Failed to place order';
      toast.error(errorMessage);
    } finally {
      setProcessingPayment(false);
    }
  };

  // Calculate totals
  const subtotal = cart?.subtotal || 0;
  const tax = cart?.tax_amount || 0;
  const shippingCost = shippingMethods.find(m => m.id === checkoutData.shipping_method_id)?.price || 0;
  const total = subtotal + tax + shippingCost;

  if (loading || cartLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading checkout...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Checkout</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Forms */}
          <div className="lg:col-span-2 space-y-6">
            {/* Shipping Address Section */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Shipping Address</h2>
                <button
                  onClick={() => setShowAddressForm(!showAddressForm)}
                  className="text-green-600 hover:text-green-700 text-sm font-medium"
                >
                  {showAddressForm ? 'Cancel' : '+ Add New Address'}
                </button>
              </div>

              {errors.shipping_address_id && (
                <p className="text-red-500 text-sm mb-4">{errors.shipping_address_id}</p>
              )}

              {showAddressForm ? (
                <form onSubmit={handleAddAddress} className="space-y-4">
                  <Input
                    label="Street Address"
                    value={newAddress.street}
                    onChange={(e) => setNewAddress({ ...newAddress, street: e.target.value })}
                    error={errors.street}
                    required
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      label="City"
                      value={newAddress.city}
                      onChange={(e) => setNewAddress({ ...newAddress, city: e.target.value })}
                      error={errors.city}
                      required
                    />
                    <Input
                      label="State"
                      value={newAddress.state}
                      onChange={(e) => setNewAddress({ ...newAddress, state: e.target.value })}
                      error={errors.state}
                      required
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      label="Country"
                      value={newAddress.country}
                      onChange={(e) => setNewAddress({ ...newAddress, country: e.target.value })}
                      error={errors.country}
                      required
                    />
                    <Input
                      label="Postal Code"
                      value={newAddress.post_code}
                      onChange={(e) => setNewAddress({ ...newAddress, post_code: e.target.value })}
                      error={errors.post_code}
                      required
                    />
                  </div>
                  <Button type="submit" disabled={loading}>
                    {loading ? 'Adding...' : 'Add Address'}
                  </Button>
                </form>
              ) : (
                <div className="space-y-3">
                  {addresses.length === 0 ? (
                    <p className="text-gray-500 text-sm">No addresses found. Please add a shipping address.</p>
                  ) : (
                    addresses.map((address) => (
                      <label
                        key={address.id}
                        className={`block p-4 border rounded-lg cursor-pointer transition-colors ${
                          checkoutData.shipping_address_id === address.id
                            ? 'border-green-600 bg-green-50'
                            : 'border-gray-300 hover:border-green-400'
                        }`}
                      >
                        <input
                          type="radio"
                          name="shipping_address"
                          value={address.id}
                          checked={checkoutData.shipping_address_id === address.id}
                          onChange={(e) => setCheckoutData({ ...checkoutData, shipping_address_id: e.target.value })}
                          className="mr-3"
                        />
                        <span className="text-gray-900">
                          {address.street}, {address.city}, {address.state} {address.post_code}, {address.country}
                        </span>
                      </label>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* Shipping Method Section */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Shipping Method</h2>
              
              {errors.shipping_method_id && (
                <p className="text-red-500 text-sm mb-4">{errors.shipping_method_id}</p>
              )}

              <div className="space-y-3">
                {shippingMethods.length === 0 ? (
                  <p className="text-gray-500 text-sm">No shipping methods available.</p>
                ) : (
                  shippingMethods.map((method) => (
                    <label
                      key={method.id}
                      className={`block p-4 border rounded-lg cursor-pointer transition-colors ${
                        checkoutData.shipping_method_id === method.id
                          ? 'border-green-600 bg-green-50'
                          : 'border-gray-300 hover:border-green-400'
                      }`}
                    >
                      <input
                        type="radio"
                        name="shipping_method"
                        value={method.id}
                        checked={checkoutData.shipping_method_id === method.id}
                        onChange={(e) => setCheckoutData({ ...checkoutData, shipping_method_id: e.target.value })}
                        className="mr-3"
                      />
                      <div className="inline-block">
                        <div className="flex justify-between items-center">
                          <span className="font-medium text-gray-900">{method.name}</span>
                          <span className="ml-4 text-gray-900">${method.price.toFixed(2)}</span>
                        </div>
                        {method.description && (
                          <p className="text-sm text-gray-500 mt-1">{method.description}</p>
                        )}
                        {method.estimated_days && (
                          <p className="text-sm text-gray-500">Estimated delivery: {method.estimated_days} days</p>
                        )}
                      </div>
                    </label>
                  ))
                )}
              </div>
            </div>

            {/* Payment Method Section */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Payment Method</h2>
              
              {errors.payment_method_id && (
                <p className="text-red-500 text-sm mb-4">{errors.payment_method_id}</p>
              )}

              <div className="space-y-3">
                {paymentMethods.length === 0 ? (
                  <div>
                    <p className="text-gray-500 text-sm mb-3">No payment methods found.</p>
                    <Button
                      onClick={() => navigate('/account/payment-methods')}
                      variant="outline"
                    >
                      Add Payment Method
                    </Button>
                  </div>
                ) : (
                  paymentMethods.map((method) => (
                    <label
                      key={method.id}
                      className={`block p-4 border rounded-lg cursor-pointer transition-colors ${
                        checkoutData.payment_method_id === method.id
                          ? 'border-green-600 bg-green-50'
                          : 'border-gray-300 hover:border-green-400'
                      }`}
                    >
                      <input
                        type="radio"
                        name="payment_method"
                        value={method.id}
                        checked={checkoutData.payment_method_id === method.id}
                        onChange={(e) => setCheckoutData({ ...checkoutData, payment_method_id: e.target.value })}
                        className="mr-3"
                      />
                      <span className="text-gray-900">
                        {method.type} {method.last_four ? `****${method.last_four}` : ''}
                      </span>
                    </label>
                  ))
                )}
              </div>
            </div>

            {/* Order Notes */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Order Notes (Optional)</h2>
              <textarea
                value={checkoutData.notes}
                onChange={(e) => setCheckoutData({ ...checkoutData, notes: e.target.value })}
                placeholder="Add any special instructions for your order..."
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Right Column - Order Summary */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6 sticky top-4">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Order Summary</h2>

              {/* Cart Items */}
              <div className="space-y-4 mb-6 max-h-64 overflow-y-auto">
                {cart?.items?.map((item) => (
                  <div key={item.id} className="flex gap-3">
                    {item.variant?.primary_image && (
                      <img
                        src={item.variant.primary_image}
                        alt={item.variant.product_name || item.variant.name}
                        className="w-16 h-16 object-cover rounded"
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {item.variant?.product_name || 'Product'}
                      </p>
                      <p className="text-sm text-gray-500">{item.variant?.name}</p>
                      <p className="text-sm text-gray-500">Qty: {item.quantity}</p>
                    </div>
                    <p className="text-sm font-medium text-gray-900">
                      ${(item.price_per_unit * item.quantity).toFixed(2)}
                    </p>
                  </div>
                ))}
              </div>

              {/* Totals */}
              <div className="border-t pt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Subtotal</span>
                  <span className="text-gray-900">${subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Shipping</span>
                  <span className="text-gray-900">${shippingCost.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Tax</span>
                  <span className="text-gray-900">${tax.toFixed(2)}</span>
                </div>
                <div className="border-t pt-2 flex justify-between font-semibold text-lg">
                  <span className="text-gray-900">Total</span>
                  <span className="text-gray-900">${total.toFixed(2)}</span>
                </div>
              </div>

              {/* Place Order Button */}
              <Button
                onClick={handlePlaceOrder}
                disabled={processingPayment || addresses.length === 0 || paymentMethods.length === 0}
                className="w-full mt-6"
              >
                {processingPayment ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                  </span>
                ) : (
                  'Place Order'
                )}
              </Button>

              <p className="text-xs text-gray-500 text-center mt-4">
                By placing your order, you agree to our terms and conditions
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Checkout;
