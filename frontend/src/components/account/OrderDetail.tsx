import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeftIcon, PackageIcon, DownloadIcon, MapPinIcon } from 'lucide-react';
import { OrdersAPI } from '../../api/orders';
import { toast } from 'react-hot-toast';
import { unwrapResponse, extractErrorMessage } from '../../utils/api-response';

export const OrderDetail = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOrder = async () => {
      if (!orderId) return;
      
      try {
        setLoading(true);
        const response = await OrdersAPI.getOrder(orderId);
        const orderData = response?.data || response;
        setOrder(orderData);
      } catch (error) {
        toast.error('Failed to load order details');
        console.error('Error fetching order:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchOrder();
  }, [orderId]);

  const handleDownloadInvoice = async () => {
    try {
      await OrdersAPI.getOrderInvoice(orderId);
      toast.success('Invoice downloaded successfully');
    } catch (error) {
      toast.error('Failed to download invoice');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'delivered':
      case 'confirmed':
      case 'completed':
        return 'bg-success-light text-success-dark dark:bg-success-dark dark:text-success-light';
      case 'shipped':
      case 'out_for_delivery':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
      case 'processing':
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
      case 'cancelled':
      case 'payment_failed':
      case 'failed':
      case 'refunded':
        return 'bg-error-light text-error-dark dark:bg-error-dark dark:text-error-light';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="p-3 sm:p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="p-3 sm:p-6 text-center">
        <p className="text-gray-500 dark:text-gray-400">Order not found</p>
        <Link to="/account/orders" className="text-primary hover:underline mt-4 inline-block">
          Back to Orders
        </Link>
      </div>
    );
  }

  return (
    <div className="p-3 sm:p-6">
      <button
        onClick={() => navigate('/account/orders')}
        className="flex items-center text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 mb-6 transition-colors"
      >
        <ArrowLeftIcon size={20} className="mr-2" />
        Back to Orders
      </button>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-6 gap-4">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Order Details
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Order ID: {order.id}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Placed on: {new Date(order.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <span className={`px-3 py-1 text-sm rounded-full ${getStatusColor(order.status)}`}>
              {order.status}
            </span>
            <div className="flex flex-wrap gap-2 justify-end">
              <Link
                to={`/track-order/${order.id}`}
                className="flex items-center px-3 py-2 text-xs sm:text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <MapPinIcon size={16} className="mr-1 sm:mr-2" />
                Track Order
              </Link>
              <button
                onClick={handleDownloadInvoice}
                className="flex items-center px-3 py-2 text-xs sm:text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <DownloadIcon size={16} className="mr-1 sm:mr-2" />
                Download Invoice
              </button>
            </div>
          </div>
        </div>

        {/* Order Items */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Order Items
          </h2>
          <div className="space-y-4">
            {order.items?.map((item: any) => {
              // Get primary image from variant images array (same logic as ProductCard)
              let imageUrl = null;
              if (item.variant?.images && item.variant.images.length > 0) {
                const primaryImage = item.variant.images.find((img: any) => img.is_primary);
                imageUrl = primaryImage?.url || item.variant.images[0]?.url;
              }
              
              return (
                <div key={item.id} className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gray-200 dark:bg-gray-600 rounded overflow-hidden flex-shrink-0">
                    {imageUrl ? (
                      <img
                        src={imageUrl}
                        alt={item.variant?.product_name || item.variant?.name || 'Product'}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80"%3E%3Crect width="80" height="80" fill="%23f3f4f6"/%3E%3Cpath d="M40 25c-5.5 0-10 4.5-10 10s4.5 10 10 10 10-4.5 10-10-4.5-10-10-10zm0 15c-2.8 0-5-2.2-5-5s2.2-5 5-5 5 2.2 5 5-2.2 5-5 5z" fill="%239ca3af"/%3E%3Cpath d="M55 20H25c-2.8 0-5 2.2-5 5v30c0 2.8 2.2 5 5 5h30c2.8 0 5-2.2 5-5V25c0-2.8-2.2-5-5-5zm0 35H25V25h30v30z" fill="%239ca3af"/%3E%3C/svg%3E';
                          e.currentTarget.onerror = null;
                        }}
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <PackageIcon size={24} className="text-gray-400" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white text-sm sm:text-base">
                      {item.variant?.product_name || item.variant?.name || 'Product'}
                    </p>
                    {item.variant?.name && item.variant?.product_name && (
                      <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                        Variant: {item.variant.name}
                      </p>
                    )}
                    <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                      Quantity: {item.quantity} × ${(item.price_per_unit || 0).toFixed(2)}
                    </p>
                  </div>
                  <p className="font-medium text-gray-900 dark:text-white whitespace-nowrap text-sm sm:text-base">
                    ${item.total_price?.toFixed(2)}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Order Summary */}
        <div className="border-t border-gray-200 dark:border-gray-700 mt-6 pt-6">
          {(() => {
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
            
            const hasDiscount = discount > 0;
            const hasShipping = shipping > 0;
            const hasTax = tax > 0;
            
            return (
              <>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600 dark:text-gray-400">Subtotal</span>
                  <span className="text-gray-900 dark:text-white">${subtotal.toFixed(2)}</span>
                </div>
                {hasDiscount && (
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-green-600 dark:text-green-400">Discount</span>
                    <span className="text-green-600 dark:text-green-400">
                      -${discount.toFixed(2)}
                      {order.discount_type === 'percentage' && ` (${((discount / subtotal) * 100).toFixed(0)}%)`}
                    </span>
                  </div>
                )}
                {hasShipping && (
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-600 dark:text-gray-400">Shipping</span>
                    <span className="text-gray-900 dark:text-white">${shipping.toFixed(2)}</span>
                  </div>
                )}
                {hasTax && (
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-600 dark:text-gray-400">
                      Tax{order.tax_rate && ` (${(order.tax_rate * 100).toFixed(0)}%)`}
                    </span>
                    <span className="text-gray-900 dark:text-white">${tax.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between items-center text-lg font-semibold border-t border-gray-200 dark:border-gray-700 pt-2 mt-2">
                  <span className="text-gray-900 dark:text-white">Total</span>
                  <span className="text-gray-900 dark:text-white">${order.total_amount?.toFixed(2)}</span>
                </div>
              </>
            );
          })()}
        </div>

        {/* Shipping Address */}
        {order.shipping_address && (
          <div className="border-t border-gray-200 dark:border-gray-700 mt-6 pt-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Shipping Address
            </h2>
            <div className="text-gray-600 dark:text-gray-400">
              <p>{order.shipping_address.street}</p>
              <p>{order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.post_code}</p>
              <p>{order.shipping_address.country}</p>
            </div>
          </div>
        )}

        {/* Order Notes */}
        {order.notes && (
          <div className="border-t border-gray-200 dark:border-gray-700 mt-6 pt-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Order Notes
            </h2>
            <p className="text-gray-600 dark:text-gray-400">{order.notes}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderDetail;
