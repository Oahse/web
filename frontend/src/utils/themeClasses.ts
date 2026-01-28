// Theme utility classes for consistent styling across components

export interface ThemeClasses {
  primary: string;
  secondary: string;
  success: string;
  warning: string;
  error: string;
  info: string;
  light: string;
  dark: string;
}

export const themeClasses: ThemeClasses = {
  primary: 'bg-blue-600 hover:bg-blue-700 text-white',
  secondary: 'bg-gray-600 hover:bg-gray-700 text-white',
  success: 'bg-green-600 hover:bg-green-700 text-white',
  warning: 'bg-yellow-600 hover:bg-yellow-700 text-white',
  error: 'bg-red-600 hover:bg-red-700 text-white',
  info: 'bg-cyan-600 hover:bg-cyan-700 text-white',
  light: 'bg-gray-100 hover:bg-gray-200 text-gray-900',
  dark: 'bg-gray-900 hover:bg-gray-800 text-white',
};

export function combineThemeClasses(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

export function getInputClasses(error?: string): string {
  const baseClasses = 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500';
  const errorClasses = error ? 'border-red-500 focus:ring-red-500' : 'border-gray-300';
  return combineThemeClasses(baseClasses, errorClasses);
}

export function getButtonClasses(
  variant: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'light' | 'dark' = 'primary',
  size: 'sm' | 'md' | 'lg' = 'md',
  disabled = false
): string {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-200';
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : '';
  
  return combineThemeClasses(
    baseClasses,
    themeClasses[variant],
    sizeClasses[size],
    disabledClasses
  );
}

export function getCardClasses(elevated = false): string {
  const baseClasses = 'bg-white rounded-lg border border-gray-200';
  const elevatedClasses = elevated ? 'shadow-lg' : 'shadow-sm';
  return combineThemeClasses(baseClasses, elevatedClasses);
}

export function getTextClasses(
  variant: 'primary' | 'secondary' | 'muted' | 'success' | 'warning' | 'error' = 'primary',
  size: 'xs' | 'sm' | 'base' | 'lg' | 'xl' = 'base'
): string {
  const variantClasses = {
    primary: 'text-gray-900',
    secondary: 'text-gray-700',
    muted: 'text-gray-500',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600',
  };

  const sizeClasses = {
    xs: 'text-xs',
    sm: 'text-sm',
    base: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
  };

  return combineThemeClasses(variantClasses[variant], sizeClasses[size]);
}