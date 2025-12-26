/**
 * Enhanced WebSocket Service for Real-time Communication
 * 
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Message queuing during disconnections
 * - Event-based subscription system
 * - Connection health monitoring
 * - Structured message handling
 * - Authentication support
 */

export enum WebSocketStatus {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTING = 'disconnecting',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
  RECONNECTING = 'reconnecting'
}

export enum MessageType {
  // System messages
  PING = 'ping',
  PONG = 'pong',
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  ERROR = 'error',
  
  // Subscription messages
  SUBSCRIBE = 'subscribe',
  UNSUBSCRIBE = 'unsubscribe',
  SUBSCRIPTION_RESPONSE = 'subscription_response',
  
  // Business messages
  NOTIFICATION = 'notification',
  ORDER_UPDATE = 'order_update',
  CART_UPDATE = 'cart_update',
  PRODUCT_UPDATE = 'product_update',
  INVENTORY_UPDATE = 'inventory_update',
  PRICE_UPDATE = 'price_update',
  USER_STATUS = 'user_status',
  
  // Admin messages
  ADMIN_BROADCAST = 'admin_broadcast',
  SYSTEM_ANNOUNCEMENT = 'system_announcement'
}

export interface WebSocketMessage {
  type: MessageType;
  data: Record<string, any>;
  user_id?: string;
  connection_id?: string;
  timestamp?: string;
  message_id?: string;
}

export interface WebSocketConfig {
  url: string;
  token?: string;
  userId?: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  messageQueueSize?: number;
}

export interface ConnectionStats {
  status: WebSocketStatus;
  connectedAt?: Date;
  lastPing?: Date;
  lastPong?: Date;
  reconnectAttempts: number;
  messagesSent: number;
  messagesReceived: number;
  queuedMessages: number;
}

class EnhancedWebSocketService {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private status: WebSocketStatus = WebSocketStatus.DISCONNECTED;
  private eventListeners = new Map<string, Set<Function>>();
  private messageQueue: WebSocketMessage[] = [];
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private stats: ConnectionStats;
  
  // Status change callbacks
  private statusCallbacks = new Set<(status: WebSocketStatus) => void>();
  
  constructor(config: WebSocketConfig) {
    this.config = {
      autoReconnect: true,
      maxReconnectAttempts: 10,
      reconnectInterval: 1000,
      heartbeatInterval: 30000,
      messageQueueSize: 100,
      ...config
    };
    
    this.stats = {
      status: WebSocketStatus.DISCONNECTED,
      reconnectAttempts: 0,
      messagesSent: 0,
      messagesReceived: 0,
      queuedMessages: 0
    };
  }

  /**
   * Register status change callback
   */
  onStatusChange(callback: (status: WebSocketStatus) => void): () => void {
    this.statusCallbacks.add(callback);
    return () => this.statusCallbacks.delete(callback);
  }

