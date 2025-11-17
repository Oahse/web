/**
 * Notification API endpoints
 */

import { apiClient } from './client';


export class NotificationAPI {
  /**
   * Get current user's notifications
   */
  static async getUserNotifications(params) {
    const queryParams = new URLSearchParams();

    if (params?.read !== undefined) queryParams.append('read', params.read.toString());
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `/notifications${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Mark a notification as read
   */
  static async markNotificationAsRead(notificationId) {
    return await apiClient.put(`/notifications/${notificationId}/read`);
  }

  /**
   * Mark all notifications as read
   */
  static async markAllNotificationsAsRead() {
    return await apiClient.put('/notifications/mark-all-read');
  }

  /**
   * Get unread notification count
   */
  static async getUnreadCount() {
    const response = await apiClient.get('/notifications?read=false&limit=1');
    return response.data?.pagination?.total || 0;
  }

  /**
   * Delete a notification
   */
  static async deleteNotification(notificationId) {
    return await apiClient.delete(`/notifications/${notificationId}`);
  }
}

export default NotificationAPI;