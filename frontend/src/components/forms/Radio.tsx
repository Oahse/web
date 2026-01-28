import React from 'react';
import { cn } from '../../utils/utils';



export const Radio = ({
  label,
  error,
  id,
  className,
  ...props
}) => {
  return (
    <div className="flex items-center">
      <input
        type="radio"
        id={id}
        className={cn(
          'h-4 w-4 text-primary focus:ring-primary/50 border-border rounded-full bg-surface transition-colors',
          className
        )}
        {...props}
      />
      {label && (
        <label htmlFor={id} className="ml-2 block text-sm text-copy-light">
          {label}
        </label>
      )}
      {error && <p className="text-sm text-error mt-1">{error}</p>}
    </div>
  );
};
