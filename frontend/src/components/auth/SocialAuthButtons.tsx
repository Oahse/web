/**
 * Social Authentication Buttons Component
 * Supports Google, Facebook, and TikTok OAuth
 */

// eslint-disable-next-line no-unused-vars
import React, { useEffect } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import FacebookLogin from '@greatsumini/react-facebook-login';
import { FaFacebook, FaTiktok } from 'react-icons/fa';
import { toast } from 'react-hot-toast';
import { apiClient } from '../../apis';

const SocialAuthButtons = ({
  mode = 'login',
  onSuccess,
  onError
}) => {
  const facebookAppId = import.meta.env.VITE_FACEBOOK_APP_ID;
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  const isHttps = window.location.protocol === 'https:';

  // Initialize Facebook SDK
  useEffect(() => {
    if (!facebookAppId || !isHttps) return;

    // Load Facebook SDK
    window.fbAsyncInit = function() {
      window.FB.init({
        appId: facebookAppId,
        cookie: true,
        xfbml: true,
        version: 'v18.0'
      });
    };

    // Load the SDK asynchronously
    (function(d, s, id) {
      var js, fjs = d.getElementsByTagName(s)[0];
      if (d.getElementById(id)) return;
      js = d.createElement(s);
      js.id = id;
      js.src = "https://connect.facebook.net/en_US/sdk.js";
      fjs.parentNode.insertBefore(js, fjs);
    }(document, 'script', 'facebook-jssdk'));
  }, [facebookAppId, isHttps]);

  // Google OAuth Success Handler
  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const response = await apiClient.post('/auth/social/google', {
        credential: credentialResponse.credential,
        mode
      });

      if (response.success) {
        // Store tokens and user data
        localStorage.setItem('banwee_access_token', response.data.access_token);
        localStorage.setItem('banwee_user', JSON.stringify(response.data.user));
        
        toast.success(`Successfully ${mode === 'login' ? 'logged in' : 'registered'} with Google!`);
        onSuccess?.();
      }
    } catch (error) {
      const errorMessage = error.message || `Failed to ${mode} with Google`;
      toast.error(errorMessage);
      onError?.(errorMessage);
    }
  };

  // Google OAuth Error Handler
  const handleGoogleError = () => {
    const errorMessage = `Google ${mode} failed`;
    toast.error(errorMessage);
    onError?.(errorMessage);
  };

  // Facebook OAuth Success Handler
  const handleFacebookSuccess = async (response) => {
    try {
      if (response.accessToken) {
        const apiResponse = await apiClient.post('/auth/social/facebook', {
          access_token: response.accessToken,
          user_id: response.userID,
          mode
        });

        if (apiResponse.success) {
          // Store tokens and user data
          localStorage.setItem('banwee_access_token', apiResponse.data.access_token);
          localStorage.setItem('banwee_user', JSON.stringify(apiResponse.data.user));
          
          toast.success(`Successfully ${mode === 'login' ? 'logged in' : 'registered'} with Facebook!`);
          onSuccess?.();
        }
      }
    } catch (error) {
      const errorMessage = error.message || `Failed to ${mode} with Facebook`;
      toast.error(errorMessage);
      onError?.(errorMessage);
    }
  };

  // Facebook OAuth Error Handler
  const handleFacebookError = () => {
    const errorMessage = `Facebook ${mode} failed`;
    toast.error(errorMessage);
    onError?.(errorMessage);
  };

  // TikTok OAuth Handler (Custom implementation)
  const handleTikTokAuth = async () => {
    try {
      // TikTok OAuth flow - redirect to backend endpoint
      const clientId = import.meta.env.VITE_TIKTOK_CLIENT_ID;
      const redirectUri = `${window.location.origin}/auth/tiktok/callback`;
      const state = Math.random().toString(36).substring(7);
      
      // Store state for verification
      localStorage.setItem('tiktok_oauth_state', state);
      
      const tiktokAuthUrl = `https://www.tiktok.com/auth/authorize/` +
        `?client_key=${clientId}` +
        `&scope=user.info.basic` +
        `&response_type=code` +
        `&redirect_uri=${encodeURIComponent(redirectUri)}` +
        `&state=${state}`;
      
      // Redirect to TikTok OAuth
      window.location.href = tiktokAuthUrl;
    } catch (error) {
      const errorMessage = error.message || `Failed to ${mode} with TikTok`;
      toast.error(errorMessage);
      onError?.(errorMessage);
    }
  };

  return (
    <div className="space-y-3">
      <div className="text-center text-sm text-gray-600 dark:text-gray-400 mb-4">
        Or {mode} with
      </div>

      {/* Show warning if social auth is not properly configured */}
      {(!googleClientId || !facebookAppId) && (
        <div className="text-xs text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded mb-2">
          Social authentication requires configuration. Please add your OAuth credentials to .env file.
        </div>
      )}

      {/* Show HTTPS warning for Facebook */}
      {!isHttps && facebookAppId && (
        <div className="text-xs text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded mb-2">
          Facebook login requires HTTPS. Please use a secure connection.
        </div>
      )}

      {/* Google OAuth */}
      {googleClientId && (
        <GoogleLogin
          onSuccess={handleGoogleSuccess}
          onError={handleGoogleError}
          useOneTap={false}
          theme="outline"
          size="large"
          text={mode === 'login' ? 'signin_with' : 'signup_with'}
        />
      )}

      {/* Facebook OAuth */}
      {facebookAppId && isHttps && (
        <FacebookLogin
          appId={facebookAppId}
          onSuccess={handleFacebookSuccess}
          onFail={handleFacebookError}
          onProfileSuccess={(response) => {
            // Handle profile data if needed
          }}
          className="w-full"
          render={({ onClick }) => (
            <button
              onClick={onClick}
              className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm bg-white dark:bg-gray-800 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              <FaFacebook className="w-5 h-5 text-blue-600 mr-3" />
              {mode === 'login' ? 'Sign in' : 'Sign up'} with Facebook
            </button>
          )}
        />
      )}

      {/* TikTok OAuth */}
      <button
        onClick={handleTikTokAuth}
        className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm bg-white dark:bg-gray-800 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-pink-500 transition-colors"
      >
        <FaTiktok className="w-5 h-5 text-black dark:text-white mr-3" />
        {mode === 'login' ? 'Sign in' : 'Sign up'} with TikTok
      </button>

      {/* Divider */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300 dark:border-gray-600" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400">
            Or continue with email
          </span>
        </div>
      </div>
    </div>
  );
};

export default SocialAuthButtons;