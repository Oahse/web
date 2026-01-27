/**
 * Google OAuth Provider Wrapper
 * Provides Google OAuth context to the entire app
 */


import { GoogleOAuthProvider as GoogleProvider } from '@react-oauth/google';
import { ReactNode } from 'react';

interface GoogleOAuthProviderProps {
  children: ReactNode;
}

const GoogleOAuthProvider = ({ children }: GoogleOAuthProviderProps) => {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  // Check if client ID is valid (not empty, not placeholder, and follows Google's format)
  const isValidClientId = clientId && 
    clientId !== 'placeholder_google_client_id' && 
    clientId.includes('.googleusercontent.com');

  if (!isValidClientId) {
    console.warn('Google OAuth Client ID not found or invalid. Social login with Google will not work.');
    return <>{children}</>;
  }

  return (
    <GoogleProvider clientId={clientId}>
      {children}
    </GoogleProvider>
  );
};

export default GoogleOAuthProvider;