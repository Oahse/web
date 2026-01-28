import React from 'react';
import { RefreshCwIcon, XIcon } from 'lucide-react';
import { themeClasses } from '../../lib/themeClasses';

interface AutoRenewToggleProps {
  isEnabled: boolean;
  onToggle: (enabled: boolean) => void;
  showDetails?: boolean;
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
}

export const AutoRenewToggle: React.FC<AutoRenewToggleProps> = ({
  isEnabled,
  onToggle,
  showDetails = true,
  size = 'md',
  disabled = false,
  loading = false
}) => {
  const sizeClasses = {
    sm: 'w-10 h-6',
    md: 'w-12 h-7',
    lg: 'w-14 h-8'
  };

  const thumbSizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  const translateClasses = {
    sm: isEnabled ? 'translate-x-4' : 'translate-x-1',
    md: isEnabled ? 'translate-x-5' : 'translate-x-1',
    lg: isEnabled ? 'translate-x-6' : 'translate-x-1'
  };

  return (
    <div className="flex items-center space-x-3">
      {/* Toggle Switch */}
      <button
        type="button"
        onClick={() => !disabled && !loading && onToggle(!isEnabled)}
        disabled={disabled || loading}
        className={`
          relative inline-flex items-center rounded-full transition-colors duration-200 ease-in-out
          ${sizeClasses[size]}
          ${disabled || loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          ${isEnabled 
            ? 'bg-green-500 hover:bg-green-600' 
            : 'bg-gray-300 hover:bg-gray-400'
          }
          focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2
        `}
        aria-pressed={isEnabled}
        aria-label={`Auto-renew ${isEnabled ? 'enabled' : 'disabled'}`}
      >
        <span
          className={`
            inline-block rounded-full bg-white shadow-lg transform transition-transform duration-200 ease-in-out
            ${thumbSizeClasses[size]}
            ${translateClasses[size]}
          `}
        >
          {loading ? (
            <RefreshCwIcon 
              className={`w-3 h-3 text-gray-400 animate-spin ${
                size === 'sm' ? 'w-2 h-2' : size === 'lg' ? 'w-4 h-4' : 'w-3 h-3'
              }`}
            />
          ) : isEnabled ? (
            <RefreshCwIcon 
              className={`text-green-500 ${
                size === 'sm' ? 'w-2 h-2' : size === 'lg' ? 'w-4 h-4' : 'w-3 h-3'
              }`}
            />
          ) : (
            <XIcon 
              className={`text-gray-400 ${
                size === 'sm' ? 'w-2 h-2' : size === 'lg' ? 'w-4 h-4' : 'w-3 h-3'
              }`}
            />
          )}
        </span>
      </button>

      {/* Label and Details */}
      <div className="flex-1">
        <div className="flex items-center space-x-2">
          <span className={`${themeClasses.text.primary} font-medium text-sm`}>
            Auto-Renew
          </span>
          <span className={`
            px-2 py-1 rounded-full text-xs font-medium
            ${isEnabled 
              ? 'bg-green-100 text-green-800' 
              : 'bg-gray-100 text-gray-600'
            }
          `}>
            {isEnabled ? 'ON' : 'OFF'}
          </span>
        </div>
        
        {showDetails && (
          <p className={`${themeClasses.text.secondary} text-xs mt-1`}>
            {isEnabled 
              ? 'Your subscription will automatically renew at the end of each billing period.'
              : 'Your subscription will not renew automatically. You\'ll need to manually renew it.'
            }
          </p>
        )}
      </div>
    </div>
  );
};