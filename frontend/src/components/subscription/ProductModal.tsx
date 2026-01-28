import React, { useState, useEffect } from 'react';
import { 
  XIcon, 
  PackageIcon, 
  TrashIcon, 
  AlertTriangleIcon,
  LoaderIcon
} from 'lucide-react';
import { themeClasses, combineThemeClasses, getButtonClasses } from '../../lib/themeClasses';
import { formatCurrency } from '../../utils/orderCalculations';
import { toast } from 'react-hot-toast';
import { getSubscription } from '../../apis/subscription';
import type { Subscription } from '../../types';

interface SubscriptionProduct {
  id: string;
  name: string;
  price: number;
  current_price?: number;
  image?: string;
  quantity?: number;
}

interface ProductModalProps {
  subscriptionId: string;
  isOpen: boolean;
  onClose: () => void;
  onProductRemove: (productId: string) => Promise<void>;
}

interface ProductModalState {
  products: SubscriptionProduct[];
  isLoading: boolean;
  error: string | null;
  removingProductId: string | null;
}

export const ProductModal: React.FC<ProductModalProps> = ({
  subscriptionId,
  isOpen,
  onClose,
  onProductRemove
}) => {
  const [state, setState] = useState<ProductModalState>({
    products: [],
    isLoading: false,
    error: null,
    removingProductId: null
  });

  const [showConfirmDialog, setShowConfirmDialog] = useState<{
    show: boolean;
    productId: string;
    productName: string;
  }>({
    show: false,
    productId: '',
    productName: ''
  });

  // Load subscription details when modal opens
  useEffect(() => {
    if (isOpen && subscriptionId) {
      loadSubscriptionDetails();
    }
  }, [isOpen, subscriptionId]);

  const loadSubscriptionDetails = async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const subscription: Subscription = await getSubscription(subscriptionId);
      
      setState(prev => ({
        ...prev,
        products: subscription.products || [],
        isLoading: false
      }));
    } catch (error) {
      console.error('Failed to load subscription details:', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to load subscription details',
        isLoading: false
      }));
      toast.error('Failed to load subscription details');
    }
  };

  const handleRemoveProduct = async (productId: string) => {
    setState(prev => ({ ...prev, removingProductId: productId }));
    
    try {
      await onProductRemove(productId);
      
      // Remove product from local state
      setState(prev => ({
        ...prev,
        products: prev.products.filter(p => p.id !== productId),
        removingProductId: null
      }));
      
      setShowConfirmDialog({ show: false, productId: '', productName: '' });
      toast.success('Product removed from subscription');
    } catch (error) {
      console.error('Failed to remove product:', error);
      setState(prev => ({ ...prev, removingProductId: null }));
      toast.error('Failed to remove product');
    }
  };

  const confirmRemoveProduct = (productId: string, productName: string) => {
    setShowConfirmDialog({
      show: true,
      productId,
      productName
    });
  };

  const handleClose = () => {
    setShowConfirmDialog({ show: false, productId: '', productName: '' });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Modal Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className={combineThemeClasses(
          themeClasses.card.base,
          'w-full max-w-4xl max-h-[90vh] flex flex-col'
        )}>
          {/* Header */}
          <div className="p-6 border-b border-border flex-shrink-0">
            <div className="flex justify-between items-center">
              <div>
                <h2 className={combineThemeClasses(themeClasses.text.heading, 'text-2xl font-bold')}>
                  Subscription Products
                </h2>
                <p className={combineThemeClasses(themeClasses.text.secondary, 'text-sm mt-1')}>
                  Manage products in your subscription
                </p>
              </div>
              <button
                onClick={handleClose}
                className={combineThemeClasses(
                  themeClasses.text.muted,
                  'hover:text-primary p-2 rounded-full hover:bg-surface-hover transition-colors'
                )}
              >
                <XIcon size={24} />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {state.isLoading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <LoaderIcon className={combineThemeClasses(
                  themeClasses.text.muted,
                  'w-8 h-8 animate-spin mb-4'
                )} />
                <p className={combineThemeClasses(themeClasses.text.secondary, 'text-sm')}>
                  Loading subscription details...
                </p>
              </div>
            ) : state.error ? (
              <div className="flex flex-col items-center justify-center py-12">
                <AlertTriangleIcon className={combineThemeClasses(
                  themeClasses.text.error,
                  'w-8 h-8 mb-4'
                )} />
                <p className={combineThemeClasses(themeClasses.text.error, 'text-sm mb-4')}>
                  {state.error}
                </p>
                <button
                  onClick={loadSubscriptionDetails}
                  className={getButtonClasses('outline')}
                >
                  Try Again
                </button>
              </div>
            ) : state.products.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <PackageIcon className={combineThemeClasses(
                  themeClasses.text.muted,
                  'w-12 h-12 mb-4'
                )} />
                <p className={combineThemeClasses(themeClasses.text.secondary, 'text-sm')}>
                  No products in this subscription
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {state.products.map((product) => (
                    <div
                      key={product.id}
                      className={combineThemeClasses(
                        themeClasses.card.base,
                        'p-4 hover:shadow-md transition-shadow'
                      )}
                    >
                      <div className="flex items-start gap-4">
                        {/* Product Image */}
                        <div className="flex-shrink-0">
                          {product.image ? (
                            <img
                              src={product.image}
                              alt={product.name}
                              className="w-16 h-16 rounded-lg object-cover border border-border"
                            />
                          ) : (
                            <div className="w-16 h-16 rounded-lg bg-surface-elevated flex items-center justify-center border border-border">
                              <PackageIcon className={combineThemeClasses(
                                themeClasses.text.muted,
                                'w-6 h-6'
                              )} />
                            </div>
                          )}
                        </div>

                        {/* Product Details */}
                        <div className="flex-1 min-w-0">
                          <h3 className={combineThemeClasses(
                            themeClasses.text.primary,
                            'font-semibold text-lg mb-1 truncate'
                          )}>
                            {product.name}
                          </h3>
                          
                          <div className="flex items-center gap-2 mb-2">
                            <span className={combineThemeClasses(
                              themeClasses.text.primary,
                              'font-medium'
                            )}>
                              {formatCurrency(product.current_price || product.price, 'USD')}
                            </span>
                            <span className={combineThemeClasses(themeClasses.text.secondary, 'text-sm')}>
                              per item
                            </span>
                          </div>

                          {product.quantity && (
                            <div className="flex items-center gap-2 mb-3">
                              <span className={combineThemeClasses(themeClasses.text.secondary, 'text-sm')}>
                                Quantity: {product.quantity}
                              </span>
                            </div>
                          )}

                          {/* Actions */}
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => confirmRemoveProduct(product.id, product.name)}
                              disabled={state.removingProductId === product.id}
                              className={combineThemeClasses(
                                'px-3 py-1 text-sm rounded-md border border-red-300 text-red-700 hover:bg-red-50 transition-colors flex items-center gap-1',
                                state.removingProductId === product.id ? 'opacity-50 cursor-not-allowed' : ''
                              )}
                            >
                              {state.removingProductId === product.id ? (
                                <>
                                  <LoaderIcon className="w-3 h-3 animate-spin" />
                                  Removing...
                                </>
                              ) : (
                                <>
                                  <TrashIcon className="w-3 h-3" />
                                  Remove
                                </>
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-border flex-shrink-0">
            <div className="flex justify-end">
              <button
                onClick={handleClose}
                className={getButtonClasses('outline')}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      {showConfirmDialog.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
          <div className={combineThemeClasses(themeClasses.card.base, 'w-full max-w-md')}>
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <AlertTriangleIcon className={combineThemeClasses(
                  themeClasses.text.warning,
                  'w-6 h-6'
                )} />
                <h3 className={combineThemeClasses(themeClasses.text.heading, 'text-lg font-semibold')}>
                  Remove Product
                </h3>
              </div>
              
              <p className={combineThemeClasses(themeClasses.text.secondary, 'mb-6')}>
                Are you sure you want to remove "{showConfirmDialog.productName}" from your subscription? 
                This action cannot be undone.
              </p>
              
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowConfirmDialog({ show: false, productId: '', productName: '' })}
                  className={getButtonClasses('outline')}
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleRemoveProduct(showConfirmDialog.productId)}
                  disabled={state.removingProductId === showConfirmDialog.productId}
                  className={combineThemeClasses(
                    'px-4 py-2 rounded-md bg-red-600 hover:bg-red-700 text-white font-medium transition-colors flex items-center gap-2',
                    state.removingProductId === showConfirmDialog.productId ? 'opacity-50 cursor-not-allowed' : ''
                  )}
                >
                  {state.removingProductId === showConfirmDialog.productId ? (
                    <>
                      <LoaderIcon className="w-4 h-4 animate-spin" />
                      Removing...
                    </>
                  ) : (
                    <>
                      <TrashIcon className="w-4 h-4" />
                      Remove Product
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};