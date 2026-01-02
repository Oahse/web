import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  id?: string;
  className?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  id,
  className,
  type = 'text',
  ...props
}) => {
  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-copy">
          {label}
        </label>
      )}
      <input
        type={type}
        id={id}
        className={`w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-1 bg-surface text-copy transition-colors ${error ? 'border-error focus:ring-error/50' : 'border-border focus:ring-primary/50 hover:border-border-strong'} ${className || ''}`}
        {...props}
      />
      {error && <p className="text-sm text-error mt-1">{error}</p>}
      {helperText && !error && <p className="text-sm text-copy-lighter mt-1">{helperText}</p>}
    </div>
  );
};
