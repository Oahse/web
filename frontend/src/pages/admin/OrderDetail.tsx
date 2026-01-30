import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader, AlertCircle, ArrowLeft, DownloadIcon, MapPin, Truck, Package, DollarSign, Clock, CheckCircle } from 'lucide-react';
import AdminAPI from '@/api/admin';
import apiClient from '@/api/client';
import toast from 'react-hot-toast';

interface OrderDetail {
  id: string;
  order_number: string;
  user_email: string;
  user?: {
    firstname?: string;
    lastname?: string;
    email: string;
    phone?: string;
  };
  total_amount: number;
  subtotal: number;
  shipping_cost: number;
  tax_amount: number;
  tax_rate: number;
  currency: string;
  order_status: string;
  payment_status: string;
  fulfillment_status: string;
  created_at: string;
  updated_at: string;
  confirmed_at?: string;
  shipped_at?: string;
  delivered_at?: string;
  cancelled_at?: string;
  shipping_method?: string;
  shipping_address?: any;
  billing_address?: any;
  tracking_number?: string;
  carrier?: string;
  customer_notes?: string;
  internal_notes?: string;
  items?: OrderItem[];
  source?: string;
  subscription_id?: string;
  [key: string]: any;
}

interface OrderItem {
  id: string;
  product_id?: string;
  product_name?: string;
  variant_id?: string;
  variant_name?: string;
  sku?: string;
  quantity: number;
  unit_price?: number;
  price_per_unit?: number;
  total_price?: number;
  product?: { id: string; name?: string; slug?: string };
  variant?: { id: string; sku?: string; name?: string; images?: { id: string; url: string; alt_text?: string; is_primary?: boolean }[] };
  [key: string]: any;
}

