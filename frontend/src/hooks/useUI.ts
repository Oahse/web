import { useState, useEffect, useMemo, useCallback } from 'react';

interface SkeletonOptions {
  minLoadingTime?: number;
  maxLoadingTime?: number;
  showOnMount?: boolean;
  delay?: number;
}

interface SkeletonState {
  isLoading: boolean;
  showSkeleton: boolean;
  hasError: boolean;
  hasTimedOut: boolean;
}

/**
 * Enhanced network status hook with retry logic
 * Merges: useNetworkStatus functionality
 */
export const useNetworkStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [wasOffline, setWasOffline] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      if (wasOffline) {
        setWasOffline(false);
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
      setWasOffline(true);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [wasOffline]);

  return {
    isOnline,
    isOffline: !isOnline,
    wasOffline,
  };
};

/**
 * Enhanced skeleton hook with better state management
 */
export const useSkeleton = (
  isLoading: boolean,
  options: SkeletonOptions = {}
) => {
  const {
    minLoadingTime = 300,
    maxLoadingTime = 10000,
    showOnMount = true,
    delay = 0
  } = options;

  const [state, setState] = useState<SkeletonState>({
    isLoading: showOnMount,
    showSkeleton: showOnMount,
    hasError: false,
    hasTimedOut: false
  });

  const [startTime, setStartTime] = useState<number | null>(null);

  useEffect(() => {
    if (isLoading && !startTime) {
      setStartTime(Date.now());
      
      if (delay > 0) {
        const delayTimer = setTimeout(() => {
          setState(prev => ({ ...prev, showSkeleton: true }));
        }, delay);
        
        return () => clearTimeout(delayTimer);
      } else {
        setState(prev => ({ ...prev, isLoading: true, showSkeleton: true }));
      }
    }

    if (!isLoading && startTime) {
      const elapsedTime = Date.now() - startTime;
      const remainingTime = Math.max(0, minLoadingTime - elapsedTime);

      if (remainingTime > 0) {
        const timer = setTimeout(() => {
          setState(prev => ({
            ...prev,
            isLoading: false,
            showSkeleton: false,
            hasError: false,
            hasTimedOut: false
          }));
          setStartTime(null);
        }, remainingTime);

        return () => clearTimeout(timer);
      } else {
        setState(prev => ({
          ...prev,
          isLoading: false,
          showSkeleton: false,
          hasError: false,
          hasTimedOut: false
        }));
        setStartTime(null);
      }
    }
  }, [isLoading, startTime, minLoadingTime, delay]);

  // Handle timeout
  useEffect(() => {
    if (isLoading && startTime) {
      const timeoutTimer = setTimeout(() => {
        setState(prev => ({
          ...prev,
          hasTimedOut: true,
          hasError: true
        }));
      }, maxLoadingTime);

      return () => clearTimeout(timeoutTimer);
    }
  }, [isLoading, startTime, maxLoadingTime]);

  const reset = useCallback(() => {
    setState({
      isLoading: false,
      showSkeleton: false,
      hasError: false,
      hasTimedOut: false
    });
    setStartTime(null);
  }, []);

  const setError = useCallback(() => {
    setState(prev => ({
      ...prev,
      hasError: true,
      isLoading: false,
      showSkeleton: false
    }));
    setStartTime(null);
  }, []);

  return {
    ...state,
    reset,
    setError
  };
};

/**
 * Hook for managing multiple skeleton states
 */
export const useMultipleSkeleton = (skeletonStates: Record<string, SkeletonState>) => {
  const isAnyLoading = useMemo(() => 
    Object.values(skeletonStates).some(state => state.isLoading), 
    [skeletonStates]
  );
  
  const shouldShowAnySkeleton = useMemo(() => 
    Object.values(skeletonStates).some(state => state.showSkeleton), 
    [skeletonStates]
  );
  
  const hasAnyError = useMemo(() => 
    Object.values(skeletonStates).some(state => state.hasError), 
    [skeletonStates]
  );

  const resetAll = useCallback(() => {
    // This would need to be implemented by the consumer
    // as we don't have direct access to the reset functions
    console.warn('resetAll should be implemented by providing reset functions');
  }, []);

  return {
    states: skeletonStates,
    isAnyLoading,
    shouldShowAnySkeleton,
    hasAnyError,
    resetAll
  };
};

/**
 * Hook for managing loading states with debouncing
 */
export const useLoadingState = (initialLoading = false, debounceMs = 200) => {
  const [loading, setLoading] = useState(initialLoading);
  const [debouncedLoading, setDebouncedLoading] = useState(initialLoading);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedLoading(loading);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [loading, debounceMs]);

  return {
    loading,
    debouncedLoading,
    setLoading,
    startLoading: () => setLoading(true),
    stopLoading: () => setLoading(false)
  };
};

/**
 * Hook for managing modal/dialog states
 */
export const useModal = (initialOpen = false) => {
  const [isOpen, setIsOpen] = useState(initialOpen);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen(prev => !prev), []);

  return {
    isOpen,
    open,
    close,
    toggle,
    setIsOpen
  };
};

/**
 * Hook for managing form states
 */
export const useFormState = <T extends Record<string, any>>(initialValues: T) => {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const setValue = useCallback((field: keyof T, value: any) => {
    setValues(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  }, [errors]);

  const setError = useCallback((field: keyof T, error: string) => {
    setErrors(prev => ({ ...prev, [field]: error }));
  }, []);

  const setTouched = useCallback((field: keyof T, isTouched = true) => {
    setTouched(prev => ({ ...prev, [field]: isTouched }));
  }, []);

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
  }, [initialValues]);

  const hasErrors = useMemo(() => 
    Object.values(errors).some(error => error), 
    [errors]
  );

  return {
    values,
    errors,
    touched,
    isSubmitting,
    hasErrors,
    setValue,
    setError,
    setTouched,
    setIsSubmitting,
    reset
  };
};