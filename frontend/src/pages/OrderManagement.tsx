import React, { useState, useEffect } from 'react';
import OrderList from '../components/order/OrderList';
import OrderDetails from '../components/order/OrderDetails';
import SupplierOrderDashboard from '../components/supplier/SupplierOrderDashboard';
import { useAuth } from '../contexts/AuthContext';
import { usePaginatedApi } from '../hooks/useApi';
import { OrdersAPI } from '../apis';

/**
 * OrderManagement component provides a centralized view for managing orders.
 * Its functionality adapts based on the authenticated user's role (customer, supplier, or admin).
 */
const OrderManagement = () => {
  // Access user information from the authentication context
  const { user } = useAuth();
  // State to hold the currently selected order for detail viewing
  const [selectedOrder, setSelectedOrder] = useState(null);
  // State for filtering orders (e.g., by status, date range)
  const [filters, setFilters] = useState({});
  // State to toggle between list view and dashboard view for suppliers
  const [view, setView] = useState('list');

  /**
   * Determines the user's role based on the authenticated user object.
   * Defaults to 'customer' if no user is logged in or role is not recognized.
   * @returns {'customer' | 'supplier' | 'admin'} The determined role.
   */
  const getUserRole = () => {
    if (!user) return 'customer';
    switch (user.role) {
      case 'Supplier':
        return 'supplier';
      case 'Admin':
      case 'SuperAdmin':
      case 'GodAdmin':
        return 'admin';
      default:
        return 'customer';
    }
  };

  const userRole = getUserRole();

  // Custom hook for fetching paginated API data
  const {
    data: paginatedOrders,
    loading,
    execute: fetchOrders // Function to manually trigger data fetching
  } = usePaginatedApi({ showErrorToast: false });

  /**
   * Effect hook to fetch orders whenever user role or filters change.
   * Constructs the appropriate API call based on the user's role.
   */
  useEffect(() => {
    let apiCall;
    // Prepare parameters for the API call
    const params = {
      page: 1,
      limit: 20,
      status: filters.status,
      date_from: filters.startDate,
      date_to: filters.endDate,
    };

    // Select the correct API endpoint based on user role
    switch (userRole) {
      case 'supplier':
        apiCall = () => OrdersAPI.getSupplierOrders(params);
        break;
      case 'admin':
        apiCall = () => OrdersAPI.getAllOrders({ ...params, customer_id: filters.userId });
        break;
      default:
        apiCall = () => OrdersAPI.getOrders(params);
    }
    fetchOrders(apiCall); // Execute the API call
  }, [userRole, filters, fetchOrders]);

  /**
   * Handles updating the status of an order.
   * @param {string} orderId - The ID of the order to update.
   * @param {string} newStatus - The new status for the order.
   */
  const handleStatusUpdate = async (orderId, newStatus) => {
    try {
      // Call the API to update the order status
      const result = await OrdersAPI.updateOrderStatus(orderId, { status: newStatus });
      if (result) {
        fetchOrders(OrdersAPI.getOrders); // Re-fetch all orders to reflect the change
        // If the updated order is currently selected, update its status in the local state
        if (selectedOrder?.id === orderId) {
          setSelectedOrder(prev => prev ? { ...prev, status: newStatus } : null);
        }
      }
    } catch (error) {
      console.error("Failed to update order status", error);
    }
  };

  /**
   * Handles adding a note to a selected order.
   * @param {string} note - The note content to add.
   */
  const handleAddNote = async (note) => {
    if (!selectedOrder) return; // Ensure an order is selected

    try {
      // Call the API to add a note to the order
      const result = await OrdersAPI.addOrderNote(selectedOrder.id, note);
      if (result) {
        // Update the selected order's notes in the local state
        setSelectedOrder(prev => prev ? { ...prev, notes: [result, ...prev.notes] } : null);
      }
    } catch (error) {
      console.error("Failed to add order note", error);
    }
  };

  /**
   * Handles a click on a notification, typically to view the associated order.
   * @param {object} notification - The notification object, potentially containing an orderId.
   */
  const handleNotificationClick = (notification) => {
    if (notification.orderId) {
      // Find the order in the currently fetched paginated orders
      const order = paginatedOrders?.data.find(o => o.id === notification.orderId);
      if (order) {
        setSelectedOrder(order); // Set the found order as selected to display its details
      }
    }
  };

  // Extract orders from paginated data, defaulting to an empty array if no data
  const orders = paginatedOrders?.data || [];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header section with dynamic title based on user role */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {userRole === 'supplier' ? 'Supplier Dashboard' : 'Order Management'}
            </h1>
            <p className="text-gray-600 mt-2">
              {userRole === 'customer' && 'Track and manage your orders'}
              {userRole === 'supplier' && 'Manage your orders and track their progress'}
              {userRole === 'admin' && 'Oversee all orders and system operations'}
            </p>
          </div>

          <div className="flex items-center space-x-4">
            {/* Supplier view toggle buttons (List/Dashboard) */}
            {userRole === 'supplier' && (
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setView('list')}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    view === 'list' 
                      ? 'bg-white text-gray-900 shadow-sm' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  List View
                </button>
                <button
                  onClick={() => setView('dashboard')}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    view === 'dashboard' 
                      ? 'bg-white text-gray-900 shadow-sm' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Dashboard
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Conditional rendering based on user role and view state */}
        {userRole === 'supplier' && view === 'dashboard' && user ? (
          <SupplierOrderDashboard supplierId={user.id} />
        ) : (
          <div className="space-y-6">
            <OrderList
              orders={orders}
              userRole={userRole}
              filters={filters}
              onFilterChange={setFilters}
              onStatusUpdate={userRole !== 'customer' ? handleStatusUpdate : undefined}
              onOrderSelect={setSelectedOrder}
              loading={loading}
            />
          </div>
        )}

        {/* Order Details Modal/Sidebar */}
        {selectedOrder && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                  Order Details - #{selectedOrder.id.slice(-8)}
                </h2>
                <button
                  onClick={() => setSelectedOrder(null)}
                  className="text-gray-400 hover:text-gray-600 text-xl"
                >
                  ✕
                </button>
              </div>
              <div className="p-6">
                <OrderDetails
                  order={selectedOrder}
                  editable={userRole !== 'customer'}
                  showTracking={true}
                  onAddNote={userRole !== 'customer' ? handleAddNote : undefined}
                  onStatusUpdate={userRole !== 'customer' ? handleStatusUpdate : undefined}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderManagement;