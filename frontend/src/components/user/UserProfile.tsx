import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { UserAPI } from '../../apis/users';
import { useAuth } from '../../contexts/AuthContext';
import { Loading } from '../Loading';
import { Error } from '../Error';

interface UserData {
  id: string;
  email: string;
  firstname: string;
  lastname: string;
  phone?: string;
  date_of_birth?: string;
  profile_picture?: string;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

interface UserProfileProps {
  userId?: string;
  onUserUpdate?: (user: UserData) => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({ userId, onUserUpdate }) => {
  // ✅ Using useState for all local state management
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [formData, setFormData] = useState<Partial<UserData>>({});
  const [saving, setSaving] = useState<boolean>(false);

  const { user: currentUser, isAuthenticated } = useAuth();

  // Fetch user data
  const fetchUser = async (id?: string) => {
    const targetUserId = id || userId || (currentUser as any)?.id;
    if (!targetUserId) {
      setError('No user ID provided');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await UserAPI.getUserById(targetUserId);
      if (response.success) {
        setUser(response.data);
        setFormData(response.data);
      } else {
        setError(response.message || 'Failed to load user data');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load user data');
      console.error('Failed to fetch user:', err);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    if (isAuthenticated) {
      fetchUser();
    }
  }, [userId, isAuthenticated]);

  // Handle form input changes
  const handleInputChange = (field: keyof UserData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Save user changes
  const handleSave = async () => {
    if (!user) return;

    setSaving(true);
    try {
      const response = await UserAPI.updateUser(user.id, formData);
      if (response.success) {
        const updatedUser = response.data;
        setUser(updatedUser);
        setFormData(updatedUser);
        setIsEditing(false);
        toast.success('Profile updated successfully');
        
        // Notify parent component
        if (onUserUpdate) {
          onUserUpdate(updatedUser);
        }
      } else {
        toast.error(response.message || 'Failed to update profile');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to update profile');
      console.error('Failed to update user:', err);
    } finally {
      setSaving(false);
    }
  };

  // Cancel editing
  const handleCancel = () => {
    setFormData(user || {});
    setIsEditing(false);
  };

  // Upload profile picture
  const handleProfilePictureUpload = async (file: File) => {
    if (!user) return;

    const formData = new FormData();
    formData.append('profile_picture', file);

    setSaving(true);
    try {
      const response = await UserAPI.uploadProfilePicture(user.id, formData);
      if (response.success) {
        const updatedUser = { ...user, profile_picture: response.data.profile_picture };
        setUser(updatedUser);
        toast.success('Profile picture updated');
        
        if (onUserUpdate) {
          onUserUpdate(updatedUser);
        }
      } else {
        toast.error(response.message || 'Failed to upload profile picture');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to upload profile picture');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <Loading text="Loading profile..." />;
  }

  if (error) {
    return <Error message={error} onRetry={() => fetchUser()} />;
  }

  if (!user) {
    return <div className="text-center py-8">No user data available</div>;
  }

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="heading text-xl">Profile Information</h2>
          {!isEditing ? (
            <button
              onClick={() => setIsEditing(true)}
              className="button-text px-4 py-2 text-primary hover:bg-primary/10 rounded-lg transition-colors"
            >
              Edit Profile
            </button>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={handleCancel}
                disabled={saving}
                className="button-text px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="button-text px-4 py-2 bg-primary text-white hover:bg-primary-dark rounded-lg transition-colors disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Profile Picture */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center gap-4">
          <div className="relative">
            <img
              src={user.profile_picture || '/default-avatar.png'}
              alt="Profile"
              className="w-20 h-20 rounded-full object-cover border-2 border-gray-200"
            />
            {isEditing && (
              <label className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full cursor-pointer opacity-0 hover:opacity-100 transition-opacity">
                <span className="text-white text-xs">Change</span>
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleProfilePictureUpload(file);
                  }}
                />
              </label>
            )}
          </div>
          <div>
            <h3 className="heading text-lg">{user.firstname} {user.lastname}</h3>
            <p className="body-text text-gray-600">{user.email}</p>
            {user.is_verified ? (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                ✓ Verified
              </span>
            ) : (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-yellow-100 text-yellow-800">
                Unverified
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Form Fields */}
      <div className="px-6 py-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* First Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              First Name
            </label>
            {isEditing ? (
              <input
                type="text"
                value={formData.firstname || ''}
                onChange={(e) => handleInputChange('firstname', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            ) : (
              <p className="body-text py-2">{user.firstname}</p>
            )}
          </div>

          {/* Last Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Last Name
            </label>
            {isEditing ? (
              <input
                type="text"
                value={formData.lastname || ''}
                onChange={(e) => handleInputChange('lastname', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            ) : (
              <p className="body-text py-2">{user.lastname}</p>
            )}
          </div>
        </div>

        {/* Email */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Email Address
          </label>
          <p className="body-text py-2 text-gray-500">{user.email} (cannot be changed)</p>
        </div>

        {/* Phone */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Phone Number
          </label>
          {isEditing ? (
            <input
              type="tel"
              value={formData.phone || ''}
              onChange={(e) => handleInputChange('phone', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              placeholder="Enter phone number"
            />
          ) : (
            <p className="body-text py-2">{user.phone || 'Not provided'}</p>
          )}
        </div>

        {/* Date of Birth */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Date of Birth
          </label>
          {isEditing ? (
            <input
              type="date"
              value={formData.date_of_birth || ''}
              onChange={(e) => handleInputChange('date_of_birth', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          ) : (
            <p className="body-text py-2">
              {user.date_of_birth ? new Date(user.date_of_birth).toLocaleDateString() : 'Not provided'}
            </p>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
        <div className="flex justify-between text-sm text-gray-500">
          <span>Member since: {new Date(user.created_at).toLocaleDateString()}</span>
          <span>Last updated: {new Date(user.updated_at).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  );
};