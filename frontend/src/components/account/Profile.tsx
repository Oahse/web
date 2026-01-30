import React, { useState, useEffect } from 'react';
import { UserIcon, MailIcon, PhoneIcon, MapPinIcon, CalendarIcon, GlobeIcon, SaveIcon } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useAuth } from '../../store/AuthContext';
import { AuthAPI } from '../../api';
import { unwrapResponse, extractErrorMessage } from '../../utils/api-response';
import { SkeletonProfile } from '../ui/SkeletonProfile';

/**
 * Profile component allows users to view and edit their personal information.
 */
export const Profile = () => {
  const { user, updateUser } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    firstname: '',
    lastname: '',
    email: '',
    phone: '',
    age: '',
    gender: '',
    country: '',
    language: 'en',
    timezone: '',
    is_active: true,
  });

  // Initialize form data with user information
  useEffect(() => {
    if (user) {
      setFormData({
        firstname: user.firstname || '',
        lastname: user.lastname || '',
        email: user.email || '',
        phone: user.phone || '',
        age: (user as any).age?.toString() || '',
        gender: (user as any).gender || '',
        country: (user as any).country || '',
        language: (user as any).language || 'en',
        timezone: (user as any).timezone || '',
        is_active: (user as any).is_active ?? true,
      });
    }
  }, [user]);

  /**
   * Handles changes to form input fields.
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  /**
   * Handles form submission to update user profile.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Convert data to match backend schema
      const submissionData = {
        firstname: formData.firstname,
        lastname: formData.lastname,
        email: formData.email,
        phone: formData.phone || undefined,
        age: formData.age || undefined,  // Keep as string since DB expects VARCHAR
        gender: formData.gender || undefined,
        country: formData.country || undefined,
        language: formData.language || undefined,
        timezone: formData.timezone || undefined,
        is_active: formData.is_active,
      };

      const result = await AuthAPI.updateProfile(submissionData);
      
      // Handle wrapped response
      const data = unwrapResponse(result);
      
      if (data) {
        // Update user in context - this should trigger the useEffect to refresh form data
        updateUser(data);
        toast.success('Profile updated successfully');
        setIsEditing(false);
      }
    } catch (error: any) {
      const errorMessage = extractErrorMessage(error);
      toast.error(errorMessage || 'Failed to update profile');
      console.error('Profile update error:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Cancels editing and resets form data.
   */
  const handleCancel = () => {
    if (user) {
      setFormData({
        firstname: user.firstname || '',
        lastname: user.lastname || '',
        email: user.email || '',
        phone: user.phone || '',
        age: (user as any).age?.toString() || '',
        gender: (user as any).gender || '',
        country: (user as any).country || '',
        language: (user as any).language || 'en',
        timezone: (user as any).timezone || '',
        is_active: (user as any).is_active ?? true,
      });
    }
    setIsEditing(false);
  };

  if (!user) {
    return <SkeletonProfile />;
  }

  return (
    <div className="p-3 space-y-3">
      
      {/* Profile Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xl font-bold">
              {user.firstname?.charAt(0) || user.full_name?.charAt(0) || 'U'}
            </div>
            <div className="ml-3">
              <h2 className="text-lg font-semibold text-main dark:text-white">
                {user.full_name || `${user.firstname} ${user.lastname}`}
              </h2>
              <p className="text-sm text-copy-light dark:text-gray-400">{user.email}</p>
              <div className="flex items-center mt-1">
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                  user.verified 
                    ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
                    : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100'
                }`}>
                  {user.verified ? '✓ Verified' : '⚠ Unverified'}
                </span>
                <span className="ml-2 text-xs text-copy-light dark:text-gray-400 capitalize">
                  {user.role}
                </span>
              </div>
            </div>
          </div>
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="px-3 py-2 bg-primary hover:bg-primary-dark text-white rounded-md transition-colors text-sm"
            >
              Edit Profile
            </button>
          )}
        </div>
      </div>

      {/* Profile Information */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
        <h3 className="text-base font-medium text-main dark:text-white mb-3">
          Personal Information
        </h3>

        {isEditing ? (
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* First Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  First Name *
                </label>
                <input
                  type="text"
                  name="firstname"
                  value={formData.firstname}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white text-sm"
                  required
                />
              </div>

              {/* Last Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Last Name *
                </label>
                <input
                  type="text"
                  name="lastname"
                  value={formData.lastname}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white text-sm"
                  required
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white text-sm"
                  required
                />
              </div>

              {/* Phone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Phone
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white text-sm"
                  placeholder="+1 (555) 123-4567"
                />
              </div>

              {/* Age */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Age
                </label>
                <input
                  type="number"
                  name="age"
                  value={formData.age}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white text-sm"
                  min="13"
                  max="120"
                />
              </div>

              {/* Gender */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Gender
                </label>
                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white text-sm"
                >
                  <option value="">Select Gender</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              {/* Country */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Country
                </label>
                <input
                  type="text"
                  name="country"
                  value={formData.country}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white text-sm"
                  placeholder="United States"
                />
              </div>

              {/* Language */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Language
                </label>
                <select
                  name="language"
                  value={formData.language}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white text-sm"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="it">Italian</option>
                  <option value="pt">Portuguese</option>
                </select>
              </div>

              {/* Timezone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Timezone
                </label>
                <select
                  name="timezone"
                  value={formData.timezone}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white text-sm"
                >
                  <option value="">Select Timezone</option>
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Denver">Mountain Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                  <option value="Europe/London">London</option>
                  <option value="Europe/Paris">Paris</option>
                  <option value="Asia/Tokyo">Tokyo</option>
                  <option value="Asia/Shanghai">Shanghai</option>
                </select>
              </div>
            </div>

            {/* Form Actions */}
            <div className="mt-4 flex justify-end space-x-2">
              <button
                type="button"
                onClick={handleCancel}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 text-sm"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-2 bg-primary hover:bg-primary-dark text-white rounded-md flex items-center text-sm"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Saving...
                  </>
                ) : (
                  <>
                    <SaveIcon size={14} className="mr-2" />
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            {/* Display Mode - Only Show Relevant Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Basic Information */}
              <div className="flex items-start">
                <UserIcon size={16} className="text-gray-400 mr-3 mt-1" />
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Full Name</p>
                  <p className="text-sm text-gray-900 dark:text-white font-medium">
                    {user.firstname} {user.lastname}
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <MailIcon size={16} className="text-gray-400 mr-3 mt-1" />
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Email</p>
                  <p className="text-sm text-gray-900 dark:text-white font-medium">{user.email}</p>
                </div>
              </div>

              {user.phone && (
                <div className="flex items-start">
                  <PhoneIcon size={16} className="text-gray-400 mr-3 mt-1" />
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Phone</p>
                    <p className="text-sm text-gray-900 dark:text-white font-medium">{user.phone}</p>
                  </div>
                </div>
              )}

              {/* Personal Details */}
              {(user as any).age && (
                <div className="flex items-start">
                  <CalendarIcon size={16} className="text-gray-400 mr-3 mt-1" />
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Age</p>
                    <p className="text-sm text-gray-900 dark:text-white font-medium">{(user as any).age} years</p>
                  </div>
                </div>
              )}

              {(user as any).gender && (
                <div className="flex items-start">
                  <UserIcon size={16} className="text-gray-400 mr-3 mt-1" />
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Gender</p>
                    <p className="text-sm text-gray-900 dark:text-white font-medium capitalize">{(user as any).gender}</p>
                  </div>
                </div>
              )}

              {/* Location & Preferences */}
              {(user as any).country && (
                <div className="flex items-start">
                  <MapPinIcon size={16} className="text-gray-400 mr-3 mt-1" />
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Country</p>
                    <p className="text-sm text-gray-900 dark:text-white font-medium">{(user as any).country}</p>
                  </div>
                </div>
              )}

              {(user as any).language && (
                <div className="flex items-start">
                  <GlobeIcon size={16} className="text-gray-400 mr-3 mt-1" />
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Language</p>
                    <p className="text-sm text-gray-900 dark:text-white font-medium capitalize">{(user as any).language}</p>
                  </div>
                </div>
              )}

              {(user as any).timezone && (
                <div className="flex items-start">
                  <GlobeIcon size={16} className="text-gray-400 mr-3 mt-1" />
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Timezone</p>
                    <p className="text-sm text-gray-900 dark:text-white font-medium">{(user as any).timezone}</p>
                  </div>
                </div>
              )}

              {/* Account Status - Important Info */}
              <div className="flex items-start">
                <UserIcon size={16} className="text-gray-400 mr-3 mt-1" />
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Account Status</p>
                  <p className="text-sm text-gray-900 dark:text-white font-medium capitalize">
                    {(user as any).account_status || (user.is_active ? 'Active' : 'Inactive')}
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <MailIcon size={16} className="text-gray-400 mr-3 mt-1" />
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Email Verification</p>
                  <p className="text-sm text-gray-900 dark:text-white font-medium capitalize">
                    {(user as any).verification_status || (user.verified ? 'Verified' : 'Not Verified')}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Account Information */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
        <h3 className="text-base font-medium text-gray-900 dark:text-white mb-3">
          Account Details
        </h3>
        <div className="space-y-2">
          <div className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700">
            <span className="text-sm text-gray-500 dark:text-gray-400">Member Since</span>
            <span className="text-sm text-gray-900 dark:text-white font-medium">
              {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
            </span>
          </div>
          <div className="flex justify-between items-center py-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">Last Updated</span>
            <span className="text-sm text-gray-900 dark:text-white font-medium">
              {user.updated_at ? new Date(user.updated_at).toLocaleDateString() : 'N/A'}
            </span>
          </div>
          {(user as any).last_login && (
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Last Login</span>
              <span className="text-sm text-gray-900 dark:text-white font-medium">
                {new Date((user as any).last_login).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;
