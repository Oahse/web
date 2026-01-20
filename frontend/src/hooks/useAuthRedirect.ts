import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-hot-toast';

interface UseAuthRedirectOptions {
  requireAuth?: boolean;
  redirectTo?: string;
  message?: string;
  onAuthRequired?: () => void;
}

/**
 * Custom hook to handle authentication redirects
 * @param options Configuration options for the redirect behavior
 * @returns Object with authentication state and redirect function
 */
export const useAuthRedirect = (options: UseAuthRedirectOptions = {}) => {
  const {
    requireAuth = true,
    redirectTo = '/login',
    message = 'Please login to continue',
    onAuthRequired
  } = options;

  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!isLoading && requireAuth && !isAuthenticated) {
      if (message) {
        toast.error(message);
      }
      
      if (onAuthRequired) {
        onAuthRequired();
      } else {
        // Create redirect URL with current path
        const currentPath = location.pathname + location.search;
        const redirectUrl = `${redirectTo}?redirect=${encodeURIComponent(currentPath)}`;
        navigate(redirectUrl, { replace: true });
      }
    }
  }, [isAuthenticated, isLoading, requireAuth, redirectTo, message, navigate, location, onAuthRequired]);

  const redirectToLogin = (customMessage?: string) => {
    if (customMessage) {
      toast.error(customMessage);
    }
    const currentPath = location.pathname + location.search;
    const redirectUrl = `${redirectTo}?redirect=${encodeURIComponent(currentPath)}`;
    navigate(redirectUrl);
  };

  return {
    isAuthenticated,
    isLoading,
    redirectToLogin,
    shouldRedirect: requireAuth && !isLoading && !isAuthenticated
  };
};