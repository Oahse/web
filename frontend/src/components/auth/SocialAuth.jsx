import React from 'react';
import SocialAuthButtons from './SocialAuthButtons';



const SocialAuth = ({ mode = 'login', onSuccess, onError }) => {
  return <SocialAuthButtons mode={mode} onSuccess={onSuccess} onError={onError} />;
};

export default SocialAuth;