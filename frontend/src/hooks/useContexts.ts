import { useContext } from 'react';
import { AuthContext } from '../store/AuthContext';
import { WishlistContext } from '../store/WishlistContext';
import { SkeletonContext } from '../store/SkeletonContext';
import { ThemeContext } from '../store/ThemeContext';

/**
 * Consolidated context hooks - all simple context wrappers in one place
 * Note: useCart is exported directly from CartContext to avoid conflicts
 */

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const useWishlist = () => {
  const context = useContext(WishlistContext);
  if (!context) {
    throw new Error('useWishlist must be used within a WishlistProvider');
  }
  return context;
};

export const useSkeletonContext = () => {
  const context = useContext(SkeletonContext);
  if (!context) {
    throw new Error('useSkeletonContext must be used within a SkeletonProvider');
  }
  return context;
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};