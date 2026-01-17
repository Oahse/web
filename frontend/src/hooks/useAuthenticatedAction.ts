import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

/**
 * Hook to handle actions that require authentication
 * Redirects to login if user is not authenticated, with intended action stored
 */
export const useAuthenticatedAction = () => {
  const { isAuthenticated, setIntendedDestination } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const executeWithAuth = async (action: () => Promise<boolean>, actionType: 'cart' | 'wishlist' = 'cart') => {
    if (!isAuthenticated) {
      // Store the intended destination with action type
      setIntendedDestination({ path: location.pathname, action: actionType });
      navigate('/login');
      return false;
    }

    try {
      return await action();
    } catch (error: any) {
      // If authentication error occurs during action, redirect to login
      // Check for 401 status code or authentication-related error messages
      const is401Error = error?.statusCode === 401 || error?.code === '401';
      const isAuthError = error?.message?.toLowerCase().includes('authenticated') || 
                         error?.message?.toLowerCase().includes('unauthorized') ||
                         error?.message?.toLowerCase().includes('token');
      
      if (is401Error || isAuthError) {
        setIntendedDestination({ path: location.pathname, action: actionType });
        navigate('/login');
        return false;
      }
      throw error;
    }
  };

  return { executeWithAuth, isAuthenticated };
};