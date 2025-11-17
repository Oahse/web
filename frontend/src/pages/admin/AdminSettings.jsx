import { useState, useEffect } from 'react';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';

/**
 * AdminSettings component allows administrators to view and update system-wide settings.
 * It fetches current settings and provides a form to modify them.
 */
export const AdminSettings = () => {
  // State to store the system settings fetched from the API
  const [settings, setSettings] = useState(null);
  // State to indicate if an update operation is in progress
  const [updating, setUpdating] = useState(false);

  // Function to call the API to get system settings
  const getSystemSettingsApiCall = () => AdminAPI.getSystemSettings();

  // Custom hook to handle API fetching for system settings
  const { data: fetchedSettings, loading, error, refetch } = useApi(
    getSystemSettingsApiCall, // The API call function
    { autoFetch: true, showErrorToast: false } // Options: auto-fetch on mount, suppress default error toasts
  );

  /**
   * Effect hook to update the local settings state when new settings are fetched.
   * Uses a deep comparison to prevent unnecessary re-renders if settings haven't actually changed.
   */
  useEffect(() => {
    // Helper function for deep comparison of two objects
    const deepEqual = (obj1, obj2) => {
      if (obj1 === obj2) return true;
      if (typeof obj1 !== 'object' || obj1 === null || typeof obj2 !== 'object' || obj2 === null) return false;

      const keys1 = Object.keys(obj1);
      const keys2 = Object.keys(obj2);

      if (keys1.length !== keys2.length) return false;

      for (const key of keys1) {
        if (!keys2.includes(key) || !deepEqual(obj1[key], obj2[key])) {
          return false;
        }
      }
      return true;
    };

    // Update settings only if fetchedSettings is available and different from current settings
    if (fetchedSettings && !deepEqual(fetchedSettings, settings)) {
      setSettings(fetchedSettings);
    }
  }, [fetchedSettings, settings]); // Dependencies: re-run if fetchedSettings or local settings change

  /**
   * Handles changes to form input fields.
   * Updates the local settings state based on input name and value.
   * @param {object} e - The event object from the input change.
   */
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings(prev => {
      if (!prev) return null; // If no previous settings, return null
      return {
        ...prev,
        [name]: type === 'checkbox' ? checked : value, // Handle checkbox boolean values
      };
    });
  };

  /**
   * Handles the form submission to update system settings.
   * Calls the AdminAPI to update settings and displays toast notifications.
   * @param {object} e - The event object from the form submission.
   */
  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevent default form submission behavior
    if (settings) {
      setUpdating(true); // Show updating indicator
      try {
        // Call the API to update system settings
        const data = await AdminAPI.updateSystemSettings(settings);
        setSettings(data); // Update local state with the response data
        toast.success('Settings updated successfully!'); // Show success toast
        refetch(); // Re-fetch settings to ensure UI is up-to-date
      } catch (err) {
        toast.error(`Failed to update settings: ${err.message}`); // Show error toast
      } finally {
        setUpdating(false); // Hide updating indicator
      }
    }
  };

  // Display loading message while settings are being fetched
  if (loading) {
    return <div className="p-6 text-center text-copy-light">Loading settings...</div>;
  }

  // Display error message if fetching settings failed
  if (error) {
    return (
      <div className="p-6">
        <ErrorMessage
          error={error}
          onRetry={refetch} // Provide a retry mechanism
        />
      </div>
    );
  }

  // Display message if no settings are found after loading
  if (!settings) {
    return <div className="p-6 text-center text-copy-light">No settings found.</div>;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-main mb-6">System Settings</h1>
      <form onSubmit={handleSubmit} className="bg-surface rounded-lg shadow-sm p-6 border border-border-light">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Maintenance Mode Setting */}
          <div className="flex items-center justify-between bg-background p-4 rounded-md border border-border">
            <div>
              <label htmlFor="maintenance_mode" className="block text-lg font-medium text-main">Maintenance Mode</label>
              <p className="text-sm text-copy-light">Temporarily disable site access for maintenance.</p>
            </div>
            <input
              type="checkbox"
              id="maintenance_mode"
              name="maintenance_mode"
              checked={settings.maintenance_mode}
              onChange={handleChange}
              className="toggle toggle-primary"
            />
          </div>

          {/* Registration Enabled Setting */}
          <div className="flex items-center justify-between bg-background p-4 rounded-md border border-border">
            <div>
              <label htmlFor="registration_enabled" className="block text-lg font-medium text-main">User Registration</label>
              <p className="text-sm text-copy-light">Allow new users to register accounts.</p>
            </div>
            <input
              type="checkbox"
              id="registration_enabled"
              name="registration_enabled"
              checked={settings.registration_enabled}
              onChange={handleChange}
              className="toggle toggle-primary"
            />
          </div>

          {/* Max File Size Setting */}
          <div className="bg-background p-4 rounded-md border border-border">
            <label htmlFor="max_file_size" className="block text-lg font-medium text-main mb-2">Max File Upload Size (MB)</label>
            <input
              type="number"
              id="max_file_size"
              name="max_file_size"
              value={settings.max_file_size}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-surface text-copy"
            />
            <p className="text-sm text-copy-light mt-1">Maximum size for file uploads (e.g., product images).</p>
          </div>

          {/* Allowed File Types Setting */}
          <div className="bg-background p-4 rounded-md border border-border">
            <label htmlFor="allowed_file_types" className="block text-lg font-medium text-main mb-2">Allowed File Types</label>
            <input
              type="text"
              id="allowed_file_types"
              name="allowed_file_types"
              value={settings.allowed_file_types}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-surface text-copy"
            />
            <p className="text-sm text-copy-light mt-1">Comma-separated list of allowed file extensions (e.g., jpg,png,pdf).</p>
          </div>

          {/* Email Notifications Setting */}
          <div className="flex items-center justify-between bg-background p-4 rounded-md border border-border">
            <div>
              <label htmlFor="email_notifications" className="block text-lg font-medium text-main">Email Notifications</label>
              <p className="text-sm text-copy-light">Enable or disable system-wide email notifications.</p>
            </div>
            <input
              type="checkbox"
              id="email_notifications"
              name="email_notifications"
              checked={settings.email_notifications}
              onChange={handleChange}
              className="toggle toggle-primary"
            />
          </div>

          {/* SMS Notifications Setting */}
          <div className="flex items-center justify-between bg-background p-4 rounded-md border border-border">
            <div>
              <label htmlFor="sms_notifications" className="block text-lg font-medium text-main">SMS Notifications</label>
              <p className="text-sm text-copy-light">Enable or disable system-wide SMS notifications.</p>
            </div>
            <input
              type="checkbox"
              id="sms_notifications"
              name="sms_notifications"
              checked={settings.sms_notifications}
              onChange={handleChange}
              className="toggle toggle-primary"
            />
          </div>
        </div>

        {/* Save Settings Button */}
        <div className="mt-6 text-right">
          <button
            type="submit"
            className="px-6 py-2 bg-primary text-white rounded-md hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={updating}
          >
            {updating ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </form>
    </div>
  );
};