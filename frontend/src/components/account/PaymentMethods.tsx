import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { CreditCard, PlusCircle, Trash2, CheckCircle } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useApi } from '../../hooks/useAsync';
import { PaymentsAPI } from '../../api/payments';
import { TokenManager } from '../../api/client';



/**
 * PaymentMethods component allows users to view, add, edit, delete, and set default payment methods.
 */
export const PaymentMethods = () => {
  // Custom hook to fetch payment methods from the API
  const { data: paymentMethods, loading, error, execute: fetchPaymentMethods } = useApi();
  // Local state for managing payment methods
  const [localPaymentMethods, setLocalPaymentMethods] = useState<any[]>([]);
  // State to control the visibility of the add card form
  const [showAddCardForm, setShowAddCardForm] = useState(false);
  // State for new card form data
  const [newCardData, setNewCardData] = useState({
    cardNumber: '',
    cardholderName: '',
    expiryMonth: '',
    expiryYear: '',
    cvv: '',
  });
  const [addingCard, setAddingCard] = useState(false);

  // Check if user came from checkout
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('from') === 'checkout') {
      toast.success('Add a payment method to complete your checkout!', { duration: 5000 });
    }
  }, []);

  // Effect hook to fetch payment methods on component mount
  useEffect(() => {
    console.log('PaymentMethods: Fetching payment methods...');
    console.log('PaymentMethods: Token available:', !!TokenManager.getToken());
    fetchPaymentMethods(PaymentsAPI.getPaymentMethods);
  }, [fetchPaymentMethods]);

  // Sync local state with fetched data
  useEffect(() => {
    if (paymentMethods) {
      // Handle the Response.success wrapper structure
      const data = (paymentMethods as any)?.success ? (paymentMethods as any).data : paymentMethods;
      setLocalPaymentMethods(Array.isArray(data) ? data : []);
    }
  }, [paymentMethods]);

  /**
   * Handles setting a payment method as default.
   * @param {string} id - The ID of the payment method to set as default.
   */
  const handleSetDefault = async (id: string) => {
    try {
      const response = await PaymentsAPI.setDefaultPaymentMethod(id);
      if (response.success) {
        // Update the local state to reflect the new default payment method
        setLocalPaymentMethods(localPaymentMethods?.map((pm: any) => ({ ...pm, is_default: pm.id === id })));
        toast.success('Default payment method updated');
      }
    } catch (error: any) {
      const errorMessage = error?.response?.data?.message || error?.message || 'Failed to set default payment method';
      toast.error(errorMessage);
    }
  };

  /**
   * Handles deleting a payment method.
   * @param {string} id - The ID of the payment method to delete.
   */
  const handleDeleteCard = async (id: string) => {
    try {
      const response = await PaymentsAPI.deletePaymentMethod(id);
      if (response.success || response.message) {
        // Remove the deleted payment method from the local state
        setLocalPaymentMethods(localPaymentMethods?.filter((pm: any) => pm.id !== id));
        toast.success('Payment method removed');
      }
    } catch (error: any) {
      const errorMessage = error?.response?.data?.message || error?.message || 'Failed to remove payment method';
      toast.error(errorMessage);
    }
  };

  /**
   * Handles adding a new card using modern Stripe API
   */
  const handleAddCard = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate card number (basic validation)
    if (newCardData.cardNumber.replace(/\s/g, '').length < 13) {
      toast.error('Please enter a valid card number');
      return;
    }
    
    if (!newCardData.cardholderName.trim()) {
      toast.error('Please enter cardholder name');
      return;
    }
    
    if (!newCardData.expiryMonth || !newCardData.expiryYear) {
      toast.error('Please enter card expiry date');
      return;
    }
    
    if (newCardData.cvv.length < 3) {
      toast.error('Please enter a valid CVV');
      return;
    }

    setAddingCard(true);

    try {
      // Create payment method using modern Stripe API
      const stripeKey = (import.meta as any).env?.VITE_STRIPE_PUBLIC_KEY;
      if (!stripeKey) {
        toast.error('Stripe is not configured');
        setAddingCard(false);
        return;
      }
      const stripe = (window as any).Stripe(stripeKey);
      
      const { paymentMethod, error } = await stripe.createPaymentMethod({
        type: 'card',
        card: {
          number: newCardData.cardNumber.replace(/\s/g, ''),
          exp_month: parseInt(newCardData.expiryMonth),
          exp_year: parseInt(newCardData.expiryYear),
          cvc: newCardData.cvv,
        },
        billing_details: {
          name: newCardData.cardholderName,
        },
      });

      if (error) {
        toast.error(error.message || 'Failed to create payment method');
        setAddingCard(false);
        return;
      }

      if (!paymentMethod) {
        toast.error('Failed to create payment method');
        setAddingCard(false);
        return;
      }

      // Send payment method to backend
      const payload = {
        stripe_payment_method_id: paymentMethod.id,
        type: 'card',
        provider: paymentMethod.card?.brand || 'unknown',
        last_four: paymentMethod.card?.last4 || '',
        expiry_month: paymentMethod.card?.exp_month || 0,
        expiry_year: paymentMethod.card?.exp_year || 0,
        is_default: false,
      };

      const result = await PaymentsAPI.addPaymentMethod(payload);
      
      if (result && (result.success || result.data)) {
        const newPaymentMethod = result.success ? result.data : result;
        setLocalPaymentMethods(localPaymentMethods ? [...localPaymentMethods, newPaymentMethod] : [newPaymentMethod]);
        toast.success('Payment method added successfully');
        resetForm();
      }
    } catch (error: any) {
      const errorMessage = error?.response?.data?.message || error?.message || 'Failed to add payment method';
      toast.error(errorMessage);
    } finally {
      setAddingCard(false);
    }
  };

  /**
   * Resets the add card form
   */
  const resetForm = () => {
    setShowAddCardForm(false);
    setNewCardData({
      cardNumber: '',
      cardholderName: '',
      expiryMonth: '',
      expiryYear: '',
      cvv: '',
    });
  };

  /**
   * Returns an SVG icon for a given card type provider.
   * @param {string} type - The type of card provider (e.g., 'visa', 'mastercard').
   * @returns {JSX.Element} The SVG icon component.
   */
  const getCardIcon = (type: string) => {
    switch (type) {
      case 'visa':
        return <svg className="w-8 h-6" viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="48" height="32" rx="4" fill="#F9F9F9" />
            <path d="M18.7 21.1H15.9L17.7 11H20.5L18.7 21.1Z" fill="#00579F" />
            <path d="M28.5 11.3C27.9 11.1 27 10.9 25.9 10.9C23.3 10.9 21.4 12.3 21.4 14.2C21.4 15.7 22.7 16.5 23.8 17C24.8 17.5 25.2 17.8 25.2 18.3C25.2 19 24.4 19.3 23.6 19.3C22.5 19.3 21.9 19.1 21 18.7L20.6 18.5L20.2 20.9C20.9 21.2 22.1 21.4 23.3 21.4C26.1 21.4 27.9 20 27.9 18C27.9 16.8 27.2 15.9 25.6 15.2C24.6 14.7 24 14.4 24 13.9C24 13.4 24.5 13 25.5 13C26.3 13 26.9 13.2 27.4 13.4L27.7 13.5L28.1 11.3H28.5Z" fill="#00579F" />
            <path d="M32.7 17.5C32.9 16.9 33.7 14.6 33.7 14.6C33.7 14.6 33.9 14.1 34 13.8L34.1 14.5C34.1 14.5 34.6 16.9 34.7 17.5H32.7ZM36 11H33.9C33.3 11 32.8 11.2 32.5 11.8L28.9 21.1H31.7C31.7 21.1 32.1 20 32.2 19.7C32.5 19.7 35.1 19.7 35.5 19.7C35.6 20.1 35.8 21.1 35.8 21.1H38.3L36 11Z" fill="#00579F" />
            <path d="M14.1 11L11.5 18L11.2 16.8C10.7 15.3 9.1 13.7 7.3 12.9L9.7 21.1H12.5L16.9 11H14.1Z" fill="#00579F" />
            <path d="M9.4 11.9C9.2 11.8 8.8 11.7 8.3 11.7C6.5 11.7 5.1 12.7 5.1 14.1C5.1 15.2 6.1 15.8 6.9 16.2C7.7 16.6 7.9 16.9 7.9 17.2C7.9 17.7 7.3 17.9 6.8 17.9C6.1 17.9 5.5 17.8 5 17.5L4.7 17.4L4.5 19.3C4.8 19.4 5.5 19.6 6.3 19.6C8.2 19.6 9.6 18.6 9.6 17.1C9.6 16.2 9 15.5 7.8 14.9C7.1 14.5 6.6 14.2 6.6 13.8C6.6 13.5 6.9 13.1 7.7 13.1C8.3 13.1 8.8 13.2 9.2 13.4L9.4 13.5L9.7 12L9.4 11.9Z" fill="#FAA61A" />
          </svg>;
      case 'mastercard':
        return <svg className="w-8 h-6" viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="48" height="32" rx="4" fill="#F9F9F9" />
            <path d="M30 10H18V22H30V10Z" fill="#FF5F00" />
            <path d="M19 16C19 13.6 20.3 11.5 22.2 10.3C21 9.5 19.6 9 18 9C14.1 9 11 12.1 11 16C11 19.9 14.1 23 18 23C19.6 23 21 22.5 22.2 21.7C20.3 20.5 19 18.4 19 16Z" fill="#EB001B" />
            <path d="M37 16C37 19.9 33.9 23 30 23C28.4 23 27 22.5 25.8 21.7C27.7 20.5 29 18.4 29 16C29 13.6 27.7 11.5 25.8 10.3C27 9.5 28.4 9 30 9C33.9 9 37 12.1 37 16Z" fill="#F79E1B" />
          </svg>;
      case 'amex':
        return <svg className="w-8 h-6" viewBox="0 0 48 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="48" height="32" rx="4" fill="#F9F9F9" />
            <path fillRule="evenodd" clipRule="evenodd" d="M9 11H39V21H9V11Z" fill="#006FCF" />
            <path d="M19.5 18.5L20.5 16.3L21.5 18.5H19.5ZM29 17H27V15.5H29V14H27V12.5H29V11H25.5V18.5H29V17ZM24 11L22 14.5L20 11H18V18.3L14 11H12.5L9 18.5H11L11.8 16.8H15.3L16 18.5H20V14L22 18.5L24 14V18.5H25.5V11H24ZM34.5 18.5H36.5L33.5 14.8L36.3 11H34.3L32.5 13.3L30.7 11H28.5L31.2 14.7L28.2 18.5H30.2L32.3 15.9L34.5 18.5Z" fill="white" />
          </svg>;
      default:
        return <CreditCard size={24} />;
    }
  };

  // Display loading message while payment methods are being fetched
  if (loading) {
    return <div className="p-6 text-center text-copy-light">Loading payment methods...</div>
  }

  // Display error message if fetching payment methods failed
  if (error) {
    return <div className="p-6 text-center text-error">Error: {error.message}</div>
  }

  return (
    <div className="p-6">
      {/* Show back to checkout button if user came from checkout */}
      {(() => {
        const params = new URLSearchParams(window.location.search);
        return params.get('from') === 'checkout' && (
          <div className="mb-6 p-4 bg-primary/10 border border-primary/30 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-primary font-medium">Complete Your Checkout</p>
                <p className="text-sm text-copy-light">Add a payment method to finish placing your order.</p>
              </div>
              <Link
                to="/checkout"
                className="px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-md transition-colors"
              >
                Back to Checkout
              </Link>
            </div>
          </div>
        );
      })()}
      
      <h1 className="text-2xl font-bold text-main dark:text-white mb-6">
        Payment Methods
      </h1>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-medium text-main dark:text-white">
            Saved Payment Methods
          </h2>
          {/* Button to toggle the add card form */}
          <button 
            onClick={() => setShowAddCardForm(!showAddCardForm)} 
            className="flex items-center text-primary hover:text-primary-dark"
          >
            <PlusCircle size={18} className="mr-1" />
            <span>Add New Card</span>
          </button>
        </div>
        {/* Display existing payment methods or a message if none are saved */}
        {localPaymentMethods && localPaymentMethods.length > 0 ? (
          <div className="space-y-4">
            {localPaymentMethods.map((method: any) => (
              <div key={method.id} className={`border rounded-lg p-4 ${method.is_default ? 'border-primary bg-primary/5 dark:bg-primary/10' : 'border-gray-200 dark:border-gray-700'}`}>
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <span className="mr-3">{getCardIcon(method.brand || method.provider)}</span>
                    <div>
                      <p className="font-medium text-main dark:text-white">
                        {method.brand?.charAt(0).toUpperCase() + method.brand?.slice(1) || method.provider?.charAt(0).toUpperCase() + method.provider?.slice(1)}{' '}
                        •••• {method.last_four}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Expires {method.expiry_month}/{method.expiry_year}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center">
                    {/* Set as default button or default badge */}
                    {method.is_default ? (
                      <span className="flex items-center text-xs bg-primary/10 text-primary px-2 py-1 rounded mr-3">
                        <CheckCircle size={14} className="mr-1" /> Default
                      </span>
                    ) : (
                      <button onClick={() => handleSetDefault(method.id)} className="text-sm text-gray-600 hover:text-primary dark:text-gray-400 dark:hover:text-primary mr-3">
                        Set as default
                      </button>
                    )}
                    {/* Delete button */}
                    <button 
                      onClick={() => handleDeleteCard(method.id)} 
                      className="text-copy-lighter hover:text-error dark:text-copy-lighter dark:hover:text-error p-1" 
                      disabled={method.is_default}
                      title={method.is_default ? "Cannot delete default payment method" : "Delete payment method"}
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 border border-dashed border-gray-300 dark:border-gray-700 rounded-lg">
            <CreditCard size={48} className="mx-auto text-gray-400 mb-3" />
            <p className="text-gray-500 dark:text-gray-400 mb-3">
              No payment methods saved yet
            </p>
            <button onClick={() => setShowAddCardForm(true)} className="text-primary hover:underline">
              Add your first payment method
            </button>
          </div>
        )}
        {/* Add Card Form */}
        {showAddCardForm && (
          <div className="mt-6 border-t border-gray-200 dark:border-gray-700 pt-6">
            <h3 className="text-lg font-medium text-main dark:text-white mb-4">
              Add New Payment Method
            </h3>
            <form onSubmit={handleAddCard}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Card Number Input */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Card Number
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white"
                    placeholder="1234 5678 9012 3456"
                    value={newCardData.cardNumber}
                    onChange={(e) => {
                      // Format card number with spaces
                      const value = e.target.value.replace(/\s/g, '').replace(/(\d{4})/g, '$1 ').trim();
                      setNewCardData({ ...newCardData, cardNumber: value });
                    }}
                    maxLength={19}
                    required
                  />
                </div>
                
                {/* Cardholder Name Input */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Cardholder Name
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white"
                    placeholder="John Doe"
                    value={newCardData.cardholderName}
                    onChange={(e) => setNewCardData({ ...newCardData, cardholderName: e.target.value })}
                    required
                  />
                </div>
                
                {/* Expiration Month Select */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Expiration Month
                  </label>
                  <select
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white"
                    value={newCardData.expiryMonth}
                    onChange={(e) => setNewCardData({ ...newCardData, expiryMonth: e.target.value })}
                    required
                  >
                    <option value="">Month</option>
                    {Array.from({ length: 12 }, (_, i) => {
                      const month = (i + 1).toString();
                      return (
                        <option key={month} value={month}>
                          {month.padStart(2, '0')}
                        </option>
                      );
                    })}
                  </select>
                </div>
                
                {/* Expiration Year Select */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Expiration Year
                  </label>
                  <select
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white"
                    value={newCardData.expiryYear}
                    onChange={(e) => setNewCardData({ ...newCardData, expiryYear: e.target.value })}
                    required
                  >
                    <option value="">Year</option>
                    {Array.from({ length: 10 }, (_, i) => {
                      const year = new Date().getFullYear() + i;
                      return (
                        <option key={year} value={year}>
                          {year}
                        </option>
                      );
                    })}
                  </select>
                </div>
                
                {/* CVV Input */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    CVV
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white"
                    placeholder="123"
                    value={newCardData.cvv}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\D/g, '');
                      setNewCardData({ ...newCardData, cvv: value });
                    }}
                    maxLength={4}
                    required
                  />
                </div>
              </div>
              
              {/* Form Action Buttons */}
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
                  disabled={addingCard}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={addingCard}
                >
                  {addingCard ? 'Adding...' : 'Add Card'}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
      {/* Payment Security Information */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-medium text-main dark:text-white mb-4">
          Payment Security
        </h2>
        <p className="text-gray-600 dark:text-gray-300 mb-3">
          Your payment information is securely stored using industry-standard
          encryption. We never store your full card details on our servers.
        </p>
        <p className="text-gray-600 dark:text-gray-300">
          All transactions are processed through our secure payment gateway
          partners and comply with PCI DSS standards.
        </p>
      </div>
    </div>
  );
};
