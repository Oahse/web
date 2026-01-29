/**
 * Orders API endpoints
 * 
 * ACCESS LEVELS:
 * - Public: Order tracking (no authentication required)
 * - Authenticated: Order creation, viewing own orders, order management
 * - Supplier: View and manage supplier orders, update order status
 * - Admin: View all orders, order statistics, export functionality
 */

import { apiClient } from './client'; 

// Order interface with simplified pricing structure
export interface Order {
  id: string;
  order_number: string;
  user_id: string;
  guest_email?: string;
  subscription_id?: string;
  order_status: 'pending' | 'confirmed' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'refunded';
  payment_status: 'pending' | 'authorized' | 'paid' | 'failed' | 'cancelled' | 'refunded';
  fulfillment_status: 'unfulfilled' | 'partial' | 'fulfilled' | 'cancelled';
  
  // Simplified pricing structure
  subtotal: number; // Sum of all product variant prices
  shipping_cost: number; // Updated field name
  tax_amount: number;
  tax_rate: number; // Tax rate applied (e.g., 0.08 for 8%)
  total_amount: number; // Final total: subtotal + shipping + tax
  currency: string;
  
  // Shipping information
  shipping_method?: string;
  tracking_number?: string;
  carrier?: string;
  
  // Addresses
  billing_address: any;
  shipping_address: any;
  
  // Lifecycle dates
  confirmed_at?: string;
  shipped_at?: string;
  delivered_at?: string;
  cancelled_at?: string;
  
  // Notes
  customer_notes?: string;
  internal_notes?: string;
  
  // Additional fields
  failure_reason?: string;
  idempotency_key?: string;
  source?: 'web' | 'mobile' | 'api' | 'admin';
  
  // Items
  items?: OrderItem[];
  
  // Timestamps
  created_at: string;
  updated_at?: string;
}

export interface OrderItem {
  id: string;
  order_id: string;
  variant_id: string;
  quantity: number;
  price_per_unit: number;
  total_price: number;
  created_at: string;
}

// Checkout data interface with simplified pricing
export interface CheckoutData {
  items: Array<{
    variant_id: string;
    quantity: number;
  }>;
  shipping_address: any;
  billing_address?: any;
  payment_method_id?: string;
  shipping_method_id?: string;
  promocode?: string;
  guest_email?: string;
  customer_notes?: string;
}

// Order calculation response
export interface OrderCalculation {
  subtotal: number;
  shipping_cost: number; // Updated field name
  tax_amount: number;
  tax_rate: number;
  total_amount: number;
  currency: string;
  items: Array<{
    variant_id: string;
    quantity: number;
    price_per_unit: number;
    total_price: number;
  }>;
} 

export class OrdersAPI {
  /**
   * Create new order
   * ACCESS: Authenticated - Requires user login
   */
  static async createOrder(orderData) {
    return await apiClient.post('/v1/orders', orderData);
  }

  /**
   * Validate checkout before placing order
   * ACCESS: Authenticated - Requires user login
   */
  static async validateCheckout(checkoutData: {
    shipping_address_id: string;
    shipping_method_id: string;
    payment_method_id: string;
    discount_code?: string;
    notes?: string;
    currency?: string;
    country_code?: string;
    frontend_calculated_total?: number;
  }) {
    try {
      const response = await apiClient.post('/v1/orders/checkout/validate', checkoutData);
      return {
        success: true,
        data: response.data
      };
    } catch (error: any) {
      console.error('Checkout validation failed:', error);
      return {
        success: false,
        message: error.response?.data?.message || error.message || 'Checkout validation failed',
        data: error.response?.data
      };
    }
  }

  /**
   * Place order (checkout)
   * ACCESS: Authenticated - Requires user login
   */
  static async placeOrder(checkoutData: {
    shipping_address_id: string;
    shipping_method_id: string;
    payment_method_id: string;
    discount_code?: string;
    notes?: string;
    currency?: string;
    country_code?: string;
    frontend_calculated_total?: number;
  }) {
    try {
      // Increase timeout for checkout as it involves payment processing
      const response = await apiClient.post('/v1/orders/checkout', checkoutData, { timeout: 60000 });
      return {
        success: true,
        data: response.data
      };
    } catch (error: any) {
      console.error('Order placement failed:', error);
      return {
        success: false,
        message: error.response?.data?.message || error.message || 'Order placement failed',
        data: error.response?.data
      };
    }
  }

  /**
   * Create Payment Intent and return client secret
   * ACCESS: Authenticated - Requires user login
   */
  static async createPaymentIntent(checkoutData: any) {
    return await apiClient.post('/v1/orders/create-payment-intent', checkoutData);
  }

  /**
   * Calculate tax for checkout
   * @deprecated Use TaxAPI.calculateTax() instead
   */
  static async calculateTax(taxData) {
    console.warn('OrdersAPI.calculateTax() is deprecated. Use TaxAPI.calculateTax() instead.');
    return await apiClient.post('/v1/tax/calculate', taxData);
  }

