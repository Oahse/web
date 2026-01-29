/**
 * Tests for Orders API - Comprehensive test suite aligned with backend reality
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { OrdersAPI } from '../../api/orders';
import { apiClient } from '../../api/client';

// Mock the API client
vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    download: vi.fn()
  }
}));

const mockApiClient = vi.mocked(apiClient);

describe('OrdersAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('createOrder', () => {
    it('should create new order with correct backend format', async () => {
      const orderData = {
        items: [
          { variant_id: 'var123', quantity: 2 }
        ],
        shipping_address: {
          street: '123 Main St',
          city: 'New York',
          state: 'NY',
          postal_code: '10001',
          country: 'US'
        },
        billing_address: {
          street: '123 Main St',
          city: 'New York',
          state: 'NY',
          postal_code: '10001',
          country: 'US'
        },
        payment_method_id: 'pm_123',
        shipping_method_id: 'ship_123'
      };

      const mockResponse = {
        success: true,
        data: {
          id: 'order123',
          order_number: 'ORD-2024-001',
          order_status: 'pending',
          payment_status: 'pending',
          total_amount: 129.99,
          currency: 'USD'
        },
        message: 'Order created successfully'
      };

      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await OrdersAPI.createOrder(orderData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/v1/orders', orderData);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('validateCheckout', () => {
    it('should validate checkout data before placing order', async () => {
      const checkoutData = {
        shipping_address_id: 'addr123',
        shipping_method_id: 'ship123',
        payment_method_id: 'pm123',
        discount_code: 'SAVE10',
        notes: 'Please handle with care',
        currency: 'USD',
        country_code: 'US',
        frontend_calculated_total: 129.99
      };

      const mockResponse = {
        success: true,
        data: {
          valid: true,
          calculated_total: 129.99,
          breakdown: {
            subtotal: 100.00,
            shipping_cost: 9.99,
            tax_amount: 8.80,
            discount_amount: 10.00,
            total_amount: 129.99
          },
          warnings: []
        }
      };

      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await OrdersAPI.validateCheckout(checkoutData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/v1/orders/checkout/validate', checkoutData);
      expect(result).toEqual({
        success: true,
        data: mockResponse.data
      });
    });

    it('should handle validation errors gracefully', async () => {
      const checkoutData = {
        shipping_address_id: 'addr123',
        shipping_method_id: 'ship123',
        payment_method_id: 'invalid_pm'
      };

      const mockError = {
        response: {
          data: {
            message: 'Invalid payment method',
            details: { payment_method_id: ['Payment method not found'] }
          }
        }
      };

      mockApiClient.post.mockRejectedValue(mockError);

      const result = await OrdersAPI.validateCheckout(checkoutData);

      expect(result).toEqual({
        success: false,
        message: 'Invalid payment method',
        data: mockError.response.data
      });
    });
  });

  describe('placeOrder', () => {
    it('should place order with extended timeout', async () => {
      const checkoutData = {
        shipping_address_id: 'addr123',
        shipping_method_id: 'ship123',
        payment_method_id: 'pm123',
        currency: 'USD',
        country_code: 'US'
      };

      const mockResponse = {
        success: true,
        data: {
          order: {
            id: 'order123',
            order_number: 'ORD-2024-001',
            order_status: 'confirmed',
            payment_status: 'paid',
            total_amount: 129.99
          },
          payment: {
            id: 'pay123',
            status: 'succeeded'
          }
        }
      };

      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await OrdersAPI.placeOrder(checkoutData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/v1/orders/checkout', checkoutData, { timeout: 60000 });
      expect(result).toEqual({
        success: true,
        data: mockResponse.data
      });
    });

    it('should handle order placement errors', async () => {
      const checkoutData = {
        shipping_address_id: 'addr123',
        shipping_method_id: 'ship123',
        payment_method_id: 'pm123'
      };

      const mockError = {
        response: {
          data: {
            message: 'Payment failed',
            code: 'PAYMENT_DECLINED'
          }
        }
      };

      mockApiClient.post.mockRejectedValue(mockError);

      const result = await OrdersAPI.placeOrder(checkoutData);

      expect(result).toEqual({
        success: false,
        message: 'Payment failed',
        data: mockError.response.data
      });
    });
  });

  describe('createPaymentIntent', () => {
    it('should create payment intent for Stripe', async () => {
      const checkoutData = {
        amount: 12999, // in cents
        currency: 'usd',
        payment_method_types: ['card']
      };

      const mockResponse = {
        success: true,
        data: {
          client_secret: 'pi_123_secret_456',
          payment_intent_id: 'pi_123'
        }
      };

      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await OrdersAPI.createPaymentIntent(checkoutData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/v1/orders/create-payment-intent', checkoutData);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getOrders', () => {
    it('should get user orders with filters', async () => {
      const params = {
        status: 'completed',
        page: 1,
        limit: 10,
        date_from: '2024-01-01',
        date_to: '2024-12-31'
      };

      const mockResponse = {
        success: true,
        data: {
          orders: [
            {
              id: 'order123',
              order_number: 'ORD-2024-001',
              order_status: 'completed',
              total_amount: 129.99,
              created_at: '2024-01-15T10:00:00Z'
            }
          ],
          total: 1,
          page: 1,
          per_page: 10,
          total_pages: 1
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await OrdersAPI.getOrders(params);

      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/v1/orders?status=completed&page=1&limit=10&date_from=2024-01-01&date_to=2024-12-31'
      );
      expect(result).toEqual(mockResponse);
    });

    it('should get orders without filters', async () => {
      const mockResponse = {
        success: true,
        data: { orders: [], total: 0 }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await OrdersAPI.getOrders({});

      expect(mockApiClient.get).toHaveBeenCalledWith('/v1/orders');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getOrder', () => {
    it('should get order by ID', async () => {
      const orderId = 'order123';
      const mockResponse = {
        success: true,
        data: {
          id: orderId,
          order_number: 'ORD-2024-001',
          order_status: 'completed',
          payment_status: 'paid',
          items: [
            {
              id: 'item123',
              variant_id: 'var123',
              quantity: 2,
              price_per_unit: 49.99,
              total_price: 99.98
            }
          ],
          shipping_address: {
            street: '123 Main St',
            city: 'New York',
            state: 'NY'
          },
          total_amount: 129.99
        }
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await OrdersAPI.getOrder(orderId);

      expect(mockApiClient.get).toHaveBeenCalledWith(`/v1/orders/${orderId}`);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Order Tracking', () => {
    describe('getOrderTracking', () => {
      it('should get authenticated order tracking', async () => {
        const orderId = 'order123';
        const mockResponse = {
          success: true,
          data: {
            order_id: orderId,
            tracking_number: 'TRK123456789',
            carrier: 'UPS',
            status: 'in_transit',
            tracking_events: [
              {
                status: 'shipped',
                location: 'New York, NY',
                timestamp: '2024-01-15T10:00:00Z'
              }
            ]
          }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.getOrderTracking(orderId);

        expect(mockApiClient.get).toHaveBeenCalledWith(`/v1/orders/${orderId}/tracking`);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('trackOrderPublic', () => {
      it('should get public order tracking without authentication', async () => {
        const orderId = 'order123';
        const mockResponse = {
          success: true,
          data: {
            order_number: 'ORD-2024-001',
            status: 'shipped',
            tracking_number: 'TRK123456789',
            estimated_delivery: '2024-01-20'
          }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.trackOrderPublic(orderId);

        expect(mockApiClient.get).toHaveBeenCalledWith(`/v1/orders/track/${orderId}`);
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Order Management', () => {
    describe('cancelOrder', () => {
      it('should cancel order with reason', async () => {
        const orderId = 'order123';
        const reason = 'Customer requested cancellation';

        const mockResponse = {
          success: true,
          data: {
            id: orderId,
            order_status: 'cancelled',
            cancelled_at: '2024-01-15T12:00:00Z'
          },
          message: 'Order cancelled successfully'
        };

        mockApiClient.put.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.cancelOrder(orderId, reason);

        expect(mockApiClient.put).toHaveBeenCalledWith(`/v1/orders/${orderId}/cancel`, { reason });
        expect(result).toEqual(mockResponse);
      });
    });

    describe('reorder', () => {
      it('should create new order from existing order', async () => {
        const orderId = 'order123';
        const mockResponse = {
          success: true,
          data: {
            new_order_id: 'order456',
            cart_id: 'cart789'
          },
          message: 'Items added to cart for reorder'
        };

        mockApiClient.post.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.reorder(orderId);

        expect(mockApiClient.post).toHaveBeenCalledWith(`/orders/${orderId}/reorder`);
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Refunds', () => {
    describe('requestRefund', () => {
      it('should request order refund', async () => {
        const orderId = 'order123';
        const refundData = {
          reason: 'Product defective',
          items: [
            { item_id: 'item123', quantity: 1, reason: 'Damaged on arrival' }
          ]
        };

        const mockResponse = {
          success: true,
          data: {
            refund_id: 'ref123',
            status: 'pending',
            amount: 49.99
          },
          message: 'Refund request submitted'
        };

        mockApiClient.post.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.requestRefund(orderId, refundData);

        expect(mockApiClient.post).toHaveBeenCalledWith(`/refunds/orders/${orderId}/request`, refundData);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('checkRefundEligibility', () => {
      it('should check if order is eligible for refund', async () => {
        const orderId = 'order123';
        const mockResponse = {
          success: true,
          data: {
            eligible: true,
            reasons: ['Product defective', 'Wrong item received'],
            deadline: '2024-02-15T00:00:00Z'
          }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.checkRefundEligibility(orderId);

        expect(mockApiClient.get).toHaveBeenCalledWith(`/refunds/orders/${orderId}/eligibility`);
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Order Notes', () => {
    describe('addOrderNote', () => {
      it('should add note to order', async () => {
        const orderId = 'order123';
        const note = 'Please deliver to back door';

        const mockResponse = {
          success: true,
          data: {
            note_id: 'note123',
            content: note,
            created_at: '2024-01-15T10:00:00Z'
          }
        };

        mockApiClient.post.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.addOrderNote(orderId, note);

        expect(mockApiClient.post).toHaveBeenCalledWith(`/orders/${orderId}/notes`, { note });
        expect(result).toEqual(mockResponse);
      });
    });

    describe('getOrderNotes', () => {
      it('should get order notes', async () => {
        const orderId = 'order123';
        const mockResponse = {
          success: true,
          data: {
            notes: [
              {
                id: 'note123',
                content: 'Please deliver to back door',
                created_at: '2024-01-15T10:00:00Z'
              }
            ]
          }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.getOrderNotes(orderId);

        expect(mockApiClient.get).toHaveBeenCalledWith(`/orders/${orderId}/notes`);
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Supplier Endpoints', () => {
    describe('getSupplierOrders', () => {
      it('should get supplier orders with filters', async () => {
        const params = {
          status: 'processing',
          page: 1,
          limit: 20,
          date_from: '2024-01-01'
        };

        const mockResponse = {
          success: true,
          data: {
            orders: [
              {
                id: 'order123',
                order_number: 'ORD-2024-001',
                customer_name: 'John Doe',
                status: 'processing'
              }
            ],
            total: 1
          }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.getSupplierOrders(params);

        expect(mockApiClient.get).toHaveBeenCalledWith(
          '/supplier/orders?status=processing&page=1&limit=20&date_from=2024-01-01'
        );
        expect(result).toEqual(mockResponse);
      });
    });

    describe('updateOrderStatus', () => {
      it('should update order status', async () => {
        const orderId = 'order123';
        const statusData = {
          status: 'processing',
          notes: 'Order is being prepared'
        };

        const mockResponse = {
          success: true,
          data: {
            id: orderId,
            order_status: 'processing',
            updated_at: '2024-01-15T10:00:00Z'
          }
        };

        mockApiClient.put.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.updateOrderStatus(orderId, statusData);

        expect(mockApiClient.put).toHaveBeenCalledWith(`/orders/${orderId}/status`, statusData);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('markAsShipped', () => {
      it('should mark order as shipped', async () => {
        const orderId = 'order123';
        const shippingData = {
          tracking_number: 'TRK123456789',
          carrier: 'UPS',
          notes: 'Shipped via UPS Ground'
        };

        const mockResponse = {
          success: true,
          data: {
            id: orderId,
            order_status: 'shipped',
            tracking_number: 'TRK123456789',
            shipped_at: '2024-01-15T10:00:00Z'
          }
        };

        mockApiClient.put.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.markAsShipped(orderId, shippingData);

        expect(mockApiClient.put).toHaveBeenCalledWith(`/orders/${orderId}/ship`, shippingData);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('markAsDelivered', () => {
      it('should mark order as delivered', async () => {
        const orderId = 'order123';
        const deliveryData = {
          delivered_at: '2024-01-20T14:30:00Z',
          notes: 'Delivered to front door'
        };

        const mockResponse = {
          success: true,
          data: {
            id: orderId,
            order_status: 'delivered',
            delivered_at: '2024-01-20T14:30:00Z'
          }
        };

        mockApiClient.put.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.markAsDelivered(orderId, deliveryData);

        expect(mockApiClient.put).toHaveBeenCalledWith(`/orders/${orderId}/deliver`, deliveryData);
        expect(result).toEqual(mockResponse);
      });

      it('should mark as delivered without data', async () => {
        const orderId = 'order123';

        const mockResponse = {
          success: true,
          data: {
            id: orderId,
            order_status: 'delivered'
          }
        };

        mockApiClient.put.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.markAsDelivered(orderId);

        expect(mockApiClient.put).toHaveBeenCalledWith(`/orders/${orderId}/deliver`, {});
        expect(result).toEqual(mockResponse);
      });
    });
  });

  describe('Admin Endpoints', () => {
    describe('getAllOrders', () => {
      it('should get all orders with admin filters', async () => {
        const params = {
          status: 'pending',
          supplier_id: 'sup123',
          customer_id: 'cust456',
          page: 1,
          limit: 50
        };

        const mockResponse = {
          success: true,
          data: {
            orders: [
              {
                id: 'order123',
                supplier_name: 'Supplier ABC',
                customer_name: 'John Doe',
                status: 'pending'
              }
            ],
            total: 1
          }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.getAllOrders(params);

        expect(mockApiClient.get).toHaveBeenCalledWith(
          '/admin/orders?status=pending&supplier_id=sup123&customer_id=cust456&page=1&limit=50'
        );
        expect(result).toEqual(mockResponse);
      });
    });

    describe('getOrderStatistics', () => {
      it('should get order statistics', async () => {
        const params = {
          date_from: '2024-01-01',
          date_to: '2024-01-31',
          group_by: 'day'
        };

        const mockResponse = {
          success: true,
          data: {
            total_orders: 150,
            total_revenue: 15000.00,
            average_order_value: 100.00,
            statistics_by_period: [
              { date: '2024-01-01', orders: 5, revenue: 500.00 }
            ]
          }
        };

        mockApiClient.get.mockResolvedValue(mockResponse);

        const result = await OrdersAPI.getOrderStatistics(params);

        expect(mockApiClient.get).toHaveBeenCalledWith(
          '/admin/orders/statistics?date_from=2024-01-01&date_to=2024-01-31&group_by=day'
        );
        expect(result).toEqual(mockResponse);
      });
    });

    describe('exportOrders', () => {
      it('should export orders as CSV', async () => {
        // Mock Date to return a fixed date
        const mockDate = new Date('2024-01-28T00:00:00Z');
        vi.spyOn(global, 'Date').mockImplementation(() => mockDate);
        mockDate.toISOString = () => '2024-01-28T00:00:00.000Z';

        const params = {
          format: 'csv',
          status: 'completed',
          date_from: '2024-01-01',
          date_to: '2024-01-31'
        };

        await OrdersAPI.exportOrders(params);

        expect(mockApiClient.download).toHaveBeenCalledWith(
          '/admin/orders/export?format=csv&status=completed&date_from=2024-01-01&date_to=2024-01-31',
          'orders-export-2024-01-28.csv'
        );
        
        vi.restoreAllMocks();
      });

      it('should export orders as Excel', async () => {
        // Mock Date to return a fixed date
        const mockDate = new Date('2024-01-28T00:00:00Z');
        vi.spyOn(global, 'Date').mockImplementation(() => mockDate);
        mockDate.toISOString = () => '2024-01-28T00:00:00.000Z';

        const params = {
          format: 'excel'
        };

        await OrdersAPI.exportOrders(params);

        expect(mockApiClient.download).toHaveBeenCalledWith(
          '/admin/orders/export?format=excel',
          'orders-export-2024-01-28.xlsx'
        );
        
        vi.restoreAllMocks();
      });
    });
  });

  describe('calculateTax (deprecated)', () => {
    it('should show deprecation warning and call tax API', async () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const taxData = {
        amount: 100,
        country: 'US',
        state: 'NY'
      };

      const mockResponse = {
        success: true,
        data: {
          tax_amount: 8.25,
          tax_rate: 0.0825
        }
      };

      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await OrdersAPI.calculateTax(taxData);

      expect(consoleSpy).toHaveBeenCalledWith('OrdersAPI.calculateTax() is deprecated. Use TaxAPI.calculateTax() instead.');
      expect(mockApiClient.post).toHaveBeenCalledWith('/v1/tax/calculate', taxData);
      expect(result).toEqual(mockResponse);

      consoleSpy.mockRestore();
    });
  });
});