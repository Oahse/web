/**
 * Shipping Tracking API
 * Integrates with multiple shipping companies (UPS, Canada Express, Royal Mail, etc.)
 */

import { apiClient } from './client';

export interface ShipmentTracking {
  id: string;
  order_id: string;
  order_item_id?: string;
  tracking_number: string;
  carrier: string;
  status: string;
  shipment_type: string;
  shipped_at?: string;
  estimated_delivery?: string;
  actual_delivery?: string;
  current_location?: {
    city?: string;
    state?: string;
    country?: string;
    coordinates?: {
      lat: number;
      lng: number;
    };
  };
  delivery_instructions?: string;
  package_weight?: number;
  package_dimensions?: {
    length: number;
    width: number;
    height: number;
  };
  package_value?: number;
  insurance_amount?: number;
  service_level?: string;
  delivery_signature_required: boolean;
  external_tracking_url?: string;
  tracking_events: TrackingEvent[];
  created_at: string;
  updated_at: string;
}

export interface TrackingEvent {
  id: string;
  shipment_id: string;
  event_timestamp: string;
  event_type: string;
  event_description: string;
  event_location?: {
    city?: string;
    state?: string;
    country?: string;
    coordinates?: {
      lat: number;
      lng: number;
    };
  };
  carrier_event_code?: string;
  estimated_delivery?: string;
  delay_reason?: string;
  contact_name?: string;
  contact_phone?: string;
  source: string;
  created_at: string;
}

export interface ShippingProvider {
  id: string;
  name: string;
  carrier: string;
  api_url: string;
  tracking_url_template: string;
  is_active: boolean;
  created_at: string;
}

export interface ShipmentCreateRequest {
  order_id: string;
  order_item_id?: string;
  carrier: string;
  tracking_number: string;
  shipment_type?: string;
  origin_address?: any;
  destination_address?: any;
  delivery_instructions?: string;
  package_weight?: number;
  package_dimensions?: {
    length: number;
    width: number;
    height: number;
  };
  package_value?: number;
  insurance_amount?: number;
  service_level?: string;
  delivery_signature_required?: boolean;
  delivery_confirmation?: string;
  notes?: string;
  internal_notes?: string;
  shipped_at?: string;
}

export interface ShipmentUpdateRequest {
  status: string;
  event_description?: string;
  event_location?: any;
  contact_name?: string;
  contact_phone?: string;
}

export interface TrackingRequest {
  tracking_number: string;
  carrier: string;
}

export class ShippingTrackingAPI {
  /**
   * Create a new shipment tracking record
   */
  static async createShipment(shipmentData: ShipmentCreateRequest) {
    const response = await apiClient.post('/shipping-tracking/shipments', shipmentData);
    return response.data;
  }

  /**
   * Get detailed tracking information for a shipment
   */
  static async getShipmentTracking(shipmentId: string) {
    const response = await apiClient.get(`/shipping-tracking/shipments/${shipmentId}`);
    return response.data;
  }

  /**
   * Get all shipments for an order
   */
  static async getOrderShipments(orderId: string) {
    const response = await apiClient.get(`/shipping-tracking/orders/${orderId}/shipments`);
    return response.data;
  }

  /**
   * Track a shipment using carrier-specific integration
   */
  static async trackShipment(trackingRequest: TrackingRequest) {
    const response = await apiClient.post('/shipping-tracking/track', trackingRequest);
    return response.data;
  }

  /**
   * Update shipment status and create tracking event
   */
  static async updateShipmentStatus(shipmentId: string, updateData: ShipmentUpdateRequest) {
    const response = await apiClient.put(`/shipping-tracking/shipments/${shipmentId}/status`, updateData);
    return response.data;
  }

  /**
   * Get list of supported shipping carriers
   */
  static async getSupportedCarriers() {
    const response = await apiClient.get('/shipping-tracking/carriers');
    return response.data;
  }

  /**
   * Get tracking URL for a shipment
   */
  static getTrackingUrl(shipment: ShipmentTracking): string | null {
    if (shipment.external_tracking_url) {
      return shipment.external_tracking_url;
    }
    
    // Fallback: generate carrier-specific URL if template is available
    const carrierUrls: Record<string, string> = {
      'ups': `https://www.ups.com/track?tracknum=${shipment.tracking_number}`,
      'canada_express': `https://www.canadapost.ca/track?trackingNumber=${shipment.tracking_number}`,
      'royal_mail': `https://www.royalmail.com/track-your-item?trackNumber=${shipment.tracking_number}`,
      'fedex': `https://www.fedex.com/fedextrack/?trknbr=${shipment.tracking_number}`,
      'dhl': `https://www.dhl.com/en/express/tracking.html?AWB=${shipment.tracking_number}`,
      'usps': `https://tools.usps.com/go/TrackConfirmAction_input?qtc_tLabels1=${shipment.tracking_number}`,
      'canada_post': `https://www.canadapost.ca/cpotools/track/trackPackage?trackingNumber=${shipment.tracking_number}`,
      'purolator': `https://www.purolator.com/en/track/tracking-summary.xhtml?pin=${shipment.tracking_number}`
    };
    
    return carrierUrls[shipment.carrier] || null;
  }