  /**
   * Get user's orders
   * ACCESS: Authenticated - Requires user login (own orders only)
   */
  static async getOrders(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);

    const url = `/v1/orders${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get order by ID
   * ACCESS: Authenticated - Requires user login (own orders only)
   */
  static async getOrder(orderId) {
    return await apiClient.get(`/v1/orders/${orderId}`);
  }

  /**
   * Get order tracking information (authenticated)
   * ACCESS: Authenticated - Requires user login (own orders only)
   */
  static async getOrderTracking(orderId) {
    return await apiClient.get(`/v1/orders/${orderId}/tracking`);
  }

  /**
   * Get order tracking information (public - no auth required)
   * ACCESS: Public - No authentication required
   */
  static async trackOrderPublic(orderId) {
    return await apiClient.get(`/v1/orders/track/${orderId}`);
  }

  /**
   * Cancel order
   * ACCESS: Authenticated - Requires user login (own orders only)
   */
  static async cancelOrder(orderId, reason) {
    return await apiClient.put(`/v1/orders/${orderId}/cancel`, { reason });
  }

  /**
   * Request order refund
   */
  static async requestRefund(orderId, data) {
    return await apiClient.post(`/refunds/orders/${orderId}/request`, data);
  }

  /**
   * Check refund eligibility
   */
  static async checkRefundEligibility(orderId) {
    return await apiClient.get(`/refunds/orders/${orderId}/eligibility`);
  }

  /**
   * Get order invoice
   */
  static async getOrderInvoice(orderId) {
    await apiClient.download(`/orders/${orderId}/invoice`, `invoice-${orderId}.pdf`);
  }

  /**
   * Reorder (create new order from existing order)
   */
  static async reorder(orderId) {
    return await apiClient.post(`/orders/${orderId}/reorder`);
  }

  /**
   * Add order note
   */
  static async addOrderNote(orderId, note) {
    return await apiClient.post(`/orders/${orderId}/notes`, { note });
  }

  /**
   * Get order notes
   */
  static async getOrderNotes(orderId) {
    return await apiClient.get(`/orders/${orderId}/notes`);
  }

  // Supplier endpoints
  /**
   * Get supplier orders
   * ACCESS: Supplier - Requires supplier role (own orders only)
   */
  static async getSupplierOrders(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);

    const url = `/supplier/orders${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Update order status
   * ACCESS: Supplier/Admin - Requires supplier or admin role
   */
  static async updateOrderStatus(orderId, data) {
    return await apiClient.put(`/orders/${orderId}/status`, data);
  }

  /**
   * Mark order as shipped
   * ACCESS: Supplier - Requires supplier role
   */
  static async markAsShipped(orderId, data) {
    return await apiClient.put(`/orders/${orderId}/ship`, data);
  }

  /**
   * Mark order as delivered
   * ACCESS: Supplier - Requires supplier role
   */
  static async markAsDelivered(orderId, data) {
    return await apiClient.put(`/orders/${orderId}/deliver`, data || {});
  }

  /**
   * Process refund
   * ACCESS: Supplier/Admin - Requires supplier or admin role
   */
  static async processRefund(refundId, data) {
    return await apiClient.put(`/refunds/${refundId}/process`, data);
  }

  // Admin endpoints
  /**
   * Get all orders
   * ACCESS: Admin Only - Requires admin role
   */
  static async getAllOrders(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.status) queryParams.append('status', params.status);
    if (params?.supplier_id) queryParams.append('supplier_id', params.supplier_id);
    if (params?.customer_id) queryParams.append('customer_id', params.customer_id);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);

    const url = `/admin/orders${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Get order statistics
   * ACCESS: Admin Only - Requires admin role
   */
  static async getOrderStatistics(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);
    if (params?.group_by) queryParams.append('group_by', params.group_by);

    const url = `/admin/orders/statistics${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await apiClient.get(url);
  }

  /**
   * Export orders
   * ACCESS: Admin Only - Requires admin role
   */
  static async exportOrders(params) {
    const queryParams = new URLSearchParams();
    
    if (params?.format) queryParams.append('format', params.format);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);
    if (params?.q) queryParams.append('q', params.q);
    if (params?.min_price) queryParams.append('min_price', params.min_price.toString());
    if (params?.max_price) queryParams.append('max_price', params.max_price.toString());

    const url = `/admin/orders/export${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    
    // Determine file extension based on format
    let extension = 'csv';
    if (params?.format === 'excel') extension = 'xlsx';
    else if (params?.format === 'pdf') extension = 'pdf';
    
    const filename = `orders-export-${new Date().toISOString().split('T')[0]}.${extension}`;
    
    await apiClient.download(url, filename);
  }
}

export default OrdersAPI;