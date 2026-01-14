import React from 'react';
import SocialAuthButtons from './SocialAuthButtons';

// Define proper TypeScript interfaces
interface User {
  id: string;
  email: string;
  firstname: string;
  lastname: string;
  role: string;
}

interface AuthError {
  message: string;
  code?: string;
}

interface SocialAuthProps {
  mode?: 'login' | 'register';
  onSuccess?: (user: User) => void;
  onError?: (error: AuthError) => void;
}

const SocialAuth: React.FC<SocialAuthProps> = ({ mode = 'login', onSuccess, onError }) => {
  return <SocialAuthButtons mode={mode} onSuccess={onSuccess} onError={onError} />;
};

export default SocialAuth;