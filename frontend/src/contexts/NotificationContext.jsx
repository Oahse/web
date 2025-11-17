import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  notificationService,
  browserNotificationService 
} from '../lib/notifications';


export const NotificationContext = createContext(undefined);



export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [preferences, setPreferences] = useState(
    notificationService.getPreferences()
  );

  useEffect(() => {
    // Subscribe to notification changes
    const unsubscribe = notificationService.subscribe((newNotifications) => {
      setNotifications(newNotifications);
    });

    // Initialize with current notifications
    setNotifications(notificationService.getAll());

    return unsubscribe;
  }, []);

  const unreadCount = notifications.filter(n => !n.read).length;

  const addNotification = (notification) => {
    const id = notificationService.add(notification);
    
    // Show browser notification if enabled and permission granted
    if (preferences.globalEnabled && !notificationService.isQuietHours()) {
      browserNotificationService.show(notification.title, {
        body: notification.message,
        tag: notification.category,
      });
    }
    
    return id;
  };

  const removeNotification = (id) => {
    notificationService.remove(id);
  };

  const markAsRead = (id) => {
    notificationService.markAsRead(id);
  };

  const markAllAsRead = () => {
    notificationService.markAllAsRead();
  };

  const clearAll = () => {
    notificationService.clear();
  };

  const updatePreferences = (newPreferences) => {
    notificationService.updatePreferences(newPreferences);
    setPreferences(notificationService.getPreferences());
  };

  const requestBrowserPermission = async () => {
    return await browserNotificationService.requestPermission();
  };

  // Convenience methods
  const success = (title, message) => {
    return addNotification({ type: 'success', title, message });
  };

  const error = (title, message) => {
    return addNotification({ type: 'error', title, message, persistent: true });
  };

  const warning = (title, message) => {
    return addNotification({ type: 'warning', title, message });
  };

  const info = (title, message) => {
    return addNotification({ type: 'info', title, message });
  };

  const value = {
    notifications,
    unreadCount,
    preferences,
    addNotification,
    removeNotification,
    markAsRead,
    markAllAsRead,
    clearAll,
    updatePreferences,
    requestBrowserPermission,
    success,
    error,
    warning,
    info,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};
export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications error: must be used within a NotificationProvider');
  }
  return context;
};