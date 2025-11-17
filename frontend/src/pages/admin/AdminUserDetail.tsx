import { useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeftIcon, EditIcon, TrashIcon, ShoppingBagIcon, CheckCircleIcon, XCircleIcon, MailIcon, PhoneIcon, CalendarIcon } from 'lucide-react';
import { useApi } from '../../hooks/useApi';
import { AdminAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';

export const AdminUserDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: apiResponse, loading, error, execute } = useApi();

  useEffect(() => {
    if (id) {
      execute(AdminAPI.getUser, id);
    }
  }, [id, execute]);

  if (error) {
    return (
      <div className="p-6">
        <ErrorMessage 
          error={error} 
          onRetry={() => id && execute(AdminAPI.getUser, id)}
          onDismiss={() => navigate('/admin/users')}
        />
      </div>
    );
  }

  if (loading || !apiResponse) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-surface-hover rounded w-1/3 mb-6"></div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-surface rounded-lg p-6 border border-border-light">
                <div className="h-6 bg-surface-hover rounded w-1/4 mb-4"></div>
                <div className="space-y-3">
                  <div className="h-4 bg-surface-hover rounded"></div>
                  <div className="h-4 bg-surface-hover rounded w-5/6"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Extract the actual user data from the API response
  const user = apiResponse?.data || apiResponse;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={() => navigate('/admin/users')}
            className="mr-4 p-2 hover:bg-surface-hover rounded-md"
          >
            <ArrowLeftIcon size={20} />
          </button>
          <div className="flex items-center">
            <div className="w-12 h-12 bg-primary/20 rounded-full flex items-center justify-center text-lg font-medium text-primary mr-4">
              {user.firstname?.[0] || 'U'}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-main">
                {user.firstname} {user.lastname}
              </h1>
              <p className="text-sm text-copy-light">User ID: {user.id}</p>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            to={`/admin/users/${user.id}/edit`}
            className="flex items-center px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark"
          >
            <EditIcon size={18} className="mr-2" />
            Edit User
          </Link>
          <button className="flex items-center px-4 py-2 border border-error text-error rounded-md hover:bg-error/10">
            <TrashIcon size={18} className="mr-2" />
            Delete
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* User Information */}
          <div className="bg-surface rounded-lg p-6 border border-border-light">
            <h2 className="text-lg font-semibold text-main mb-4">User Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-copy-light mb-1">First Name</p>
                <p className="text-copy font-medium">{user.firstname || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-copy-light mb-1">Last Name</p>
                <p className="text-copy font-medium">{user.lastname || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-copy-light mb-1">Email</p>
                <div className="flex items-center">
                  <MailIcon size={16} className="text-copy-light mr-2" />
                  <p className="text-copy font-medium">{user.email}</p>
                </div>
              </div>
              <div>
                <p className="text-sm text-copy-light mb-1">Phone</p>
                <div className="flex items-center">
                  <PhoneIcon size={16} className="text-copy-light mr-2" />
                  <p className="text-copy font-medium">{user.phone || 'N/A'}</p>
                </div>
              </div>
              <div>
                <p className="text-sm text-copy-light mb-1">Role</p>
                <span className={`inline-block px-3 py-1 rounded-full text-sm ${
                  user.role === 'Admin' ? 'bg-error/10 text-error' :
                  user.role === 'Supplier' ? 'bg-warning/10 text-warning' :
                  'bg-info/10 text-info'
                }`}>
                  {user.role || 'Customer'}
                </span>
              </div>
              <div>
                <p className="text-sm text-copy-light mb-1">Member Since</p>
                <div className="flex items-center">
                  <CalendarIcon size={16} className="text-copy-light mr-2" />
                  <p className="text-copy font-medium">
                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Orders */}
          <div className="bg-surface rounded-lg p-6 border border-border-light">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-main">Recent Orders</h2>
              <Link
                to={`/admin/orders?user=${user.id}`}
                className="text-sm text-primary hover:underline"
              >
                View All Orders
              </Link>
            </div>
            <div className="text-center text-copy-light py-8">
              <ShoppingBagIcon size={48} className="mx-auto mb-2 opacity-50" />
              <p>Order history will be displayed here</p>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status */}
          <div className="bg-surface rounded-lg p-6 border border-border-light">
            <h2 className="text-lg font-semibold text-main mb-4">Status</h2>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-copy-light mb-2">Account Status</p>
                <div className={`flex items-center ${user.active ? 'text-success' : 'text-error'}`}>
                  {user.active ? <CheckCircleIcon size={20} className="mr-2" /> : <XCircleIcon size={20} className="mr-2" />}
                  <span className="font-medium">{user.active ? 'Active' : 'Inactive'}</span>
                </div>
              </div>
              <div>
                <p className="text-sm text-copy-light mb-2">Email Verified</p>
                <div className={`flex items-center ${user.verified ? 'text-success' : 'text-warning'}`}>
                  {user.verified ? <CheckCircleIcon size={20} className="mr-2" /> : <XCircleIcon size={20} className="mr-2" />}
                  <span className="font-medium">{user.verified ? 'Verified' : 'Not Verified'}</span>
                </div>
              </div>
              <div>
                <p className="text-sm text-copy-light mb-2">Last Login</p>
                <p className="text-copy text-sm">
                  {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}
                </p>
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-surface rounded-lg p-6 border border-border-light">
            <h2 className="text-lg font-semibold text-main mb-4">Quick Stats</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <ShoppingBagIcon size={20} className="text-primary mr-2" />
                  <span className="text-sm text-copy-light">Total Orders</span>
                </div>
                <span className="font-medium text-main">{user.orders_count || 0}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="bg-surface rounded-lg p-6 border border-border-light">
            <h2 className="text-lg font-semibold text-main mb-4">Actions</h2>
            <div className="space-y-2">
              <button className="w-full px-4 py-2 border border-border rounded-md hover:bg-surface-hover text-copy">
                Reset Password
              </button>
              <button className="w-full px-4 py-2 border border-border rounded-md hover:bg-surface-hover text-copy">
                {user.active ? 'Deactivate Account' : 'Activate Account'}
              </button>
              <button className="w-full px-4 py-2 border border-border rounded-md hover:bg-surface-hover text-copy">
                Send Email
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
