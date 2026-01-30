import { OrderItemDetails } from './OrderItemDetails';
import { useState, useEffect } from 'react';
import { ChevronDownIcon, ChevronUpIcon, EyeIcon, DownloadIcon, ShoppingBagIcon, TruckIcon, ChevronLeftIcon, ChevronRightIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { SkeletonOrderTable } from '../ui/SkeletonTable';
import { usePaginatedApi } from '../../hooks/useAsync';
import OrdersAPI from '../../api/orders';
import { toast } from 'react-hot-toast';
import { useLocale } from '../../store/LocaleContext';
import { unwrapResponse, extractErrorMessage } from '../../utils/api-response';

interface Order {
  id: string;
  created_at: string;
  status: string;
  total_amount: number;
  subtotal?: number;
  discount_amount?: number;
  discount_type?: 'percentage' | 'fixed';
  tax_amount?: number;
  tax_rate?: number;
  shipping_cost?: number;
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
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalOrders, setTotalOrders] = useState(0);
  const ordersPerPage = 10;

  // Helper function to calculate and format pricing breakdown
  const calculatePricingBreakdown = (order: Order) => {
    // Calculate subtotal from items if not provided
    const calculatedSubtotal = order.items?.reduce((sum: number, item: any) => {
      return sum + (item.total_price || 0);
    }, 0) || 0;
    
    const subtotal = order.subtotal && order.subtotal > 0 ? order.subtotal : calculatedSubtotal;
    const discount = order.discount_amount || 0;
    const shipping = order.shipping_cost || order.shipping_amount || 0;
    const tax = order.tax_amount || 0;
    
    // Calculate total breakdown
    const subtotalAfterDiscount = subtotal - discount;
    const totalBeforeTax = subtotalAfterDiscount + shipping;
    const total = totalBeforeTax + tax;
    
    return {
      subtotal,
      discount,
      subtotalAfterDiscount,
      shipping,
      tax,
      total,
      hasDiscount: discount > 0,
      hasShipping: shipping > 0,
      hasTax: tax > 0
    };
  };

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

  // Update pagination info when data changes
  useEffect(() => {
    if (paginatedData) {
      // Handle Response.success wrapper
      if ((paginatedData as any)?.success) {
        const data = (paginatedData as any).data;
        if (data) {
          setTotalOrders(data.total || data.total_orders || orders.length);
          setTotalPages(data.total_pages || Math.ceil((data.total || orders.length) / ordersPerPage));
        }
      } else if (typeof paginatedData === 'object') {
        setTotalOrders((paginatedData as any).total || (paginatedData as any).total_orders || orders.length);
        setTotalPages((paginatedData as any).total_pages || Math.ceil(((paginatedData as any).total || orders.length) / ordersPerPage));
      }
    }
  }, [paginatedData, orders.length]);

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        await execute(() => OrdersAPI.getOrders({
          page: currentPage,
          limit: ordersPerPage
        }));
      } catch (error) {
        console.warn('Orders fetch failed:', error);
      }
    };
    
    fetchOrders();
  }, [execute, currentPage]);

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

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
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
      <div className="p-3">
        <SkeletonOrderTable animation={animation} rows={3} />
      </div>
    );
  }

  if (error) {
    console.error('Orders error:', error);
    
    // Handle different error types with user-friendly messages
    const getErrorMessage = (error: any) => {
      if (error.statusCode === 500) {
        if (error.message?.includes('shipping_amount')) {
          return "There's an issue with the order data format. Please contact support or try again later.";
        }
        return "Server is temporarily unavailable. Please try again in a few minutes.";
      }
      if (error.statusCode === 401) {
        return "Please log in to view your orders.";
      }
      if (error.statusCode === 403) {
        return "You don't have permission to view these orders.";
      }
      return error.message || "Failed to load orders. Please try again.";
    };

    return (
      <div className="p-3">
        <div className="text-center p-6">
          <div className="text-red-600 mb-3">
            <svg className="w-10 h-10 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-base font-medium mb-2">Unable to Load Orders</h3>
            <p className="text-sm text-gray-600">{getErrorMessage(error)}</p>
          </div>
          <button 
            onClick={() => {
              const retryFetch = async () => {
                try {
                  await execute(() => OrdersAPI.getOrders({}));
                } catch (retryError) {
                  console.warn('Retry failed:', retryError);
                }
              };
              retryFetch();
            }}
            className="mt-3 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
          >
            Try Again
          </button>
          {process.env.NODE_ENV === 'development' && (
            <div className="mt-3 text-xs text-gray-600">
              <p>Debug info:</p>
              <pre className="text-left bg-gray-100 p-2 rounded mt-2 max-h-40 overflow-auto">
                {JSON.stringify(error, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    );
  }

  return <div className="space-y-3">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-3 gap-2">
        
        {orders.length > 0 && (
          <p className="text-xs text-gray-600 dark:text-gray-300">
            {totalOrders} order{totalOrders !== 1 ? 's' : ''}
          </p>
        )}
      </div>
      
      {orders.length > 0 ? <div className="space-y-3">
          {orders.map((order: Order) => <div key={order.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center p-3 cursor-pointer gap-2" onClick={() => toggleOrderExpand(order.id)}>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-600 dark:text-gray-300 mb-1">
                    Order placed
                  </p>
                  <p className="text-xs font-medium text-gray-900 dark:text-white">
                    {new Date(order.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-600 dark:text-gray-300 mb-1">
                    Order ID
                  </p>
                  <p className="text-xs font-medium text-gray-900 dark:text-white break-all">
                    {order.id}
                  </p>
                </div>
                <div className="flex-1 min-w-0 text-right">
                  <p className="text-xs text-gray-600 dark:text-gray-300 mb-1">
                    Total
                  </p>
                  <p className="text-xs font-medium text-gray-900 dark:text-white">
                    {formatCurrency(order.total_amount)}
                  </p>
                </div>
                <div className="flex items-center space-x-2 mt-2 sm:mt-0">
                  <span className={`px-2 py-1 text-xs text-gray-900 dark:text-white rounded-full ${getStatusColor(order.status)}`}>
                    {order.status}
                  </span>
                  {expandedOrderId === order.id ? <ChevronUpIcon size={16} className="text-gray-500" /> : <ChevronDownIcon size={16} className="text-gray-500" />}
                </div>
              </div>
              {expandedOrderId === order.id && <div className="p-3 border-t border-gray-200 dark:border-gray-700">
                  <div className="space-y-3">
                    {order.items.map((item: any) => (
                      <OrderItemDetails 
                        key={item.id} 
                        productId={item.product_id} 
                        quantity={item.quantity} 
                        price={item.total_price} 
                      />
                    ))}
                  </div>
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
                      <div className="space-y-1 text-xs w-full sm:w-auto">
                        {(() => {
                          const pricing = calculatePricingBreakdown(order);
                          
                          return (
                            <>
                              <div className="flex justify-between items-center">
                                <span className="text-gray-500 dark:text-gray-400">Subtotal</span>
                                <span className="text-gray-900 dark:text-white">{formatCurrency(pricing.subtotal)}</span>
                              </div>
                              {pricing.hasDiscount && (
                                <div className="flex justify-between items-center">
                                  <span className="text-green-600 dark:text-green-400">Discount</span>
                                  <span className="text-green-600 dark:text-green-400">
                                    -{formatCurrency(pricing.discount)}
                                    {order.discount_type === 'percentage' && ` (${((pricing.discount / pricing.subtotal) * 100).toFixed(0)}%)`}
                                  </span>
                                </div>
                              )}
                              {pricing.hasShipping && (
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-500 dark:text-gray-400">Shipping</span>
                                  <span className="text-gray-900 dark:text-white">{formatCurrency(pricing.shipping)}</span>
                                </div>
                              )}
                              {pricing.hasTax && (
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-500 dark:text-gray-400">
                                    Tax{order.tax_rate && ` (${(order.tax_rate * 100).toFixed(0)}%)`}
                                  </span>
                                  <span className="text-gray-900 dark:text-white">{formatCurrency(pricing.tax)}</span>
                                </div>
                              )}
                              <div className="flex justify-between items-center pt-2 mt-2 border-t border-gray-200 dark:border-gray-700">
                                <span className="font-medium text-gray-900 dark:text-white">Total</span>
                                <span className="font-medium text-gray-900 dark:text-white">{formatCurrency(order.total_amount)}</span>
                              </div>
                            </>
                          );
                        })()}
                      </div>
                      <div className="flex flex-wrap gap-2 w-full sm:w-auto justify-start sm:justify-end">
                        <Link to={`/track-order/${order.id}`} className="flex items-center px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors min-w-[80px] justify-center">
                          <TruckIcon size={12} className="mr-1 flex-shrink-0" />
                          <span>Track</span>
                        </Link>
                        <Link to={`/account/orders/${order.id}`} className="flex items-center px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors min-w-[80px] justify-center">
                          <EyeIcon size={12} className="mr-1 flex-shrink-0" />
                          <span>Details</span>
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
                          className="flex items-center px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors min-w-[80px] justify-center"
                        >
                          <DownloadIcon size={12} className="mr-1 flex-shrink-0" />
                          <span>Invoice</span>
                        </button>
                      </div>
                    </div>
                </div>}
            </div>)}
            
            {/* Pagination - Always show for testing */}
            <div className="flex justify-center items-center space-x-2 pt-4">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="flex items-center px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeftIcon size={16} className="mr-1" />
                Previous
              </button>
              
              <div className="flex items-center space-x-1">
                {Array.from({ length: Math.min(5, totalPages > 0 ? totalPages : 1) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 1) {
                    pageNum = 1;
                  } else if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => handlePageChange(pageNum)}
                      className={`px-3 py-2 text-sm rounded transition-colors ${
                        currentPage === pageNum
                          ? 'bg-primary text-white'
                          : 'border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>
              
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage >= totalPages}
                className="flex items-center px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
                <ChevronRightIcon size={16} className="ml-1" />
              </button>
            </div>
            
            {/* Debug Info */}
            <div className="text-xs text-gray-400 dark:text-gray-500 text-center mt-2">
              Page {currentPage} of {totalPages} | Total: {totalOrders} orders
            </div>
          </div> : <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 text-center">
          <div className="w-12 h-12 mx-auto mb-3 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
            <ShoppingBagIcon size={20} className="text-gray-500 dark:text-gray-400" />
          </div>
          <h2 className="text-base font-medium text-gray-900 dark:text-white mb-2">
            No orders yet
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
            You haven't placed any orders yet.
          </p>
          <div className="space-y-2">
            <Link to="/products" className="inline-block px-3 py-2 bg-primary hover:bg-primary-dark text-white rounded-md text-sm">
              Start Shopping
            </Link>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              <button 
                onClick={() => execute(() => OrdersAPI.getOrders({
                  page: currentPage,
                  limit: ordersPerPage
                }))}
                className="text-primary hover:underline"
              >
                Refresh Orders
              </button>
            </div>
          </div>
          <div className="mt-3 text-xs text-gray-400 dark:text-gray-500">
            <p>Debug: {orders.length} orders found</p>
            <p>Loading: {loading ? 'Yes' : 'No'}</p>
            <p>Error: {error ? 'Yes' : 'No'}</p>
          </div>
        </div>}
    </div>;
};
export default Orders;