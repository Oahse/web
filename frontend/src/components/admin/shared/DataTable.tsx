import React, { useState, useEffect } from 'react';
import { 
  Loader, 
  AlertCircle, 
  Eye, 
  ChevronLeft, 
  ChevronRight, 
  SearchIcon, 
  FilterIcon, 
  PlusIcon,
  ArrowUpDownIcon,
  DownloadIcon,
  TrashIcon,
  EditIcon
} from 'lucide-react';
import { useTheme } from '../../../store/ThemeContext';
import Dropdown from '../../ui/Dropdown';

// Types
export interface Column<T = any> {
  key: string; // Changed from keyof T to string for flexibility
  label: string;
  sortable?: boolean;
  render?: (value: any, row: T) => React.ReactNode;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

export interface FilterOption {
  value: string;
  label: string;
}

export interface FilterConfig {
  key: string;
  label: string;
  type: 'select' | 'text';
  options?: FilterOption[];
  placeholder?: string;
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface AdminDataTableProps<T = any> {
  // Data
  data: T[];
  loading: boolean;
  error: string | null;
  pagination: PaginationInfo;
  
  // Columns
  columns: Column<T>[];
  
  // Actions
  fetchData: (params: FetchParams) => Promise<void>;
  onRowClick?: (row: T) => void;
  onEdit?: (row: T) => void;
  onDelete?: (row: T) => void;
  onView?: (row: T) => void;
  
  // Features
  searchable?: boolean;
  filterable?: boolean;
  sortable?: boolean;
  paginated?: boolean;
  selectable?: boolean;
  exportable?: boolean;
  
  // Customization
  searchPlaceholder?: string;
  filters?: FilterConfig[];
  actions?: React.ReactNode;
  emptyMessage?: string;
  className?: string;
  
  // Pagination
  limit?: number;
  
  // Styling
  tableClassName?: string;
  headerClassName?: string;
  rowClassName?: string | ((row: T) => string);
}

export interface FetchParams {
  page: number;
  limit: number;
  search?: string;
  filters?: Record<string, string>;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export const AdminDataTable = <T extends Record<string, any>>({
  data,
  loading,
  error,
  pagination,
  columns,
  fetchData,
  onRowClick,
  onEdit,
  onDelete,
  onView,
  searchable = true,
  filterable = true,
  sortable = true,
  paginated = true,
  selectable = false,
  exportable = false,
  searchPlaceholder = "Search...",
  filters = [],
  actions,
  emptyMessage = "No data available",
  className = "",
  limit = 10,
  tableClassName = "",
  headerClassName = "",
  rowClassName = ""
}: AdminDataTableProps<T>) => {
  const { theme } = useTheme();
  
  // State
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});
  const [sortBy, setSortBy] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedRows, setSelectedRows] = useState<Set<string | number>>(new Set());

  // Fetch data on mount and when params change
  useEffect(() => {
    fetchData({
      page,
      limit,
      search: searchQuery || undefined,
      filters: Object.keys(activeFilters).length > 0 ? activeFilters : undefined,
      sort_by: sortBy || undefined,
      sort_order: sortOrder
    });
  }, [page, searchQuery, activeFilters, sortBy, sortOrder]);

