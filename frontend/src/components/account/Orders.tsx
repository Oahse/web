import { OrderItemDetails } from './OrderItemDetails';
import { useState, useEffect } from 'react';
import { ChevronDownIcon, ChevronUpIcon, EyeIcon, DownloadIcon, ShoppingBagIcon, TruckIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { SkeletonOrderTable } from '../ui/SkeletonTable';
import { usePaginatedApi } from '../../hooks/useAsync';
import OrdersAPI from '../../apis/orders';
import { toast } from 'react-hot-toast';
import { useLocale } from '../../contexts/LocaleContext';

interface Order {
  id: string;
  created_at: string;
  status: string;
  total_amount: number;
  subtotal?: number;
  tax_amount?: number;
  shipping_amount?: number;
  items: any[];
}

interface OrdersProps {
  animation?: 'shimmer' | 'pulse' | 'wave';
}

export const Orders = ({
  animation = 'shimmer' 
}: OrdersProps) => {
  const { formatCurrency } = useLocale();
  const { data: paginatedData, loading, error, execute } = usePaginatedApi();
  const [expandedOrderId, setExpandedOrderId] = useState<string | null>(null);

  // Handle the response structure properly - moved before useEffect
  const orders = (() => {
    if (!paginatedData) return [];
    // Handle Response.success wrapper
    if ((paginatedData as any)?.success) {
      const data = (paginatedData as any).data;
      // Check if data has orders array (paginated response)
      if (data && data.orders) {
        return data.orders;
      }
      // Otherwise return data directly if it's an array
      return Array.isArray(data) ? data : [];
    }
    // Handle direct array response
    if (Array.isArray(paginatedData)) {
      return paginatedData;
    }
    // Handle object with orders property
    if (paginatedData && typeof paginatedData === 'object' && 'orders' in paginatedData) {
      return (paginatedData as any).orders || [];
    }
    return [];
  })();

  useEffect(() => {
    execute(() => OrdersAPI.getOrders({}));
  }, [execute]);

  // Debug logging
  useEffect(() => {
    if (paginatedData) {
      console.log('Orders API Response:', paginatedData);
      console.log('Processed orders:', orders);
    }
  }, [paginatedData, orders]);

  const toggleOrderExpand = (orderId: string) => {
    setExpandedOrderId(expandedOrderId === orderId ? null : orderId);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'delivered':
      case 'confirmed':
      case 'completed':
        return 'bg-success-light text-success-dark dark:bg-success-dark dark:text-success-light';
      case 'shipped':
      case 'out_for_delivery':
        return 'bg-info-light text-info-dark dark:bg-info-dark dark:text-info-light';
      case 'processing':
      case 'pending':
        return 'bg-warning-light text-warning-dark dark:bg-warning-dark dark:text-warning-light';
      case 'cancelled':
      case 'payment_failed':
      case 'failed':
      case 'refunded':
        return 'bg-error-light text-error-dark dark:bg-error-dark dark:text-error-light';
      default:
        return 'bg-surface-hover text-copy-light dark:bg-surface-active dark:text-copy-lighter';
    }
  };

  if (loading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-main dark:text-white mb-6">
          My Orders
        </h1>
        <SkeletonOrderTable animation={animation} rows={3} />
      </div>
    );
  }

  if (error) {
    console.error('Orders error:', error);
    return (
      <div>
        <h1 className="text-2xl font-bold text-main dark:text-white mb-6">
          My Orders
        </h1>
        <div className="text-error text-center p-8">
          <p>Error fetching orders: {error.message}</p>
          <button 
            onClick={() => execute(() => OrdersAPI.getOrders({}))}
            className="mt-4 px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
          >
            Try Again
          </button>
          <div className="mt-4 text-sm text-gray-600">
            <p>Debug info:</p>
            <pre className="text-left bg-gray-100 p-2 rounded mt-2">
              {JSON.stringify(error, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    );
  }

  return <div>
      <h1 className="text-2xl font-bold text-main dark:text-white mb-6">
        My Orders
      </h1>
      {orders.length > 0 ? <div className="space-y-4">
          {orders.map((order: Order) => <div key={order.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
              <div className="flex justify-between items-center p-4 cursor-pointer " onClick={() => toggleOrderExpand(order.id)}>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Order placed
                  </p>
                  <p className="font-medium text-main dark:text-white">
                    {new Date(order.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Order ID
                  </p>
                  <p className="font-medium text-main dark:text-white">
                    {order.id}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Total
                  </p>
                  <p className="font-medium text-main dark:text-white">
                    {formatCurrency(order.total_amount)}
                  </p>
                </div>
                <div>
                  <span className={`px-3 py-1 text-xs text-main dark:text-white rounded-full ${getStatusColor(order.status)}`}>
                    {order.status}
                  </span>
                </div>
                {expandedOrderId === order.id ? <ChevronUpIcon size={20} className="text-gray-500" /> : <ChevronDownIcon size={20} className="text-gray-500" />}
              </div>
              {expandedOrderId === order.id && <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="space-y-4">
                    {order.items.map((item: any) => (
                      <OrderItemDetails 
                        key={item.id} 
                        productId={item.product_id} 
                        quantity={item.quantity} 
                        price={item.total_price} 
                      />
                    ))}
                  </div>
                  <div className="mt-6 flex justify-between">
                    <div className="space-y-1 text-sm">
                      <p className="text-gray-500 dark:text-gray-400">
                        Subtotal: {formatCurrency(order.subtotal || order.total_amount)}
                      </p>
                      <p className="text-gray-500 dark:text-gray-400">
                        Shipping: {formatCurrency(order.shipping_amount || 0)}
                      </p>
                      <p className="text-gray-500 dark:text-gray-400">
                        Tax: {formatCurrency(order.tax_amount || 0)}
                      </p>
                      <p className="font-medium text-main dark:text-white">
                        Total: {formatCurrency(order.total_amount)}
                      </p>
                    </div>
                    <div className="flex space-x-2">
                      <Link to={`/track-order/${order.id}`} className="flex items-center px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700">
                        <TruckIcon size={16} className="mr-1" />
                        Track
                      </Link>
                      <Link to={`/account/orders/${order.id}`} className="flex items-center px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700">
                        <EyeIcon size={16} className="mr-1" />
                        Details
                      </Link>
                      <button 
                        onClick={async () => {
                          try {
                            await OrdersAPI.getOrderInvoice(order.id);
                            toast.success('Invoice downloaded successfully');
                          } catch (error) {
                            toast.error('Failed to download invoice');
                          }
                        }}
                        className="flex items-center px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700"
                      >
                        <DownloadIcon size={16} className="mr-1" />
                        Invoice
                      </button>
                    </div>
                  </div>
                </div>}
            </div>)}
        </div> : <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
            <ShoppingBagIcon size={24} className="text-gray-500 dark:text-gray-400" />
          </div>
          <h2 className="text-lg font-medium text-main dark:text-white mb-2">
            No orders yet
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            You haven't placed any orders yet.
          </p>
          <div className="space-y-2">
            <Link to="/products" className="inline-block px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-md">
              Start Shopping
            </Link>
            <div className="text-sm text-gray-500">
              <button 
                onClick={() => execute(() => OrdersAPI.getOrders({}))}
                className="text-primary hover:underline"
              >
                Refresh Orders
              </button>
            </div>
          </div>
          <div className="mt-4 text-xs text-gray-400">
            <p>Debug: {orders.length} orders found</p>
            <p>Loading: {loading ? 'Yes' : 'No'}</p>
            <p>Error: {error ? 'Yes' : 'No'}</p>
          </div>
        </div>}
    </div>;
};
export default Orders;