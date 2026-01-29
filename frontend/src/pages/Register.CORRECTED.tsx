import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, CheckCircle } from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { toast } from 'react-hot-toast';
import { Input } from '../components/forms/Input';
import { Checkbox } from '../components/forms/Checkbox';
import SocialAuth from '../components/auth/SocialAuth';
import { validation } from '../utils/validation';

/**
 * CORRECTED: Register component for user account creation.
 * Fixes: Issue 1.1 - Register parameter mismatch
 * 
 * Changes:
 * - Split 'name' into separate 'firstname' and 'lastname' fields
 * - Pass parameters in correct order to AuthContext.register()
 * - Better form validation and error handling
 */
export const Register = () => {
  // FIXED: Split name into firstname and lastname to match backend schema
  const [firstname, setFirstname] = useState('');
  const [lastname, setLastname] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // State to toggle password visibility
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // State for terms and conditions checkbox
  const [acceptTerms, setAcceptTerms] = useState(false);
  
  // State for loading indicator during form submission
  const [loading, setLoading] = useState(false);

  // Auth context for registration and authentication status
  const { register, isAuthenticated, isAdmin, isSupplier, intendedDestination, setIntendedDestination } = useAuth();
  
  // React Router hooks for navigation and location
  const navigate = useNavigate();
  const location = useLocation();

  /**
   * Effect hook to redirect authenticated users.
   * If a user is already logged in, they are redirected based on their role
   * or a 'redirect' parameter in the URL.
   */
  useEffect(() => {
    if (isAuthenticated) {
      // Determines the appropriate redirect path after successful login/registration
      const getRedirectPath = () => {
        // First priority: intended destination (from protected route)
        if (intendedDestination && (intendedDestination as any).path !== '/register') {
          const destination = intendedDestination as any;
          // Always redirect back to the original page where the user was
          // This allows them to continue their shopping experience
          return destination.path;
        }
        
        // Second priority: redirect query parameter
        const params = new URLSearchParams(location.search);
        const redirect = params.get('redirect');
        if (redirect) return redirect;
        
        // Third priority: role-based default
        if (isAdmin) return '/admin';
        if (isSupplier) return '/account/products';
        return '/';
      };
      const redirectPath = getRedirectPath();
      
      // Show success message based on intended action
      if (intendedDestination && (intendedDestination as any).action === 'cart') {
        toast.success('Registration successful! You can now add items to your cart.');
      } else if (intendedDestination && (intendedDestination as any).action === 'wishlist') {
        toast.success('Registration successful! You can now add items to your wishlist.');
      }
      
      navigate(redirectPath);
      // Clear intended destination after navigation
      if (intendedDestination) {
        setIntendedDestination(null);
      }
    }
  }, [isAuthenticated, navigate, location.search, isAdmin, isSupplier, intendedDestination, setIntendedDestination]);

  /**
   * Handles the form submission for user registration.
   * Performs comprehensive client-side validation before attempting to register the user
   * via the authentication context.
   * 
   * FIXED: Now passes parameters in correct order: firstname, lastname, email, password
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); // Prevent default form submission behavior

    // Comprehensive client-side validation using validation utility
    const firstnameValidation = validation.name(firstname);
    if (!firstnameValidation.valid) {
      toast.error(`First name: ${firstnameValidation.message}`);
      return;
    }

    const lastnameValidation = validation.name(lastname);
    if (!lastnameValidation.valid) {
      toast.error(`Last name: ${lastnameValidation.message}`);
      return;
    }

    const emailValidation = validation.email(email);
    if (!emailValidation.valid) {
      toast.error(emailValidation.message);
      return;
    }

    const passwordValidation = validation.password(password);
    if (!passwordValidation.valid) {
      toast.error(passwordValidation.message);
      return;
    }

    // Check password confirmation
    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    // Check terms acceptance
    if (!acceptTerms) {
      toast.error('Please accept the Terms of Service and Privacy Policy');
      return;
    }

    try {
      setLoading(true); // Show loading indicator
      
      // FIXED: Pass parameters in correct order: firstname, lastname, email, password
      // This now matches AuthContext.register signature:
      // register(firstname: string, lastname: string, email: string, password: string, phone?: string)
      await register(
        firstname.trim(), 
        lastname.trim(), 
        email.toLowerCase().trim(), 
        password
      );
      
      toast.success('Registration successful! Welcome to Banwee Organics.');
      // Navigation to dashboard/home is handled by the useEffect hook based on authentication status
    } catch (error: any) {
      // Display specific error message if available
      const errorMessage = error?.response?.data?.message || error?.message || 'Registration failed. Please try again with different credentials.';
      toast.error(errorMessage);
      setLoading(false); // Hide loading indicator
    }
  };

  return (
    <div className="container mx-auto px-4 py-12 text-copy">
      <div className="max-w-md mx-auto bg-surface p-8 rounded-lg shadow-sm border border-border-light">
        <h1 className="text-2xl font-bold text-main mb-6 text-center">Create an Account</h1>
        <form className="space-y-4" onSubmit={handleSubmit}>
          {/* First Name Input */}
          <div>
            <label className="block text-sm font-medium text-copy mb-2">First Name *</label>
            <Input
              type="text"
              placeholder="Enter your first name"
              value={firstname}
              onChange={(e) => setFirstname(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          {/* Last Name Input */}
          <div>
            <label className="block text-sm font-medium text-copy mb-2">Last Name *</label>
            <Input
              type="text"
              placeholder="Enter your last name"
              value={lastname}
              onChange={(e) => setLastname(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          {/* Email Input */}
          <div>
            <label className="block text-sm font-medium text-copy mb-2">Email *</label>
            <Input
              type="email"
              placeholder="Enter your email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          {/* Password Input */}
          <div>
            <label className="block text-sm font-medium text-copy mb-2">Password *</label>
            <div className="relative">
              <Input
                type={showPassword ? 'text' : 'password'}
                placeholder="Create a strong password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-copy-light hover:text-copy"
                disabled={loading}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            <p className="text-xs text-copy-light mt-1">
              At least 8 characters, including uppercase, lowercase, numbers, and symbols
            </p>
          </div>

          {/* Confirm Password Input */}
          <div>
            <label className="block text-sm font-medium text-copy mb-2">Confirm Password *</label>
            <div className="relative">
              <Input
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-copy-light hover:text-copy"
                disabled={loading}
              >
                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {/* Terms and Conditions */}
          <div className="flex items-start space-x-2 mt-6">
            <Checkbox
              id="terms"
              checked={acceptTerms}
              onChange={(e) => setAcceptTerms(e.target.checked)}
              disabled={loading}
            />
            <label htmlFor="terms" className="text-sm text-copy-light">
              I agree to the{' '}
              <Link to="/terms" className="text-primary hover:underline">
                Terms of Service
              </Link>
              {' '}and{' '}
              <Link to="/privacy" className="text-primary hover:underline">
                Privacy Policy
              </Link>
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full mt-6 bg-primary text-white py-2 rounded-md font-medium hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        {/* Divider */}
        <div className="mt-6 relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-surface text-copy-light">Or continue with</span>
          </div>
        </div>

        {/* Social Auth */}
        <div className="mt-6">
          <SocialAuth />
        </div>

        {/* Login Link */}
        <div className="mt-6 text-center">
          <p className="text-sm text-copy-light">
            Already have an account?{' '}
            <Link to="/login" className="text-primary hover:underline font-medium">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
