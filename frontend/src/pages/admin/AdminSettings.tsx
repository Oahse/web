import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';
import { SystemSetting, SystemSettingUpdate } from '../../types';

// Helper function to convert string values from DB to their actual types
const convertValueFromDB = (value: string, type: SystemSetting['value_type']): any => {
  switch (type) {
    case 'boolean':
      return value === 'true';
    case 'integer':
      return parseInt(value, 10);
    case 'float':
      return parseFloat(value);
    case 'uuid':
      return value; // UUIDs are handled as strings in forms
    case 'string':
    default:
      return value;
  }
};

// Helper function to convert actual types to string for DB storage
const convertValueToDB = (value: any, type: SystemSetting['value_type']): string => {
  switch (type) {
    case 'boolean':
      return value ? 'true' : 'false';
    case 'integer':
    case 'float':
    case 'uuid':
    case 'string':
    default:
      return String(value);
  }
};

/**
 * AdminSettings component allows administrators to view and update system-wide settings.
 * It fetches current settings and provides a dynamic form to modify them.
 */
export const AdminSettings = () => {
  // State to store system settings as a map for easy key-based access
  const [settingsMap, setSettingsMap] = useState<Record<string, SystemSetting> | null>(null);
  // State to indicate if an update operation is in progress
  const [updating, setUpdating] = useState(false);

  // Custom hook to handle API fetching for system settings
  const { data: fetchedSettings, loading, error, execute: fetchSettings } = useApi<SystemSetting[]>();

  // Fetch settings on component mount
  useEffect(() => {
    fetchSettings(AdminAPI.getSystemSettings);
  }, [fetchSettings]);

  /**
   * Effect hook to process fetched settings and populate the settings map.
   */
  useEffect(() => {
    if (fetchedSettings?.data) {
      const initialSettingsMap: Record<string, SystemSetting> = {};
      fetchedSettings.data.forEach(setting => {
        initialSettingsMap[setting.key] = {
          ...setting,
          value: convertValueFromDB(setting.value, setting.value_type) // Convert value for UI
        };
      });
      setSettingsMap(initialSettingsMap);
    }
  }, [fetchedSettings]);

  /**
   * Handles changes to form input fields.
   * Updates the local settings map based on input name and converted value.
   */
  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const key = name;

    setSettingsMap(prev => {
      if (!prev) return null;

      const currentSetting = prev[key];
      if (!currentSetting) return prev;

      let newValue: any;
      if (type === 'checkbox') {
        newValue = (e.target as HTMLInputElement).checked;
      } else {
        newValue = value;
      }

      return {
        ...prev,
        [key]: {
          ...currentSetting,
          value: newValue,
        },
      };
    });
  }, []);

  /**
   * Handles the form submission to update system settings.
   * Converts the settings map back to an array of SystemSettingUpdate objects
   * and calls the AdminAPI.
   */
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!settingsMap) return;

    setUpdating(true);
    try {
      const updates: SystemSettingUpdate[] = Object.values(settingsMap).map(setting => ({
        id: setting.id, // Include ID if the API expects it for PUT operations on individual settings
        key: setting.key,
        value: convertValueToDB(setting.value, setting.value_type), // Convert back to string for API
        value_type: setting.value_type,
        description: setting.description,
      }));

      // The backend API expects an array of settings to update
      await AdminAPI.updateSystemSettings(updates);
      toast.success('Settings updated successfully!');
      fetchSettings(AdminAPI.getSystemSettings); // Re-fetch to ensure consistency and display latest values
    } catch (err: any) {
      toast.error(`Failed to update settings: ${err.message || 'Unknown error'}`);
    } finally {
      setUpdating(false);
    }
  }, [settingsMap, fetchSettings]);

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
          onRetry={() => fetchSettings(AdminAPI.getSystemSettings)}
          onDismiss={() => {}}
        />
      </div>
    );
  }

  // Display message if no settings are found after loading
  if (!settingsMap || Object.keys(settingsMap).length === 0) {
    return <div className="p-6 text-center text-copy-light">No settings found.</div>;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-main mb-6">System Settings</h1>
      <form onSubmit={handleSubmit} className="bg-surface rounded-lg shadow-sm p-6 border border-border-light">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {Object.values(settingsMap).map(setting => (
            <div key={setting.id} className="bg-background p-4 rounded-md border border-border">
              <div>
                <label htmlFor={setting.key} className="block text-lg font-medium text-main">
                  {setting.key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())} {/* Humanize key */}
                </label>
                <p className="text-sm text-copy-light">{setting.description}</p>
              </div>
              {setting.value_type === 'boolean' ? (
                <input
                  type="checkbox"
                  id={setting.key}
                  name={setting.key}
                  checked={setting.value as boolean}
                  onChange={handleChange}
                  className="toggle toggle-primary"
                />
              ) : setting.value_type === 'integer' || setting.value_type === 'float' ? (
                <input
                  type="number"
                  id={setting.key}
                  name={setting.key}
                  value={setting.value as number}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-surface text-copy"
                />
              ) : ( // Default to text input for 'string' and 'uuid'
                <input
                  type="text"
                  id={setting.key}
                  name={setting.key}
                  value={setting.value as string}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-surface text-copy"
                />
              )}
            </div>
          ))}
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
