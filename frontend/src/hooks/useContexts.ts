import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { CartContext } from '../contexts/CartContext';
import { WishlistContext } from '../contexts/WishlistContext';
import { SkeletonContext } from '../contexts/SkeletonContext';
import { ThemeContext } from '../contexts/ThemeContext';

/**
 * Consolidated context hooks - all simple context wrappers in one place
 * Replaces: useAuth, useCart, useWishlist, useSkeletonContext, useTheme
 */

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider');
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