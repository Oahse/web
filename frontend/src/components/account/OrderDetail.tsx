import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeftIcon, PackageIcon, DownloadIcon, MapPinIcon } from 'lucide-react';
import { OrdersAPI } from '../../apis/orders';
import { toast } from 'react-hot-toast';

export const OrderDetail = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOrder = async () => {
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

    if (orderId) {
      fetchOrder();
    }
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
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-500">Order not found</p>
        <Link to="/account/orders" className="text-primary hover:underline mt-4 inline-block">
          Back to Orders
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6">
      <button
        onClick={() => navigate('/account/orders')}
        className="flex items-center text-copy-light hover:text-copy mb-6"
      >
        <ArrowLeftIcon size={20} className="mr-2" />
        Back to Orders
      </button>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Order Details
            </h1>
            <p className="text-gray-500 dark:text-gray-400">
              Order ID: {order.id}
            </p>
            <p className="text-gray-500 dark:text-gray-400">
              Placed on: {new Date(order.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <span className={`px-3 py-1 text-sm rounded-full ${getStatusColor(order.status)}`}>
              {order.status}
            </span>
            <div className="flex gap-2">
              <Link
                to={`/track-order/${order.id}`}
                className="flex items-center px-4 py-2 text-sm border border-border rounded hover:bg-surface-hover"
              >
                <MapPinIcon size={16} className="mr-2" />
                Track Order
              </Link>
              <button
                onClick={handleDownloadInvoice}
                className="flex items-center px-4 py-2 text-sm border border-border rounded hover:bg-surface-hover"
              >
                <DownloadIcon size={16} className="mr-2" />
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
                  <div className="w-20 h-20 bg-gray-200 dark:bg-gray-600 rounded overflow-hidden flex-shrink-0">
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
                        <PackageIcon size={32} className="text-gray-400" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white">
                      {item.variant?.product_name || item.variant?.name || 'Product'}
                    </p>
                    {item.variant?.name && item.variant?.product_name && (
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Variant: {item.variant.name}
                      </p>
                    )}
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Quantity: {item.quantity} × ${(item.price_per_unit || 0).toFixed(2)}
                    </p>
                  </div>
                  <p className="font-medium text-gray-900 dark:text-white whitespace-nowrap">
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
            // Calculate subtotal from items if not provided or is zero
            const calculatedSubtotal = order.items?.reduce((sum: number, item: any) => {
              return sum + (item.total_price || 0);
            }, 0) || 0;
            
            const displaySubtotal = order.subtotal && order.subtotal > 0 ? order.subtotal : calculatedSubtotal;
            
            return (
              <>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600 dark:text-gray-400">Subtotal</span>
                  <span className="text-gray-900 dark:text-white">${displaySubtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600 dark:text-gray-400">Shipping</span>
                  <span className="text-gray-900 dark:text-white">${(order.shipping_cost || order.shipping_amount || 0).toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600 dark:text-gray-400">Tax</span>
                  <span className="text-gray-900 dark:text-white">${(order.tax_amount || 0).toFixed(2)}</span>
                </div>
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
