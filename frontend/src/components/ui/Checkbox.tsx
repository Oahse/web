import React, { forwardRef } from 'react';
import { cn } from '../../lib/utils';
import { useTheme } from '../../contexts/ThemeContext';



export const Checkbox = forwardRef(({
  className,
  label,
  helperText,
  error,
  ...props
}, ref) => {
  const { currentTheme } = useTheme();

  return <div className="mb-2">
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input ref={ref} type="checkbox" className={cn('h-4 w-4 rounded border-border text-primary focus:ring-primary/50 bg-surface transition-colors', error && 'border-error', className)} {...props} />
          </div>
          {label && <div className="ml-2 text-sm">
              <label htmlFor={props.id} className={cn('font-medium', error ? 'text-error' : 'text-copy')}>
                {label}
              </label>
              {helperText && <p className="text-copy-lighter">{helperText}</p>}
            </div>}
        </div>
        {error && <p className="mt-1 text-sm text-error">{error}</p>}
      </div>;
});

Checkbox.displayName = 'Checkbox';