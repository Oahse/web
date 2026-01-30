import React, { useEffect, useState, createContext, useContext, useCallback } from 'react';
import { TokenManager, AuthAPI } from '../api';
import { toast } from 'react-hot-toast';

// Define proper types for the context
interface User {
  id: string;
  created_at: string;
  updated_at: string;
  email: string;
  firstname: string;
  lastname: string;
  full_name: string;
  role: string;
  verified: boolean;
  is_active: boolean;
  phone?: string;
  avatar_url?: string;
  preferences: Record<string, any>;
  active: boolean;
}

interface IntendedDestination {
  path: string;
  action?: string | null;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, rememberMe: boolean) => Promise<User>;
  register: (firstname: string, lastname: string, email: string, password: string, phone?: string) => Promise<void>;
  logout: () => Promise<void>;
  verifyEmail: (code: string) => Promise<void>;
  isAdmin: boolean;
  isSupplier: boolean;
  isCustomer: boolean;
  redirectPath: string | null;
  setRedirectPath: (path: string | null) => void;
  intendedDestination: IntendedDestination | null;
  setIntendedDestination: (destination: IntendedDestination | null) => void;
  updateUserPreferences: (preferences: Record<string, any>) => Promise<void>;
  updateUser: (updatedUserData: any) => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [redirectPath, setRedirectPath] = useState(null);
  const [intendedDestination, setIntendedDestination] = useState(null);

  // Transform API user to local user format
  const transformUser = useCallback((apiUser: any): User => ({
    id: apiUser.id,
    created_at: apiUser.created_at,
    updated_at: apiUser.updated_at,
    email: apiUser.email,
    firstname: apiUser.firstname,
    lastname: apiUser.lastname,
    full_name: apiUser.full_name || `${apiUser.firstname} ${apiUser.lastname}`,
    role: apiUser.role,
    verified: apiUser.verified || false,
    is_active: apiUser.is_active ?? true,
    phone: apiUser.phone,
    phone_verified: apiUser.phone_verified,
    avatar_url: apiUser.avatar_url,
    age: apiUser.age,
    gender: apiUser.gender,
    country: apiUser.country,
    language: apiUser.language,
    timezone: apiUser.timezone,
    account_status: apiUser.account_status,
    verification_status: apiUser.verification_status,
    preferences: apiUser.preferences || {},
    // Legacy compatibility
    active: apiUser.is_active ?? true,
  }), []);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (TokenManager.isAuthenticated()) {
        try {
          const response = await AuthAPI.getProfile();
          const transformedUser = transformUser(response.data);
          setUser(transformedUser);
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Auth check failed:', error);
          TokenManager.clearTokens();
          setUser(null);
          setIsAuthenticated(false);
        }
      }
      setIsLoading(false);
    };
    checkAuth();
  }, [transformUser]); // Add transformUser to dependency array

  const login = useCallback(async (email: string, password: string, rememberMe: boolean = false): Promise<User> => {
    setIsLoading(true);
    try {
      console.log('AuthContext: Attempting login...');
      
      // Set the remember me preference BEFORE setting tokens
      TokenManager.setRememberMe(rememberMe);
      
      const response = await AuthAPI.login({ email, password });

      // Save tokens if provided by backend (TokenManager expects tokens directly in response.data)
      TokenManager.setTokens(response.data);

      const transformedUser = transformUser(response.data.user);
      setUser(transformedUser);
      setIsAuthenticated(true);
      toast.success('Login successful!');
      console.log('AuthContext: Login successful, isAuthenticated set to true.');
      
      // Return the user so the login component can handle navigation
      return transformedUser;
    } catch (error) {
      console.error('Login error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      toast.error(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [transformUser]);

  const register = useCallback(async (firstname: string, lastname: string, email: string, password: string, phone?: string): Promise<void> => {
    setIsLoading(true);
    try {
      // Set remember me to true by default for new registrations
      TokenManager.setRememberMe(true);
      
      const response = await AuthAPI.register({ firstname, lastname, email, password, phone });

      // Save tokens if provided by backend (TokenManager expects tokens directly in response.data)
      TokenManager.setTokens(response.data);

      const transformedUser = transformUser(response.data.user);
      setUser(transformedUser);
      setIsAuthenticated(true);
      toast.success('Registration successful!');
    } catch (error) {
      console.error('Registration error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      toast.error(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [transformUser]);

  const logout = useCallback(async () => {
    try {
      await AuthAPI.logout();
    } catch (error) {
      console.warn('Logout API call failed:', error);
    } finally {
      TokenManager.clearTokens();
      setUser(null);
      setIsAuthenticated(false);
      toast.success('Logged out successfully');
    }
  }, []);

  const verifyEmail = useCallback(async (code) => {
    try {
      await AuthAPI.verifyEmail(code);
      if (user) setUser({ ...user, verified: true });
      toast.success('Email verified successfully!');
    } catch (error) {
      console.error('Email verification error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Email verification failed';
      toast.error(errorMessage);
      throw error;
    }
  }, [user]);

  const updateUserPreferences = useCallback(async (preferences: Record<string, any>): Promise<void> => {
    if (!user) return;

    try {
      // Optimistic update
      setUser({
        ...user,
        preferences: { ...user.preferences, ...preferences },
      });

      const response = await AuthAPI.updateProfile({ preferences });
      const transformedUser = transformUser(response.data);
      setUser(transformedUser);

      toast.success('Preferences updated successfully!');
    } catch (error) {
      console.error('Failed to update preferences:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to update preferences';
      toast.error(errorMessage);
      throw error;
    }
  }, [user, transformUser]);

  const updateUser = useCallback((updatedUserData: any): void => {
    if (!user) return;

    // Update user state with new data
    const transformedUser = transformUser(updatedUserData);
    setUser(transformedUser);
    TokenManager.setUser(transformedUser);
  }, [user, transformUser]);

  const setIntendedDestinationWithAction = useCallback((destination: IntendedDestination | null): void => {
    // Don't store login page as intended destination
    if (destination?.path === '/login' || destination?.path === '/register') {
      return;
    }
    setIntendedDestination(destination);
  }, []);

  // Derived roles
  const isAdmin = user?.role === 'Admin';
  const isSupplier = user?.role === 'Supplier';
  const isCustomer = user?.role === 'Customer';

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    verifyEmail,
    isAdmin,
    isSupplier,
    isCustomer,
    redirectPath,
    setRedirectPath,
    intendedDestination,
    setIntendedDestination: setIntendedDestinationWithAction,
    updateUserPreferences,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};