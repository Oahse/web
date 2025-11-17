import { useEffect, useState, createContext, useContext } from 'react';
import { TokenManager, AuthAPI } from '../apis';
import { toast } from 'react-hot-toast';

export const AuthContext = createContext(undefined);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [redirectPath, setRedirectPath] = useState(null);

  // Transform API user to local user format
  const transformUser = (apiUser) => ({
    id: apiUser.id,
    created_at: apiUser.created_at,
    updated_at: apiUser.updated_at,
    email: apiUser.email,
    firstname: apiUser.firstname,
    lastname: apiUser.lastname,
    full_name: apiUser.full_name || `${apiUser.firstname} ${apiUser.lastname}`,
    role: apiUser.role,
    verified: apiUser.verified || false,
    active: apiUser.active ?? true,
    phone: apiUser.phone,
    avatar_url: apiUser.avatar_url,
    preferences: apiUser.preferences || {},
  });

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
  }, []);

  const login = async (email, password) => {
    setIsLoading(true);
    try {
      const response = await AuthAPI.login({ email, password });

      // Save tokens if provided by backend
      if (response.data?.tokens) {
        TokenManager.setTokens(response.data.tokens);
      }

      const transformedUser = transformUser(response.data.user);
      setUser(transformedUser);
      setIsAuthenticated(true);
      toast.success('Login successful!');
    } catch (error) {
      console.error('Login error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      toast.error(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (firstname, lastname, email, password, phone) => {
    setIsLoading(true);
    try {
      const response = await AuthAPI.register({ firstname, lastname, email, password, phone });

      if (response.data?.tokens) {
        TokenManager.setTokens(response.data.tokens);
      }

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
  };

  const logout = async () => {
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
  };

  const verifyEmail = async (code) => {
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
  };

  const updateUserPreferences = async (preferences) => {
    if (!user) return;

    try {
      // Optimistic update
      // const previousUser = user;
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
  };

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
    updateUserPreferences,
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