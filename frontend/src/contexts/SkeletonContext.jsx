import React, { createContext, useState } from 'react';





const defaultConfig = {
  animation: 'shimmer',
  minLoadingTime: 300,
  showSkeletonDelay: 100,
  respectReducedMotion: true
};

export const SkeletonContext = createContext(undefined);



export const SkeletonProvider = ({
  children,
  initialConfig = {}
}) => {
  const [config, setConfig] = useState({
    ...defaultConfig,
    ...initialConfig
  });
  
  const [globalLoading, setGlobalLoading] = useState(false);

  const updateConfig = (newConfig) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  };

  // Check for reduced motion preference
  React.useEffect(() => {
    if (config.respectReducedMotion) {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      
      const handleChange = (e) => {
        if (e.matches) {
          updateConfig({ animation: 'pulse' });
        }
      };

      if (mediaQuery.matches) {
        updateConfig({ animation: 'pulse' });
      }

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [config.respectReducedMotion]);

  const value = {
    config,
    updateConfig,
    globalLoading,
    setGlobalLoading
  };

  return (
    <SkeletonContext.Provider value={value}>
      {children}
    </SkeletonContext.Provider>
  );
};