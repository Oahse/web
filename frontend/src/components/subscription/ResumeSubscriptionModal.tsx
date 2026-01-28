import React from 'react';
import { X, PlayIcon } from 'lucide-react';
import { themeClasses, combineThemeClasses, getButtonClasses } from '../../utils/themeClasses';

interface ResumeSubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  subscriptionId: string;
  planName: string;
  nextBillingDate?: string;
  loading?: boolean;
}

export const ResumeSubscriptionModal: React.FC<ResumeSubscriptionModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  subscriptionId,
  planName,
  nextBillingDate,
  loading = false
}) => {
  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleClose}
      />
      
      {/* Modal */}
      <div className={combineThemeClasses(
        'relative w-full max-w-md mx-auto rounded-lg shadow-xl',
        themeClasses.background.surface,
        'transform transition-all'
      )}>
        {/* Header */}
        <div className={combineThemeClasses(
          'flex items-center justify-between p-6 border-b',
          themeClasses.border.light
        )}>
          <div className="flex items-center gap-3">
            <div className={combineThemeClasses(
              'p-2 rounded-full',
              themeClasses.background.success,
              'bg-opacity-10'
            )}>
              <PlayIcon className={combineThemeClasses(
                'w-5 h-5',
                themeClasses.text.success
              )} />
            </div>
            <div>
              <h3 className={combineThemeClasses(
                themeClasses.text.heading,
                'text-lg font-semibold'
              )}>
                Resume Subscription
              </h3>
              <p className={combineThemeClasses(
                themeClasses.text.muted,
                'text-sm'
              )}>
                {planName} Plan
              </p>
            </div>
          </div>
          
          <button
            onClick={handleClose}
            disabled={loading}
            className={combineThemeClasses(
              'p-1 rounded-md transition-colors',
              themeClasses.text.muted,
              themeClasses.interactive.hover,
              loading ? 'opacity-50 cursor-not-allowed' : ''
            )}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="mb-4">
            <p className={combineThemeClasses(
              themeClasses.text.secondary,
              'text-sm mb-3'
            )}>
              Are you sure you want to resume this subscription? Your billing will restart and you'll be charged according to your billing cycle.
            </p>
            
            {nextBillingDate && (
              <div className={combineThemeClasses(
                'p-3 rounded-lg border',
                themeClasses.background.elevated,
                themeClasses.border.success,
                'border-opacity-30'
              )}>
                <p className={combineThemeClasses(
                  themeClasses.text.success,
                  'text-sm font-medium'
                )}>
                  Your next billing date will be: {formatDate(nextBillingDate)}
                </p>
              </div>
            )}
            
            <div className={combineThemeClasses(
              'mt-3 p-3 rounded-lg border',
              themeClasses.background.elevated,
              themeClasses.border.light
            )}>
              <h4 className={combineThemeClasses(
                themeClasses.text.heading,
                'text-sm font-medium mb-2'
              )}>
                What happens when you resume:
              </h4>
              <ul className={combineThemeClasses(
                themeClasses.text.secondary,
                'text-sm space-y-1'
              )}>
                <li>• Your subscription will become active immediately</li>
                <li>• Billing will restart according to your plan</li>
                <li>• You'll have access to all subscription benefits</li>
                <li>• Auto-renewal will be enabled (if previously set)</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className={combineThemeClasses(
          'flex items-center justify-end gap-3 p-6 border-t',
          themeClasses.border.light,
          themeClasses.background.elevated
        )}>
          <button
            onClick={handleClose}
            disabled={loading}
            className={combineThemeClasses(
              getButtonClasses('outline'),
              'px-4 py-2',
              loading ? 'opacity-50 cursor-not-allowed' : ''
            )}
          >
            Cancel
          </button>
          
          <button
            onClick={onConfirm}
            disabled={loading}
            className={combineThemeClasses(
              getButtonClasses('success'),
              'px-4 py-2 flex items-center gap-2',
              loading ? 'opacity-50 cursor-not-allowed' : ''
            )}
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Resuming...
              </>
            ) : (
              <>
                <PlayIcon className="w-4 h-4" />
                Resume Subscription
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};