  // Handle search
  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setPage(1); // Reset to first page
  };

  // Handle filter change
  const handleFilterChange = (key: string, value: string) => {
    const newFilters = { ...activeFilters };
    if (value) {
      newFilters[key] = value;
    } else {
      delete newFilters[key];
    }
    setActiveFilters(newFilters);
    setPage(1); // Reset to first page
  };

  // Handle sort
  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
    setPage(1); // Reset to first page
  };

  // Handle pagination
  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  // Handle row selection
  const handleRowSelect = (rowId: string | number) => {
    const newSelected = new Set(selectedRows);
    if (newSelected.has(rowId)) {
      newSelected.delete(rowId);
    } else {
      newSelected.add(rowId);
    }
    setSelectedRows(newSelected);
  };

  // Handle select all
  const handleSelectAll = () => {
    if (selectedRows.size === data.length) {
      setSelectedRows(new Set());
    } else {
      setSelectedRows(new Set(data.map(row => row.id)));
    }
  };

  // Export data
  const handleExport = () => {
    // Implement export functionality
    console.log('Exporting data...');
  };

  // Render cell content
  const renderCell = (column: Column<T>, row: T) => {
    const value = row[column.key];
    if (column.render) {
      return column.render(value, row);
    }
    return value;
  };

  // Get row class name
  const getRowClassName = (row: T) => {
    if (typeof rowClassName === 'function') {
      return rowClassName(row);
    }
    return rowClassName;
  };

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 ${className}`}>
      {/* Header with search and filters */}
      {(searchable || filterable || actions || exportable) && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            {/* Search and Filters */}
            <div className="flex-1 flex flex-col sm:flex-row gap-3">
              {searchable && (
                <div className="relative flex-1 max-w-md">
                  <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 dark:text-gray-500" />
                  <input
                    type="text"
                    placeholder={searchPlaceholder}
                    value={searchQuery}
                    onChange={(e) => handleSearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400"
                  />
                </div>
              )}
              
              {filterable && filters.map((filter) => (
                <div key={filter.key} className="min-w-[150px]">
                  {filter.type === 'select' ? (
                    <select
                      value={activeFilters[filter.key] || ''}
                      onChange={(e) => handleFilterChange(filter.key, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="">{filter.placeholder || `Select ${filter.label}`}</option>
                      {filter.options?.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      placeholder={filter.placeholder || `Filter by ${filter.label}`}
                      value={activeFilters[filter.key] || ''}
                      onChange={(e) => handleFilterChange(filter.key, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400"
                    />
                  )}
                </div>
              ))}
            </div>
            
            {/* Actions */}
            <div className="flex items-center gap-2">
              {actions}
              {exportable && (
                <button
                  onClick={handleExport}
                  className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 rounded-md transition-colors"
                >
                  <DownloadIcon className="h-4 w-4" />
                  <span className="hidden sm:inline">Export</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader className="h-6 w-6 animate-spin text-blue-600 dark:text-blue-400 mr-2" />
          <span className="text-gray-600 dark:text-gray-400">Loading...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="flex items-center justify-center py-12">
          <AlertCircle className="h-6 w-6 text-red-500 dark:text-red-400 mr-2" />
          <span className="text-red-600 dark:text-red-400">{error}</span>
        </div>
      )}

      {/* Data Table */}
      {!loading && !error && (
        <>
          {data.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 dark:text-gray-500 mb-2">
                <FilterIcon className="h-12 w-12 mx-auto" />
              </div>
              <p className="text-gray-500 dark:text-gray-400">{emptyMessage}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className={`w-full ${tableClassName}`}>
                {/* Table Header */}
                <thead className={`bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 ${headerClassName}`}>
                  <tr>
                    {selectable && (
                      <th className="px-4 py-3 text-left">
                        <input
                          type="checkbox"
                          checked={selectedRows.size === data.length}
                          onChange={handleSelectAll}
                          className="rounded border-gray-300 dark:border-gray-600 text-blue-600 dark:text-blue-400 focus:ring-blue-500 focus:ring-blue-400"
                        />
                      </th>
                    )}
                    {columns.map((column) => (
                      <th
                        key={String(column.key)}
                        className={`px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider ${
                          column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : ''
                        } ${column.sortable && sortable ? 'cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800' : ''}`}
                        style={{ width: column.width }}
                        onClick={() => column.sortable && sortable && handleSort(String(column.key))}
                      >
                        <div className="flex items-center gap-1">
                          {column.label}
                          {column.sortable && sortable && (
                            <ArrowUpDownIcon className="h-3 w-3 text-gray-400 dark:text-gray-500" />
                          )}
                        </div>
                      </th>
                    ))}
                    {(onView || onEdit || onDelete) && (
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        <span className="hidden sm:inline">Actions</span>
                        <span className="sm:hidden">•••</span>
                      </th>
                    )}
                  </tr>
                </thead>

                {/* Table Body */}
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {data.map((row) => (
                    <tr
                      key={row.id}
                      className={`hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${getRowClassName(row)}`}
                      onClick={() => onRowClick && onRowClick(row)}
                    >
                      {selectable && (
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            checked={selectedRows.has(row.id)}
                            onChange={() => handleRowSelect(row.id)}
                            className="rounded border-gray-300 dark:border-gray-600 text-blue-600 dark:text-blue-400 focus:ring-blue-500 focus:ring-blue-400"
                          />
                        </td>
                      )}
                      {columns.map((column) => (
                        <td
                          key={String(column.key)}
                          className={`px-4 py-3 text-sm text-gray-900 dark:text-gray-100 ${
                            column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : ''
                          }`}
                        >
                          {renderCell(column, row)}
                        </td>
                      ))}
                      {(onView || onEdit || onDelete) && (
                        <td className="px-4 py-3 text-right text-sm font-medium">
                          <div className="flex items-center justify-end gap-2">
                            {onView && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onView(row);
                                }}
                                className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300"
                                title="View"
                              >
                                <EyeIcon className="h-4 w-4" />
                              </button>
                            )}
                            {onEdit && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onEdit(row);
                                }}
                                className="text-green-600 dark:text-green-400 hover:text-green-900 dark:hover:text-green-300"
                                title="Edit"
                              >
                                <EditIcon className="h-4 w-4" />
                              </button>
                            )}
                            {onDelete && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onDelete(row);
                                }}
                                className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300"
                                title="Delete"
                              >
                                <TrashIcon className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {paginated && pagination.pages > 1 && (
            <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="text-sm text-gray-700 dark:text-gray-300">
                  <span className="block sm:hidden">
                    Page {pagination.page} of {pagination.pages}
                  </span>
                  <span className="hidden sm:block">
                    Showing {((pagination.page - 1) * pagination.limit) + 1} to{' '}
                    {Math.min(pagination.page * pagination.limit, pagination.total)} of{' '}
                    {pagination.total} results
                  </span>
                </div>
                <div className="flex items-center justify-center sm:justify-end gap-2">
                  <button
                    onClick={() => handlePageChange(pagination.page - 1)}
                    disabled={pagination.page <= 1}
                    className="p-2 border border-gray-300 dark:border-gray-600 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  
                  <span className="text-sm text-gray-700 dark:text-gray-300 hidden sm:block">
                    Page {pagination.page} of {pagination.pages}
                  </span>
                  
                  <button
                    onClick={() => handlePageChange(pagination.page + 1)}
                    disabled={pagination.page >= pagination.pages}
                    className="p-2 border border-gray-300 dark:border-gray-600 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AdminDataTable;
