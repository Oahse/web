import { toast } from 'react-hot-toast';

export interface StockThreshold {
  id: string;
  variant_id: string;
  product_name: string;
  variant_name: string;
  current_stock: number;
  low_stock_threshold: number;
  out_of_stock_threshold: number;
  critical_threshold: number;
  email_notifications_enabled: boolean;
  last_notification_sent?: string;
  status: 'in_stock' | 'low_stock' | 'critical' | 'out_of_stock';
}

export interface StockAlert {
  id: string;
  variant_id: string;
  alert_type: 'low_stock' | 'critical' | 'out_of_stock' | 'restocked';
  message: string;
  created_at: string;
  acknowledged: boolean;
  email_sent: boolean;
}

export class StockMonitoringService {
  private static instance: StockMonitoringService;
  private stockThresholds: Map<string, StockThreshold> = new Map();
  private alerts: StockAlert[] = [];
  private emailQueue: Array<{ type: string; data: any }> = [];

  static getInstance(): StockMonitoringService {
    if (!StockMonitoringService.instance) {
      StockMonitoringService.instance = new StockMonitoringService();
    }
    return StockMonitoringService.instance;
  }

  // Set stock thresholds for a variant
  setStockThreshold(variantId: string, thresholds: {
    low_stock_threshold: number;
    out_of_stock_threshold: number;
    critical_threshold: number;
    email_notifications_enabled?: boolean;
  }): void {
    const existing = this.stockThresholds.get(variantId);
    const threshold: StockThreshold = {
      id: existing?.id || `threshold_${Date.now()}_${variantId}`,
      variant_id: variantId,
      product_name: existing?.product_name || 'Unknown Product',
      variant_name: existing?.variant_name || 'Unknown Variant',
      current_stock: existing?.current_stock || 0,
      low_stock_threshold: thresholds.low_stock_threshold,
      out_of_stock_threshold: thresholds.out_of_stock_threshold,
      critical_threshold: thresholds.critical_threshold,
      email_notifications_enabled: thresholds.email_notifications_enabled ?? true,
      last_notification_sent: existing?.last_notification_sent,
      status: this.calculateStockStatus(existing?.current_stock || 0, thresholds)
    };

    this.stockThresholds.set(variantId, threshold);
  }

  // Update current stock and check thresholds
  updateStock(variantId: string, newStock: number, productName?: string, variantName?: string): StockAlert[] {
    const threshold = this.stockThresholds.get(variantId);
    if (!threshold) {
      // Create default threshold if none exists
      this.setStockThreshold(variantId, {
        low_stock_threshold: 10,
        out_of_stock_threshold: 0,
        critical_threshold: 5,
        email_notifications_enabled: true
      });
    }

    const updatedThreshold = this.stockThresholds.get(variantId)!;
    const previousStock = updatedThreshold.current_stock;
    const previousStatus = updatedThreshold.status;

    // Update stock and product info
    updatedThreshold.current_stock = newStock;
    updatedThreshold.product_name = productName || updatedThreshold.product_name;
    updatedThreshold.variant_name = variantName || updatedThreshold.variant_name;
    updatedThreshold.status = this.calculateStockStatus(newStock, updatedThreshold);

    const newAlerts: StockAlert[] = [];

    // Check if status changed and create alerts, or if this is the first time setting stock
    if (previousStatus !== updatedThreshold.status || previousStock === 0) {
      const alert = this.createStockAlert(updatedThreshold, previousStock);
      if (alert) {
        newAlerts.push(alert);
        this.alerts.unshift(alert); // Add to beginning of alerts array

        // Queue email if notifications are enabled
        if (updatedThreshold.email_notifications_enabled) {
          this.queueEmailNotification(alert, updatedThreshold);
        }

        // Show toast notification
        // this.showToastNotification(alert);
      }
    }

    this.stockThresholds.set(variantId, updatedThreshold);
    return newAlerts;
  }

  // Calculate stock status based on thresholds
  private calculateStockStatus(stock: number, thresholds: {
    low_stock_threshold: number;
    out_of_stock_threshold: number;
    critical_threshold: number;
  }): 'in_stock' | 'low_stock' | 'critical' | 'out_of_stock' {
    if (stock <= thresholds.out_of_stock_threshold) {
      return 'out_of_stock';
    } else if (stock <= thresholds.critical_threshold) {
      return 'critical';
    } else if (stock <= thresholds.low_stock_threshold) {
      return 'low_stock';
    } else {
      return 'in_stock';
    }
  }

