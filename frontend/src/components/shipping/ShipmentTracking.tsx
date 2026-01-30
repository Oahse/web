import React, { useState, useEffect } from 'react';
import { 
  Package, 
  Truck, 
  MapPin, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  XCircle, 
  RotateCcw,
  ExternalLink,
  RefreshCw,
  Calendar,
  Map,
  Phone,
  User
} from 'lucide-react';
import { ShipmentTracking, ShippingTrackingAPI } from '../../api/shipping-tracking';

interface ShipmentTrackingProps {
  shipmentId?: string;
  orderId?: string;
  trackingNumber?: string;
  carrier?: string;
  autoRefresh?: boolean;
  showActions?: boolean;
  compact?: boolean;
}

export const ShipmentTracking: React.FC<ShipmentTrackingProps> = ({
  shipmentId,
  orderId,
  trackingNumber,
  carrier,
  autoRefresh = false,
  showActions = true,
  compact = false
}) => {
  const [shipment, setShipment] = useState<ShipmentTracking | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (shipmentId) {
      fetchShipment(shipmentId);
    } else if (orderId) {
      fetchOrderShipments(orderId);
    } else if (trackingNumber && carrier) {
      trackShipment(trackingNumber, carrier);
    }
  }, [shipmentId, orderId, trackingNumber, carrier]);

  useEffect(() => {
    if (autoRefresh && shipment?.status === 'in_transit') {
      const interval = setInterval(() => {
        refreshTracking();
      }, 5 * 60 * 1000); // Refresh every 5 minutes

      return () => clearInterval(interval);
    }
  }, [autoRefresh, shipment]);

  const fetchShipment = async (id: string) => {
    setLoading(true);
    setError('');
    try {
      const response = await ShippingTrackingAPI.getShipmentTracking(id);
      setShipment(response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch shipment tracking');
    } finally {
      setLoading(false);
    }
  };

  const fetchOrderShipments = async (id: string) => {
    setLoading(true);
    setError('');
    try {
      const shipments = await ShippingTrackingAPI.getOrderShipments(id);
      if (shipments.data && shipments.data.length > 0) {
        setShipment(shipments.data[0]); // Get the first shipment
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch order shipments');
    } finally {
      setLoading(false);
    }
  };

  const trackShipment = async (trackingNum: string, carrierName: string) => {
    setLoading(true);
    setError('');
    try {
      const response = await ShippingTrackingAPI.trackShipment({
        tracking_number: trackingNum,
        carrier: carrierName
      });
      setShipment(response.data.shipment);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to track shipment');
    } finally {
      setLoading(false);
    }
  };

  const refreshTracking = async () => {
    if (!shipment?.tracking_number || !shipment?.carrier) return;
    
    setRefreshing(true);
    try {
      const response = await ShippingTrackingAPI.trackShipment({
        tracking_number: shipment.tracking_number,
        carrier: shipment.carrier
      });
      setShipment(response.data.shipment);
    } catch (err: any) {
      console.error('Failed to refresh tracking:', err);
    } finally {
      setRefreshing(false);
    }
  };

  const openTrackingUrl = () => {
    if (!shipment) return;
    
    const url = ShippingTrackingAPI.getTrackingUrl(shipment);
    if (url) {
      window.open(url, '_blank');
    }
  };

  const getStatusInfo = () => {
    if (!shipment) return null;
    return ShippingTrackingAPI.formatStatus(shipment.status);
  };

  const formatLocation = (location: any) => {
    if (!location) return 'Unknown location';
    
    const parts = [];
    if (location.city) parts.push(location.city);
    if (location.state) parts.push(location.state);
    if (location.country) parts.push(location.country);
    
    return parts.join(', ') || 'Unknown location';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getLatestEvent = () => {
    if (!shipment) return null;
    return ShippingTrackingAPI.getLatestEvent(shipment);
  };

  const getTimeline = () => {
    if (!shipment) return [];
    return ShippingTrackingAPI.getTrackingTimeline(shipment);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading tracking information...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
      </div>
    );
  }

  if (!shipment) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="text-center text-gray-500">
          <Package className="h-8 w-8 mx-auto mb-2" />
          <p>No tracking information available</p>
        </div>
      </div>
    );
  }

  const statusInfo = getStatusInfo();
  const latestEvent = getLatestEvent();
  const timeline = getTimeline();
  const isDelayed = ShippingTrackingAPI.isDelayed(shipment);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img
              src={ShippingTrackingAPI.getCarrierLogo(shipment.carrier)}
              alt={ShippingTrackingAPI.getCarrierDisplayName(shipment.carrier)}
              className="h-8 w-8 object-contain"
            />
            <div>
              <h3 className="font-semibold text-gray-900">
                {ShippingTrackingAPI.getCarrierDisplayName(shipment.carrier)}
              </h3>
              <p className="text-sm text-gray-600 font-mono">
                {shipment.tracking_number}
              </p>
            </div>
          </div>
          
          {showActions && (
            <div className="flex items-center space-x-2">
              <button
                onClick={refreshTracking}
                disabled={refreshing}
                className="p-2 text-gray-600 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title="Refresh tracking"
              >
                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={openTrackingUrl}
                className="p-2 text-gray-600 hover:text-blue-600 transition-colors"
                title="Open tracking website"
              >
                <ExternalLink className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>

        {/* Status */}
        <div className="mt-4 flex items-center space-x-2">
          <statusInfo.icon className={`h-5 w-5 ${statusInfo.color}`} />
          <span className={`font-medium ${statusInfo.color}`}>
            {statusInfo.text}
          </span>
          {isDelayed && (
            <span className="text-red-600 text-sm font-medium">
              (Delayed)
            </span>
          )}
        </div>

        {/* Delivery Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 text-sm">
          <div>
            <span className="text-gray-500">Shipped:</span>
            <p className="font-medium">
              {shipment.shipped_at ? formatDate(shipment.shipped_at) : 'Not shipped'}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Estimated:</span>
            <p className="font-medium">
              {shipment.estimated_delivery 
                ? `${formatDate(shipment.estimated_delivery)} (${ShippingTrackingAPI.getTimeRemaining(shipment.estimated_delivery)})`
                : 'Unknown'
              }
            </p>
          </div>
          <div>
            <span className="text-gray-500">Delivered:</span>
            <p className="font-medium">
              {shipment.actual_delivery ? formatDate(shipment.actual_delivery) : 'Not delivered'}
            </p>
          </div>
        </div>
      </div>

      {/* Current Location */}
      {shipment.current_location && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <MapPin className="h-4 w-4 text-blue-600" />
            <span className="font-medium text-gray-900">Current Location</span>
          </div>
          <p className="text-gray-600">{formatLocation(shipment.current_location)}</p>
        </div>
      )}

      {/* Latest Event */}
      {latestEvent && !compact && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Clock className="h-4 w-4 text-gray-600" />
            <span className="font-medium text-gray-900">Latest Update</span>
          </div>
          <p className="text-gray-600">{latestEvent.event_description}</p>
          <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
            <span>{formatLocation(latestEvent.event_location)}</span>
            <span>{formatDate(latestEvent.event_timestamp)}</span>
          </div>
        </div>
      )}

      {/* Timeline */}
      {!compact && timeline.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-4">Tracking Timeline</h4>
          <div className="space-y-4">
            {timeline.map((event, index) => (
              <div key={event.id} className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    index === 0 ? 'bg-green-100' : 'bg-gray-100'
                  }`}>
                    {index === 0 ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                    )}
                  </div>
                  {index < timeline.length - 1 && (
                    <div className="absolute left-4 top-8 w-0.5 h-8 bg-gray-300"></div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">
                    {event.event_description}
                  </p>
                  <div className="flex items-center justify-between mt-1 text-xs text-gray-500">
                    <span>{formatLocation(event.event_location)}</span>
                    <span>{formatDate(event.event_timestamp)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Package Details */}
      {!compact && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-4">Package Details</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {shipment.package_weight && (
              <div>
                <span className="text-gray-500">Weight:</span>
                <p className="font-medium">{shipment.package_weight} kg</p>
              </div>
            )}
            {shipment.package_dimensions && (
              <div>
                <span className="text-gray-500">Dimensions:</span>
                <p className="font-medium">
                  {shipment.package_dimensions.length} × {shipment.package_dimensions.width} × {shipment.package_dimensions.height} cm
                </p>
              </div>
            )}
            {shipment.service_level && (
              <div>
                <span className="text-gray-500">Service:</span>
                <p className="font-medium">{shipment.service_level}</p>
              </div>
            )}
            {shipment.delivery_signature_required && (
              <div>
                <span className="text-gray-500">Signature Required:</span>
                <p className="font-medium">Yes</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ShipmentTracking;
