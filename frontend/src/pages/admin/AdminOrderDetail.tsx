import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PrinterIcon, ArrowLeftIcon } from 'lucide-react';
import { useApi } from '../../hooks/useAsync';
import { AdminAPI } from '../../apis';
import ErrorMessage from '../../components/common/ErrorMessage';
import { toast } from 'react-hot-toast';


export const AdminOrderDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: orderResponse, loading, error, execute } = useApi();

  React.useEffect(() => {
    if (id) {
      execute(() => AdminAPI.getOrder(id));
    }
  }, [id, execute]);

  const order = orderResponse?.data || orderResponse;

  if (loading) {
    return <div className="p-6">Loading order details...</div>;
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorMessage 
          error={error} 
          onRetry={() => execute(() => AdminAPI.getOrder(id))} 
          onDismiss={() => navigate('/admin/orders')}
        />
      </div>
    );
  }

  if (!order) {
    return <div className="p-6">Order not found.</div>;
  }

  const handleDownloadInvoice = async () => {
    try {
      await AdminAPI.getOrderInvoice(id);
      toast.success('Invoice downloaded successfully');
    } catch (error) {
      toast.error('Failed to download invoice');
      console.error('Error downloading invoice:', error);
    }
  };

  return (
    <div className="p-6">
      <button
        onClick={() => navigate('/admin/orders')}
        className="flex items-center text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200 mb-6"
      >
        <ArrowLeftIcon size={20} className="mr-2" />
        Back to Orders
      </button>

      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Order Details: {order.id}</h1>
        <button
          onClick={handleDownloadInvoice}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
        >
          <PrinterIcon size={18} />
          Download Invoice
        </button>
      </div>
      <div className="bg-white shadow-sm rounded-lg p-4">
        <p><strong>Customer:</strong> {order.user?.firstname} {order.user?.lastname}</p>
        <p><strong>Email:</strong> {order.user?.email}</p>
        <p><strong>Status:</strong> {order.status}</p>
        <p><strong>Total Amount:</strong> ${order.total_amount?.toFixed(2)}</p>
        <p><strong>Created At:</strong> {new Date(order.created_at).toLocaleString()}</p>
      </div>

      <div className="mt-6 bg-white shadow-sm rounded-lg p-4">
        <h2 className="text-xl font-bold mb-4">Shipping Details</h2>
        <p><strong>Carrier:</strong> {order.carrier_name || 'Not available'}</p>
        <p><strong>Tracking Number:</strong> {order.tracking_number || 'Not available'}</p>
      </div>

      <div className="mt-6 bg-white shadow-sm rounded-lg p-4">
        <h2 className="text-xl font-bold mb-4">Payment Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p><strong>Payment Status:</strong> {order.payment_status || 'N/A'}</p>
            <p><strong>Total Paid:</strong> {order.currency} {order.total_amount?.toFixed(2)}</p>
            <p><strong>Payment Method ID:</strong> {order.payment_method_id || 'N/A'}</p>
          </div>
          <div>
            <h3><strong>Billing Address:</strong></h3>
            {order.billing_address ? (
              <>
                <p>{order.billing_address.street}</p>
                <p>{order.billing_address.city}, {order.billing_address.state} {order.billing_address.post_code}</p>
                <p>{order.billing_address.country}</p>
              </>
            ) : (
              <p>Not available</p>
            )}
          </div>
        </div>
      </div>

      {order.tracking_events && order.tracking_events.length > 0 && (
        <div className="mt-6 bg-white shadow-sm rounded-lg p-4">
          <h2 className="text-xl font-bold mb-4">Tracking Events</h2>
          <div className="space-y-3">
            {order.tracking_events.map((event: any) => (
              <div key={event.id} className="border-l-4 border-primary pl-4 py-2">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-semibold text-gray-900">{event.status}</p>
                    <p className="text-sm text-gray-600">{event.description}</p>
                    {event.location && (
                      <p className="text-xs text-gray-500 mt-1">📍 {event.location}</p>
                    )}
                  </div>
                  <span className="text-xs text-gray-500">
                    {new Date(event.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-6">
        <h2 className="text-xl font-bold mb-4">Order Items</h2>
        <div className="bg-white shadow-sm rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {order.items?.map((item: any) => (
                <tr key={item.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {item.variant?.product?.name || item.variant?.product_name || 'Product'}
                    {item.variant?.name && ` (${item.variant.name})`}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">{item.quantity}</td>
                  <td className="px-6 py-4 whitespace-nowrap">${item.price_per_unit?.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap">${item.total_price?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default AdminOrderDetail;