import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { AdminAPI } from '../../apis/admin';
import { toast } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { ImageUploader } from '../../components/ui/ImageUploader';

/**
 * AdminNewUser component allows administrators to create new user accounts.
 * It includes fields for user details, role selection, and avatar upload.
 */
export const AdminNewUser = () => {
  const navigate = useNavigate();
  // State for loading indicator during form submission
  const [loading, setLoading] = useState(false);
  // State for storing and displaying any errors during form submission
  const [error, setError] = useState(null);

  // useForm hook from react-hook-form for form management and validation
  const {
    register, // Function to register inputs with React Hook Form
    handleSubmit, // Function to handle form submission with validation
    setValue, // Function to manually set form input values
    formState: { errors }, // Object containing form errors
  } = useForm({
    // Default values for the form fields
    defaultValues: {
      email: '',
      firstname: '',
      lastname: '',
      password: '',
      role: 'Customer',
      verified: false,
      active: true,
      phone: '',
      avatar_url: '',
    },
  });

  /**
   * Handles the form submission. This function is called when the form passes validation.
   * It attempts to create a new user via the AdminAPI and navigates to the user list on success.
   * @param {object} data - The form data containing new user details.
   */
  const onSubmit = async (data) => {
    setLoading(true); // Show loading indicator
    setError(null); // Clear any previous errors
    try {
      await AdminAPI.createUser(data); // Call the API to create the user
      toast.success('User created successfully!'); // Show success toast
      navigate('/admin/users'); // Navigate to the user management page
    } catch (err) {
      console.error('AdminNewUser createUser error:', err); // Log the error
      setError(err); // Set error state
      toast.error(`Failed to create user: ${err.message}`); // Show error toast
    } finally {
      setLoading(false); // Hide loading indicator
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8 mb-8">
      <h1 className="text-2xl font-bold text-main mb-4">Create New User</h1>
      <div className="bg-surface rounded-lg shadow-sm p-6 border border-border-light">
        {/* Display general error message if any */}
        {error && (
          <div className="bg-error/10 text-error p-3 rounded-md mb-4">
            {typeof error.message === 'string'
              ? error.message
              : 'An unexpected error occurred.'}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          {/* Email Input Field */}
          <div className="mb-4">
            <label htmlFor="email" className="block text-sm font-medium text-copy-light mb-1">
              Email
            </label>
            <input
              type="email"
              id="email"
              className="w-full px-3 py-2 border border-border rounded-md"
              {...register('email')}
            />
            {errors.email && <div className="text-error text-xs mt-1">{errors.email.message}</div>}
          </div>

          {/* First Name Input Field */}
          <div className="mb-4">
            <label htmlFor="firstname" className="block text-sm font-medium text-copy-light mb-1">
              First Name
            </label>
            <input
              type="text"
              id="firstname"
              className="w-full px-3 py-2 border border-border rounded-md"
              {...register('firstname')}
            />
            {errors.firstname && <div className="text-error text-xs mt-1">{errors.firstname.message}</div>}
          </div>

          {/* Last Name Input Field */}
          <div className="mb-4">
            <label htmlFor="lastname" className="block text-sm font-medium text-copy-light mb-1">
              Last Name
            </label>
            <input
              type="text"
              id="lastname"
              className="w-full px-3 py-2 border border-border rounded-md"
              {...register('lastname')}
            />
            {errors.lastname && <div className="text-error text-xs mt-1">{errors.lastname.message}</div>}
          </div>

          {/* Password Input Field */}
          <div className="mb-4">
            <label htmlFor="password" className="block text-sm font-medium text-copy-light mb-1">
              Password
            </label>
            <input
              type="password"
              id="password"
              className="w-full px-3 py-2 border border-border rounded-md"
              {...register('password')}
              autoComplete="new-password"
            />
            {errors.password && <div className="text-error text-xs mt-1">{errors.password.message}</div>}
          </div>

          {/* Role Selection Dropdown */}
          <div className="mb-4">
            <label htmlFor="role" className="block text-sm font-medium text-copy-light mb-1">
              Role
            </label>
            <select
              id="role"
              className="w-full px-3 py-2 border border-border rounded-md"
              {...register('role')}
            >
              <option value="Customer">Customer</option>
              <option value="Supplier">Supplier</option>
              <option value="Admin">Admin</option>
            </select>
            {errors.role && <div className="text-error text-xs mt-1">{errors.role.message}</div>}
          </div>

          {/* Verified Checkbox */}
          <div className="mb-4 flex items-center">
            <input type="checkbox" id="verified" {...register('verified')} className="mr-2" />
            <label htmlFor="verified" className="text-sm">Verified</label>
          </div>

          {/* Active Checkbox */}
          <div className="mb-4 flex items-center">
            <input type="checkbox" id="active" {...register('active')} className="mr-2" />
            <label htmlFor="active" className="text-sm">Active</label>
          </div>

          {/* Phone Input Field */}
          <div className="mb-4">
            <label htmlFor="phone" className="block text-sm font-medium text-copy-light mb-1">Phone</label>
            <input
              type="tel"
              id="phone"
              className="w-full px-3 py-2 border border-border rounded-md"
              {...register('phone')}
            />
            {errors.phone && <div className="text-error text-xs mt-1">{errors.phone.message}</div>}
          </div>

          {/* Avatar URL Uploader */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-copy-light mb-1">Avatar</label>
            <ImageUploader
              onUploadSuccess={(url) => setValue('avatar_url', url)}
              currentImageUrl={''} // You might want to pass an initial avatar_url if editing
              label="Upload Avatar"
            />
            {errors.avatar_url && <div className="text-error text-xs mt-1">{errors.avatar_url.message}</div>}
          </div>

          {/* Form Submission and Cancel Buttons */}
          <div className="mt-6 flex justify-end space-x-3">
            <button
              type="submit"
              className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create User'}
            </button>
            <button
              type="button"
              className="px-4 py-2 border border-border rounded-md text-copy hover:bg-surface-hover"
              onClick={() => navigate('/admin/users')}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
export default AdminNewUser;