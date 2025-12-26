import React, { createContext, useEffect, useState, useCallback } from 'react';
import {
  createWebSocketService,
  WebSocketStatus,
  MessageType,
  type WebSocketMessage,
  type ConnectionStats
} from '../lib/websocket';
import { useNotifications } from '../hooks/useNotifications';
import { useAuth } from './AuthContext';
import { Notification } from '../types';

interface WebSocketContextType {
  // Connection status
  status: WebSocketStatus;
  stats: ConnectionStats;
  isConnected: boolean;
  
  // Connection management
  connect: () => Promise<void>;
  disconnect: () => void;
  
  // Subscription methods
  subscribe: (events: string[]) => void;
  unsubscribe: (events: string[]) => void;
  
  // Business-specific subscriptions
  subscribeToOrder: (orderId: string, handler: Function) => () => void;
  subscribeToProduct: (productId: string, handler: Function) => () => void;
  subscribeToNotifications: (handler: Function) => () => void;
  subscribeToCart: (handler: Function) => () => void;
  
  // Message sending
  sendMessage: (message: Partial<WebSocketMessage>) => boolean;
}

export const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: React.ReactNode;
  autoConnect?: boolean;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({
  children,
  autoConnect = true,
}) => {
  const [status, setStatus] = useState<WebSocketStatus>(WebSocketStatus.DISCONNECTED);
  const [stats, setStats] = useState<ConnectionStats>({
    status: WebSocketStatus.DISCONNECTED,
    reconnectAttempts: 0,
    messagesSent: 0,
    messagesReceived: 0,
    queuedMessages: 0
  });
  
  const { info, warning, error, removeNotification: removeToast } = useNotifications();
  const { user, isAuthenticated, token } = useAuth();
  
  // Create WebSocket service instance
  const [wsService] = useState(() => {
    const baseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/v1/ws';
    
    return createWebSocketService({
      url: baseUrl,
      token: token || undefined,
      userId: user?.id,
      autoReconnect: true,
      maxReconnectAttempts: 10,
      reconnectInterval: 1000,
      heartbeatInterval: 30000,
      messageQueueSize: 100
    });
  });

  // Update service configuration when auth changes
  useEffect(() => {
    if (wsService) {
      // Update configuration
      wsService['config'] = {
        ...wsService['config'],
        token: token || undefined,
        userId: user?.id
      };
    }
  }, [user?.id, token, wsService]);

  // Status change handler
  useEffect(() => {
    const unsubscribe = wsService.onStatusChange((newStatus: WebSocketStatus) => {
      setStatus(newStatus);
      setStats(wsService.getStats());
      
      // Show status notifications
      switch (newStatus) {
        case WebSocketStatus.CONNECTED:
          info('Connected', 'Real-time updates are now available');
          break;
        case WebSocketStatus.DISCONNECTED:
          warning('Disconnected', 'Real-time updates are temporarily unavailable');
          break;
        case WebSocketStatus.ERROR:
          error('Connection Error', 'Failed to connect to real-time service');
          break;
        case WebSocketStatus.RECONNECTING:
          info('Reconnecting', 'Attempting to restore real-time connection');
          break;
      }
    });

    return unsubscribe;
  }, [wsService, info, warning, error]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      wsService.connect().catch(err => {
        console.error('Failed to connect WebSocket:', err);
      });
    }

    return () => {
      wsService.disconnect();
    };
  }, [wsService, autoConnect]);

  // Set up global event handlers
  useEffect(() => {
    // Order update notifications
    const unsubscribeOrderUpdates = wsService.on(MessageType.ORDER_UPDATE, (message: WebSocketMessage) => {
      const { order_id, status: orderStatus, order_number } = message.data;
      const displayId = order_number || order_id;

      switch (orderStatus) {
        case 'shipped':
          info(
            'Order Shipped',
            `Your order ${displayId} has been shipped and is on its way!`
          );
          break;
        case 'delivered':
          info(
            'Order Delivered',
            `Your order ${displayId} has been delivered successfully!`
          );
          break;
        case 'cancelled':
          warning(
            'Order Cancelled',
            `Order ${displayId} has been cancelled.`
          );
          break;
        default:
          info(
            'Order Update',
            `Your order ${displayId} status has been updated to ${orderStatus}`
          );
          break;
      }
    });

    // Product/Inventory updates
    const unsubscribeInventoryUpdates = wsService.on(MessageType.INVENTORY_UPDATE, (message: WebSocketMessage) => {
      const { product_name, current_stock, threshold, product_id } = message.data;
      
      if (current_stock === 0) {
        error(
          'Out of Stock',
          `${product_name || `Product ${product_id}`} is now out of stock`
        );
      } else if (threshold && current_stock <= threshold) {
        warning(
          'Low Stock Alert',
          `${product_name || `Product ${product_id}`} is running low (${current_stock} remaining)`
        );
      }
    });

    // Product updates
    const unsubscribeProductUpdates = wsService.on(MessageType.PRODUCT_UPDATE, (message: WebSocketMessage) => {
      const { product_name, product_id, update_type } = message.data;
      
      if (update_type === 'price_change') {
        info(
          'Price Update',
          `Price updated for ${product_name || `Product ${product_id}`}`
        );
      }
    });

    // Price updates during checkout
    const unsubscribePriceUpdates = wsService.on(MessageType.PRICE_UPDATE, (message: WebSocketMessage) => {
      const { summary, items, message: updateMessage } = message.data;
      
      if (summary.total_price_change > 0) {
        warning(
          'Prices Updated',
          updateMessage || `Prices have increased for ${summary.total_items_updated} items in your cart.`
        );
      } else if (summary.total_price_change < 0) {
        info(
          'Price Reduction!',
          updateMessage || `Great news! Prices reduced for ${summary.total_items_updated} items. You save $${Math.abs(summary.total_price_change).toFixed(2)}!`
        );
      } else {
        info(
          'Prices Updated',
          updateMessage || `Prices have been updated for ${summary.total_items_updated} items in your cart.`
        );
      }
      
      // Trigger cart refresh to show updated prices
      window.dispatchEvent(new CustomEvent('priceUpdate', { 
        detail: { 
          items, 
          summary,
          message: updateMessage 
        } 
      }));
    });

    // Notification service event listeners
    let unsubscribeNewNotification: (() => void) | undefined;
    let unsubscribeNotificationUpdate: (() => void) | undefined;
    let unsubscribeNotificationDeleted: (() => void) | undefined;

    if (isAuthenticated && user?.id) {
      unsubscribeNewNotification = wsService.on(MessageType.NOTIFICATION, (message: WebSocketMessage) => {
        const notification = message.data as Notification;
        
        // Show toast notification
        switch (notification.type) {
          case 'error':
            error(notification.title || 'Error', notification.message, notification.id);
            break;
          case 'warning':
            warning(notification.title || 'Warning', notification.message, notification.id);
            break;
          case 'success':
            info(notification.title || 'Success', notification.message, notification.id);
            break;
          default:
            info(notification.title || 'Notification', notification.message, notification.id);
            break;
        }
      });

      // Handle notification deletions
      unsubscribeNotificationDeleted = wsService.on('notification_deleted', (message: WebSocketMessage) => {
        const { notification_id } = message.data;
        removeToast(notification_id);
      });
    }

    // Cart updates
    const unsubscribeCartUpdates = wsService.on(MessageType.CART_UPDATE, (message: WebSocketMessage) => {
      const { action, item_count } = message.data;
      
      if (action === 'item_added') {
        info('Cart Updated', 'Item added to your cart');
      } else if (action === 'item_removed') {
        info('Cart Updated', 'Item removed from your cart');
      } else if (item_count !== undefined) {
        info('Cart Updated', `You have ${item_count} items in your cart`);
      }
    });

    // Admin broadcasts
    const unsubscribeAdminBroadcast = wsService.on(MessageType.ADMIN_BROADCAST, (message: WebSocketMessage) => {
      const { title, content, priority } = message.data;
      
      switch (priority) {
        case 'high':
          error(title || 'Important Notice', content);
          break;
        case 'medium':
          warning(title || 'Notice', content);
          break;
        default:
          info(title || 'Announcement', content);
          break;
      }
    });

    return () => {
      unsubscribeOrderUpdates();
      unsubscribeInventoryUpdates();
      unsubscribeProductUpdates();
      unsubscribePriceUpdates();
      unsubscribeCartUpdates();
      unsubscribeAdminBroadcast();
      
      if (unsubscribeNewNotification) unsubscribeNewNotification();
      if (unsubscribeNotificationUpdate) unsubscribeNotificationUpdate();
      if (unsubscribeNotificationDeleted) unsubscribeNotificationDeleted();
    };
  }, [wsService, info, warning, error, removeToast, user?.id, isAuthenticated]);

  // Context value
  const contextValue: WebSocketContextType = {
    // Connection status
    status,
    stats,
    isConnected: status === WebSocketStatus.CONNECTED,
    
    // Connection management
    connect: useCallback(() => wsService.connect(), [wsService]),
    disconnect: useCallback(() => wsService.disconnect(), [wsService]),
    
    // Subscription methods
    subscribe: useCallback((events: string[]) => wsService.subscribe(events), [wsService]),
    unsubscribe: useCallback((events: string[]) => wsService.unsubscribe(events), [wsService]),
    
    // Business-specific subscriptions
    subscribeToOrder: useCallback((orderId: string, handler: Function) => 
      wsService.subscribeToOrder(orderId, handler), [wsService]),
    subscribeToProduct: useCallback((productId: string, handler: Function) => 
      wsService.subscribeToProduct(productId, handler), [wsService]),
    subscribeToNotifications: useCallback((handler: Function) => 
      wsService.subscribeToNotifications(handler), [wsService]),
    subscribeToCart: useCallback((handler: Function) => 
      wsService.subscribeToCart(handler), [wsService]),
    
    // Message sending
    sendMessage: useCallback((message: Partial<WebSocketMessage>) => 
      wsService.sendMessage(message), [wsService])
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
};
