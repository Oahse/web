import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { useApi } from '../../hooks/useApi';
import { NotificationsAPI } from '../../apis/notifications';

/**
 * SupplierNotifications component displays notifications for suppliers.
 * It allows viewing, filtering, marking as read, and handling notification clicks.
 */
const SupplierNotifications = ({
  onNotificationClick
}) => {
  // Custom hook to fetch notifications from the API
  const { data: notifications, loading, error, execute: fetchNotifications, setData: setNotifications } = useApi();
  // State to store the count of unread notifications
  const [unreadCount, setUnreadCount] = useState(0);
  // State to control the visibility of the notifications dropdown
  const [showDropdown, setShowDropdown] = useState(false);
  // State to control the current filter for notifications (all, unread, orders)
  const [filter, setFilter] = useState('all');

  // Effect hook to fetch notifications on component mount
  useEffect(() => {
    fetchNotifications(NotificationsAPI.getNotifications);
  }, [fetchNotifications]);

  // Effect hook to update the unread count whenever notifications data changes
  useEffect(() => {
    if (notifications) {
      setUnreadCount(notifications.filter(n => !n.read).length);
    }
  }, [notifications]);

  /**
   * Returns an emoji icon based on the notification type.
   * @param {string} type - The type of the notification.
   * @returns {string} An emoji representing the notification type.
   */
  const getNotificationIcon = (type) => {
    switch (type) {
      case 'order_update':
        return '📦';
      case 'system':
        return '⚙️';
      default:
        return '📢';
    }
  };

  /**
   * Marks a specific notification as read via API call and updates local state.
   * @param {string} notificationId - The ID of the notification to mark as read.
   */
  const markAsRead = async (notificationId) => {
    try {
      await NotificationsAPI.markAsRead(notificationId);
      // Update the local state to mark the notification as read
      setNotifications(notifications?.map(n => n.id === notificationId ? { ...n, read: true } : n));
    } catch (error) {
      console.error('Failed to mark notification as read', error);
    }
  };

  /**
   * Marks all notifications as read via API call and updates local state.
   */
  const markAllAsRead = async () => {
    try {
      await NotificationsAPI.markAllAsRead();
      // Update all notifications in local state as read
      setNotifications(notifications?.map(n => ({ ...n, read: true })));
    } catch (error) {
      console.error('Failed to mark all notifications as read', error);
    }
  };

  /**
   * Handles a click on an individual notification.
   * Marks it as read and triggers the onNotificationClick callback if provided.
   * @param {object} notification - The clicked notification object.
   */
  const handleNotificationClick = (notification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
    
    if (onNotificationClick) {
      onNotificationClick(notification);
    }
    
    setShowDropdown(false); // Close dropdown after clicking a notification
  };

  // Filters notifications based on the current filter state
  const filteredNotifications = notifications?.filter(notification => {
    switch (filter) {
      case 'unread':
        return !notification.read;
      case 'orders':
        return notification.type === 'order_update';
      default:
        return true;
    }
  }) || [];

  return (
    <div className="relative">
      {/* Notification Bell Button */}
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg"
      >
        <div className="text-xl">🔔</div>
        {/* Unread count badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notifications Dropdown */}
      {showDropdown && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          {/* Dropdown Header with Close Button and Filter Tabs */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900">Notifications</h3>
              <button
                onClick={() => setShowDropdown(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            {/* Filter tabs for notifications */}
            <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setFilter('all')}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  filter === 'all' 
                    ? 'bg-white text-gray-900 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                All ({notifications?.length || 0})
              </button>
              <button
                onClick={() => setFilter('unread')}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  filter === 'unread' 
                    ? 'bg-white text-gray-900 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Unread ({unreadCount})
              </button>
              <button
                onClick={() => setFilter('orders')}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  filter === 'orders' 
                    ? 'bg-white text-gray-900 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Orders
              </button>
            </div>

            {/* Mark all as read button */}
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="mt-2 text-sm text-blue-600 hover:text-blue-800"
              >
                Mark all as read
              </button>
            )}
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="p-8 text-center">Loading...</div>
            ) : error ? (
              <div className="p-8 text-center text-red-500">Error: {error.message}</div>
            ) : filteredNotifications.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {filteredNotifications.map((notification) => (
                  <div
                    key={notification.id}
                    onClick={() => handleNotificationClick(notification)}
                    className={`
                      p-4 cursor-pointer hover:bg-gray-50 transition-colors border-l-4
                      border-l-gray-500 bg-gray-50
                      ${!notification.read ? 'bg-blue-50' : 'bg-white'}
                    `}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="text-lg flex-shrink-0">
                        {getNotificationIcon(notification.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className={`text-sm font-medium ${!notification.read ? 'text-gray-900' : 'text-gray-700'}`}>
                            {notification.title}
                          </p>
                          {!notification.read && (
                            <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0"></div>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {notification.message}
                        </p>
                        <div className="flex items-center justify-between mt-2">
                          <time className="text-xs text-gray-500">
                            {format(new Date(notification.created_at), 'MMM dd, HH:mm')}
                          </time>
                          {notification.data?.orderId && (
                            <span className="text-xs text-blue-600 font-medium">
                              Order #{notification.data.orderId}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center">
                <div className="text-4xl mb-2">📭</div>
                <p className="text-gray-500">
                  {filter === 'unread' 
                    ? 'No unread notifications' 
                    : filter === 'orders'
                    ? 'No order notifications'
                    : 'No notifications'
                  }
                </p>
              </div>
            )}
          </div>

          {/* Dropdown Footer */}
          {filteredNotifications.length > 0 && (
            <div className="p-3 border-t border-gray-200 bg-gray-50 rounded-b-lg">
              <button className="w-full text-sm text-blue-600 hover:text-blue-800 font-medium">
                View All Notifications
              </button>
            </div>
          )}
        </div>
      )}

      {/* Backdrop for closing dropdown when clicking outside */}
      {showDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  );
};

export default SupplierNotifications;