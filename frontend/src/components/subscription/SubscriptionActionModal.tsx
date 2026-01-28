import React, { useState } from 'react';
import { X, TrashIcon, PauseIcon, PlayIcon, AlertTriangleIcon } from 'lucide-react';
import { themeClasses, combineThemeClasses, getButtonClasses } from '../../utils/themeClasses';

export type SubscriptionAction = 'cancel' | 'pause' | 'resume';

interface SubscriptionActionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason?: string) => void;
  action: SubscriptionAction;
  subscriptionId: string;
  planName: string;
  loading?: boolean;
}

const actionConfig = {
  cancel: {
    title: 'Cancel Subscription',
    icon: TrashIcon,
    iconColor: 'text-red-500',
    iconBg: 'bg-red-100',
    buttonStyle: 'danger',
    buttonText: 'Cancel Subscription',
    loadingText: 'Cancelling...',
    requiresConfirmation: true,
    confirmationText: 'CANCEL',
    warning: 'This action cannot be undone',
    description: 'Once cancelled, you\'ll lose access to all subscription benefits immediately. Your current billing cycle will complete, but no future charges will occur.',
    reasonPlaceholder: 'e.g., Too expensive, not using enough, found better alternative...',
    reasonLabel: 'Why are you cancelling? (optional)',
    reasonHelp: 'Your feedback helps us improve'
  },
  pause: {
    title: 'Pause Subscription',
    icon: PauseIcon,
    iconColor: 'text-yellow-500',
    iconBg: 'bg-yellow-100',
    buttonStyle: 'warning',
    buttonText: 'Pause Subscription',
    loadingText: 'Pausing...',
    requiresConfirmation: false,
    warning: 'Your current billing cycle will complete',
    description: 'Your subscription will be paused and you won\'t be charged until you resume it. You can resume at any time from your subscription management page.',
    reasonPlaceholder: 'e.g., Going on vacation, temporary financial constraints, trying other options...',
    reasonLabel: 'Please provide a reason for pausing (optional):',
    reasonHelp: 'This helps us improve our service'
  },
  resume: {
    title: 'Resume Subscription',
    icon: PlayIcon,
    iconColor: 'text-green-500',
    iconBg: 'bg-green-100',
    buttonStyle: 'primary',
    buttonText: 'Resume Subscription',
    loadingText: 'Resuming...',
    requiresConfirmation: false,
    description: 'Your subscription will be resumed and billing will continue on your next scheduled date.',
    reasonPlaceholder: 'e.g., Ready to continue, issue resolved...',
    reasonLabel: 'Any additional notes? (optional):',
    reasonHelp: 'Help us understand your experience'
  }
};

export const SubscriptionActionModal: React.FC<SubscriptionActionModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  action,
  subscriptionId,
  planName,
  loading = false
}) => {
  const [reason, setReason] = useState('');
  const [confirmText, setConfirmText] = useState('');

  const config = actionConfig[action];
  const Icon = config.icon;

  const handleConfirm = () => {
    onConfirm(reason.trim() || undefined);
    setReason('');
    setConfirmText('');
  };

  const handleClose = () => {
    if (!loading) {
      setReason('');
      setConfirmText('');
      onClose();
    }
  };

  const isConfirmValid = !config.requiresConfirmation || 
    confirmText.toLowerCase() === config.confirmationText?.toLowerCase();

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
              config.iconBg
            )}>
              <Icon className={combineThemeClasses(
                'w-5 h-5',
                config.iconColor
              )} />
            </div>
            <div>
              <h3 className={combineThemeClasses(
                themeClasses.text.heading,
                'text-lg font-semibold'
              )}>
                {config.title}
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
            {/* Warning for destructive actions */}
            {action === 'cancel' && (
              <div className={combineThemeClasses(
                'p-4 rounded-lg border-2 border-dashed mb-4',
                'border-red-300 bg-red-50'
              )}>
                <div className="flex items-start gap-3">
                  <AlertTriangleIcon className="w-5 h-5 mt-0.5 flex-shrink-0 text-red-500" />
                  <div>
                    <h4 className="font-semibold text-sm mb-1 text-red-800">
                      {config.warning}
                    </h4>
                    <p className="text-sm text-red-700">
                      {config.description}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Info for non-destructive actions */}
            {action !== 'cancel' && (
              <>
                <p className={combineThemeClasses(
                  themeClasses.text.secondary,
                  'text-sm mb-3'
                )}>
                  {config.description}
                </p>
                
                {config.warning && (
                  <div className={combineThemeClasses(
                    'p-3 rounded-lg border mb-4',
                    themeClasses.background.elevated,
                    'border-yellow-300 border-opacity-30'
                  )}>
                    <p className="text-sm font-medium text-yellow-700">
                      Note: {config.warning}
                    </p>
                  </div>
                )}
              </>
            )}

            {/* Reason input */}
            <div className="mb-4">
              <label 
                htmlFor="action-reason"
                className={combineThemeClasses(
                  themeClasses.text.primary,
                  'block text-sm font-medium mb-2'
                )}
              >
                {config.reasonLabel}
              </label>
              <textarea
                id="action-reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                disabled={loading}
                placeholder={config.reasonPlaceholder}
                rows={3}
                maxLength={500}
                className={combineThemeClasses(
                  'w-full px-3 py-2 border rounded-md resize-none transition-colors',
                  themeClasses.background.surface,
                  themeClasses.border.light,
                  themeClasses.text.primary,
                  'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                  'placeholder:text-gray-400',
                  loading ? 'opacity-50 cursor-not-allowed' : ''
                )}
              />
              <div className="flex justify-between items-center mt-1">
                <p className={combineThemeClasses(
                  themeClasses.text.muted,
                  'text-xs'
                )}>
                  {config.reasonHelp}
                </p>
                <span className={combineThemeClasses(
                  themeClasses.text.muted,
                  'text-xs'
                )}>
                  {reason.length}/500
                </span>
              </div>
            </div>

            {/* Confirmation input for destructive actions */}
            {config.requiresConfirmation && (
              <div className="mb-4">
                <label 
                  htmlFor="confirm-action"
                  className={combineThemeClasses(
                    themeClasses.text.primary,
                    'block text-sm font-medium mb-2'
                  )}
                >
                  Type "{config.confirmationText}" to confirm {action}
                </label>
                <input
                  id="confirm-action"
                  type="text"
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  disabled={loading}
                  placeholder={`Type ${config.confirmationText} here`}
                  className={combineThemeClasses(
                    'w-full px-3 py-2 border rounded-md transition-colors',
                    themeClasses.background.surface,
                    isConfirmValid ? 'border-green-300' : themeClasses.border.light,
                    themeClasses.text.primary,
                    'focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent',
                    'placeholder:text-gray-400',
                    loading ? 'opacity-50 cursor-not-allowed' : ''
                  )}
                />
              </div>
            )}
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
            {action === 'cancel' ? 'Keep Subscription' : 'Cancel'}
          </button>
          
          <button
            onClick={handleConfirm}
            disabled={loading || !isConfirmValid}
            className={combineThemeClasses(
              getButtonClasses(config.buttonStyle as any),
              'px-4 py-2 flex items-center gap-2',
              (loading || !isConfirmValid) ? 'opacity-50 cursor-not-allowed' : ''
            )}
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                {config.loadingText}
              </>
            ) : (
              <>
                <Icon className="w-4 h-4" />
                {config.buttonText}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};