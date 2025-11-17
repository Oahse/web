import { useState, useEffect } from 'react';





export const useSkeleton = (
  isLoading,
  options = {}
) => {
  const {
    minLoadingTime = 300,
    maxLoadingTime = 10000,
    showOnMount = true,
    delay = 0
  } = options;

  const [state, setState] = useState({
    isLoading: showOnMount,
    showSkeleton: showOnMount,
    hasError: false,
    hasTimedOut: false
  });

  const [startTime, setStartTime] = useState(null);

  useEffect(() => {
    if (isLoading && !startTime) {
      setStartTime(Date.now());
      
      // Apply delay before showing skeleton
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
        // Ensure minimum loading time
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

  const reset = () => {
    setState({
      isLoading: false,
      showSkeleton: false,
      hasError: false,
      hasTimedOut: false
    });
    setStartTime(null);
  };

  const setError = () => {
    setState(prev => ({
      ...prev,
      hasError: true,
      isLoading: false,
      showSkeleton: false
    }));
    setStartTime(null);
  };

  return {
    ...state,
    reset,
    setError
  };
};

// Hook for managing multiple skeleton states
export const useMultipleSkeleton = (skeletonStates) => {
  const isAnyLoading = Object.values(skeletonStates).some(state => state.isLoading);
  const shouldShowAnySkeleton = Object.values(skeletonStates).some(state => state.showSkeleton);
  const hasAnyError = Object.values(skeletonStates).some(state => state.hasError);

  return {
    states: skeletonStates,
    isAnyLoading,
    shouldShowAnySkeleton,
    hasAnyError,
    resetAll: () => Object.values(skeletonStates).forEach(state => state.reset())
  };
};