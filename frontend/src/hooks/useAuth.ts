import { useContext } from 'react';
import { AuthContext } from '../store/AuthContext';
import { toast } from 'react-hot-toast';

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  const executeWithAuth = async (
    action: () => Promise<void> | void,
    actionName: string = 'perform this action'
  ) => {
    if (!context.isAuthenticated) {
      context.setIntendedDestination({
        path: window.location.pathname,
        action: actionName
      });
      toast.error(`Please log in to ${actionName}`);
      window.location.href = '/login';
      return;
    }

    try {
      await action();
    } catch (error) {
      console.error(`Failed to ${actionName}:`, error);
      toast.error(`Failed to ${actionName}`);
      throw error;
    }
  };

  return {
    ...context,
    executeWithAuth
  };
};

// Alias for backward compatibility
export const useAuthRedirect = useAuth;
export const useAuthenticatedAction = useAuth;
