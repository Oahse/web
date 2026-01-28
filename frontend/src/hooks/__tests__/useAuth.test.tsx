import { renderHook, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useAuth } from '../useAuth';
import { AuthProvider } from '../../store/AuthContext';
import { ReactNode } from 'react';

// Mock the AuthAPI and TokenManager
vi.mock('../../apis', () => ({
  TokenManager: {
    isAuthenticated: vi.fn(),
    getToken: vi.fn(),
    setTokens: vi.fn(),
    clearTokens: vi.fn(),
    setUser: vi.fn(),
  },
  AuthAPI: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getProfile: vi.fn(),
    verifyEmail: vi.fn(),
    updateProfile: vi.fn(),
  },
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

import { TokenManager, AuthAPI } from '../../apis';
import { toast } from 'react-hot-toast';

const mockTokenManager = TokenManager as any;
const mockAuthAPI = AuthAPI as any;
const mockToast = toast as any;

// Test wrapper component
const createWrapper = () => {
  return ({ children }: { children: ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  );
};

describe('useAuth Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTokenManager.isAuthenticated.mockReturnValue(false);
    mockTokenManager.getToken.mockReturnValue(null);
  });

  describe('Authentication State Management', () => {
    it('provides initial unauthenticated state', () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });

    it('initializes with authenticated user when token exists', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        firstname: 'John',
        lastname: 'Doe',
        role: 'Customer',
        verified: true,
      };

      mockTokenManager.isAuthenticated.mockReturnValue(true);
      mockAuthAPI.getProfile.mockResolvedValue({ data: mockUser });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
        expect(result.current.user).toEqual(expect.objectContaining({
          id: '1',
          email: 'test@example.com',
          firstname: 'John',
          lastname: 'Doe',
          role: 'Customer',
        }));
      });
    });

    it('handles authentication check failure', async () => {
      mockTokenManager.isAuthenticated.mockReturnValue(true);
      mockAuthAPI.getProfile.mockRejectedValue(new Error('Token expired'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(false);
        expect(result.current.user).toBeNull();
        expect(mockTokenManager.clearTokens).toHaveBeenCalled();
      });
    });
  });

  describe('Login Flow', () => {
    it('handles successful login', async () => {
      const loginData = { email: 'test@example.com', password: 'password123' };
      const mockResponse = {
        data: {
          user: {
            id: '1',
            email: 'test@example.com',
            firstname: 'John',
            lastname: 'Doe',
            role: 'Customer',
            verified: true,
          },
          tokens: {
            access_token: 'access-token',
            refresh_token: 'refresh-token',
          },
        },
      };

      mockAuthAPI.login.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      const user = await result.current.login(loginData.email, loginData.password);

      expect(mockAuthAPI.login).toHaveBeenCalledWith(loginData);
      expect(mockTokenManager.setTokens).toHaveBeenCalledWith(mockResponse.data.tokens);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(expect.objectContaining({
        id: '1',
        email: 'test@example.com',
      }));
      expect(mockToast.success).toHaveBeenCalledWith('Login successful!');
      expect(user).toEqual(expect.objectContaining({ id: '1' }));
    });

    it('handles login failure', async () => {
      const loginData = { email: 'test@example.com', password: 'wrongpassword' };
      const mockError = new Error('Invalid credentials');

      mockAuthAPI.login.mockRejectedValue(mockError);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await expect(result.current.login(loginData.email, loginData.password))
        .rejects.toThrow('Invalid credentials');

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(mockToast.error).toHaveBeenCalledWith('Invalid credentials');
    });

    it('handles login without tokens in response', async () => {
      const loginData = { email: 'test@example.com', password: 'password123' };
      const mockResponse = {
        data: {
          user: {
            id: '1',
            email: 'test@example.com',
            firstname: 'John',
            lastname: 'Doe',
            role: 'Customer',
            verified: true,
          },
        },
      };

      mockAuthAPI.login.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await result.current.login(loginData.email, loginData.password);

      expect(mockTokenManager.setTokens).not.toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(true);
    });
  });

  describe('Registration Flow', () => {
    it('handles successful registration', async () => {
      const registerData = {
        firstname: 'John',
        lastname: 'Doe',
        email: 'test@example.com',
        password: 'password123',
        phone: '+1234567890',
      };
      const mockResponse = {
        data: {
          user: {
            id: '1',
            email: 'test@example.com',
            firstname: 'John',
            lastname: 'Doe',
            role: 'Customer',
            verified: false,
          },
          tokens: {
            access_token: 'access-token',
            refresh_token: 'refresh-token',
          },
        },
      };

      mockAuthAPI.register.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await result.current.register(
        registerData.firstname,
        registerData.lastname,
        registerData.email,
        registerData.password,
        registerData.phone
      );

      expect(mockAuthAPI.register).toHaveBeenCalledWith(registerData);
      expect(mockTokenManager.setTokens).toHaveBeenCalledWith(mockResponse.data.tokens);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(expect.objectContaining({
        id: '1',
        email: 'test@example.com',
        verified: false,
      }));
      expect(mockToast.success).toHaveBeenCalledWith('Registration successful!');
    });

    it('handles registration failure', async () => {
      const registerData = {
        firstname: 'John',
        lastname: 'Doe',
        email: 'invalid-email',
        password: 'weak',
        phone: '+1234567890',
      };
      const mockError = new Error('Validation failed');

      mockAuthAPI.register.mockRejectedValue(mockError);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await expect(result.current.register(
        registerData.firstname,
        registerData.lastname,
        registerData.email,
        registerData.password,
        registerData.phone
      )).rejects.toThrow('Validation failed');

      expect(result.current.isAuthenticated).toBe(false);
      expect(mockToast.error).toHaveBeenCalledWith('Validation failed');
    });
  });

  describe('Logout Flow', () => {
    it('handles successful logout', async () => {
      // Set up authenticated state first
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        firstname: 'John',
        lastname: 'Doe',
        role: 'Customer',
        verified: true,
      };

      mockTokenManager.isAuthenticated.mockReturnValue(true);
      mockAuthAPI.getProfile.mockResolvedValue({ data: mockUser });
      mockAuthAPI.logout.mockResolvedValue({});

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      // Wait for initial auth check
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      // Perform logout
      await result.current.logout();

      expect(mockAuthAPI.logout).toHaveBeenCalled();
      expect(mockTokenManager.clearTokens).toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(mockToast.success).toHaveBeenCalledWith('Logged out successfully');
    });

    it('handles logout API failure gracefully', async () => {
      mockAuthAPI.logout.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await result.current.logout();

      expect(mockTokenManager.clearTokens).toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(mockToast.success).toHaveBeenCalledWith('Logged out successfully');
    });
  });

  describe('Token Refresh and Error Handling', () => {
    it('clears tokens when profile fetch fails', async () => {
      mockTokenManager.isAuthenticated.mockReturnValue(true);
      mockAuthAPI.getProfile.mockRejectedValue(new Error('Unauthorized'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(mockTokenManager.clearTokens).toHaveBeenCalled();
        expect(result.current.isAuthenticated).toBe(false);
        expect(result.current.user).toBeNull();
      });
    });

    it('handles email verification', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        firstname: 'John',
        lastname: 'Doe',
        role: 'Customer',
        verified: false,
      };

      mockTokenManager.isAuthenticated.mockReturnValue(true);
      mockAuthAPI.getProfile.mockResolvedValue({ data: mockUser });
      mockAuthAPI.verifyEmail.mockResolvedValue({});

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.user?.verified).toBe(false);
      });

      await result.current.verifyEmail('verification-code');

      expect(mockAuthAPI.verifyEmail).toHaveBeenCalledWith('verification-code');
      expect(result.current.user?.verified).toBe(true);
      expect(mockToast.success).toHaveBeenCalledWith('Email verified successfully!');
    });

    it('handles email verification failure', async () => {
      const mockError = new Error('Invalid verification code');
      mockAuthAPI.verifyEmail.mockRejectedValue(mockError);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await expect(result.current.verifyEmail('invalid-code'))
        .rejects.toThrow('Invalid verification code');

      expect(mockToast.error).toHaveBeenCalledWith('Invalid verification code');
    });
  });

  describe('User Preferences and Profile Updates', () => {
    it('updates user preferences successfully', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        firstname: 'John',
        lastname: 'Doe',
        role: 'Customer',
        verified: true,
        preferences: { theme: 'light' },
      };

      mockTokenManager.isAuthenticated.mockReturnValue(true);
      mockAuthAPI.getProfile.mockResolvedValue({ data: mockUser });
      mockAuthAPI.updateProfile.mockResolvedValue({
        data: { ...mockUser, preferences: { theme: 'dark' } }
      });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.user?.preferences?.theme).toBe('light');
      });

      await result.current.updateUserPreferences({ theme: 'dark' });

      expect(mockAuthAPI.updateProfile).toHaveBeenCalledWith({
        preferences: { theme: 'dark' }
      });
      expect(result.current.user?.preferences?.theme).toBe('dark');
      expect(mockToast.success).toHaveBeenCalledWith('Preferences updated successfully!');
    });

    it('handles preference update failure', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        firstname: 'John',
        lastname: 'Doe',
        role: 'Customer',
        verified: true,
        preferences: { theme: 'light' },
      };

      mockTokenManager.isAuthenticated.mockReturnValue(true);
      mockAuthAPI.getProfile.mockResolvedValue({ data: mockUser });
      mockAuthAPI.updateProfile.mockRejectedValue(new Error('Update failed'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.user).toBeTruthy();
      });

      await expect(result.current.updateUserPreferences({ theme: 'dark' }))
        .rejects.toThrow('Update failed');

      expect(mockToast.error).toHaveBeenCalledWith('Update failed');
    });

    it('updates user data directly', () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      const updatedUserData = {
        id: '1',
        email: 'updated@example.com',
        firstname: 'Jane',
        lastname: 'Smith',
        role: 'Admin',
        verified: true,
      };

      result.current.updateUser(updatedUserData);

      expect(result.current.user).toEqual(expect.objectContaining({
        id: '1',
        email: 'updated@example.com',
        firstname: 'Jane',
        lastname: 'Smith',
        role: 'Admin',
      }));
      expect(mockTokenManager.setUser).toHaveBeenCalled();
    });
  });

  describe('Role-based Properties', () => {
    it('correctly identifies admin users', async () => {
      const mockUser = {
        id: '1',
        email: 'admin@example.com',
        firstname: 'Admin',
        lastname: 'User',
        role: 'Admin',
        verified: true,
      };

      mockTokenManager.isAuthenticated.mockReturnValue(true);
      mockAuthAPI.getProfile.mockResolvedValue({ data: mockUser });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isAdmin).toBe(true);
        expect(result.current.isSupplier).toBe(false);
        expect(result.current.isCustomer).toBe(false);
      });
    });

    it('correctly identifies supplier users', async () => {
      const mockUser = {
        id: '1',
        email: 'supplier@example.com',
        firstname: 'Supplier',
        lastname: 'User',
        role: 'Supplier',
        verified: true,
      };

      mockTokenManager.isAuthenticated.mockReturnValue(true);
      mockAuthAPI.getProfile.mockResolvedValue({ data: mockUser });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isAdmin).toBe(false);
        expect(result.current.isSupplier).toBe(true);
        expect(result.current.isCustomer).toBe(false);
      });
    });

    it('correctly identifies customer users', async () => {
      const mockUser = {
        id: '1',
        email: 'customer@example.com',
        firstname: 'Customer',
        lastname: 'User',
        role: 'Customer',
        verified: true,
      };

      mockTokenManager.isAuthenticated.mockReturnValue(true);
      mockAuthAPI.getProfile.mockResolvedValue({ data: mockUser });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isAdmin).toBe(false);
        expect(result.current.isSupplier).toBe(false);
        expect(result.current.isCustomer).toBe(true);
      });
    });
  });

  describe('Navigation and Redirect Handling', () => {
    it('manages redirect paths', () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      result.current.setRedirectPath('/dashboard');
      expect(result.current.redirectPath).toBe('/dashboard');
    });

    it('manages intended destinations', () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      result.current.setIntendedDestination('/profile', 'edit');
      expect(result.current.intendedDestination).toEqual({
        path: '/profile',
        action: 'edit',
      });
    });

    it('does not store login/register pages as intended destinations', () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      result.current.setIntendedDestination('/login');
      expect(result.current.intendedDestination).toBeNull();

      result.current.setIntendedDestination('/register');
      expect(result.current.intendedDestination).toBeNull();
    });
  });

  describe('Error Handling Edge Cases', () => {
    it('throws error when used outside AuthProvider', () => {
      expect(() => {
        renderHook(() => useAuth());
      }).toThrow('useAuth must be used within an AuthProvider');
    });

    it('handles non-Error objects in login', async () => {
      mockAuthAPI.login.mockRejectedValue('String error');

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await expect(result.current.login('test@example.com', 'password'))
        .rejects.toBe('String error');

      expect(mockToast.error).toHaveBeenCalledWith('Login failed');
    });

    it('handles non-Error objects in registration', async () => {
      mockAuthAPI.register.mockRejectedValue('String error');

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await expect(result.current.register('John', 'Doe', 'test@example.com', 'password', '+1234567890'))
        .rejects.toBe('String error');

      expect(mockToast.error).toHaveBeenCalledWith('Registration failed');
    });

    it('handles non-Error objects in email verification', async () => {
      mockAuthAPI.verifyEmail.mockRejectedValue('String error');

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await expect(result.current.verifyEmail('code'))
        .rejects.toBe('String error');

      expect(mockToast.error).toHaveBeenCalledWith('Email verification failed');
    });

    it('handles non-Error objects in preference updates', async () => {
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        firstname: 'John',
        lastname: 'Doe',
        role: 'Customer',
        verified: true,
        preferences: {},
      };

      mockTokenManager.isAuthenticated.mockReturnValue(true);
      mockAuthAPI.getProfile.mockResolvedValue({ data: mockUser });
      mockAuthAPI.updateProfile.mockRejectedValue('String error');

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.user).toBeTruthy();
      });

      await expect(result.current.updateUserPreferences({ theme: 'dark' }))
        .rejects.toBe('String error');

      expect(mockToast.error).toHaveBeenCalledWith('Failed to update preferences');
    });
  });
});