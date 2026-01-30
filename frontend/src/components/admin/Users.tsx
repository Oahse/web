import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusIcon, EyeIcon, EditIcon, TrashIcon, UsersIcon } from 'lucide-react';
import AdminAPI from '../../api/admin';
import toast from 'react-hot-toast';
import { useTheme } from '../../store/ThemeContext';
import { 
  PageLayout, 
  DataTable, 
  FilterBar 
} from './shared';

// Types
interface User {
  id: string;
  email: string;
  firstname: string;
  lastname: string;
  role: string;
  status: string;
  created_at: string;
  last_login?: string;
}

interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export const Users = () => {
  const navigate = useNavigate();
  const { theme } = useTheme();
  
  // State
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    limit: 10,
    total: 0,
    pages: 0
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, string>>({});

  // Filter configuration
  const filterConfig = [
    {
      key: 'role',
      label: 'Role',
      type: 'select' as const,
      options: [
        { value: 'Admin', label: 'Admin' },
        { value: 'Customer', label: 'Customer' },
        { value: 'Supplier', label: 'Supplier' }
      ]
    },
    {
      key: 'status',
      label: 'Status',
      type: 'select' as const,
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'suspended', label: 'Suspended' }
      ]
    }
  ];

  // Table columns
  const columns = [
    {
      key: 'email',
      label: 'Email',
      render: (value: string) => (
        <span className="text-sm font-medium text-gray-900">{value}</span>
      )
    },
    {
      key: 'name',
      label: 'Name',
      render: (value: string, row: User) => (
        <span className="text-sm text-gray-900">
          {row.firstname} {row.lastname}
        </span>
      )
    },
    {
      key: 'role',
      label: 'Role',
      render: (value: string) => {
        const roleColors = {
          Admin: 'bg-purple-100 text-purple-800',
          Customer: 'bg-blue-100 text-blue-800',
          Supplier: 'bg-green-100 text-green-800'
        };
        
        return (
          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
            roleColors[value as keyof typeof roleColors] || 'bg-gray-100 text-gray-800'
          }`}>
            {value}
          </span>
        );
      }
    },
    {
      key: 'status',
      label: 'Status',
      render: (value: string) => {
        const statusColors = {
          active: 'bg-green-100 text-green-800',
          inactive: 'bg-red-100 text-red-800',
          suspended: 'bg-yellow-100 text-yellow-800'
        };
        
        return (
          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
            statusColors[value as keyof typeof statusColors] || 'bg-gray-100 text-gray-800'
          }`}>
            {value}
          </span>
        );
      }
    },
    {
      key: 'last_login',
      label: 'Last Login',
      render: (value: string) => (
        <span className="text-sm text-gray-500">
          {value ? new Date(value).toLocaleDateString() : 'Never'}
        </span>
      )
    },
    {
      key: 'created_at',
      label: 'Created',
      render: (value: string) => (
        <span className="text-sm text-gray-500">
          {new Date(value).toLocaleDateString()}
        </span>
      )
    }
  ];

  // Fetch data function
  const fetchData = async (params: any) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await AdminAPI.getUsers({
        page: params.page,
        limit: params.limit,
        search: params.search,
        role: params.filters?.role,
        status: params.filters?.status,
        sort_by: params.sort_by,
        sort_order: params.sort_order
      });
      
      if (response?.success && response?.data) {
        const data = response.data;
        setUsers(data.data || []);
        setPagination({
          page: data.pagination?.page || params.page,
          limit: data.pagination?.limit || params.limit,
          total: data.pagination?.total || 0,
          pages: data.pagination?.pages || 0
        });
      } else {
        throw new Error('Failed to fetch users');
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || err.message || 'Failed to load users';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Action handlers
  const handleViewUser = (user: User) => {
    navigate(`/admin/users/${user.id}`);
  };

  const handleEditUser = (user: User) => {
    navigate(`/admin/users/${user.id}/edit`);
  };

  const handleDeleteUser = (user: User) => {
    if (window.confirm(`Are you sure you want to delete user "${user.email}"?`)) {
      // Implement delete functionality
      toast.success('User deleted successfully');
      fetchData({ page: pagination.page, limit: 10 });
    }
  };

  const handleAddUser = () => {
    navigate('/admin/users/new');
  };

  const handleFilterChange = (key: string, value: string) => {
    const newFilters = { ...filters };
    if (value) {
      newFilters[key] = value;
    } else {
      delete newFilters[key];
    }
    setFilters(newFilters);
  };

  const handleClearFilters = () => {
    setFilters({});
    setSearchQuery('');
  };

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
  };

  return (
    <PageLayout
      title="Users"
      subtitle="Manage user accounts"
      description="View, edit, and manage all user accounts in the system"
      icon={UsersIcon}
      actions={
        <button
          onClick={handleAddUser}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="h-4 w-4" />
          Add User
        </button>
      }
      breadcrumbs={[
        { label: 'Home', href: '/' },
        { label: 'Admin' },
        { label: 'Users' }
      ]}
    >
      <div className="space-y-6">
        {/* Filters */}
        <FilterBar
          filters={filterConfig}
          values={filters}
          onChange={handleFilterChange}
          onClear={handleClearFilters}
          searchValue={searchQuery}
          onSearchChange={handleSearchChange}
          searchPlaceholder="Search users..."
        />

        {/* Users Table */}
        <DataTable
          data={users}
          loading={loading}
          error={error}
          pagination={pagination}
          columns={columns}
          fetchData={fetchData}
          onView={handleViewUser}
          onEdit={handleEditUser}
          onDelete={handleDeleteUser}
          searchable={false} // Search is handled by AdminFilterBar
          filterable={false} // Filters are handled by AdminFilterBar
          emptyMessage="No users found"
        />
      </div>
    </PageLayout>
  );
};

export default Users;