  /**
   * Register event listener
   */
  on(eventType: string, handler: Function): () => void {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, new Set());
    }
    this.eventListeners.get(eventType)?.add(handler);

    return () => {
      this.eventListeners.get(eventType)?.delete(handler);
      if (this.eventListeners.get(eventType)?.size === 0) {
        this.eventListeners.delete(eventType);
      }
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
        console.warn('WebSocket already connected or connecting.');
        resolve();
        return;
      }

      this.setStatus(WebSocketStatus.CONNECTING);
      
      // Build WebSocket URL
      let wsUrl = this.config.url;
      const params = new URLSearchParams();
      
      if (this.config.token) {
        params.append('token', this.config.token);
      }
      
      if (params.toString()) {
        wsUrl += `?${params.toString()}`;
      }
      
      // Add user ID to path if specified
      if (this.config.userId) {
        wsUrl = wsUrl.replace('/ws', `/ws/notifications/${this.config.userId}`);
      }

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.setStatus(WebSocketStatus.CONNECTED);
        this.stats.connectedAt = new Date();
        this.reconnectAttempts = 0;
        
        // Process queued messages
        this.processMessageQueue();
        
        // Start heartbeat
        this.startHeartbeat();
        
        // Auto-subscribe to common events if authenticated
        if (this.config.userId && this.config.token) {
          this.subscribe(['notifications', 'user_status', 'order_updates', 'cart_updates']);
        }
        
        resolve();
      };

      this.ws.onclose = (event) => {
        this.setStatus(WebSocketStatus.DISCONNECTED);
        this.stopHeartbeat();
        
        console.log('WebSocket closed:', event.code, event.reason);
        
        // Attempt reconnection if enabled
        if (this.config.autoReconnect && this.reconnectAttempts < this.config.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        this.setStatus(WebSocketStatus.ERROR);
        reject(new Error('WebSocket connection failed'));
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(event.data);
      };
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.config.autoReconnect = false; // Disable auto-reconnect
    this.clearReconnectTimer();
    this.stopHeartbeat();
    
    if (this.ws) {
      this.setStatus(WebSocketStatus.DISCONNECTING);
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    
    this.setStatus(WebSocketStatus.DISCONNECTED);
    this.eventListeners.clear();
    this.messageQueue = [];
  }

  /**
   * Send message to server
   */
  sendMessage(message: Partial<WebSocketMessage>): boolean {
    const fullMessage: WebSocketMessage = {
      type: MessageType.NOTIFICATION,
      data: {},
      timestamp: new Date().toISOString(),
      message_id: this.generateMessageId(),
      ...message
    };

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(fullMessage));
        this.stats.messagesSent++;
        return true;
      } catch (error) {
        console.error('Failed to send message:', error);
        this.queueMessage(fullMessage);
        return false;
      }
    } else {
      this.queueMessage(fullMessage);
      return false;
    }
  }

  /**
   * Subscribe to event types
   */
  subscribe(events: string[]): void {
    this.sendMessage({
      type: MessageType.SUBSCRIBE,
      data: { events }
    });
  }

  /**
   * Unsubscribe from event types
   */
  unsubscribe(events: string[]): void {
    this.sendMessage({
      type: MessageType.UNSUBSCRIBE,
      data: { events }
    });
  }

  /**
   * Get connection statistics
   */
  getStats(): ConnectionStats {
    return {
      ...this.stats,
      status: this.status,
      queuedMessages: this.messageQueue.length
    };
  }

  /**
   * Get current connection status
   */
  getStatus(): WebSocketStatus {
    return this.status;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.status === WebSocketStatus.CONNECTED;
  }

  // Private methods

  private setStatus(status: WebSocketStatus): void {
    if (this.status !== status) {
      this.status = status;
      this.stats.status = status;
      this.statusCallbacks.forEach(callback => callback(status));
    }
  }

  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data);
      this.stats.messagesReceived++;
      
      // Handle system messages
      if (message.type === MessageType.PING) {
        this.handlePing(message);
        return;
      }
      
      if (message.type === MessageType.PONG) {
        this.handlePong(message);
        return;
      }
      
      // Emit to event listeners
      this.emitEvent(message.type, message);
      this.emitEvent('message', message); // Generic message event
      
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error, data);
    }
  }

  private handlePing(message: WebSocketMessage): void {
    this.stats.lastPing = new Date();
    
    // Send pong response
    this.sendMessage({
      type: MessageType.PONG,
      data: {
        client_timestamp: message.data.timestamp,
        server_timestamp: new Date().toISOString()
      }
    });
  }

  private handlePong(message: WebSocketMessage): void {
    this.stats.lastPong = new Date();
  }

  private emitEvent(eventType: string, message: WebSocketMessage): void {
    const listeners = this.eventListeners.get(eventType);
    if (listeners) {
      listeners.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error(`Error in event handler for ${eventType}:`, error);
        }
      });
    }
  }

  private queueMessage(message: WebSocketMessage): void {
    if (this.messageQueue.length >= this.config.messageQueueSize) {
      this.messageQueue.shift(); // Remove oldest message
    }
    this.messageQueue.push(message);
  }

  private processMessageQueue(): void {
    const queuedMessages = [...this.messageQueue];
    this.messageQueue = [];
    
    queuedMessages.forEach(message => {
      this.sendMessage(message);
    });
  }

  private scheduleReconnect(): void {
    this.clearReconnectTimer();
    this.setStatus(WebSocketStatus.RECONNECTING);
    
    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts),
      30000 // Max 30 seconds
    );
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.config.maxReconnectAttempts})`);
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.stats.reconnectAttempts = this.reconnectAttempts;
      this.connect().catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.sendMessage({
          type: MessageType.PING,
          data: { timestamp: new Date().toISOString() }
        });
      }
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Business-specific methods

  /**
   * Subscribe to order updates for a specific order
   */
  subscribeToOrder(orderId: string, handler: Function): () => void {
    this.subscribe(['order_updates']);
    return this.on(MessageType.ORDER_UPDATE, (message: WebSocketMessage) => {
      if (message.data.order_id === orderId || message.data.orderId === orderId) {
        handler(message.data);
      }
    });
  }

  /**
   * Subscribe to product inventory updates
   */
  subscribeToProduct(productId: string, handler: Function): () => void {
    this.subscribe(['product_updates', 'inventory_updates']);
    return this.on(MessageType.PRODUCT_UPDATE, (message: WebSocketMessage) => {
      if (message.data.product_id === productId || message.data.productId === productId) {
        handler(message.data);
      }
    });
  }

  /**
   * Subscribe to user-specific notifications
   */
  subscribeToNotifications(handler: Function): () => void {
    this.subscribe(['notifications']);
    return this.on(MessageType.NOTIFICATION, handler);
  }

  /**
   * Subscribe to cart updates
   */
  subscribeToCart(handler: Function): () => void {
    this.subscribe(['cart_updates']);
    return this.on(MessageType.CART_UPDATE, handler);
  }
}

// Service instances
export const createWebSocketService = (config: WebSocketConfig) => new EnhancedWebSocketService(config);

// Legacy exports for backward compatibility
export const orderTrackingService = createWebSocketService({
  url: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/v1/ws'
});

export const inventoryService = createWebSocketService({
  url: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/v1/ws'
});

export const notificationService = createWebSocketService({
  url: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/v1/ws'
});