import React, { forwardRef } from 'react';
import { cn } from '../../lib/utils';
import { ChevronDownIcon } from 'lucide-react';


export const Select = forwardRef(({
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
  return <div className={cn('mb-4', fullWidth && 'w-full')}>
        {label && <label htmlFor={props.id} className="block text-sm font-medium text-copy mb-1">
            {label}
          </label>}
        <div className="relative">
          <select ref={ref} className={cn('w-full appearance-none px-4 border rounded-md focus:outline-none focus:ring-1 transition-colors pr-10 bg-surface text-copy', sizeStyles[size], error ? 'border-error focus:border-error focus:ring-error/50' : 'border-border focus:border-primary focus:ring-primary/50 hover:border-border-strong', className)} {...props}>
            {options.map(option => <option key={option.value} value={option.value}>
                {option.label}
              </option>)}
          </select>
          <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
            <ChevronDownIcon className="h-5 w-5 text-copy-lighter" />
          </div>
        </div>
        {error ? <p className="mt-1 text-sm text-error">{error}</p> : helperText ? <p className="mt-1 text-sm text-copy-lighter">{helperText}</p> : null}
      </div>;
});
Select.displayName = 'Select';