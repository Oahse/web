import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  PackageIcon, 
  TruckIcon, 
  CheckCircleIcon, 
  ClockIcon,
  MapPinIcon,
  ArrowLeftIcon,
  PrinterIcon
} from 'lucide-react';
import { OrdersAPI } from '../api/orders';
import { toast } from 'react-hot-toast';

interface TrackingEvent {
  id: string;
  status: string;
  description: string;
  location: string | null;
  timestamp: string;
}

interface TrackingData {
  order_id: string;
  status: string;
  tracking_number: string | null;
  carrier_name: string | null;
  estimated_delivery: string | null;
  tracking_events: TrackingEvent[];
}

const statusSteps = [
  { key: 'pending', label: 'Order Placed', icon: ClockIcon },
  { key: 'confirmed', label: 'Confirmed', icon: CheckCircleIcon },
  { key: 'shipped', label: 'Shipped', icon: TruckIcon },
  { key: 'delivered', label: 'Delivered', icon: PackageIcon },
];

export const TrackOrder = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const [tracking, setTracking] = useState<TrackingData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTracking = async () => {
      try {
        setLoading(true);
        // Use public tracking endpoint (no authentication required)
        const response = await OrdersAPI.trackOrderPublic(orderId);
        const trackingData = response?.data || response;
        setTracking(trackingData);
      } catch (error) {
        toast.error('Order not found or tracking information unavailable');
        console.error('Error fetching tracking:', error);
      } finally {
        setLoading(false);
      }
    };

    if (orderId) {
      fetchTracking();
    }
  }, [orderId]);

  const getCurrentStepIndex = (status: string) => {
    // Normalize status to match our steps
    const normalizedStatus = status.toLowerCase();
    
    // Map various statuses to our timeline steps
    if (normalizedStatus === 'delivered') return 3;
    if (normalizedStatus === 'shipped' || normalizedStatus === 'out_for_delivery' || normalizedStatus === 'in_transit') return 2;
    if (normalizedStatus === 'confirmed' || normalizedStatus === 'processing') return 1;
    if (normalizedStatus === 'pending') return 0;
    
    // Default to pending for unknown statuses
    return 0;
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'delivered':
        return 'text-green-600 dark:text-green-400';
      case 'shipped':
      case 'out_for_delivery':
        return 'text-blue-600 dark:text-blue-400';
      case 'confirmed':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'pending':
        return 'text-gray-600 dark:text-gray-400';
      case 'cancelled':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
            <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!tracking) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-4xl mx-auto text-center">
          <PackageIcon size={64} className="mx-auto text-gray-400 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Order Not Found
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            We couldn't find tracking information for this order.
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
            Please check your order number and try again.
          </p>
          <Link 
            to="/account/track-order" 
            className="inline-block px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
          >
            Search Another Order
          </Link>
        </div>
      </div>
    );
  }

  const currentStepIndex = getCurrentStepIndex(tracking.status);

  const handleDownloadInvoice = async () => {
    try {
      await OrdersAPI.getOrderInvoice(orderId);
      toast.success('Invoice downloaded successfully');
    } catch (error) {
      toast.error('Failed to download invoice');
      console.error('Error downloading invoice:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200 mb-6"
        >
          <ArrowLeftIcon size={20} className="mr-2" />
          Back
        </button>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Track Your Order
              </h1>
              <p className="text-gray-500 dark:text-gray-400">
                Order ID: {tracking.order_id}
              </p>
            </div>
            <button
              onClick={handleDownloadInvoice}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
            >
              <PrinterIcon size={18} />
              Download Invoice
            </button>
          </div>

          {tracking.tracking_number && (
            <div className="flex items-center gap-2 mb-4">
              <span className="text-sm text-gray-600 dark:text-gray-400">Tracking Number:</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {tracking.tracking_number}
              </span>
              {tracking.carrier_name && (
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  ({tracking.carrier_name})
                </span>
              )}
            </div>
          )}

          {tracking.estimated_delivery && (
            <div className="flex items-center gap-2 mb-6">
              <ClockIcon size={16} className="text-gray-400" />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Estimated Delivery: {new Date(tracking.estimated_delivery).toLocaleDateString()}
              </span>
            </div>
          )}

          {/* Status Timeline */}
          <div className="relative mb-8">
            <div className="flex justify-between items-center">
              {statusSteps.map((step, index) => {
                const Icon = step.icon;
                const isCompleted = index <= currentStepIndex;
                const isCurrent = index === currentStepIndex;

                return (
                  <div key={step.key} className="flex flex-col items-center flex-1 relative">
                    {/* Connector Line */}
                    {index < statusSteps.length - 1 && (
                      <div
                        className={`absolute top-6 left-1/2 w-full h-0.5 ${
                          isCompleted ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'
                        }`}
                        style={{ zIndex: 0 }}
                      />
                    )}

                    {/* Icon Circle */}
                    <div
                      className={`relative z-10 w-12 h-12 rounded-full flex items-center justify-center mb-2 ${
                        isCompleted
                          ? 'bg-primary text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-400'
                      } ${isCurrent ? 'ring-4 ring-primary ring-opacity-30' : ''}`}
                    >
                      <Icon size={24} />
                    </div>

                    {/* Label */}
                    <span
                      className={`text-xs text-center ${
                        isCompleted
                          ? 'text-gray-900 dark:text-white font-medium'
                          : 'text-gray-500 dark:text-gray-400'
                      }`}
                    >
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Current Status */}
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Current Status
            </h2>
            <p className={`text-xl font-bold ${getStatusColor(tracking.status)}`}>
              {tracking.status.charAt(0).toUpperCase() + tracking.status.slice(1).replace(/_/g, ' ')}
            </p>
            {tracking.status === 'cancelled' && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                This order has been cancelled
              </p>
            )}
          </div>
        </div>

        {/* Tracking Events Timeline */}
        {tracking.tracking_events && tracking.tracking_events.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Tracking History
            </h2>
            <div className="space-y-4">
              {tracking.tracking_events
                .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                .map((event, index) => (
                  <div key={event.id} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className="w-3 h-3 rounded-full bg-primary"></div>
                      {index < tracking.tracking_events.length - 1 && (
                        <div className="w-0.5 h-full bg-gray-300 dark:bg-gray-600 mt-2"></div>
                      )}
                    </div>
                    <div className="flex-1 pb-6">
                      <div className="flex items-start justify-between mb-1">
                        <p className="font-medium text-gray-900 dark:text-white">
                          {event.status.charAt(0).toUpperCase() + event.status.slice(1).replace('_', ' ')}
                        </p>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          {new Date(event.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                        {event.description}
                      </p>
                      {event.location && (
                        <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
                          <MapPinIcon size={14} />
                          <span>{event.location}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrackOrder;
