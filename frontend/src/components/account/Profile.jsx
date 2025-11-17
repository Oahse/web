import React, { useState, useEffect } from 'react';
import { UserIcon, MailIcon, PhoneIcon, MapPinIcon, CalendarIcon, GlobeIcon, SaveIcon } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useAuth } from '../../contexts/AuthContext';
import { AuthAPI } from '../../apis';

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
  });

  // Initialize form data with user information
  useEffect(() => {
    if (user) {
      setFormData({
        firstname: user.firstname || '',
        lastname: user.lastname || '',
        email: user.email || '',
        phone: user.phone || '',
        age: user.age || '',
        gender: user.gender || '',
        country: user.country || '',
        language: user.language || 'en',
        timezone: user.timezone || '',
      });
    }
  }, [user]);

  /**
   * Handles changes to form input fields.
   */
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  /**
   * Handles form submission to update user profile.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await AuthAPI.updateProfile(formData);
      if (result) {
        // Update user in context
        updateUser(result);
        toast.success('Profile updated successfully');
        setIsEditing(false);
      }
    } catch (error) {
      toast.error('Failed to update profile');
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
        age: user.age || '',
        gender: user.gender || '',
        country: user.country || '',
        language: user.language || 'en',
        timezone: user.timezone || '',
      });
    }
    setIsEditing(false);
  };

  if (!user) {
    return <div className="p-6 text-center text-copy-light">Loading profile...</div>;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-main dark:text-white mb-6">
        My Profile
      </h1>

      {/* Profile Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <div className="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center text-primary text-2xl font-bold">
              {user.firstname?.charAt(0) || user.full_name?.charAt(0) || 'U'}
            </div>
            <div className="ml-4">
              <h2 className="text-xl font-semibold text-main dark:text-white">
                {user.full_name || `${user.firstname} ${user.lastname}`}
              </h2>
              <p className="text-copy-light">{user.email}</p>
              <div className="flex items-center mt-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  user.verified 
                    ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
                    : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100'
                }`}>
                  {user.verified ? '✓ Verified' : '⚠ Unverified'}
                </span>
                <span className="ml-2 text-xs text-copy-light capitalize">
                  {user.role}
                </span>
              </div>
            </div>
          </div>
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-md transition-colors"
            >
              Edit Profile
            </button>
          )}
        </div>
      </div>

      {/* Profile Information */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-main dark:text-white mb-4">
          Personal Information
        </h3>

        {isEditing ? (
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white"
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white"
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white"
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white"
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white"
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white"
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white"
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-primary dark:bg-gray-700 dark:text-white"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="it">Italian</option>
                  <option value="pt">Portuguese</option>
                </select>
              </div>
            </div>

            {/* Form Actions */}
            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={handleCancel}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-md flex items-center"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Saving...
                  </>
                ) : (
                  <>
                    <SaveIcon size={16} className="mr-2" />
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            {/* Display Mode */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex items-start">
                <UserIcon size={20} className="text-gray-400 mr-3 mt-1" />
                <div>
                  <p className="text-sm text-copy-light">Full Name</p>
                  <p className="text-main dark:text-white font-medium">
                    {user.firstname} {user.lastname}
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <MailIcon size={20} className="text-gray-400 mr-3 mt-1" />
                <div>
                  <p className="text-sm text-copy-light">Email</p>
                  <p className="text-main dark:text-white font-medium">{user.email}</p>
                </div>
              </div>

              {user.phone && (
                <div className="flex items-start">
                  <PhoneIcon size={20} className="text-gray-400 mr-3 mt-1" />
                  <div>
                    <p className="text-sm text-copy-light">Phone</p>
                    <p className="text-main dark:text-white font-medium">{user.phone}</p>
                  </div>
                </div>
              )}

              {user.country && (
                <div className="flex items-start">
                  <MapPinIcon size={20} className="text-gray-400 mr-3 mt-1" />
                  <div>
                    <p className="text-sm text-copy-light">Country</p>
                    <p className="text-main dark:text-white font-medium">{user.country}</p>
                  </div>
                </div>
              )}

              {user.age && (
                <div className="flex items-start">
                  <CalendarIcon size={20} className="text-gray-400 mr-3 mt-1" />
                  <div>
                    <p className="text-sm text-copy-light">Age</p>
                    <p className="text-main dark:text-white font-medium">{user.age} years</p>
                  </div>
                </div>
              )}

              {user.language && (
                <div className="flex items-start">
                  <GlobeIcon size={20} className="text-gray-400 mr-3 mt-1" />
                  <div>
                    <p className="text-sm text-copy-light">Language</p>
                    <p className="text-main dark:text-white font-medium capitalize">{user.language}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Account Information */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mt-6">
        <h3 className="text-lg font-medium text-main dark:text-white mb-4">
          Account Information
        </h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700">
            <span className="text-copy-light">Account Status</span>
            <span className={`px-2 py-1 text-xs rounded-full ${
              user.active 
                ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
                : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
            }`}>
              {user.active ? 'Active' : 'Inactive'}
            </span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700">
            <span className="text-copy-light">Email Verification</span>
            <span className={`px-2 py-1 text-xs rounded-full ${
              user.verified 
                ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100'
            }`}>
              {user.verified ? 'Verified' : 'Not Verified'}
            </span>
          </div>
          <div className="flex justify-between items-center py-2">
            <span className="text-copy-light">Member Since</span>
            <span className="text-main dark:text-white font-medium">
              {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
