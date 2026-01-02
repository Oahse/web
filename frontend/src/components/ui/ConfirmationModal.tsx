import React from 'react';
import { XIcon, AlertTriangleIcon } from 'lucide-react';

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  loading?: boolean;
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger',
  loading = false,
}) => {
  if (!isOpen) return null;

  const variantStyles = {
    danger: {
      icon: 'text-error',
      button: 'bg-error hover:bg-error/90 text-white',
      iconBg: 'bg-error/10',
    },
    warning: {
      icon: 'text-warning',
      button: 'bg-warning hover:bg-warning/90 text-white',
      iconBg: 'bg-warning/10',
    },
    info: {
      icon: 'text-primary',
      button: 'bg-primary hover:bg-primary/90 text-white',
      iconBg: 'bg-primary/10',
    },
  };

  const styles = variantStyles[variant];

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
              <div className={`flex-shrink-0 w-10 h-10 rounded-full ${styles.iconBg} flex items-center justify-center mr-3`}>
                <AlertTriangleIcon size={20} className={styles.icon} />
              </div>
              <h3 className="text-lg font-semibold text-main">{title}</h3>
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
            <p className="text-copy text-sm leading-relaxed">{message}</p>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 p-4 border-t border-border-light">
            <button
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-copy border border-border rounded-md hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {cancelText}
            </button>
            <button
              onClick={onConfirm}
              disabled={loading}
              className={`px-4 py-2 text-sm font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center ${styles.button}`}
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Processing...
                </>
              ) : (
                confirmText
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};