  // Create stock alert
  private createStockAlert(threshold: StockThreshold, previousStock: number): StockAlert | null {
    let alertType: StockAlert['alert_type'];
    let message: string;

    switch (threshold.status) {
      case 'out_of_stock':
        alertType = 'out_of_stock';
        message = `${threshold.product_name} (${threshold.variant_name}) is now out of stock!`;
        break;
      case 'critical':
        alertType = 'critical';
        message = `${threshold.product_name} (${threshold.variant_name}) has critically low stock: ${threshold.current_stock} remaining`;
        break;
      case 'low_stock':
        alertType = 'low_stock';
        message = `${threshold.product_name} (${threshold.variant_name}) is running low: ${threshold.current_stock} remaining`;
        break;
      case 'in_stock':
        if (previousStock <= threshold.out_of_stock_threshold) {
          alertType = 'restocked';
          message = `${threshold.product_name} (${threshold.variant_name}) has been restocked: ${threshold.current_stock} available`;
        } else {
          return null; // No alert needed for normal stock levels
        }
        break;
      default:
        return null;
    }

    return {
      id: `alert_${Date.now()}_${threshold.variant_id}`,
      variant_id: threshold.variant_id,
      alert_type: alertType,
      message,
      created_at: new Date().toISOString(),
      acknowledged: false,
      email_sent: false
    };
  }

  // Queue email notification
  private queueEmailNotification(alert: StockAlert, threshold: StockThreshold): void {
    const emailData = {
      type: 'stock_alert',
      data: {
        alert,
        threshold,
        recipient: 'admin@banwee.com', // This should come from settings
        subject: `Stock Alert: ${threshold.product_name}`,
        template: 'stock_alert_template'
      }
    };

    this.emailQueue.push(emailData);
    
    // Process email queue (in a real app, this would be handled by a background service)
    this.processEmailQueue();
  }

  // Process email queue
  private async processEmailQueue(): Promise<void> {
    while (this.emailQueue.length > 0) {
      const emailData = this.emailQueue.shift();
      if (emailData) {
        try {
          await this.sendStockAlertEmail(emailData.data);
          
          // Mark alert as email sent
          const alert = this.alerts.find(a => a.id === emailData.data.alert.id);
          if (alert) {
            alert.email_sent = true;
          }

          // Update last notification sent
          const threshold = this.stockThresholds.get(emailData.data.alert.variant_id);
          if (threshold) {
            threshold.last_notification_sent = new Date().toISOString();
          }
        } catch (error) {
          console.error('Failed to send stock alert email:', error);
          // Re-queue the email for retry (with exponential backoff in a real implementation)
        }
      }
    }
  }

  // Send stock alert email (mock implementation)
  private async sendStockAlertEmail(emailData: any): Promise<void> {
    // In a real implementation, this would call your email service API
    console.log('Sending stock alert email:', emailData);
    
    // Mock API call
    return new Promise((resolve) => {
      setTimeout(() => {
        console.log(`Stock alert email sent for ${emailData.threshold.product_name}`);
        resolve();
      }, 1000);
    });
  }

  // Show toast notification
  private showToastNotification(alert: StockAlert): void {
    switch (alert.alert_type) {
      case 'out_of_stock':
        toast.error(alert.message, { duration: 5000 });
        break;
      case 'critical':
        toast.error(alert.message, { duration: 4000 });
        break;
      case 'low_stock':
        toast(alert.message, { duration: 3000 });
        break;
      case 'restocked':
        toast.success(alert.message, { duration: 3000 });
        break;
    }
  }

  // Get all stock thresholds
  getAllThresholds(): StockThreshold[] {
    return Array.from(this.stockThresholds.values());
  }

  // Get threshold for specific variant
  getThreshold(variantId: string): StockThreshold | undefined {
    return this.stockThresholds.get(variantId);
  }

  // Get all alerts
  getAllAlerts(): StockAlert[] {
    return this.alerts;
  }

  // Get unacknowledged alerts
  getUnacknowledgedAlerts(): StockAlert[] {
    return this.alerts.filter(alert => !alert.acknowledged);
  }

  // Acknowledge alert
  acknowledgeAlert(alertId: string): void {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.acknowledged = true;
    }
  }

  // Get stock status for variant
  getStockStatus(variantId: string): {
    status: 'in_stock' | 'low_stock' | 'critical' | 'out_of_stock';
    message: string;
    color: string;
  } {
    const threshold = this.stockThresholds.get(variantId);
    if (!threshold) {
      return {
        status: 'in_stock',
        message: 'Stock status unknown',
        color: 'gray'
      };
    }

    const statusConfig = {
      in_stock: {
        message: `${threshold.current_stock} in stock`,
        color: 'green'
      },
      low_stock: {
        message: `Low stock: ${threshold.current_stock} remaining`,
        color: 'yellow'
      },
      critical: {
        message: `Critical: Only ${threshold.current_stock} left!`,
        color: 'orange'
      },
      out_of_stock: {
        message: 'Out of stock',
        color: 'red'
      }
    };

    return {
      status: threshold.status,
      ...statusConfig[threshold.status]
    };
  }

  // Bulk update stock levels (for inventory management)
  bulkUpdateStock(updates: Array<{
    variant_id: string;
    new_stock: number;
    product_name?: string;
    variant_name?: string;
  }>): StockAlert[] {
    const allAlerts: StockAlert[] = [];
    
    updates.forEach(update => {
      const alerts = this.updateStock(
        update.variant_id,
        update.new_stock,
        update.product_name,
        update.variant_name
      );
      allAlerts.push(...alerts);
    });

    return allAlerts;
  }
}

// Export singleton instance
export const stockMonitor = StockMonitoringService.getInstance();