import React from 'react';
import { XIcon, CheckCircleIcon, InfoIcon, AlertCircleIcon } from 'lucide-react';

interface NotificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  message: string;
  variant?: 'success' | 'info' | 'warning';
  autoClose?: boolean;
  autoCloseDelay?: number;
}

export const NotificationModal: React.FC<NotificationModalProps> = ({
  isOpen,
  onClose,
  title,
  message,
  variant = 'info',
  autoClose = false,
  autoCloseDelay = 3000,
}) => {
  React.useEffect(() => {
    if (isOpen && autoClose) {
      const timer = setTimeout(() => {
        onClose();
      }, autoCloseDelay);
      return () => clearTimeout(timer);
    }
  }, [isOpen, autoClose, autoCloseDelay, onClose]);

  if (!isOpen) return null;

  const variantStyles = {
    success: {
      icon: CheckCircleIcon,
      iconColor: 'text-green-600',
      iconBg: 'bg-green-100',
      borderColor: 'border-green-200',
    },
    info: {
      icon: InfoIcon,
      iconColor: 'text-blue-600',
      iconBg: 'bg-blue-100',
      borderColor: 'border-blue-200',
    },
    warning: {
      icon: AlertCircleIcon,
      iconColor: 'text-yellow-600',
      iconBg: 'bg-yellow-100',
      borderColor: 'border-yellow-200',
    },
  };

  const styles = variantStyles[variant];
  const IconComponent = styles.icon;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className={`relative bg-surface rounded-lg shadow-xl max-w-md w-full mx-auto border ${styles.borderColor}`}>
          {/* Header */}
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center">
              <div className={`flex-shrink-0 w-10 h-10 rounded-full ${styles.iconBg} flex items-center justify-center mr-3`}>
                <IconComponent size={20} className={styles.iconColor} />
              </div>
              <div>
                {title && <h3 className="text-lg font-semibold text-main">{title}</h3>}
                <p className="text-copy text-sm leading-relaxed">{message}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-copy-light hover:text-copy p-1 rounded-md hover:bg-surface-hover"
            >
              <XIcon size={20} />
            </button>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end p-4 border-t border-border-light">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary-dark"
            >
              OK
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};