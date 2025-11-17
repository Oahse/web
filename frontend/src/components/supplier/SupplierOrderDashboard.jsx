import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import OrderDetails from '../order/OrderDetails';
import { usePaginatedApi } from '../../hooks/useApi';
import { OrdersAPI } from '../../apis';

/**
 * SupplierOrderDashboard component provides a dashboard view for suppliers to manage their orders.
 * It includes features for filtering, bulk actions, and viewing order details.
 */
const SupplierOrderDashboard = () => {
  // Custom hook to fetch paginated order data from the API
  const { data: paginatedOrders, loading, error, execute: fetchOrders } = usePaginatedApi();
  // State to hold the currently selected order for detail viewing
  const [selectedOrder, setSelectedOrder] = useState(null);
  // State for filtering orders (e.g., by status, date range)
  const [filters, setFilters] = useState({});
  // State to manage selected orders for bulk actions
  const [selectedOrders, setSelectedOrders] = useState(new Set());
  // State to store the chosen bulk action (e.g., 'Shipped', 'Processing')
  const [bulkAction, setBulkAction] = useState('');

  // Effect hook to fetch orders whenever the filters change
  useEffect(() => {
    fetchOrders(() => OrdersAPI.getSupplierOrders({ status: filters.status, date_from: filters.startDate, date_to: filters.endDate }));
  }, [fetchOrders, filters]);

  /**
   * Determines the Tailwind CSS classes for an order status to apply appropriate styling.
   * @param {string} status - The status of the order.
   * @returns {string} Tailwind CSS classes for the status badge.
   */
  const getStatusColor = (status) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'shipped':
        return 'bg-purple-100 text-purple-800';
      case 'delivered':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'returned':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  /**
   * Toggles the selection state of an individual order for bulk actions.
   * @param {string} orderId - The ID of the order to toggle.
   */
  const handleOrderSelect = (orderId) => {
    const newSelected = new Set(selectedOrders);
    if (newSelected.has(orderId)) {
      newSelected.delete(orderId);
    } else {
      newSelected.add(orderId);
    }
    setSelectedOrders(newSelected);
  };

  /**
   * Selects or deselects all orders currently displayed.
   */
  const handleSelectAll = () => {
    if (selectedOrders.size === paginatedOrders?.data.length) {
      setSelectedOrders(new Set()); // Deselect all
    } else {
      setSelectedOrders(new Set(paginatedOrders?.data.map(order => order.id))); // Select all
    }
  };

  /**
   * Executes the chosen bulk action on all selected orders.
   * Currently supports updating order status.
   */
  const handleBulkAction = async () => {
    if (!bulkAction || selectedOrders.size === 0) return; // Do nothing if no action or no orders selected

    for (const orderId of selectedOrders) {
      try {
        // Update status for each selected order
        await OrdersAPI.updateOrderStatus(orderId, { status: bulkAction });
      } catch (error) {
        console.error(`Failed to update order ${orderId}`, error);
      }
    }

    fetchOrders(() => OrdersAPI.getSupplierOrders()); // Re-fetch orders to reflect changes
    setSelectedOrders(new Set()); // Clear selection
    setBulkAction(''); // Reset bulk action dropdown
  };

  /**
   * Handles updating the status of a single order.
   * @param {string} orderId - The ID of the order to update.
   * @param {string} newStatus - The new status for the order.
   */
  const handleStatusUpdate = async (orderId, newStatus) => {
    try {
      const result = await OrdersAPI.updateOrderStatus(orderId, { status: newStatus });
      if (result) {
        fetchOrders(() => OrdersAPI.getSupplierOrders()); // Re-fetch orders
        // If the updated order is currently selected, update its status in the local state
        if (selectedOrder?.id === orderId) {
          setSelectedOrder(prev => prev ? { ...prev, status: newStatus } : null);
        }
      }
    } catch (error) {
      console.error('Failed to update order status', error);
    }
  };

  /**
   * Handles adding a note to a selected order.
   * @param {string} note - The note content to add.
   */
  const handleAddNote = async (note) => {
    if (!selectedOrder) return; // Ensure an order is selected

    try {
      await OrdersAPI.addOrderNote(selectedOrder.id, note);
      fetchOrders(() => OrdersAPI.getSupplierOrders()); // Re-fetch orders to show the new note
    } catch (error) {
      console.error('Failed to add note', error);
    }
  };

  // Display loading spinner while orders are being fetched
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  // Display error message if fetching orders failed
  if (error) {
    return <div className="p-6 text-center text-red-500">Error: {error.message}</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Order Management</h1>
          <p className="text-gray-600 mt-1">Manage your orders and track their progress</p>
        </div>
        <div className="flex items-center space-x-3">
          <span className="text-sm text-gray-500">
            {paginatedOrders?.pagination.total || 0} orders
          </span>
        </div>
      </div>

      {/* Filters Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              value={filters.status || ''}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value || undefined }))}
            >
              <option value="">All Statuses</option>
              <option value="Pending">Pending</option>
              <option value="Processing">Processing</option>
              <option value="Shipped">Shipped</option>
              <option value="Delivered">Delivered</option>
              <option value="Cancelled">Cancelled</option>
              <option value="Returned">Returned</option>
            </select>
          </div>

          {/* Start Date Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
            <input
              type="date"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              value={filters.startDate || ''}
              onChange={(e) => setFilters(prev => ({ ...prev, startDate: e.target.value || undefined }))}
            />
          </div>

          {/* End Date Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
            <input
              type="date"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              value={filters.endDate || ''}
              onChange={(e) => setFilters(prev => ({ ...prev, endDate: e.target.value || undefined }))}
            />
          </div>

          {/* Amount Range Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Amount Range</label>
            <div className="flex space-x-2">
              <input
                type="number"
                placeholder="Min"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                value={filters.minAmount || ''}
                onChange={(e) => setFilters(prev => ({ ...prev, minAmount: e.target.value ? Number(e.target.value) : undefined }))}
              />
              <input
                type="number"
                placeholder="Max"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                value={filters.maxAmount || ''}
                onChange={(e) => setFilters(prev => ({ ...prev, maxAmount: e.target.value ? Number(e.target.value) : undefined }))}
              />
            </div>
          </div>
        </div>

        {/* Clear Filters Button */}
        <div className="mt-4 flex items-center justify-between">
          <button
            onClick={() => setFilters({})}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Bulk Actions Section */}
      {selectedOrders.size > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-sm font-medium text-blue-900">
                {selectedOrders.size} orders selected
              </span>
              <select
                className="border border-blue-300 rounded-md px-3 py-1 text-sm bg-white"
                value={bulkAction}
                onChange={(e) => setBulkAction(e.target.value)}
              >
                <option value="">Choose action...</option>
                <option value="Shipped">Mark as Shipped</option>
                <option value="Processing">Mark as Processing</option>
                <option value="export">Export Selected</option>
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleBulkAction}
                disabled={!bulkAction}
                className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Apply
              </button>
              <button
                onClick={() => setSelectedOrders(new Set())}
                className="px-3 py-1 text-blue-600 text-sm hover:text-blue-800"
              >
                Clear Selection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Orders Table Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedOrders.size === paginatedOrders?.data.length && paginatedOrders?.data.length > 0}
                    onChange={handleSelectAll}
                    className="rounded border-gray-300"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Order
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Customer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedOrders?.data.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedOrders.has(order.id)}
                      onChange={() => handleOrderSelect(order.id)}
                      className="rounded border-gray-300"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        #{order.id.slice(-8)}
                      </div>
                      <div className="text-sm text-gray-500">
                        {order.items.length} items
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      User {order.user_id.slice(-8)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(order.status)}`}>
                      {order.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {order.currency}{order.total_amount}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {format(new Date(order.created_at), 'MMM dd, yyyy')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => setSelectedOrder(order)}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Empty state for orders table */}
        {paginatedOrders?.data.length === 0 && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📦</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No orders found</h3>
            <p className="text-gray-500">
              {paginatedOrders?.pagination.total === 0 
                ? "You don't have any orders yet." 
                : "No orders match your current filters."
              }
            </p>
          </div>
        )}
      </div>

      {/* Order Details Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Order Details - #{selectedOrder.id.slice(-8)}
              </h2>
              <button
                onClick={() => setSelectedOrder(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="p-6">
              <OrderDetails
                order={selectedOrder}
                editable={true}
                showTracking={true}
                onAddNote={handleAddNote}
                onStatusUpdate={handleStatusUpdate}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SupplierOrderDashboard;