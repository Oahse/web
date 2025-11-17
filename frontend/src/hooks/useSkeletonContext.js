import { useContext } from 'react';
import { SkeletonContext } from '../contexts/SkeletonContext';

export const useSkeletonContext = () => {
  const context = useContext(SkeletonContext);
  if (!context) {
    throw new Error('useSkeletonContext must be used within a SkeletonProvider');
  }
  return context;
};
