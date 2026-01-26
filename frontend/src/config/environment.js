/**
 * Environment Configuration
 * Handles dynamic URL loading based on environment
 */

const environment = import.meta.env.VITE_ENVIRONMENT || 'local';

// Dynamic URL configuration based on environment
const getApiBaseUrl = () => {
  if (environment === 'local' || environment === 'development') {
    const devUrl = import.meta.env.VITE_API_BASE_URL_DEV || import.meta.env.VITE_API_BASE_URL;
    return devUrl ? `${devUrl}/v1` : 'http://localhost:8000/v1';
  }
  const prodUrl = import.meta.env.VITE_API_BASE_URL_PROD || import.meta.env.VITE_API_BASE_URL;
  return prodUrl ? `${prodUrl}/v1` : 'https://api.banwee.com/v1';
};

const getAppUrl = () => {
  if (environment === 'local' || environment === 'development') {
    return import.meta.env.VITE_APP_URL_DEV || import.meta.env.VITE_APP_URL || 'http://localhost:5173';
  }
  return import.meta.env.VITE_APP_URL_PROD || import.meta.env.VITE_APP_URL || 'https://www.banwee.com';
};



export const config = {
  // Environment
  environment,
  isDevelopment: environment === 'local' || environment === 'development',
  isProduction: environment === 'production',
  
  // URLs
  apiBaseUrl: getApiBaseUrl(),
  appUrl: getAppUrl(),
  
  // Application
  appName: import.meta.env.VITE_APP_NAME || 'Banwee',
  appDescription: import.meta.env.VITE_APP_DESCRIPTION || 'Discover premium organic products from Africa',
  
  // Stripe
  stripePublicKey: import.meta.env.VITE_STRIPE_PUBLIC_KEY,
  
  // Social Authentication
  googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID,
  facebookAppId: import.meta.env.VITE_FACEBOOK_APP_ID,
  
  // Feature Flags
  enableCartPersistence: import.meta.env.VITE_ENABLE_CART_PERSISTENCE === 'true',
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  
  // Analytics
  gaTrackingId: import.meta.env.VITE_GA_TRACKING_ID,
  hotjarId: import.meta.env.VITE_HOTJAR_ID,
  
  // Development
  debugMode: import.meta.env.VITE_DEBUG_MODE === 'true',
  logLevel: import.meta.env.VITE_LOG_LEVEL || 'info',
};

// Validation
if (!config.stripePublicKey) {
  console.warn('VITE_STRIPE_PUBLIC_KEY is not set');
}

if (config.isProduction && config.debugMode) {
  console.warn('Debug mode is enabled in production');
}

// Log configuration in development
if (config.isDevelopment) {
  console.log('Environment Configuration:', {
    environment: config.environment,
    apiBaseUrl: config.apiBaseUrl,
    appUrl: config.appUrl,
    debugMode: config.debugMode,
  });
}

export default config;