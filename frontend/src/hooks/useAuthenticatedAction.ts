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
    } catch (error) {
      // If authentication error occurs during action, redirect to login
      if (error instanceof Error && error.message.includes('authenticated')) {
        setIntendedDestination({ path: location.pathname, action: actionType });
        navigate('/login');
        return false;
      }
      throw error;
    }
  };

  return { executeWithAuth, isAuthenticated };
};