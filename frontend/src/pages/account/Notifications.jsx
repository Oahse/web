import { useState, useEffect } from 'react';
import { CheckCircle, Mail, Trash2 } from 'lucide-react';
import { useApi } from '../../hooks/useApi';
import { NotificationAPI } from '../../apis/notification';
import { toast } from 'react-hot-toast';

/**
 * Notifications component displays a user's notifications and allows them to mark as read or delete them.
 */
export const Notifications = () => {
  // State for current page and limit for pagination
  const [page] = useState(1);
  const [limit] = useState(10);

  // Fetch notifications using the custom useApi hook
  const { data: notificationsData, loading, error, refetch } = useApi(
    () => NotificationAPI.getUserNotifications({ page: 1, limit }),
    { autoFetch: true } // Automatically fetch data on component mount
  );

  /**
   * Handles marking a specific notification as read.
   * Displays a toast notification on success or failure and refetches notifications.
   * @param {string} notificationId - The ID of the notification to mark as read.
   */
  const handleMarkAsRead = async (notificationId) => {
    try {
      await NotificationAPI.markNotificationAsRead(notificationId);
      toast.success('Notification marked as read!');
      refetch(); // Re-fetch notifications to update the UI
    } catch (err) {
      toast.error(`Failed to mark notification as read: ${err.message}`);
    }
  };

  /**
   * Handles deleting a specific notification.
   * Displays a toast notification on success or failure and refetches notifications.
   * @param {string} notificationId - The ID of the notification to delete.
   */
  const handleDeleteNotification = async (notificationId) => {
    try {
      await NotificationAPI.deleteNotification(notificationId);
      toast.success('Notification deleted!');
      refetch(); // Re-fetch notifications to update the UI
    } catch (err) {
      toast.error(`Failed to delete notification: ${err.message}`);
    }
  };

  // Display loading spinner while fetching notifications
  if (loading) {
    return (
      <div className="max-w-md mx-auto mt-8 p-4">
        <div className="flex justify-center items-center min-h-[200px]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  // Display error message if fetching notifications fails
  if (error) {
    return (
      <div className="max-w-md mx-auto mt-8 p-4">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> Error loading notifications: {error.message}</span>
        </div>
      </div>
    );
  }

  // Extract notifications and pagination data
  const notifications = notificationsData?.data || [];
  const pagination = notificationsData?.pagination;

  return (
    <div className="max-w-md mx-auto mt-8 p-4">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Your Notifications</h1>

      {notifications.length === 0 ? (
        <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Info!</strong>
          <span className="block sm:inline"> You have no notifications.</span>
        </div>
      ) : (
        <ul className="space-y-3">
          {notifications.map((notification) => (
            <li
              key={notification.id}
              className={`flex items-center p-4 rounded-lg shadow-sm border ${notification.read ? 'bg-white border-gray-200' : 'bg-blue-50 border-blue-200'}`}
            >
              <div className="flex-shrink-0 mr-3">
                {notification.read ? <Mail size={20} className="text-gray-500" /> : <Mail size={20} className="text-blue-600" />}
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-800">{notification.message}</p>
                <p className="text-sm text-gray-500">Type: {notification.type} - {new Date(notification.created_at).toLocaleString()}</p>
              </div>
              <div className="flex items-center ml-4">
                {!notification.read && (
                  <button
                    onClick={() => handleMarkAsRead(notification.id)}
                    className="p-2 rounded-full text-blue-600 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    title="Mark as read"
                  >
                    <CheckCircle size={20} />
                  </button>
                )}
                <button
                  onClick={() => handleDeleteNotification(notification.id)}
                  className="p-2 rounded-full text-red-600 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500 ml-2"
                  title="Delete notification"
                >
                  <Trash2 size={20} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* Pagination controls */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex justify-center mt-6">
          <p className="text-gray-600">Page {pagination.page} of {pagination.total_pages}</p>
          {/* Add actual pagination buttons here if needed */}
        </div>
      )}
    </div>
  );
};
