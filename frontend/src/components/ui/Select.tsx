import React, { forwardRef } from 'react';
import { cn } from '../../lib/utils';
import { ChevronDownIcon } from 'lucide-react';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  label?: React.ReactNode;
  helperText?: string;
  error?: string;
  options: SelectOption[];
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(({
  className,
  label,
  helperText,
  error,
  options,
  size = 'md',
  fullWidth = false,
  ...props
}, ref) => {
  const sizeStyles = {
    sm: 'py-1 text-sm',
    md: 'py-2',
    lg: 'py-3 text-lg'
  };

  return (
    <div className={cn('mb-4', fullWidth && 'w-full')}>
      {label && (
        <label htmlFor={props.id} className="block text-sm font-medium text-copy mb-1">
          {label}
        </label>
      )}
      <div className="relative">
        <select 
          ref={ref} 
          className={cn(
            'w-full appearance-none px-4 border rounded-md focus:outline-none focus:ring-1 transition-colors pr-10 bg-surface text-copy', 
            sizeStyles[size], 
            error 
              ? 'border-error focus:border-error focus:ring-error/50' 
              : 'border-border focus:border-primary focus:ring-primary/50 hover:border-border-strong', 
            className
          )} 
          {...props}
        >
          {options.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDownIcon 
          size={16} 
          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-copy-light pointer-events-none" 
        />
      </div>
      {(helperText || error) && (
        <p className={cn('mt-1 text-xs', error ? 'text-error' : 'text-copy-light')}>
          {error || helperText}
        </p>
      )}
    </div>
  );
});

Select.displayName = 'Select';