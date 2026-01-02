import React from 'react';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  id?: string;
  className?: string;
}

export const Textarea: React.FC<TextareaProps> = ({
  label,
  error,
  id,
  className,
  ...props
}) => {
  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-copy">
          {label}
        </label>
      )}
      <textarea
        id={id}
        className={`w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-1 bg-surface text-copy transition-colors resize-vertical ${error ? 'border-error focus:ring-error/50' : 'border-border focus:ring-primary/50 hover:border-border-strong'} ${className || ''}`}
        {...props}
      />
      {error && <p className="text-sm text-error mt-1">{error}</p>}
    </div>
  );
};
