import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-hot-toast';
import { Input } from '../components/forms/Input';
import { Checkbox } from '../components/forms/Checkbox';
import { SkeletonLoginForm } from '../components/ui/SkeletonForm';
import { useSkeleton } from '../hooks/useSkeleton';
import SocialAuth from '../components/auth/SocialAuth';

/**
 * Login component for user authentication.
 * Handles user login, social authentication, and redirection after successful login.
 */
export const Login = ({ isInitialLoading = false }) => {
  // State variables for form fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  // State to toggle password visibility
  const [showPassword, setShowPassword] = useState(false);
  // State for 'Remember Me' checkbox
  const [rememberMe, setRememberMe] = useState(false);
  // State for loading indicator during form submission
  const [loading, setLoading] = useState(false);

  // Auth context for login functionality and authentication status
  const { login, isAuthenticated, isAdmin, isSupplier, redirectPath, setRedirectPath, intendedDestination, setIntendedDestination } = useAuth();
  // Custom hook for managing skeleton loading state
  const skeleton = useSkeleton(isInitialLoading, { showOnMount: false });
  // React Router hooks for navigation and location
  const navigate = useNavigate();
  const location = useLocation();

  /**
   * Determines the appropriate redirect path after successful login.
   * Checks for intended destination, 'redirect' parameter in the URL, or defaults based on user role.
   * @returns {string} The path to redirect to.
   */
  const getRedirectPath = useCallback((user: any) => {
    // First priority: intended destination (from protected route)
    if (intendedDestination && (intendedDestination as any).path !== '/login') {
      const destination = intendedDestination as any;
      // If the action was to add to cart, redirect to cart page
      if (destination.action === 'cart') {
        return '/cart';
      }
      // If the action was to add to wishlist, redirect to wishlist page
      if (destination.action === 'wishlist') {
        return '/account/wishlist';
      }
      // Otherwise redirect to the original path
      return destination.path;
    }
    
    // Second priority: redirect query parameter
    const params = new URLSearchParams(location.search);
    const redirect = params.get('redirect');
    if (redirect) return redirect;
    
    // Third priority: role-based default
    if (user?.role === 'Admin' || user?.role === 'Supplier') return '/admin';
    return '/account';
  }, [location.search, intendedDestination]);

  /**
   * Effect hook to redirect authenticated users.
   * If a user is already logged in, they are redirected to a stored path or a default path.
   */
  useEffect(() => {
    if (isAuthenticated) {
      const path = redirectPath || getRedirectPath({ role: isAdmin ? 'Admin' : isSupplier ? 'Supplier' : 'Customer' });
      navigate(path, { replace: true });
      setRedirectPath(null); // Clear redirect path after navigation
      // Clear intended destination after navigation
      if (intendedDestination) {
        setIntendedDestination(null);
      }
    }
  }, [isAuthenticated]); // Simplified dependencies to prevent infinite loop

  /**
   * Handles the form submission for user login.
   * Performs client-side validation before attempting to log in the user
   * via the authentication context.
   */
  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevent default form submission behavior

    // Client-side validation checks
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }

    try {
      setLoading(true); // Show loading indicator
      // Attempt to log in the user through the AuthContext
      const user = await login(email, password);
      // Navigate to intended destination or default path
      const path = getRedirectPath(user);
      navigate(path, { replace: true });
      // Clear intended destination after navigation
      if (intendedDestination) {
        setIntendedDestination(null);
      }
    } catch (error) {
      // Display error message if login fails
      toast.error('Login failed. Please check your email and password.');
    } finally {
      setLoading(false); // Hide loading indicator
    }
  };

  // Show skeleton loader while initial loading is in progress
  if (skeleton.showSkeleton) {
    return (
      <div className="container mx-auto px-4 py-12 text-copy">
        <div className="max-w-md mx-auto">
          <SkeletonLoginForm />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-12 text-copy">
      <div className="max-w-md mx-auto bg-surface p-8 rounded-lg shadow-sm border border-border-light">
        <h1 className="text-2xl font-bold text-main mb-6 text-center">Login to Your Account</h1>
        <form className="space-y-4" onSubmit={handleSubmit}>
          {/* Email Address Input */}
          <Input
            label="Email Address"
            id="email"
            type="email"
            placeholder="your@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
          {/* Password Input and Forgot Password Link */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label htmlFor="password" className="block text-sm font-medium text-main">
                Password
              </label>
              <Link to="/forgot-password" className="text-xs text-primary hover:underline">
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                className="pr-10"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? (
                  <EyeOff size={18} className="text-copy-lighter" />
                ) : (
                  <Eye size={18} className="text-copy-lighter" />
                )}
              </button>
            </div>
          </div>
          {/* Remember Me Checkbox */}
          <Checkbox
            label="Remember me"
            id="remember"
            checked={rememberMe}
            onChange={() => setRememberMe(!rememberMe)}
          />
          {/* Submit Button */}
          <button
            type="submit"
            className="w-full bg-primary hover:bg-primary-dark text-white py-3 rounded-md transition-colors flex justify-center items-center"
            disabled={loading}>
            {loading ? (
              <span className="flex items-center">
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Logging in...
              </span>
            ) : (
              'Login'
            )}
          </button>
        </form>
        {/* Social Authentication Section */}
        <div className="relative flex items-center justify-center my-6">
          <div className="border-t border-border-light w-full"></div>
          <span className="bg-surface px-3 text-sm text-copy-light absolute">Or continue with</span>
        </div>

        <SocialAuth mode="login" />
        {/* Register Link */}
        <p className="text-center mt-6 text-sm text-copy-light">
          Don&apos;t have an account? <Link to="/register" className="text-primary hover:underline">Register</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;