/**
 * Tests for Stock Monitoring Service - Comprehensive test suite
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { StockMonitoringService, stockMonitor, StockThreshold, StockAlert } from '../../utils/stock';
import { toast } from 'react-hot-toast';

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    __call: vi.fn()
  }
}));

describe('StockMonitoringService', () => {
  let service: StockMonitoringService;

  beforeEach(() => {
    // Create a fresh instance for each test
    service = new (StockMonitoringService as any)();
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Singleton Pattern', () => {
    it('should return the same instance', () => {
      const instance1 = StockMonitoringService.getInstance();
      const instance2 = StockMonitoringService.getInstance();
      expect(instance1).toBe(instance2);
    });

    it('should export a singleton instance', () => {
      expect(stockMonitor).toBeInstanceOf(StockMonitoringService);
    });
  });

  describe('setStockThreshold', () => {
    it('should set stock thresholds for a variant', () => {
      const variantId = 'var123';
      const thresholds = {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5,
        email_notifications_enabled: true
      };

      service.setStockThreshold(variantId, thresholds);
      const threshold = service.getThreshold(variantId);

      expect(threshold).toBeDefined();
      expect(threshold?.variant_id).toBe(variantId);
      expect(threshold?.low_stock_threshold).toBe(10);
      expect(threshold?.critical_threshold).toBe(5);
      expect(threshold?.email_notifications_enabled).toBe(true);
    });

    it('should update existing thresholds', () => {
      const variantId = 'var123';
      
      // Set initial thresholds
      service.setStockThreshold(variantId, {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5
      });

      // Update thresholds
      service.setStockThreshold(variantId, {
        low_stock_threshold: 20,
        out_of_stock_threshold: 1,
        critical_threshold: 8
      });

      const threshold = service.getThreshold(variantId);
      expect(threshold?.low_stock_threshold).toBe(20);
      expect(threshold?.critical_threshold).toBe(8);
    });

    it('should default email notifications to true', () => {
      service.setStockThreshold('var123', {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5
      });

      const threshold = service.getThreshold('var123');
      expect(threshold?.email_notifications_enabled).toBe(true);
    });

    it('should preserve existing product and variant names', () => {
      const variantId = 'var123';
      
      // First set with product info
      service.updateStock(variantId, 15, 'Test Product', 'Red - Large');
      
      // Then update thresholds
      service.setStockThreshold(variantId, {
        low_stock_threshold: 20,
        out_of_stock_threshold: 0,
        critical_threshold: 5
      });

      const threshold = service.getThreshold(variantId);
      expect(threshold?.product_name).toBe('Test Product');
      expect(threshold?.variant_name).toBe('Red - Large');
    });
  });

  describe('updateStock', () => {
    beforeEach(() => {
      service.setStockThreshold('var123', {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5,
        email_notifications_enabled: false // Disable emails for testing
      });
    });

    it('should update stock and return alerts for status changes', () => {
      const alerts = service.updateStock('var123', 3, 'Test Product', 'Red - Large');
      
      expect(alerts).toHaveLength(1);
      expect(alerts[0].alert_type).toBe('critical');
      expect(alerts[0].message).toContain('critically low stock');
      
      const threshold = service.getThreshold('var123');
      expect(threshold?.current_stock).toBe(3);
      expect(threshold?.status).toBe('critical');
    });

    it('should create default thresholds if none exist', () => {
      const alerts = service.updateStock('var456', 8, 'New Product', 'Blue - Medium');
      
      const threshold = service.getThreshold('var456');
      expect(threshold).toBeDefined();
      expect(threshold?.low_stock_threshold).toBe(10);
      expect(threshold?.critical_threshold).toBe(5);
      expect(threshold?.current_stock).toBe(8);
    });

    it('should not create alerts if status does not change', () => {
      // Set initial stock in normal range
      service.updateStock('var123', 15);
      
      // Update to another normal stock level
      const alerts = service.updateStock('var123', 12);
      
      expect(alerts).toHaveLength(0);
    });

    it('should create restocked alert when moving from out of stock to in stock', () => {
      // First set to out of stock
      service.updateStock('var123', 0);
      
      // Then restock
      const alerts = service.updateStock('var123', 20);
      
      expect(alerts).toHaveLength(1);
      expect(alerts[0].alert_type).toBe('restocked');
      expect(alerts[0].message).toContain('has been restocked');
    });

    it('should update product and variant names', () => {
      service.updateStock('var123', 5, 'Updated Product', 'Green - Small');
      
      const threshold = service.getThreshold('var123');
      expect(threshold?.product_name).toBe('Updated Product');
      expect(threshold?.variant_name).toBe('Green - Small');
    });
  });

  describe('Stock Status Calculation', () => {
    beforeEach(() => {
      service.setStockThreshold('var123', {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5
      });
    });

    it('should calculate in_stock status correctly', () => {
      service.updateStock('var123', 15);
      const status = service.getStockStatus('var123');
      
      expect(status.status).toBe('in_stock');
      expect(status.message).toBe('15 in stock');
      expect(status.color).toBe('green');
    });

    it('should calculate low_stock status correctly', () => {
      service.updateStock('var123', 8);
      const status = service.getStockStatus('var123');
      
      expect(status.status).toBe('low_stock');
      expect(status.message).toBe('Low stock: 8 remaining');
      expect(status.color).toBe('yellow');
    });

    it('should calculate critical status correctly', () => {
      service.updateStock('var123', 3);
      const status = service.getStockStatus('var123');
      
      expect(status.status).toBe('critical');
      expect(status.message).toBe('Critical: Only 3 left!');
      expect(status.color).toBe('orange');
    });

    it('should calculate out_of_stock status correctly', () => {
      service.updateStock('var123', 0);
      const status = service.getStockStatus('var123');
      
      expect(status.status).toBe('out_of_stock');
      expect(status.message).toBe('Out of stock');
      expect(status.color).toBe('red');
    });

    it('should handle unknown variant gracefully', () => {
      const status = service.getStockStatus('unknown_variant');
      
      expect(status.status).toBe('in_stock');
      expect(status.message).toBe('Stock status unknown');
      expect(status.color).toBe('gray');
    });
  });

  describe('Alert Management', () => {
    beforeEach(() => {
      service.setStockThreshold('var123', {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5,
        email_notifications_enabled: false
      });
    });

    it('should store alerts in the alerts array', () => {
      service.updateStock('var123', 3, 'Test Product', 'Red - Large');
      
      const allAlerts = service.getAllAlerts();
      expect(allAlerts).toHaveLength(1);
      expect(allAlerts[0].variant_id).toBe('var123');
      expect(allAlerts[0].acknowledged).toBe(false);
    });

    it('should get unacknowledged alerts', () => {
      service.updateStock('var123', 3);
      service.updateStock('var456', 0);
      
      const unacknowledged = service.getUnacknowledgedAlerts();
      expect(unacknowledged).toHaveLength(2);
    });

    it('should acknowledge alerts', () => {
      service.updateStock('var123', 3);
      const alerts = service.getAllAlerts();
      const alertId = alerts[0].id;
      
      service.acknowledgeAlert(alertId);
      
      const unacknowledged = service.getUnacknowledgedAlerts();
      expect(unacknowledged).toHaveLength(0);
      
      const acknowledgedAlert = service.getAllAlerts().find(a => a.id === alertId);
      expect(acknowledgedAlert?.acknowledged).toBe(true);
    });

    it('should handle acknowledging non-existent alerts', () => {
      expect(() => service.acknowledgeAlert('non-existent')).not.toThrow();
    });
  });

  describe('Bulk Stock Updates', () => {
    it('should handle bulk stock updates', () => {
      const updates = [
        { variant_id: 'var1', new_stock: 3, product_name: 'Product 1', variant_name: 'Variant 1' },
        { variant_id: 'var2', new_stock: 0, product_name: 'Product 2', variant_name: 'Variant 2' },
        { variant_id: 'var3', new_stock: 15, product_name: 'Product 3', variant_name: 'Variant 3' }
      ];

      const allAlerts = service.bulkUpdateStock(updates);
      
      expect(allAlerts.length).toBeGreaterThan(0);
      
      // Check that all variants were updated
      expect(service.getThreshold('var1')).toBeDefined();
      expect(service.getThreshold('var2')).toBeDefined();
      expect(service.getThreshold('var3')).toBeDefined();
    });

    it('should return combined alerts from all updates', () => {
      const updates = [
        { variant_id: 'var1', new_stock: 3 }, // Should trigger critical alert
        { variant_id: 'var2', new_stock: 0 }  // Should trigger out of stock alert
      ];

      const allAlerts = service.bulkUpdateStock(updates);
      
      expect(allAlerts).toHaveLength(2);
      expect(allAlerts.some(a => a.alert_type === 'critical')).toBe(true);
      expect(allAlerts.some(a => a.alert_type === 'out_of_stock')).toBe(true);
    });
  });

  describe('Email Notifications', () => {
    beforeEach(() => {
      // Mock the private sendStockAlertEmail method
      vi.spyOn(service as any, 'sendStockAlertEmail').mockResolvedValue(undefined);
    });

    it('should queue email notifications when enabled', async () => {
      service.setStockThreshold('var123', {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5,
        email_notifications_enabled: true
      });

      service.updateStock('var123', 3, 'Test Product', 'Red - Large');
      
      // Wait for email processing
      await vi.runAllTimersAsync();
      
      expect((service as any).sendStockAlertEmail).toHaveBeenCalled();
    });

    it('should not queue emails when notifications are disabled', async () => {
      service.setStockThreshold('var123', {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5,
        email_notifications_enabled: false
      });

      service.updateStock('var123', 3, 'Test Product', 'Red - Large');
      
      await vi.runAllTimersAsync();
      
      expect((service as any).sendStockAlertEmail).not.toHaveBeenCalled();
    });

    it('should mark alerts as email sent after successful email', async () => {
      service.setStockThreshold('var123', {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5,
        email_notifications_enabled: true
      });

      service.updateStock('var123', 3, 'Test Product', 'Red - Large');
      
      await vi.runAllTimersAsync();
      
      const alerts = service.getAllAlerts();
      expect(alerts[0].email_sent).toBe(true);
    });

    it('should update last notification sent timestamp', async () => {
      service.setStockThreshold('var123', {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5,
        email_notifications_enabled: true
      });

      service.updateStock('var123', 3, 'Test Product', 'Red - Large');
      
      await vi.runAllTimersAsync();
      
      const threshold = service.getThreshold('var123');
      expect(threshold?.last_notification_sent).toBeDefined();
    });

    it('should handle email sending errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.spyOn(service as any, 'sendStockAlertEmail').mockRejectedValue(new Error('Email failed'));

      service.setStockThreshold('var123', {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5,
        email_notifications_enabled: true
      });

      service.updateStock('var123', 3, 'Test Product', 'Red - Large');
      
      await vi.runAllTimersAsync();
      
      expect(consoleSpy).toHaveBeenCalledWith('Failed to send stock alert email:', expect.any(Error));
      
      consoleSpy.mockRestore();
    });
  });

  describe('Data Retrieval', () => {
    beforeEach(() => {
      service.setStockThreshold('var1', {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5
      });
      service.setStockThreshold('var2', {
        low_stock_threshold: 15,
        out_of_stock_threshold: 1,
        critical_threshold: 8
      });
    });

    it('should get all thresholds', () => {
      const thresholds = service.getAllThresholds();
      
      expect(thresholds).toHaveLength(2);
      expect(thresholds.some(t => t.variant_id === 'var1')).toBe(true);
      expect(thresholds.some(t => t.variant_id === 'var2')).toBe(true);
    });

    it('should get specific threshold by variant ID', () => {
      const threshold = service.getThreshold('var1');
      
      expect(threshold).toBeDefined();
      expect(threshold?.variant_id).toBe('var1');
      expect(threshold?.low_stock_threshold).toBe(10);
    });

    it('should return undefined for non-existent threshold', () => {
      const threshold = service.getThreshold('non-existent');
      expect(threshold).toBeUndefined();
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle negative stock values', () => {
      service.updateStock('var123', -5);
      
      const threshold = service.getThreshold('var123');
      expect(threshold?.current_stock).toBe(-5);
      expect(threshold?.status).toBe('out_of_stock');
    });

    it('should handle very large stock values', () => {
      service.updateStock('var123', 999999);
      
      const threshold = service.getThreshold('var123');
      expect(threshold?.current_stock).toBe(999999);
      expect(threshold?.status).toBe('in_stock');
    });

    it('should handle decimal stock values', () => {
      service.updateStock('var123', 5.5);
      
      const threshold = service.getThreshold('var123');
      expect(threshold?.current_stock).toBe(5.5);
    });

    it('should handle empty product and variant names', () => {
      service.updateStock('var123', 10, '', '');
      
      const threshold = service.getThreshold('var123');
      expect(threshold?.product_name).toBe('');
      expect(threshold?.variant_name).toBe('');
    });

    it('should handle special characters in product names', () => {
      service.updateStock('var123', 10, 'Product & Co. "Special" <Item>', 'Variant #1 (50% off)');
      
      const threshold = service.getThreshold('var123');
      expect(threshold?.product_name).toBe('Product & Co. "Special" <Item>');
      expect(threshold?.variant_name).toBe('Variant #1 (50% off)');
    });

    it('should handle concurrent stock updates', () => {
      const promises = Array.from({ length: 10 }, (_, i) => 
        Promise.resolve(service.updateStock('var123', i + 1))
      );

      expect(() => Promise.all(promises)).not.toThrow();
    });
  });

  describe('Alert Message Generation', () => {
    beforeEach(() => {
      service.setStockThreshold('var123', {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5,
        email_notifications_enabled: false
      });
    });

    it('should generate appropriate out of stock message', () => {
      const alerts = service.updateStock('var123', 0, 'Test Product', 'Red - Large');
      
      expect(alerts[0].message).toBe('Test Product (Red - Large) is now out of stock!');
    });

    it('should generate appropriate critical stock message', () => {
      const alerts = service.updateStock('var123', 3, 'Test Product', 'Red - Large');
      
      expect(alerts[0].message).toBe('Test Product (Red - Large) has critically low stock: 3 remaining');
    });

    it('should generate appropriate low stock message', () => {
      const alerts = service.updateStock('var123', 8, 'Test Product', 'Red - Large');
      
      expect(alerts[0].message).toBe('Test Product (Red - Large) is running low: 8 remaining');
    });

    it('should generate appropriate restocked message', () => {
      // First set to out of stock
      service.updateStock('var123', 0, 'Test Product', 'Red - Large');
      
      // Then restock
      const alerts = service.updateStock('var123', 20, 'Test Product', 'Red - Large');
      
      expect(alerts[0].message).toBe('Test Product (Red - Large) has been restocked: 20 available');
    });
  });
});