export const AdminOrderDetail = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);
  const [newStatus, setNewStatus] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'overview' | 'items' | 'shipping' | 'notes'>('overview');
  const [invoicePreviewHtml, setInvoicePreviewHtml] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    const fetchOrder = async () => {
      try {
        setLoading(true);
        setError(null);
        
        if (!orderId) {
          setError('Order ID not provided');
          return;
        }

        const response = await AdminAPI.getOrder(orderId);
        // Admin API may return a wrapped response: { success, data }
        // apiClient.get returns response.data already, so handle both shapes
        const data = response?.data?.data || response?.data || response;
        setOrder(data);
        setNewStatus((data?.order_status || data?.status || '').toString().toUpperCase());
      } catch (err: any) {
        const message = err?.response?.data?.message || 'Failed to load order details';
        setError(message);
        toast.error(message);
      } finally {
        setLoading(false);
      }
    };

    fetchOrder();
  }, [orderId]);

  const handleStatusUpdate = async () => {
    if (!orderId || !newStatus || newStatus === order?.order_status) {
      return;
    }

    try {
      setUpdating(true);
      // Backend expects lowercase status values; convert before sending
      await AdminAPI.updateOrderStatus(orderId, newStatus.toLowerCase());
      toast.success('Order status updated successfully');
      if (order) {
        setOrder({ ...order, order_status: newStatus.toLowerCase() });
      }
    } catch (err: any) {
      const message = err?.response?.data?.message || 'Failed to update order status';
      toast.error(message);
    } finally {
      setUpdating(false);
    }
  };

  const handleDownloadInvoice = async () => {
    if (!orderId) return;
    try {
      setPreviewLoading(true);

      // Try fetching as blob to detect content-type (PDF vs JSON/HTML)
      const client = apiClient.getClient();
      const resp = await client.get(`/admin/orders/${orderId}/invoice`, { responseType: 'blob' });

      const contentType = resp.headers['content-type'] || '';

      // If it's a PDF (or other binary), trigger download
      if (contentType.includes('application/pdf') || contentType.includes('application/octet-stream')) {
        const blob = new Blob([resp.data], { type: contentType });
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `invoice-${orderId}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
        toast.success('Invoice downloaded');
        return;
      }

      // Otherwise attempt to parse text (could be JSON or HTML)
      const text = await resp.data.text();

      // Try JSON first
      try {
        const json = JSON.parse(text);
        // If backend returned an invoice object with html or invoice_content, prefer that
        if (json?.invoice_html || json?.html || json?.invoice_content) {
          setInvoicePreviewHtml(json.invoice_html || json.html || json.invoice_content);
          toast.success('Invoice preview loaded');
          return;
        }

        // If backend returned an invoice_path (server generated file), trigger download via AdminAPI
        if (json?.invoice_path) {
          await AdminAPI.getOrderInvoice(orderId);
          toast.success('Invoice downloaded');
          return;
        }

        // Otherwise stringify and show
        setInvoicePreviewHtml(`<pre>${JSON.stringify(json, null, 2)}</pre>`);
        toast.success('Invoice preview loaded');
        return;
      } catch (e) {
        // Not JSON — assume it's HTML
        setInvoicePreviewHtml(text);
        toast.success('Invoice preview loaded');
        return;
      }
    } catch (err: any) {
      // Fallback: call AdminAPI.download which uses apiClient.download
      try {
        await AdminAPI.getOrderInvoice(orderId);
        toast.success('Invoice downloaded');
      } catch (e) {
        toast.error('Failed to download invoice');
      }
    } finally {
      setPreviewLoading(false);
    }
  };

  const formatCurrency = (amount: number | undefined | null) => {
    const n = Number(amount);
    if (n !== n || n < 0) return new Intl.NumberFormat('en-US', { style: 'currency', currency: order?.currency || 'USD' }).format(0);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: order?.currency || 'USD',
    }).format(n);
  };

  const getStatusColor = (status: string) => {
    const key = String(status || '').toUpperCase();
    const statusMap: Record<string, string> = {
      'PENDING': 'bg-yellow-100 text-yellow-800',
      'PROCESSING': 'bg-blue-100 text-blue-800',
      'SHIPPED': 'bg-indigo-100 text-indigo-800',
      'DELIVERED': 'bg-green-100 text-green-800',
      'CANCELLED': 'bg-red-100 text-red-800',
      'RETURNED': 'bg-gray-100 text-gray-800',
    };
    return statusMap[key] || 'bg-gray-100 text-gray-800';
  };

  const getPaymentStatusColor = (status: string) => {
    const key = String(status || '').toUpperCase();
    const statusMap: Record<string, string> = {
      'PAID': 'bg-green-100 text-green-800',
      'PENDING': 'bg-yellow-100 text-yellow-800',
      'FAILED': 'bg-red-100 text-red-800',
      'REFUNDED': 'bg-blue-100 text-blue-800',
    };
    return statusMap[key] || 'bg-gray-100 text-gray-800';
  };

  const formatStatus = (status?: string) => {
    if (!status) return '-';
    const s = String(status || '').toLowerCase();
    // replace underscores and hyphens with spaces, capitalize first letter
    const cleaned = s.replace(/[_-]/g, ' ');
    return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader className="w-12 h-12 text-primary animate-spin" />
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/admin/orders')}
            className="flex items-center gap-2 text-primary hover:text-primary/80"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Orders
          </button>
        </div>

        <div className="bg-destructive/10 border border-destructive rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-destructive">Error</p>
            <p className="text-destructive/80 text-sm">{error || 'Order not found'}</p>
          </div>
        </div>
      </div>
    );
  }

  const statusOptions = ['PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED'];

  return (
    <div className="space-y-6">
      {/* Header with Back Button */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/admin/orders')}
            className="flex items-center gap-2 text-primary hover:text-primary/80"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Orders
          </button>
          <div>
            <h1 className="text-3xl font-bold text-copy">Order #{order.order_number}</h1>
            <p className="text-sm text-copy-light">{order.id}</p>
          </div>
        </div>
        <button
          onClick={handleDownloadInvoice}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-copy-inverse rounded-lg hover:bg-primary/90 transition"
        >
          <DownloadIcon className="w-4 h-4" />
          Download Invoice
        </button>
      </div>

      {/* Invoice Preview / Download */}
      <div>
        {previewLoading && (
          <div className="mb-4">
            <p className="text-sm text-copy-light">Loading invoice preview...</p>
          </div>
        )}

        {invoicePreviewHtml && (
          <div className="mb-6 bg-surface rounded-lg border border-border-light p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="font-semibold">Invoice Preview</p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => window.print()}
                  className="px-3 py-1 bg-muted rounded text-sm"
                >
                  Print
                </button>
                <button
                  onClick={() => AdminAPI.getOrderInvoice(orderId || '')}
                  className="px-3 py-1 bg-primary text-copy-inverse rounded text-sm"
                >
                  Download
                </button>
              </div>
            </div>
            <div className="overflow-auto max-h-[60vh] border border-border-light">
              <div className="p-4" dangerouslySetInnerHTML={{ __html: invoicePreviewHtml }} />
            </div>
          </div>
        )}
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Order Status */}
        <div className="bg-surface rounded-lg border border-border-light p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-copy-light">Order Status</p>
            <Package className="w-4 h-4 text-primary" />
          </div>
          <p className={`px-3 py-1 rounded-full text-xs font-bold w-fit ${getStatusColor(order.order_status)}`}>
            {formatStatus(order.order_status)}
          </p>
        </div>

        {/* Payment Status */}
        <div className="bg-surface rounded-lg border border-border-light p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-copy-light">Payment Status</p>
            <DollarSign className="w-4 h-4 text-success" />
          </div>
          <p className={`px-3 py-1 rounded-full text-xs font-bold w-fit ${getPaymentStatusColor(order.payment_status)}`}>
            {formatStatus(order.payment_status)}
          </p>
        </div>

        {/* Fulfillment Status */}
        <div className="bg-surface rounded-lg border border-border-light p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-copy-light">Fulfillment</p>
            <CheckCircle className="w-4 h-4 text-warning" />
          </div>
          <p className="text-sm font-semibold text-copy">{formatStatus(order.fulfillment_status || order.fulfillment_status)}</p>
        </div>

        {/* Order Total */}
        <div className="bg-surface rounded-lg border border-border-light p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-copy-light">Total Amount</p>
            <DollarSign className="w-4 h-4 text-success" />
          </div>
          <p className="text-lg font-bold text-copy">{formatCurrency(order.total_amount)}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-border-light">
        {(['overview', 'items', 'shipping', 'notes'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-semibold capitalize transition ${
              activeTab === tab
                ? 'text-primary border-b-2 border-primary'
                : 'text-copy-light hover:text-copy'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Order Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* General Information */}
            <div className="bg-surface rounded-lg border border-border-light p-6">
              <h3 className="text-lg font-bold text-copy mb-4">General Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-copy-light">Order Date</p>
                  <p className="text-copy font-semibold">
                    {new Date(order.created_at).toLocaleDateString()} {new Date(order.created_at).toLocaleTimeString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-copy-light">Last Updated</p>
                  <p className="text-copy font-semibold">
                    {new Date(order.updated_at).toLocaleDateString()} {new Date(order.updated_at).toLocaleTimeString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-copy-light">Order Source</p>
                  <p className="text-copy font-semibold capitalize">{order.source || 'WEB'}</p>
                </div>
                <div>
                  <p className="text-sm text-copy-light">Currency</p>
                  <p className="text-copy font-semibold">{order.currency}</p>
                </div>
              </div>
            </div>

            {/* Customer Information */}
            <div className="bg-surface rounded-lg border border-border-light p-6">
              <h3 className="text-lg font-bold text-copy mb-4">Customer Information</h3>
              <div className="space-y-3">
                {order.user?.firstname && (
                  <div>
                    <p className="text-sm text-copy-light">Name</p>
                    <p className="text-copy font-semibold">
                      {order.user.firstname} {order.user.lastname || ''}
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-copy-light">Email</p>
                  <p className="text-copy font-semibold">{order.user_email || order.user?.email}</p>
                </div>
                {order.user?.phone && (
                  <div>
                    <p className="text-sm text-copy-light">Phone</p>
                    <p className="text-copy font-semibold">{order.user.phone}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Timeline */}
            <div className="bg-surface rounded-lg border border-border-light p-6">
              <h3 className="text-lg font-bold text-copy mb-4">Order Timeline</h3>
              <div className="space-y-3">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-primary/20 rounded-full flex items-center justify-center mt-1">
                    <Clock className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-semibold text-copy">Order Placed</p>
                    <p className="text-sm text-copy-light">
                      {new Date(order.created_at).toLocaleDateString()} {new Date(order.created_at).toLocaleTimeString()}
                    </p>
                  </div>
                </div>

                {order.confirmed_at && (
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-success/20 rounded-full flex items-center justify-center mt-1">
                      <CheckCircle className="w-5 h-5 text-success" />
                    </div>
                    <div>
                      <p className="font-semibold text-copy">Order Confirmed</p>
                      <p className="text-sm text-copy-light">
                        {new Date(order.confirmed_at).toLocaleDateString()} {new Date(order.confirmed_at).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                )}

                {order.shipped_at && (
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-primary/20 rounded-full flex items-center justify-center mt-1">
                      <Truck className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold text-copy">Shipped</p>
                      <p className="text-sm text-copy-light">
                        {new Date(order.shipped_at).toLocaleDateString()} {new Date(order.shipped_at).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                )}

                {order.delivered_at && (
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-success/20 rounded-full flex items-center justify-center mt-1">
                      <CheckCircle className="w-5 h-5 text-success" />
                    </div>
                    <div>
                      <p className="font-semibold text-copy">Delivered</p>
                      <p className="text-sm text-copy-light">
                        {new Date(order.delivered_at).toLocaleDateString()} {new Date(order.delivered_at).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar - Status Management & Pricing */}
          <div className="space-y-6">
            {/* Status Management */}
            <div className="bg-surface rounded-lg border border-border-light p-6">
              <h3 className="text-lg font-bold text-copy mb-4">Update Status</h3>
              <div className="space-y-4">
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-border-light rounded-lg bg-surface text-copy focus:outline-none focus:border-primary"
                >
                  {statusOptions.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>

                <button
                  onClick={handleStatusUpdate}
                  disabled={updating || newStatus === order.order_status}
                  className="w-full px-4 py-2 bg-primary text-copy-inverse rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  {updating ? 'Updating...' : 'Update Status'}
                </button>
              </div>
            </div>

            {/* Pricing Breakdown */}
            <div className="bg-surface rounded-lg border border-border-light p-6">
              <h3 className="text-lg font-bold text-copy mb-4">Pricing Details</h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-copy-light">Subtotal</span>
                  <span className="text-copy font-semibold">
                    {formatCurrency(order.subtotal ?? order.sub_total ?? (order.items?.reduce((s, i) => s + (Number(i.total_price) || Number(i.price_per_unit) * (i.quantity || 0)), 0)))}
                  </span>
                </div>

                <div className="flex justify-between text-sm">
                  <span className="text-copy-light">Shipping Cost</span>
                  <span className="text-copy font-semibold">{formatCurrency(order.shipping_cost)}</span>
                </div>

                <div className="flex justify-between text-sm">
                  <span className="text-copy-light">
                    Tax ({((order.tax_rate ?? 0) * 100).toFixed(1)}%)
                  </span>
                  <span className="text-copy font-semibold">{formatCurrency(order.tax_amount)}</span>
                </div>

                <div className="border-t border-border-light pt-3 flex justify-between">
                  <span className="text-copy font-bold">Total</span>
                  <span className="text-lg font-bold text-primary">{formatCurrency(order.total_amount)}</span>
                </div>
              </div>
            </div>

            {/* Tracking Information */}
            {order.tracking_number && (
              <div className="bg-surface rounded-lg border border-border-light p-6">
                <h3 className="text-lg font-bold text-copy mb-4">Tracking Information</h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-copy-light">Tracking Number</p>
                    <p className="text-copy font-mono font-semibold">{order.tracking_number}</p>
                  </div>
                  {order.carrier && (
                    <div>
                      <p className="text-sm text-copy-light">Carrier</p>
                      <p className="text-copy font-semibold">{order.carrier}</p>
                    </div>
                  )}
                  {order.shipping_method && (
                    <div>
                      <p className="text-sm text-copy-light">Shipping Method</p>
                      <p className="text-copy font-semibold">{order.shipping_method}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Items Tab */}
      {activeTab === 'items' && (
        <div className="bg-surface rounded-lg border border-border-light overflow-hidden">
          <div className="p-6 border-b border-border-light">
            <h3 className="text-lg font-bold text-copy">Order Items ({order.items?.length || 0})</h3>
          </div>

          {order.items && order.items.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-surface-dark border-b border-border-light">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Image</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Product</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Variant</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Quantity</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Unit Price</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-copy-light">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {order.items.map((item, index) => {
                    const unitPrice = Number(item.unit_price ?? item.price_per_unit ?? 0);
                    const qty = Number(item.quantity ?? 0);
                    const total = Number(item.total_price) || unitPrice * qty;
                    const primaryImage = item.variant?.images?.find((img: { is_primary?: boolean }) => img.is_primary) || item.variant?.images?.[0];
                    const imageUrl = primaryImage?.url;
                    return (
                      <tr key={item.id || index} className="border-b border-border-light hover:bg-surface-light">
                        <td className="px-6 py-4">
                          {imageUrl ? (
                            <img
                              src={imageUrl}
                              alt={primaryImage?.alt_text || item.product_name || 'Product'}
                              className="w-12 h-12 object-cover rounded border border-border-light"
                            />
                          ) : (
                            <div className="w-12 h-12 rounded border border-border-light bg-surface-dark flex items-center justify-center text-copy-light text-xs">—</div>
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm text-copy font-semibold">
                          {item.product_name ?? item.product?.name ?? 'N/A'}
                        </td>
                        <td className="px-6 py-4 text-sm text-copy-light">
                          {item.variant_name ?? item.sku ?? item.variant?.sku ?? 'N/A'}
                        </td>
                        <td className="px-6 py-4 text-sm text-copy">{item.quantity}</td>
                        <td className="px-6 py-4 text-sm text-copy">{formatCurrency(unitPrice)}</td>
                        <td className="px-6 py-4 text-sm font-semibold text-copy">{formatCurrency(total)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-6 text-center text-copy-light">No items in this order</div>
          )}
        </div>
      )}

      {/* Shipping Tab */}
      {activeTab === 'shipping' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Billing Address */}
          <div className="bg-surface rounded-lg border border-border-light p-6">
            <div className="flex items-center gap-2 mb-4">
              <MapPin className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-bold text-copy">Billing Address</h3>
            </div>
            {order.billing_address ? (
              <div className="space-y-2 text-sm text-copy">
                <p className="font-semibold">{order.billing_address.full_name}</p>
                <p>{order.billing_address.street_address}</p>
                {order.billing_address.apartment && <p>{order.billing_address.apartment}</p>}
                <p>
                  {order.billing_address.city}, {order.billing_address.province} {order.billing_address.postal_code}
                </p>
                <p>{order.billing_address.country}</p>
                {order.billing_address.phone && <p className="mt-3 font-semibold">{order.billing_address.phone}</p>}
              </div>
            ) : (
              <p className="text-copy-light">No billing address</p>
            )}
          </div>

          {/* Shipping Address */}
          <div className="bg-surface rounded-lg border border-border-light p-6">
            <div className="flex items-center gap-2 mb-4">
              <Truck className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-bold text-copy">Shipping Address</h3>
            </div>
            {order.shipping_address ? (
              <div className="space-y-2 text-sm text-copy">
                <p className="font-semibold">{order.shipping_address.full_name}</p>
                <p>{order.shipping_address.street_address}</p>
                {order.shipping_address.apartment && <p>{order.shipping_address.apartment}</p>}
                <p>
                  {order.shipping_address.city}, {order.shipping_address.province} {order.shipping_address.postal_code}
                </p>
                <p>{order.shipping_address.country}</p>
                {order.shipping_address.phone && <p className="mt-3 font-semibold">{order.shipping_address.phone}</p>}
              </div>
            ) : (
              <p className="text-copy-light">No shipping address</p>
            )}
          </div>

          {/* Shipping Details */}
          <div className="lg:col-span-2 bg-surface rounded-lg border border-border-light p-6">
            <h3 className="text-lg font-bold text-copy mb-4">Shipping Details</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-copy-light">Method</p>
                <p className="text-copy font-semibold">{order.shipping_method || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-copy-light">Cost</p>
                <p className="text-copy font-semibold">{formatCurrency(order.shipping_cost)}</p>
              </div>
              <div>
                <p className="text-sm text-copy-light">Tracking Number</p>
                <p className="text-copy font-mono">{order.tracking_number || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-copy-light">Carrier</p>
                <p className="text-copy font-semibold">{order.carrier || 'N/A'}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Notes Tab */}
      {activeTab === 'notes' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Customer Notes */}
          <div className="bg-surface rounded-lg border border-border-light p-6">
            <h3 className="text-lg font-bold text-copy mb-4">Customer Notes</h3>
            <p className="text-copy whitespace-pre-wrap">
              {order.customer_notes || '(No customer notes)'}
            </p>
          </div>

          {/* Internal Notes */}
          <div className="bg-surface rounded-lg border border-border-light p-6">
            <h3 className="text-lg font-bold text-copy mb-4">Internal Notes</h3>
            <p className="text-copy whitespace-pre-wrap">
              {order.internal_notes || '(No internal notes)'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminOrderDetail;
