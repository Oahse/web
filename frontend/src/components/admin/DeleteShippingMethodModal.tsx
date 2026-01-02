import React from 'react';
import { TruckIcon, AlertTriangleIcon, XIcon } from 'lucide-react';

interface ShippingMethod {
  id: string;
  name: string;
  description: string;
  price: number;
  estimated_days: number;
  is_active: boolean;
}

interface DeleteShippingMethodModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  method: ShippingMethod | null;
  loading?: boolean;
}

export const DeleteShippingMethodModal: React.FC<DeleteShippingMethodModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  method,
  loading = false,
}) => {
  if (!isOpen || !method) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-surface rounded-lg shadow-xl max-w-md w-full mx-auto border border-border-light">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border-light">
            <div className="flex items-center">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-error/10 flex items-center justify-center mr-3">
                <AlertTriangleIcon size={20} className="text-error" />
              </div>
              <h3 className="text-lg font-semibold text-main">Delete Shipping Method</h3>
            </div>
            <button
              onClick={onClose}
              className="text-copy-light hover:text-copy p-1 rounded-md hover:bg-surface-hover"
              disabled={loading}
            >
              <XIcon size={20} />
            </button>
          </div>

          {/* Content */}
          <div className="p-4">
            {/* Method Preview */}
            <div className="bg-surface-hover rounded-lg p-3 mb-4 border border-border-light">
              <div className="flex items-center mb-2">
                <TruckIcon size={18} className="text-primary mr-2" />
                <span className="font-medium text-main">{method.name}</span>
                <span className={`ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                  method.is_active
                    ? 'bg-success/10 text-success'
                    : 'bg-error/10 text-error'
                }`}>
                  {method.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <p className="text-sm text-copy-light mb-1">{method.description}</p>
              <div className="flex items-center text-sm text-copy">
                <span className="font-medium">${method.price}</span>
                <span className="mx-2">•</span>
                <span>{method.estimated_days} {method.estimated_days === 1 ? 'day' : 'days'}</span>
              </div>
            </div>

            {/* Warning Message */}
            <div className="bg-warning/10 border border-warning/20 rounded-lg p-3 mb-4">
              <div className="flex items-start">
                <AlertTriangleIcon size={16} className="text-warning mt-0.5 mr-2 flex-shrink-0" />
                <div className="text-sm">
                  <p className="font-medium text-warning mb-1">Warning</p>
                  <p className="text-copy">
                    This action cannot be undone. Deleting this shipping method may affect:
                  </p>
                  <ul className="mt-2 text-copy-light text-xs list-disc list-inside space-y-1">
                    <li>Existing orders that use this shipping method</li>
                    <li>Customer checkout options</li>
                    <li>Historical shipping data</li>
                  </ul>
                </div>
              </div>
            </div>

            <p className="text-copy text-sm">
              Are you sure you want to delete <strong>"{method.name}"</strong>?
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 p-4 border-t border-border-light">
            <button
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-copy border border-border rounded-md hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              onClick={onConfirm}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium bg-error hover:bg-error/90 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Deleting...
                </>
              ) : (
                'Delete Method'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};