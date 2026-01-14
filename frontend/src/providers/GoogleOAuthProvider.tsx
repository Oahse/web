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

  if (!clientId) {
    console.warn('Google OAuth Client ID not found. Social login with Google will not work.');
    return <>{children}</>;
  }

  return (
    <GoogleProvider clientId={clientId}>
      {children}
    </GoogleProvider>
  );
};

export default GoogleOAuthProvider;