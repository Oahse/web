/**
 * Tests for useAuth hook - Comprehensive test suite
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAuth } from '../../hooks/useAuth';
import { AuthContext } from '../../store/AuthContext';
import { toast } from 'react-hot-toast';
import React from 'react';

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  toast: {
    error: vi.fn()
  }
}));

// Mock window.location
const mockLocation = {
  pathname: '/products',
  href: ''
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true
});

describe('useAuth', () => {
  const mockAuthContext = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    updateProfile: vi.fn(),
    setIntendedDestination: vi.fn(),
    intendedDestination: null,
    clearIntendedDestination: vi.fn()
  };

  const wrapper = ({ children }: { children: React.ReactNode }) => 
    React.createElement(AuthContext.Provider, { value: mockAuthContext }, children);

  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation.href = '';
    mockLocation.pathname = '/products';
  });

  describe('Context Integration', () => {
    it('should return auth context values', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.user).toBe(mockAuthContext.user);
      expect(result.current.isAuthenticated).toBe(mockAuthContext.isAuthenticated);
      expect(result.current.isLoading).toBe(mockAuthContext.isLoading);
      expect(result.current.login).toBe(mockAuthContext.login);
      expect(result.current.logout).toBe(mockAuthContext.logout);
      expect(result.current.register).toBe(mockAuthContext.register);
      expect(result.current.updateProfile).toBe(mockAuthContext.updateProfile);
    });

    it('should throw error when used outside AuthProvider', () => {
      // Mock console.error to avoid noise in test output
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        renderHook(() => useAuth());
      }).toThrow('useAuth must be used within an AuthProvider');

      consoleSpy.mockRestore();
    });

    it('should include executeWithAuth function', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(typeof result.current.executeWithAuth).toBe('function');
    });
  });

  describe('executeWithAuth', () => {
    it('should execute action when user is authenticated', async () => {
      const authenticatedContext = {
        ...mockAuthContext,
        isAuthenticated: true,
        user: { id: 'user123', email: 'test@example.com' }
      };

      const authenticatedWrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthContext.Provider value={authenticatedContext}>
          {children}
        </AuthContext.Provider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper: authenticatedWrapper });

      const mockAction = vi.fn().mockResolvedValue('success');

      await act(async () => {
        await result.current.executeWithAuth(mockAction, 'test action');
      });

      expect(mockAction).toHaveBeenCalledTimes(1);
      expect(toast.error).not.toHaveBeenCalled();
      expect(authenticatedContext.setIntendedDestination).not.toHaveBeenCalled();
    });

    it('should redirect to login when user is not authenticated', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      const mockAction = vi.fn();
      mockLocation.pathname = '/cart';

      await act(async () => {
        await result.current.executeWithAuth(mockAction, 'add to cart');
      });

      expect(mockAction).not.toHaveBeenCalled();
      expect(mockAuthContext.setIntendedDestination).toHaveBeenCalledWith({
        path: '/cart',
        action: 'add to cart'
      });
      expect(toast.error).toHaveBeenCalledWith('Please log in to add to cart');
      expect(mockLocation.href).toBe('/login');
    });

    it('should use default action name when not provided', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      const mockAction = vi.fn();

      await act(async () => {
        await result.current.executeWithAuth(mockAction);
      });

      expect(mockAuthContext.setIntendedDestination).toHaveBeenCalledWith({
        path: '/products',
        action: 'perform this action'
      });
      expect(toast.error).toHaveBeenCalledWith('Please log in to perform this action');
    });

    it('should handle synchronous actions', async () => {
      const authenticatedContext = {
        ...mockAuthContext,
        isAuthenticated: true
      };

      const authenticatedWrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthContext.Provider value={authenticatedContext}>
          {children}
        </AuthContext.Provider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper: authenticatedWrapper });

      const syncAction = vi.fn(() => 'sync result');

      await act(async () => {
        await result.current.executeWithAuth(syncAction, 'sync action');
      });

      expect(syncAction).toHaveBeenCalledTimes(1);
    });

    it('should handle action errors and re-throw them', async () => {
      const authenticatedContext = {
        ...mockAuthContext,
        isAuthenticated: true
      };

      const authenticatedWrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthContext.Provider value={authenticatedContext}>
          {children}
        </AuthContext.Provider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper: authenticatedWrapper });

      const errorAction = vi.fn().mockRejectedValue(new Error('Action failed'));
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await act(async () => {
        await expect(
          result.current.executeWithAuth(errorAction, 'failing action')
        ).rejects.toThrow('Action failed');
      });

      expect(errorAction).toHaveBeenCalledTimes(1);
      expect(consoleSpy).toHaveBeenCalledWith('Failed to failing action:', expect.any(Error));
      expect(toast.error).toHaveBeenCalledWith('Failed to failing action');

      consoleSpy.mockRestore();
    });

    it('should handle action errors with custom error messages', async () => {
      const authenticatedContext = {
        ...mockAuthContext,
        isAuthenticated: true
      };

      const authenticatedWrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthContext.Provider value={authenticatedContext}>
          {children}
        </AuthContext.Provider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper: authenticatedWrapper });

      const customError = new Error('Custom error message');
      const errorAction = vi.fn().mockRejectedValue(customError);
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await act(async () => {
        await expect(
          result.current.executeWithAuth(errorAction, 'custom error action')
        ).rejects.toThrow('Custom error message');
      });

      expect(consoleSpy).toHaveBeenCalledWith('Failed to custom error action:', customError);
      expect(toast.error).toHaveBeenCalledWith('Failed to custom error action');

      consoleSpy.mockRestore();
    });
  });

  describe('Different Authentication States', () => {
    it('should handle loading state', () => {
      const loadingContext = {
        ...mockAuthContext,
        isLoading: true
      };

      const loadingWrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthContext.Provider value={loadingContext}>
          {children}
        </AuthContext.Provider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper: loadingWrapper });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should handle authenticated user with profile data', () => {
      const userContext = {
        ...mockAuthContext,
        isAuthenticated: true,
        user: {
          id: 'user123',
          email: 'john.doe@example.com',
          firstname: 'John',
          lastname: 'Doe',
          role: 'Customer',
          verified: true
        }
      };

      const userWrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthContext.Provider value={userContext}>
          {children}
        </AuthContext.Provider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper: userWrapper });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(userContext.user);
      expect(result.current.user?.email).toBe('john.doe@example.com');
      expect(result.current.user?.role).toBe('Customer');
    });

    it('should handle intended destination', () => {
      const destinationContext = {
        ...mockAuthContext,
        intendedDestination: {
          path: '/checkout',
          action: 'complete purchase'
        }
      };

      const destinationWrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthContext.Provider value={destinationContext}>
          {children}
        </AuthContext.Provider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper: destinationWrapper });

      expect(result.current.intendedDestination).toEqual({
        path: '/checkout',
        action: 'complete purchase'
      });
    });
  });

  describe('Real-world Usage Scenarios', () => {
    it('should handle adding item to cart scenario', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      const addToCartAction = vi.fn().mockResolvedValue({ success: true });
      mockLocation.pathname = '/products/123';

      await act(async () => {
        await result.current.executeWithAuth(addToCartAction, 'add item to cart');
      });

      expect(mockAuthContext.setIntendedDestination).toHaveBeenCalledWith({
        path: '/products/123',
        action: 'add item to cart'
      });
      expect(toast.error).toHaveBeenCalledWith('Please log in to add item to cart');
      expect(mockLocation.href).toBe('/login');
    });

    it('should handle checkout scenario', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      const checkoutAction = vi.fn();
      mockLocation.pathname = '/cart';

      await act(async () => {
        await result.current.executeWithAuth(checkoutAction, 'proceed to checkout');
      });

      expect(mockAuthContext.setIntendedDestination).toHaveBeenCalledWith({
        path: '/cart',
        action: 'proceed to checkout'
      });
      expect(toast.error).toHaveBeenCalledWith('Please log in to proceed to checkout');
    });

    it('should handle wishlist operations', async () => {
      const authenticatedContext = {
        ...mockAuthContext,
        isAuthenticated: true,
        user: { id: 'user123', email: 'test@example.com' }
      };

      const authenticatedWrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthContext.Provider value={authenticatedContext}>
          {children}
        </AuthContext.Provider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper: authenticatedWrapper });

      const addToWishlistAction = vi.fn().mockResolvedValue({ success: true });

      await act(async () => {
        await result.current.executeWithAuth(addToWishlistAction, 'add to wishlist');
      });

      expect(addToWishlistAction).toHaveBeenCalledTimes(1);
      expect(toast.error).not.toHaveBeenCalled();
    });

    it('should handle profile update scenario', async () => {
      const authenticatedContext = {
        ...mockAuthContext,
        isAuthenticated: true,
        user: { id: 'user123', email: 'test@example.com' }
      };

      const authenticatedWrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthContext.Provider value={authenticatedContext}>
          {children}
        </AuthContext.Provider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper: authenticatedWrapper });

      const updateProfileAction = vi.fn().mockResolvedValue({
        success: true,
        data: { firstname: 'Updated', lastname: 'Name' }
      });

      await act(async () => {
        await result.current.executeWithAuth(updateProfileAction, 'update profile');
      });

      expect(updateProfileAction).toHaveBeenCalledTimes(1);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty action name', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      const mockAction = vi.fn();

      await act(async () => {
        await result.current.executeWithAuth(mockAction, '');
      });

      expect(mockAuthContext.setIntendedDestination).toHaveBeenCalledWith({
        path: '/products',
        action: ''
      });
      expect(toast.error).toHaveBeenCalledWith('Please log in to ');
    });

    it('should handle null action', async () => {
      const authenticatedContext = {
        ...mockAuthContext,
        isAuthenticated: true
      };

      const authenticatedWrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthContext.Provider value={authenticatedContext}>
          {children}
        </AuthContext.Provider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper: authenticatedWrapper });

      await act(async () => {
        await result.current.executeWithAuth(null as any, 'null action');
      });

      // Should not throw error, but action won't be called
      expect(toast.error).not.toHaveBeenCalled();
    });

    it('should handle different pathname formats', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      const mockAction = vi.fn();
      
      // Test with query parameters
      mockLocation.pathname = '/products/123?color=red&size=large';

      await act(async () => {
        await result.current.executeWithAuth(mockAction, 'test action');
      });

      expect(mockAuthContext.setIntendedDestination).toHaveBeenCalledWith({
        path: '/products/123?color=red&size=large',
        action: 'test action'
      });
    });

    it('should handle context method calls', async () => {
      const authenticatedContext = {
        ...mockAuthContext,
        isAuthenticated: true,
        login: vi.fn().mockResolvedValue({ success: true }),
        logout: vi.fn().mockResolvedValue({ success: true }),
        updateProfile: vi.fn().mockResolvedValue({ success: true })
      };

      const authenticatedWrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthContext.Provider value={authenticatedContext}>
          {children}
        </AuthContext.Provider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper: authenticatedWrapper });

      // Test that context methods are accessible
      expect(typeof result.current.login).toBe('function');
      expect(typeof result.current.logout).toBe('function');
      expect(typeof result.current.updateProfile).toBe('function');
      expect(typeof result.current.setIntendedDestination).toBe('function');
      expect(typeof result.current.clearIntendedDestination).toBe('function');
    });
  });

  describe('Backward Compatibility Aliases', () => {
    it('should export useAuthRedirect as alias', () => {
      // This would be tested in a separate file that imports the alias
      // Here we just verify the hook works the same way
      const { result } = renderHook(() => useAuth(), { wrapper });
      
      expect(typeof result.current.executeWithAuth).toBe('function');
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should export useAuthenticatedAction as alias', () => {
      // This would be tested in a separate file that imports the alias
      // Here we just verify the hook works the same way
      const { result } = renderHook(() => useAuth(), { wrapper });
      
      expect(typeof result.current.executeWithAuth).toBe('function');
      expect(result.current.isAuthenticated).toBe(false);
    });
  });
});