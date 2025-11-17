import { useState, useEffect } from 'react';
import { BellIcon, CheckIcon, TrashIcon, RefreshCwIcon } from 'lucide-react';
import { NotificationAPI } from '../../apis/notification';

export const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all', 'unread', 'read'
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState(null);

  const fetchNotifications = async (currentPage = 1, readFilter = null) => {
    try {
      setLoading(true);
      const params = { page: currentPage, limit: 20 };
      if (readFilter !== null) {
        params.read = readFilter;
      }
      
      const response = await NotificationAPI.getUserNotifications(params);
      if (response.success && response.data?.data) {
        setNotifications(response.data.data);
        setPagination(response.data.pagination);
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const readFilter = filter === 'unread' ? false : filter === 'read' ? true : null;
    fetchNotifications(page, readFilter);
  }, [page, filter]);

  const handleMarkAsRead = async (notificationId) => {
    try {
      await NotificationAPI.markNotificationAsRead(notificationId);
      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await NotificationAPI.markAllNotificationsAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const handleDelete = async (notificationId) => {
    try {
      await NotificationAPI.deleteNotification(notificationId);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  const handleRefresh = () => {
    const readFilter = filter === 'unread' ? false : filter === 'read' ? true : null;
    fetchNotifications(page, readFilter);
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'order':
        return '📦';
      case 'success':
        return '✅';
      case 'warning':
        return '⚠️';
      case 'error':
        return '❌';
      default:
        return '🔔';
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-surface rounded-lg shadow-md p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-copy">Notifications</h1>
            {unreadCount > 0 && (
              <p className="text-sm text-copy-light mt-1">
                You have {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
              </p>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleRefresh}
              className="p-2 hover:bg-surface-hover rounded-full transition-colors"
              title="Refresh"
            >
              <RefreshCwIcon size={20} className="text-copy" />
            </button>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllAsRead}
                className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark transition-colors text-sm"
              >
                Mark all as read
              </button>
            )}
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex space-x-4 mb-6 border-b border-border">
          <button
            onClick={() => { setFilter('all'); setPage(1); }}
            className={`pb-2 px-1 transition-colors ${
              filter === 'all'
                ? 'border-b-2 border-primary text-primary font-semibold'
                : 'text-copy-light hover:text-copy'
            }`}
          >
            All
          </button>
          <button
            onClick={() => { setFilter('unread'); setPage(1); }}
            className={`pb-2 px-1 transition-colors ${
              filter === 'unread'
                ? 'border-b-2 border-primary text-primary font-semibold'
                : 'text-copy-light hover:text-copy'
            }`}
          >
            Unread
          </button>
          <button
            onClick={() => { setFilter('read'); setPage(1); }}
            className={`pb-2 px-1 transition-colors ${
              filter === 'read'
                ? 'border-b-2 border-primary text-primary font-semibold'
                : 'text-copy-light hover:text-copy'
            }`}
          >
            Read
          </button>
        </div>

        {/* Notifications List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="text-copy-light mt-4">Loading notifications...</p>
          </div>
        ) : notifications.length === 0 ? (
          <div className="text-center py-12">
            <BellIcon size={64} className="mx-auto text-copy-light opacity-50 mb-4" />
            <p className="text-copy-light text-lg">No notifications to display</p>
          </div>
        ) : (
          <div className="space-y-2">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-4 rounded-lg border transition-colors ${
                  !notification.read
                    ? 'bg-primary/5 border-primary/20'
                    : 'bg-surface-hover border-border'
                }`}
              >
                <div className="flex items-start space-x-4">
                  <span className="text-3xl flex-shrink-0">
                    {getNotificationIcon(notification.type)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className={`${!notification.read ? 'font-semibold' : ''} text-copy`}>
                      {notification.message}
                    </p>
                    <p className="text-sm text-copy-light mt-1">
                      {formatTimestamp(notification.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2 flex-shrink-0">
                    {!notification.read && (
                      <button
                        onClick={() => handleMarkAsRead(notification.id)}
                        className="p-2 hover:bg-surface-active rounded transition-colors"
                        title="Mark as read"
                      >
                        <CheckIcon size={20} className="text-primary" />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(notification.id)}
                      className="p-2 hover:bg-surface-active rounded transition-colors"
                      title="Delete"
                    >
                      <TrashIcon size={20} className="text-copy-light hover:text-error" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {pagination && pagination.pages > 1 && (
          <div className="flex items-center justify-center space-x-2 mt-6">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 border border-border rounded-md hover:bg-surface-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-copy">
              Page {page} of {pagination.pages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(pagination.pages, p + 1))}
              disabled={page === pagination.pages}
              className="px-4 py-2 border border-border rounded-md hover:bg-surface-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Notifications;
