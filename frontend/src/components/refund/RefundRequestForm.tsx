/**
 * Painless Refund Request Form - Simple, guided refund process
 * Makes refunds easy with smart defaults and clear guidance
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { OrdersAPI } from '../../apis/orders';
import { toast } from 'react-hot-toast';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';

interface RefundRequestFormProps {
  order: any;
  onSuccess: (refundId: string) => void;
  onCancel: () => void;
}

const REFUND_REASONS = [
  {
    value: 'defective_product',
    label: 'Defective or damaged product',
    description: 'Item arrived broken, damaged, or not working',
    autoApprove: true,
    requiresReturn: false
  },
  {
    value: 'wrong_item',
    label: 'Wrong item received',
    description: 'Received different item than ordered',
    autoApprove: true,
    requiresReturn: false
  },
  {
    value: 'not_as_described',
    label: 'Item not as described',
    description: 'Product differs significantly from description',
    autoApprove: false,
    requiresReturn: true
  },
  {
    value: 'damaged_in_shipping',
    label: 'Damaged during shipping',
    description: 'Item was damaged during delivery',
    autoApprove: true,
    requiresReturn: false
  },
  {
    value: 'changed_mind',
    label: 'Changed my mind',
    description: 'No longer need or want the item',
    autoApprove: false,
    requiresReturn: true
  },
  {
    value: 'size_issue',
    label: 'Size/fit issue',
    description: 'Item doesn\'t fit as expected',
    autoApprove: false,
    requiresReturn: true
  },
  {
    value: 'quality_issue',
    label: 'Quality not as expected',
    description: 'Product quality is below expectations',
    autoApprove: false,
    requiresReturn: true
  },
  {
    value: 'late_delivery',
    label: 'Delivered too late',
    description: 'Item arrived after needed date',
    autoApprove: true,
    requiresReturn: true
  },
  {
    value: 'other',
    label: 'Other reason',
    description: 'Please explain in the notes below',
    autoApprove: false,
    requiresReturn: true
  }
];

export const RefundRequestForm: React.FC<RefundRequestFormProps> = ({
  order,
  onSuccess,
  onCancel
}) => {
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Form state
  const [selectedItems, setSelectedItems] = useState({});
  const [selectedReason, setSelectedReason] = useState('');
  const [customerReason, setCustomerReason] = useState('');
  const [customerNotes, setCustomerNotes] = useState('');
  const [refundType, setRefundType] = useState('full_refund');
  
  // Calculated values
  const [refundAmount, setRefundAmount] = useState(0);
  const [willAutoApprove, setWillAutoApprove] = useState(false);

  // Initialize with all items selected for full refund
  useEffect(() => {
    if (order?.items) {
      const initialSelection = {};
      order.items.forEach(item => {
        initialSelection[item.id] = {
          selected: true,
          quantity: item.quantity,
          maxQuantity: item.quantity
        };
      });
      setSelectedItems(initialSelection);
    }
  }, [order]);

  // Calculate refund amount when selection changes
  useEffect(() => {
    calculateRefundAmount();
  }, [selectedItems, order]);

  // Check auto-approval eligibility
  useEffect(() => {
    checkAutoApprovalEligibility();
  }, [selectedReason, selectedItems, order]);

  const calculateRefundAmount = () => {
    if (!order?.items) return;

    let total = 0;
    let allItemsSelected = true;
    let totalOrderItems = 0;
    let totalSelectedItems = 0;

    order.items.forEach(item => {
      totalOrderItems += item.quantity;
      const selection = selectedItems[item.id];
      if (selection?.selected) {
        total += item.price_per_unit * selection.quantity;
        totalSelectedItems += selection.quantity;
      } else {
        allItemsSelected = false;
      }
    });

    // Add shipping if all items are being refunded
    if (allItemsSelected && totalSelectedItems === totalOrderItems) {
      total += order.shipping_cost || order.shipping_amount || 0;
    }

    // Add proportional tax
    if (order.tax_amount) {
      const taxRate = order.tax_amount / order.subtotal;
      total += total * taxRate;
    }

    setRefundAmount(total);
  };

  const checkAutoApprovalEligibility = () => {
    const reason = REFUND_REASONS.find(r => r.value === selectedReason);
    if (!reason || !order) {
      setWillAutoApprove(false);
      return;
    }

    // Check if eligible for auto-approval
    const orderAge = Math.floor((Date.now() - new Date(order.created_at).getTime()) / (1000 * 60 * 60 * 24));
    const isEligible = (
      reason.autoApprove &&
      orderAge <= 30 &&
      refundAmount <= 500 &&
      refundType === 'full_refund'
    );

    setWillAutoApprove(isEligible);
  };

  const handleItemSelection = (itemId, field, value) => {
    setSelectedItems(prev => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        [field]: value
      }
    }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      // Prepare refund request
      const refundItems = Object.entries(selectedItems)
        .filter(([_, selection]) => selection.selected)
        .map(([itemId, selection]) => ({
          order_item_id: itemId,
          quantity: selection.quantity,
          condition_notes: selection.conditionNotes || ''
        }));

      if (refundItems.length === 0) {
        toast.error('Please select at least one item to refund');
        return;
      }

      const refundRequest = {
        refund_type: refundType,
        reason: selectedReason,
        customer_reason: customerReason,
        customer_notes: customerNotes,
        items: refundItems
      };

      const response = await OrdersAPI.requestRefund(order.id, refundRequest);

      if (response?.success) {
        toast.success(
          willAutoApprove 
            ? 'Refund approved! Processing now...' 
            : 'Refund request submitted successfully!'
        );
        onSuccess(response.data.id);
      } else {
        throw new Error('Failed to submit refund request');
      }
    } catch (error) {
      console.error('Refund request failed:', error);
      const errorMessage = error?.response?.data?.message || error?.message || 'Failed to submit refund request';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const selectedReason_obj = REFUND_REASONS.find(r => r.value === selectedReason);
  const selectedItemsCount = Object.values(selectedItems).filter(item => item.selected).length;

  return (
    <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-sm border">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={onCancel}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <ArrowLeftIcon className="w-5 h-5 text-gray-600" />
            </button>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Request Refund</h2>
              <p className="text-sm text-gray-600">Order #{order.order_number}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-600">Refund Amount</div>
            <div className="text-2xl font-bold text-green-600">
              ${refundAmount.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Step 1: Select Items */}
        {currentStep === 1 && (
          <div>
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">Select Items to Refund</h3>
              <p className="text-gray-600">Choose which items you'd like to return or get refunded for.</p>
            </div>

            <div className="space-y-4">
              {order.items?.map((item) => (
                <div
                  key={item.id}
                  className={`border rounded-lg p-4 transition-colors ${
                    selectedItems[item.id]?.selected
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200'
                  }`}
                >
                  <div className="flex items-start space-x-4">
                    <input
                      type="checkbox"
                      checked={selectedItems[item.id]?.selected || false}
                      onChange={(e) => handleItemSelection(item.id, 'selected', e.target.checked)}
                      className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    
                    <img
                      src={item.product?.image_url || '/placeholder-product.jpg'}
                      alt={item.product?.name}
                      className="w-16 h-16 object-cover rounded"
                    />
                    
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{item.product?.name}</h4>
                      <p className="text-sm text-gray-600">
                        ${item.price_per_unit.toFixed(2)} each
                      </p>
                      
                      {selectedItems[item.id]?.selected && (
                        <div className="mt-3 flex items-center space-x-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Quantity to refund
                            </label>
                            <select
                              value={selectedItems[item.id]?.quantity || item.quantity}
                              onChange={(e) => handleItemSelection(item.id, 'quantity', parseInt(e.target.value))}
                              className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                              {Array.from({ length: item.quantity }, (_, i) => i + 1).map(num => (
                                <option key={num} value={num}>{num}</option>
                              ))}
                            </select>
                            <p className="text-xs text-gray-500 mt-1">
                              Ordered: {item.quantity}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className="text-right">
                      <div className="font-semibold text-gray-900">
                        ${(item.price_per_unit * (selectedItems[item.id]?.quantity || item.quantity)).toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 flex justify-between">
              <div className="text-sm text-gray-600">
                {selectedItemsCount} of {order.items?.length} items selected
              </div>
              <Button
                onClick={() => setCurrentStep(2)}
                disabled={selectedItemsCount === 0}
              >
                Continue
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: Select Reason */}
        {currentStep === 2 && (
          <div>
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">Why are you requesting a refund?</h3>
              <p className="text-gray-600">This helps us improve our service and process your refund faster.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {REFUND_REASONS.map((reason) => (
                <label
                  key={reason.value}
                  className={`block p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedReason === reason.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="refund_reason"
                    value={reason.value}
                    checked={selectedReason === reason.value}
                    onChange={(e) => setSelectedReason(e.target.value)}
                    className="sr-only"
                  />
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 mb-1">
                        {reason.label}
                      </div>
                      <div className="text-sm text-gray-600">
                        {reason.description}
                      </div>
                      {reason.autoApprove && (
                        <div className="mt-2 flex items-center text-xs text-green-600">
                          <CheckCircleIcon className="w-3 h-3 mr-1" />
                          Fast approval
                        </div>
                      )}
                    </div>
                  </div>
                </label>
              ))}
            </div>

            {/* Additional details */}
            {selectedReason && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Please provide more details (optional)
                  </label>
                  <textarea
                    value={customerReason}
                    onChange={(e) => setCustomerReason(e.target.value)}
                    placeholder="Help us understand what happened..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Additional notes (optional)
                  </label>
                  <textarea
                    value={customerNotes}
                    onChange={(e) => setCustomerNotes(e.target.value)}
                    placeholder="Any other information you'd like us to know..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={2}
                  />
                </div>
              </div>
            )}

            <div className="mt-6 flex justify-between">
              <Button
                onClick={() => setCurrentStep(1)}
                variant="outline"
              >
                Back
              </Button>
              <Button
                onClick={() => setCurrentStep(3)}
                disabled={!selectedReason}
              >
                Continue
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Review and Submit */}
        {currentStep === 3 && (
          <div>
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">Review Your Refund Request</h3>
              <p className="text-gray-600">Please review the details before submitting.</p>
            </div>

            {/* Auto-approval notice */}
            {willAutoApprove && (
              <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <CheckCircleIcon className="w-6 h-6 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-green-900">Instant Approval</h4>
                    <p className="text-sm text-green-700 mt-1">
                      Your refund qualifies for automatic approval and will be processed immediately.
                      You should see the refund in your account within 3-5 business days.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Return requirements */}
            {selectedReason_obj?.requiresReturn && (
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <InformationCircleIcon className="w-6 h-6 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-900">Return Required</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      You'll need to return the item(s) to complete your refund. 
                      We'll email you a prepaid return label once your refund is approved.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Summary */}
            <div className="bg-gray-50 rounded-lg p-6 mb-6">
              <h4 className="font-medium text-gray-900 mb-4">Refund Summary</h4>
              
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Reason:</span>
                  <span className="font-medium">{selectedReason_obj?.label}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Items:</span>
                  <span className="font-medium">{selectedItemsCount} item(s)</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Return required:</span>
                  <span className="font-medium">
                    {selectedReason_obj?.requiresReturn ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="border-t pt-3">
                  <div className="flex justify-between text-lg font-semibold">
                    <span>Total refund:</span>
                    <span className="text-green-600">${refundAmount.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-between">
              <Button
                onClick={() => setCurrentStep(2)}
                variant="outline"
              >
                Back
              </Button>
              <Button
                onClick={handleSubmit}
                loading={loading}
                className="bg-green-600 hover:bg-green-700"
              >
                {loading ? 'Submitting...' : 'Submit Refund Request'}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RefundRequestForm;