import React from 'react';

interface AnimatedLoaderProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'spinner' | 'dots' | 'pulse' | 'wave';
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning';
  text?: string;
  className?: string;
}

export const AnimatedLoader: React.FC<AnimatedLoaderProps> = ({
  size = 'md',
  variant = 'spinner',
  color = 'primary',
  text,
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  const colorClasses = {
    primary: 'border-blue-600 dark:border-blue-400',
    secondary: 'border-gray-600 dark:border-gray-400',
    success: 'border-green-600 dark:border-green-400',
    error: 'border-red-600 dark:border-red-400',
    warning: 'border-yellow-600 dark:border-yellow-400'
  };

  const renderLoader = () => {
    switch (variant) {
      case 'spinner':
        return (
          <div className={`${sizeClasses[size]} border-4 ${colorClasses[color]} border-t-transparent rounded-full animate-spin`} />
        );
      
      case 'dots':
        return (
          <div className="flex space-x-2">
            {[0, 1, 2].map((index) => (
              <div
                key={index}
                className={`${sizeClasses[size]} ${colorClasses[color]} rounded-full animate-bounce`}
                style={{
                  animationDelay: `${index * 0.1}s`,
                  animationDuration: '0.6s'
                }}
              />
            ))}
          </div>
        );
      
      case 'pulse':
        return (
          <div className={`${sizeClasses[size]} ${colorClasses[color]} rounded-full animate-pulse`} />
        );
      
      case 'wave':
        return (
          <div className="flex space-x-1">
            {[0, 1, 2, 3, 4].map((index) => (
              <div
                key={index}
                className={`${sizeClasses[size]} ${colorClasses[color]} rounded-full animate-pulse`}
                style={{
                  animationDelay: `${index * 0.1}s`,
                  animationDuration: '1s'
                }}
              />
            ))}
          </div>
        );
      
      default:
        return <div className={`${sizeClasses[size]} ${colorClasses[color]} rounded-full animate-spin`} />;
    }
  };

  return (
    <div className={`flex flex-col items-center justify-center space-y-4 ${className}`}>
      {renderLoader()}
      {text && (
        <p className="text-sm text-gray-600 dark:text-gray-400 animate-pulse">
          {text}
        </p>
      )}
    </div>
  );
};

// Page transition loader with fade effect
export const PageTransitionLoader: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="relative">
      {isLoading && (
        <div className="fixed inset-0 bg-white dark:bg-gray-900 z-50 flex items-center justify-center">
          <div className="text-center">
            <AnimatedLoader size="xl" variant="spinner" color="primary" />
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400 animate-pulse">
              Loading...
            </p>
          </div>
        </div>
      )}
      <div className={`transition-opacity duration-500 ${isLoading ? 'opacity-0' : 'opacity-100'}`}>
        {children}
      </div>
    </div>
  );
};

// Skeleton card with shimmer effect
export const ShimmerCard: React.FC<{
  lines?: number;
  showAvatar?: boolean;
  showButton?: boolean;
  className?: string;
}> = ({ lines = 3, showAvatar = false, showButton = false, className = '' }) => {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 ${className}`}>
      <div className="animate-pulse">
        {showAvatar && (
          <div className="flex items-center space-x-4 mb-4">
            <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-full" />
            <div className="flex-1">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
            </div>
          </div>
        )}
        
        <div className="space-y-3">
          {Array.from({ length: lines }).map((_, index) => (
            <div
              key={index}
              className="h-4 bg-gray-200 dark:bg-gray-700 rounded"
              style={{
                width: index === lines - 1 ? '70%' : '100%',
                animationDelay: `${index * 0.1}s`
              }}
            />
          ))}
        </div>
        
        {showButton && (
          <div className="mt-6 h-10 bg-gray-200 dark:bg-gray-700 rounded w-full" />
        )}
      </div>
    </div>
  );
};

// Loading overlay for specific components
export const LoadingOverlay: React.FC<{
  isLoading: boolean;
  text?: string;
  variant?: 'spinner' | 'dots' | 'pulse';
  size?: 'sm' | 'md' | 'lg';
}> = ({ isLoading, text, variant = 'spinner', size = 'md' }) => {
  if (!isLoading) return null;

  return (
    <div className="absolute inset-0 bg-white dark:bg-gray-900 bg-opacity-90 dark:bg-opacity-90 flex items-center justify-center z-10">
      <div className="text-center">
        <AnimatedLoader size={size} variant={variant} color="primary" />
        {text && (
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            {text}
          </p>
        )}
      </div>
    </div>
  );
};

// Progress bar loader
export const ProgressBar: React.FC<{
  progress: number;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning';
  showText?: boolean;
  animated?: boolean;
  className?: string;
}> = ({ progress, color = 'primary', showText = true, animated = true, className = '' }) => {
  const colorClasses = {
    primary: 'bg-blue-600 dark:bg-blue-400',
    secondary: 'bg-gray-600 dark:bg-gray-400',
    success: 'bg-green-600 dark:bg-green-400',
    error: 'bg-red-600 dark:bg-red-400',
    warning: 'bg-yellow-600 dark:bg-yellow-400'
  };

  return (
    <div className={`w-full ${className}`}>
      {showText && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">Loading</span>
          <span className="text-sm text-gray-600 dark:text-gray-400">{Math.round(progress)}%</span>
        </div>
      )}
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full ${colorClasses[color]} ${animated ? 'transition-all duration-300 ease-out' : ''}`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};

// Staggered animation for multiple items
export const StaggeredAnimation: React.FC<{
  children: React.ReactNode[];
  staggerDelay?: number;
  className?: string;
}> = ({ children, staggerDelay = 100, className = '' }) => {
  return (
    <div className={className}>
      {React.Children.map(children, (child, index) => (
        <div
          key={index}
          className="animate-fade-in"
          style={{
            animationDelay: `${index * staggerDelay}ms`,
            animationDuration: '500ms',
            animationFillMode: 'both'
          }}
        >
          {child}
        </div>
      ))}
    </div>
  );
};

export default AnimatedLoader;