  /**
   * Get carrier-specific tracking URL template
   */
  static getCarrierTrackingUrl(carrier: string, trackingNumber: string): string {
    const templates: Record<string, string> = {
      'ups': `https://www.ups.com/track?tracknum={tracking_number}`,
      'canada_express': `https://www.canadapost.ca/track?trackingNumber={tracking_number}`,
      'royal_mail': `https://www.royalmail.com/track-your-item?trackNumber={tracking_number}`,
      'fedex': `https://www.fedex.com/fedextrack/?trknbr={tracking_number}`,
      'dhl': `https://www.dhl.com/en/express/tracking.html?AWB={tracking_number}`,
      'usps': `https://tools.usps.com/go/TrackConfirmAction_input?qtc_tLabels1={tracking_number}`,
      'canada_post': `https://www.canadapost.ca/cpotools/track/trackPackage?trackingNumber={tracking_number}`,
      'purolator': `https://www.purolator.com/en/track/tracking-summary.xhtml?pin={tracking_number}`
    };
    
    return templates[carrier] || `https://www.google.com/search?q=${carrier}+tracking+${trackingNumber}`;
  }

  /**
   * Get carrier logo URL
   */
  static getCarrierLogo(carrier: string): string {
    const logos: Record<string, string> = {
      'ups': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/UPS_logo_2014.svg/200px-UPS_logo_2014.svg.png',
      'canada_express': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Canada_Post_logo_2020.svg/200px-Canada_Post_logo_2020.svg.png',
      'royal_mail': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Royal_Mail_logo.svg/200px-Royal_Mail_logo.svg.png',
      'fedex': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/FedEx_logo_2014.svg/200px-FedEx_logo_2014.svg.png',
      'dhl': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/DHL_2017_logo.svg/200px-DHL_2017_logo.svg.png',
      'usps': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/USPS_logo_2014.svg/200px-USPS_logo_2014.svg.png',
      'canada_post': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Canada_Post_logo_2020.svg/200px-Canada_Post_logo_2020.svg.png',
      'purolator': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Purolator_logo.svg/200px-Purolator_logo.svg.png'
    };
    
    return logos[carrier] || '/images/default-carrier-logo.png';
  }

  /**
   * Get carrier display name
   */
  static getCarrierDisplayName(carrier: string): string {
    const names: Record<string, string> = {
      'ups': 'UPS',
      'canada_express': 'Canada Express',
      'royal_mail': 'Royal Mail',
      'fedex': 'FedEx',
      'dhl': 'DHL',
      'usps': 'USPS',
      'canada_post': 'Canada Post',
      'purolator': 'Purolator'
    };
    
    return names[carrier] || carrier;
  }

  /**
   * Format tracking status for display
   */
  static formatStatus(status: string): { text: string; color: string; icon: string } {
    const statusMap: Record<string, { text: string; color: string; icon: string }> = {
      'pending': { text: 'Pending', color: 'text-gray-500', icon: 'clock' },
      'in_transit': { text: 'In Transit', color: 'text-blue-500', icon: 'truck' },
      'out_for_delivery': { text: 'Out for Delivery', color: 'text-orange-500', icon: 'map-pin' },
      'delivered': { text: 'Delivered', color: 'text-green-500', icon: 'check-circle' },
      'delayed': { text: 'Delayed', color: 'text-red-500', icon: 'alert-circle' },
      'exception': { text: 'Exception', color: 'text-red-600', icon: 'x-circle' },
      'returned': { text: 'Returned', color: 'text-yellow-600', icon: 'rotate-ccw' },
      'cancelled': { text: 'Cancelled', color: 'text-gray-400', icon: 'x' }
    };
    
    return statusMap[status] || { text: status, color: 'text-gray-500', icon: 'help-circle' };
  }

  /**
   * Format shipment type for display
   */
  static formatShipmentType(type: string): string {
    const types: Record<string, string> = {
      'standard': 'Standard Shipping',
      'express': 'Express Shipping',
      'overnight': 'Overnight Shipping',
      'international': 'International Shipping',
      'freight': 'Freight Shipping'
    };
    
    return types[type] || type;
  }

  /**
   * Get estimated delivery time remaining
   */
  static getTimeRemaining(estimatedDelivery: string): string {
    if (!estimatedDelivery) return 'Unknown';
    
    const now = new Date();
    const delivery = new Date(estimatedDelivery);
    const diffMs = delivery.getTime() - now.getTime();
    
    if (diffMs <= 0) return 'Delivered';
    
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    
    if (diffDays > 0) {
      return `${diffDays} day${diffDays > 1 ? 's' : ''}`;
    } else if (diffHours > 0) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''}`;
    } else {
      return 'Less than an hour';
    }
  }

  /**
   * Check if shipment is delayed
   */
  static isDelayed(shipment: ShipmentTracking): boolean {
    if (!shipment.estimated_delivery) return false;
    
    const now = new Date();
    const delivery = new Date(shipment.estimated_delivery);
    
    return now > delivery && shipment.status !== 'delivered';
  }

  /**
   * Get latest tracking event
   */
  static getLatestEvent(shipment: ShipmentTracking): TrackingEvent | null {
    if (!shipment.tracking_events || shipment.tracking_events.length === 0) {
      return null;
    }
    
    return shipment.tracking_events.reduce((latest, event) => {
      return new Date(event.event_timestamp) > new Date(latest.event_timestamp) ? event : latest;
    });
  }

  /**
   * Get tracking timeline sorted by date
   */
  static getTrackingTimeline(shipment: ShipmentTracking): TrackingEvent[] {
    if (!shipment.tracking_events) return [];
    
    return [...shipment.tracking_events].sort((a, b) => 
      new Date(b.event_timestamp).getTime() - new Date(a.event_timestamp).getTime()
    );
  }
}

export default ShippingTrackingAPI;
