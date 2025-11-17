import { useState, useCallback } from 'react';
import { BellIcon, CheckIcon, TrashIcon, MailIcon, AlertCircleIcon, InfoIcon } from 'lucide-react';
import { usePaginatedApi } from '../../hooks/useApi';
import NotificationAPI from '../../apis/notification';
import ErrorMessage from '../../components/common/ErrorMessage';

export const AdminNotifications = () => {
  const [filter, setFilter] = useState('all');

  const apiCall = useCallback((page: number, limit: number) => {
    return NotificationAPI.getUserNotifications({
      read: filter === 'unread' ? false : filter === 'read' ? true : undefined,
      page,
      limit,
    });
  }, [filter]);

  const {
    data: notifications,
    loading,
    error,
    execute: fetchNotifications,
    page: currentPage,
    limit: itemsPerPage,
    totalPages,
    goToPage,
  } = usePaginatedApi(
    apiCall,
    1,
    20,
    { showErrorToast: false, autoFetch: true }
  );

  if (error) {
    return (
      <div className="p-6">
        <ErrorMessage
          error={error}
          onRetry={() => fetchNotifications()}
          onDismiss={() => {}}
        />
      </div>
    );
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckIcon size={20} className="text-success" />;
      case 'error':
        return <AlertCircleIcon size={20} className="text-error" />;
      case 'warning':
        return <AlertCircleIcon size={20} className="text-warning" />;
      default:
        return <InfoIcon size={20} className="text-info" />;
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between">
        <div className="flex items-center mb-4 md:mb-0">
          <BellIcon size={28} className="mr-3 text-primary" />
          <h1 className="text-2xl font-bold text-main">Notifications</h1>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-md text-sm ${
              filter === 'all'
                ? 'bg-primary text-white'
                : 'bg-surface border border-border text-copy hover:bg-surface-hover'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('unread')}
            className={`px-4 py-2 rounded-md text-sm ${
              filter === 'unread'
                ? 'bg-primary text-white'
                : 'bg-surface border border-border text-copy hover:bg-surface-hover'
            }`}
          >
            Unread
          </button>
          <button
            onClick={() => setFilter('read')}
            className={`px-4 py-2 rounded-md text-sm ${
              filter === 'read'
                ? 'bg-primary text-white'
                : 'bg-surface border border-border text-copy hover:bg-surface-hover'
            }`}
          >
            Read
          </button>
        </div>
      </div>

      <div className="bg-surface rounded-lg shadow-sm border border-border-light">
        {loading ? (
          <div className="divide-y divide-border-light">
            {[...Array(5)].map((_, index) => (
              <div key={index} className="p-4 animate-pulse">
                <div className="flex items-start space-x-4">
                  <div className="w-10 h-10 bg-surface-hover rounded-full"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-surface-hover rounded w-3/4"></div>
                    <div className="h-3 bg-surface-hover rounded w-1/2"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : notifications.length === 0 ? (
          <div className="p-12 text-center">
            <MailIcon size={48} className="mx-auto mb-4 text-copy-lighter" />
            <p className="text-copy-light">No notifications found</p>
          </div>
        ) : (
          <div className="divide-y divide-border-light">
            {notifications.map((notification: any) => (
              <div
                key={notification.id}
                className={`p-4 hover:bg-surface-hover transition-colors ${
                  !notification.read ? 'bg-primary/5' : ''
                }`}
              >
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 mt-1">
                    {getNotificationIcon(notification.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className={`text-sm ${!notification.read ? 'font-semibold text-main' : 'text-copy'}`}>
                          {notification.message}
                        </p>
                        <p className="text-xs text-copy-light mt-1">
                          {notification.created_at ? new Date(notification.created_at).toLocaleString() : 'Just now'}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        {!notification.read && (
                          <button
                            className="p-1 text-copy-light hover:text-success"
                            title="Mark as read"
                          >
                            <CheckIcon size={18} />
                          </button>
                        )}
                        <button
                          className="p-1 text-copy-light hover:text-error"
                          title="Delete"
                        >
                          <TrashIcon size={18} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-copy-light">
            Page {currentPage} of {totalPages}
          </p>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-3 py-1 border border-border rounded-md text-sm text-copy-light bg-background disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border border-border rounded-md text-sm text-copy-light bg-background disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
