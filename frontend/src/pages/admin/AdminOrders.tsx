import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { SearchIcon, FilterIcon, ChevronDownIcon, EyeIcon, PrinterIcon, MoreHorizontalIcon, CalendarIcon, DownloadIcon } from 'lucide-react';
import { usePaginatedApi } from '../../hooks/useAsync';
import { useLocale } from '../../store/LocaleContext';
import { AdminAPI, OrdersAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { Pagination } from '../../components/ui/Pagination';
import { toast } from 'react-hot-toast';

export const AdminOrders = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [submittedSearchTerm, setSubmittedSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showMoreFilters, setShowMoreFilters] = useState(false);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [updatingOrderId, setUpdatingOrderId] = useState<string | null>(null);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const { formatCurrency } = useLocale();
  const [isExporting, setIsExporting] = useState(false);

  // Close export menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (showExportMenu && !target.closest('.export-menu-container')) {
        setShowExportMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showExportMenu]);

  const apiCall = useCallback((page: number, limit: number) => {
    return AdminAPI.getAllOrders({
      status: filterStatus !== 'all' ? filterStatus : undefined,
      q: submittedSearchTerm || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      min_price: minPrice ? parseFloat(minPrice) : undefined,
      max_price: maxPrice ? parseFloat(maxPrice) : undefined,
      page,
      limit,
    });
  }, [filterStatus, submittedSearchTerm, dateFrom, dateTo, minPrice, maxPrice]);

  // API call for orders
  const {
    data: orders,
    loading: ordersLoading,
    error: ordersError,
    execute: fetchOrders,
    page: currentPage,
    limit: itemsPerPage,
    totalPages,
    total: totalOrders,
    goToPage,
  } = usePaginatedApi(
    apiCall,
    1,
    10,
    { showErrorToast: false, autoFetch: true }
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedSearchTerm(searchTerm);
    goToPage(1);
  };

  const handleStatusUpdate = async (orderId: string, newStatus: string) => {
    try {
      setUpdatingOrderId(orderId);
      await AdminAPI.updateOrderStatus(orderId, newStatus);
      // Refresh orders list
      await fetchOrders();
      toast.success('Order status updated successfully');
    } catch (error) {
      console.error('Failed to update order status:', error);
      toast.error('Failed to update order status. Please try again.');
    } finally {
      setUpdatingOrderId(null);
    }
  };

  const handleDownloadInvoice = async (orderId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await AdminAPI.getOrderInvoice(orderId);
      toast.success('Invoice downloaded successfully');
    } catch (error) {
      console.error('Failed to download invoice:', error);
      toast.error('Failed to download invoice');
    }
  };

  const handleExport = async (format: 'csv' | 'excel' | 'pdf') => {
    try {
      setIsExporting(true);
      setShowExportMenu(false);
      
      await OrdersAPI.exportOrders({
        format,
        status: filterStatus !== 'all' ? filterStatus : undefined,
        q: submittedSearchTerm || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        min_price: minPrice ? parseFloat(minPrice) : undefined,
        max_price: maxPrice ? parseFloat(maxPrice) : undefined,
      });
      
      toast.success(`Orders exported to ${format.toUpperCase()} successfully`);
    } catch (error) {
      console.error('Failed to export orders:', error);
      toast.error('Failed to export orders');
    } finally {
      setIsExporting(false);
    }
  };

  // Status options for filter
  const statusOptions = [{
    value: 'all',
    label: 'All Statuses'
  }, {
    value: 'pending',
    label: 'Pending'
  }, {
    value: 'confirmed',
    label: 'Confirmed'
  }, {
    value: 'shipped',
    label: 'Shipped'
  }, {
    value: 'delivered',
    label: 'Delivered'
  }, {
    value: 'cancelled',
    label: 'Cancelled'
  }];

  if (ordersError) {
    return (
      <div className="p-6">
        <ErrorMessage
          error={ordersError}
          onRetry={() => fetchOrders()}
          onDismiss={() => window.location.reload()}
        />
      </div>
    );
  }

  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalOrders || orders.length);

  return (
    <div className="p-4 sm:p-6 max-w-full">
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between">
        <h1 className="text-2xl font-bold text-main mb-2 md:mb-0">Orders</h1>
        <div className="flex items-center space-x-2">
          <button className="flex items-center px-3 py-1.5 bg-surface border border-border rounded-md text-sm">
            <CalendarIcon size={16} className="mr-2" />
            Last 30 Days
          </button>
          <div className="relative export-menu-container">
            <button 
              onClick={() => setShowExportMenu(!showExportMenu)}
              disabled={isExporting}
              className="flex items-center px-3 py-1.5 bg-primary text-white rounded-md text-sm hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <DownloadIcon size={16} className="mr-2" />
              {isExporting ? 'Exporting...' : 'Export'}
              <ChevronDownIcon size={16} className="ml-1" />
            </button>
            {showExportMenu && !isExporting && (
              <div className="absolute right-0 mt-2 w-40 bg-surface rounded-md shadow-lg border border-border-light z-20">
                <div className="py-1">
                  <button
                    onClick={() => handleExport('csv')}
                    className="w-full text-left px-4 py-2 text-sm text-copy hover:bg-surface-hover"
                  >
                    Export as CSV
                  </button>
                  <button
                    onClick={() => handleExport('excel')}
                    className="w-full text-left px-4 py-2 text-sm text-copy hover:bg-surface-hover"
                  >
                    Export as Excel
                  </button>
                  <button
                    onClick={() => handleExport('pdf')}
                    className="w-full text-left px-4 py-2 text-sm text-copy hover:bg-surface-hover"
                  >
                    Export as PDF
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      {/* Filters and search */}
      <div className="bg-surface rounded-lg shadow-sm p-4 mb-6 border border-border-light">
        <form onSubmit={handleSearch}>
          <div className="flex flex-col md:flex-row md:items-center space-y-3 md:space-y-0 md:space-x-4">
            <div className="flex-grow">
              <div className="relative">
                <input type="text" placeholder="Search orders by ID, customer name or email..." className="w-full pl-10 pr-4 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
                <SearchIcon size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-copy-lighter" />
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="relative">
                <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="appearance-none pl-3 pr-10 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy">
                  {statusOptions.map(option => <option key={option.value} value={option.value}>
                      {option.label}
                    </option>)}
                </select>
                <ChevronDownIcon size={16} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-copy-light pointer-events-none" />
              </div>
              <button type="button" onClick={() => setShowMoreFilters(!showMoreFilters)} className="flex items-center px-3 py-2 border border-border rounded-md hover:bg-surface-hover text-copy">
                <FilterIcon size={18} className="mr-2" />
                More Filters
              </button>
              <button type="submit" className="flex items-center px-3 py-2 bg-primary text-white rounded-md hover:bg-primary-dark">
                <SearchIcon size={18} className="mr-2" />
                Search
              </button>
            </div>
          </div>
        </form>
        {showMoreFilters && (
          <div className="mt-4 pt-4 border-t border-border-light">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm text-copy-light mb-1 block">Date From</label>
                <input type="date" className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
              </div>
              <div>
                <label className="text-sm text-copy-light mb-1 block">Date To</label>
                <input type="date" className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" value={dateTo} onChange={e => setDateTo(e.target.value)} />
              </div>
              <div>
                <label className="text-sm text-copy-light mb-1 block">Min Price</label>
                <input type="number" placeholder="0.00" className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" value={minPrice} onChange={e => setMinPrice(e.target.value)} />
              </div>
              <div>
                <label className="text-sm text-copy-light mb-1 block">Max Price</label>
                <input type="number" placeholder="1000.00" className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary bg-background text-copy" value={maxPrice} onChange={e => setMaxPrice(e.target.value)} />
              </div>
            </div>
          </div>
        )}
      </div>
      {/* Orders table */}
      <div className="bg-surface rounded-lg shadow-sm border border-border-light overflow-hidden">
        {/* Desktop Table View */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-background text-left text-copy-light text-sm">
                <th className="py-3 px-4 font-medium">Order ID</th>
                <th className="py-3 px-4 font-medium">Customer</th>
                <th className="py-3 px-4 font-medium">Date</th>
                <th className="py-3 px-4 font-medium">Status</th>
                <th className="py-3 px-4 font-medium">Payment</th>
                <th className="py-3 px-4 font-medium">Items</th>
                <th className="py-3 px-4 font-medium">Total</th>
                <th className="py-3 px-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {ordersLoading ? (
                // Loading skeleton
                [...Array(5)].map((_, index) => (
                  <tr key={index} className="border-t border-border-light animate-pulse">
                    <td className="py-3 px-4"><div className="w-20 h-4 bg-surface-hover rounded"></div></td>
                    <td className="py-3 px-4">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-surface-hover rounded-full mr-3"></div>
                        <div>
                          <div className="w-24 h-4 bg-surface-hover rounded mb-1"></div>
                          <div className="w-32 h-3 bg-surface-hover rounded"></div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4"><div className="w-16 h-4 bg-surface-hover rounded"></div></td>
                    <td className="py-3 px-4"><div className="w-16 h-6 bg-surface-hover rounded-full"></div></td>
                    <td className="py-3 px-4"><div className="w-12 h-6 bg-surface-hover rounded-full"></div></td>
                    <td className="py-3 px-4"><div className="w-8 h-4 bg-surface-hover rounded"></div></td>
                    <td className="py-3 px-4"><div className="w-16 h-4 bg-surface-hover rounded"></div></td>
                    <td className="py-3 px-4"><div className="w-20 h-8 bg-surface-hover rounded"></div></td>
                  </tr>
                ))
              ) : (
                (orders || []).map((order) => (
                  <tr key={order.id} className="border-t border-border-light hover:bg-surface-hover">
                    <td className="py-3 px-4">
                      <Link to={`/admin/orders/${order.id}`} className="font-medium text-primary hover:underline">
                        {order.id}
                      </Link>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-primary/20 rounded-full mr-3 flex items-center justify-center text-xs font-medium text-primary">
                          {order.user?.firstname?.[0] || order.user?.full_name?.[0] || 'U'}
                        </div>
                        <div>
                          <p className="font-medium text-main">
                            {order.user?.full_name || `${order.user?.firstname} ${order.user?.lastname}` || 'Unknown Customer'}
                          </p>
                          <p className="text-xs text-copy-light">
                            {order.user?.email || 'No email'}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-copy-light">
                      {new Date(order.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        order.status === 'delivered' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
                        order.status === 'shipped' || order.status === 'out_for_delivery' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300' :
                        order.status === 'confirmed' || order.status === 'processing' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' :
                        order.status === 'cancelled' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' :
                        'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      }`}>
                        {order.status?.charAt(0).toUpperCase() + order.status?.slice(1).replace('_', ' ') || 'Pending'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        order.payment_status === 'completed' || order.payment_status === 'succeeded' || order.payment_status === 'paid' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
                        order.payment_status === 'pending' || order.payment_status === 'processing' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' :
                        order.payment_status === 'failed' || order.payment_status === 'cancelled' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' :
                        'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      }`}>
                        {order.payment_status?.charAt(0).toUpperCase() + order.payment_status?.slice(1).replace('_', ' ') || 'Completed'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">{order.items?.length || 0}</td>
                    <td className="py-3 px-4 font-medium text-main">
                      {formatCurrency(order.total_amount || 0)}
                    </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <Link to={`/admin/orders/${order.id}`} className="p-1 text-copy-light hover:text-primary" title="View">
                        <EyeIcon size={18} />
                      </Link>
                      <button 
                        onClick={(e) => handleDownloadInvoice(order.id, e)}
                        className="p-1 text-copy-light hover:text-main" 
                        title="Download Invoice"
                      >
                        <PrinterIcon size={18} />
                      </button>
                      <div className="relative group">
                        <button className="p-1 text-copy-light hover:text-main" disabled={updatingOrderId === order.id}>
                          <MoreHorizontalIcon size={18} />
                        </button>
                        <div className="absolute right-0 mt-1 hidden group-hover:block bg-surface rounded-md shadow-lg border border-border-light z-10 w-44">
                          <div className="py-1">
                            <div className="px-4 py-2 text-xs text-copy-light font-medium">Update Status</div>
                            {statusOptions.filter(opt => opt.value !== 'all' && opt.value !== order.status).map(statusOpt => (
                              <button
                                key={statusOpt.value}
                                onClick={() => handleStatusUpdate(order.id, statusOpt.value)}
                                disabled={updatingOrderId === order.id}
                                className="w-full text-left px-4 py-2 text-sm text-copy hover:bg-surface-hover disabled:opacity-50"
                              >
                                {statusOpt.label}
                              </button>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>))
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile List View */}
        <div className="md:hidden">
          {ordersLoading ? (
            <div className="space-y-3 p-4">
              {[...Array(5)].map((_, index) => (
                <div key={index} className="bg-background rounded-lg p-4 border border-border-light animate-pulse">
                  <div className="space-y-2">
                    <div className="w-3/4 h-4 bg-surface-hover rounded"></div>
                    <div className="w-1/2 h-3 bg-surface-hover rounded"></div>
                    <div className="w-full h-3 bg-surface-hover rounded"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (orders || []).length > 0 ? (
            <div className="space-y-3 p-4">
              {(orders || []).map((order) => (
                <div key={order.id} className="bg-background rounded-lg p-4 border border-border-light">
                  <div className="space-y-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <Link to={`/admin/orders/${order.id}`} className="font-medium text-primary hover:underline text-sm">
                          Order #{order.id?.slice(0, 8)}
                        </Link>
                        <p className="text-xs text-copy-light mt-1">
                          {new Date(order.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        order.status === 'delivered' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
                        order.status === 'shipped' || order.status === 'out_for_delivery' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300' :
                        order.status === 'confirmed' || order.status === 'processing' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' :
                        order.status === 'cancelled' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' :
                        'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      }`}>
                        {order.status?.charAt(0).toUpperCase() + order.status?.slice(1).replace('_', ' ') || 'Pending'}
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-primary/20 rounded-full flex items-center justify-center text-xs font-medium text-primary">
                        {order.user?.firstname?.[0] || order.user?.full_name?.[0] || 'U'}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-main truncate">
                          {order.user?.full_name || `${order.user?.firstname} ${order.user?.lastname}` || 'Unknown'}
                        </p>
                        <p className="text-xs text-copy-light truncate">
                          {order.user?.email || 'No email'}
                        </p>
                      </div>
                    </div>

                    <div className="flex justify-between items-center pt-2 border-t border-border-light">
                      <div>
                        <p className="text-xs text-copy-light">Total</p>
                        <p className="text-sm font-semibold text-main">{formatCurrency(order.total_amount || 0)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-copy-light">Items</p>
                        <p className="text-sm font-medium text-main text-center">{order.items?.length || 0}</p>
                      </div>
                      <div>
                        <p className="text-xs text-copy-light">Payment</p>
                        <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                          order.payment_status === 'completed' || order.payment_status === 'succeeded' || order.payment_status === 'paid' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
                          order.payment_status === 'pending' || order.payment_status === 'processing' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' :
                          order.payment_status === 'failed' || order.payment_status === 'cancelled' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' :
                          'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                        }`}>
                          {order.payment_status?.charAt(0).toUpperCase() + order.payment_status?.slice(1).replace('_', ' ') || 'Completed'}
                        </span>
                      </div>
                    </div>

                    <div className="flex space-x-2 pt-2">
                      <Link 
                        to={`/admin/orders/${order.id}`} 
                        className="flex-1 text-center py-2 px-3 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/90"
                      >
                        View Details
                      </Link>
                      <button 
                        onClick={(e) => handleDownloadInvoice(order.id, e)}
                        className="py-2 px-3 border border-border-light rounded-md text-sm text-copy-light hover:bg-surface-hover"
                        title="Download Invoice"
                      >
                        <PrinterIcon size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-12 text-center text-copy-light">
              <p>No orders found</p>
            </div>
          )}
        </div>

        {/* Empty state for desktop */}
        {orders.length === 0 && !ordersLoading && (
          <div className="hidden md:block py-12 text-center text-copy-light">
            <p>No orders found</p>
          </div>
        )}
      </div>
      {/* Pagination */}
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        totalItems={totalOrders || orders.length}
        itemsPerPage={itemsPerPage}
        onPageChange={goToPage}
        showingStart={startIndex + 1}
        showingEnd={endIndex}
        itemName="orders"
        className="mt-6"
      />
    </div>
  );
};
export default AdminOrders;