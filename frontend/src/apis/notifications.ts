import { apiClient   } from './client';


export class NotificationsAPI {
  static async getNotifications(params) {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.unread) queryParams.append('unread', params.unread.toString());
    const url = `/notifications${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  static async markAsRead(notificationId) {
    return await apiClient.put(`/notifications/${notificationId}/read`);
  }

  static async markAllAsRead() {
    return await apiClient.put('/notifications/read-all');
  }
}

export default NotificationsAPI;
