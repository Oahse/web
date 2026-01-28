import React, { forwardRef } from 'react';
import { cn } from '../../utils/utils';
import { ChevronDownIcon } from 'lucide-react';
import { themeClasses, combineThemeClasses, getInputClasses } from '../../utils/themeClasses';

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
  variant?: 'default' | 'outline' | 'filled';
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(({
  className,
  label,
  helperText,
  error,
  options,
  size = 'md',
  fullWidth = false,
  variant = 'default',
  ...props
}, ref) => {
  const sizeStyles = {
    sm: 'py-1.5 text-sm',
    md: 'py-2.5 text-sm sm:text-base',
    lg: 'py-3 text-lg'
  };

  const variantStyles = {
    default: getInputClasses(error ? 'error' : 'default'),
    outline: combineThemeClasses(
      'border-2 bg-transparent',
      error ? themeClasses.border.error : themeClasses.border.default,
      'focus:border-primary focus:ring-primary/20'
    ),
    filled: combineThemeClasses(
      themeClasses.background.elevated,
      'border-transparent focus:border-primary focus:ring-primary/20'
    )
  };

  return (
    <div className={combineThemeClasses('relative', fullWidth && 'w-full', !label && 'mb-0')}>
      {label && (
        <label htmlFor={props.id} className={combineThemeClasses(themeClasses.text.primary, 'block text-sm font-medium mb-2')}>
          {label}
        </label>
      )}
      <div className="relative">
        <select 
          ref={ref} 
          className={combineThemeClasses(
            'w-full appearance-none px-4 rounded-lg focus:outline-none focus:ring-2 transition-all duration-200 pr-10',
            sizeStyles[size],
            variantStyles[variant],
            props.disabled && themeClasses.input.disabled,
            className
          )} 
          {...props}
        >
          {options.map(option => (
            <option key={option.value} value={option.value} className={combineThemeClasses(themeClasses.background.surface, themeClasses.text.primary)}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDownIcon 
          size={size === 'sm' ? 14 : size === 'lg' ? 18 : 16} 
          className={combineThemeClasses(
            themeClasses.text.muted,
            'absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none transition-colors'
          )} 
        />
      </div>
      {(helperText || error) && (
        <p className={combineThemeClasses(
          'mt-2 text-xs',
          error ? themeClasses.text.error : themeClasses.text.muted
        )}>
          {error || helperText}
        </p>
      )}
    </div>
  );
});

Select.displayName = 'Select';