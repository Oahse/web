/**
 * WebSocket Service for Real-time Notifications
 * Handles cart updates, payment notifications, and other real-time events
 */

import { config } from '../config/environment.js';

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 1000; // Start with 1 second
    this.listeners = new Map();
    this.isConnected = false;
    this.userId = null;
    this.sessionId = null;
  }

  connect(userId = null, sessionId = null) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    this.userId = userId;
    this.sessionId = sessionId;

    try {
      const wsUrl = new URL(config.webSocketUrl);
      if (userId) {
        wsUrl.searchParams.set('user_id', userId);
      }
      if (sessionId) {
        wsUrl.searchParams.set('session_id', sessionId);
      }

      this.ws = new WebSocket(wsUrl.toString());
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);

      if (config.debugMode) {
        console.log('WebSocket connecting to:', wsUrl.toString());
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.scheduleReconnect();
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
    this.reconnectAttempts = 0;
  }

  handleOpen() {
    this.isConnected = true;
    this.reconnectAttempts = 0;
    this.reconnectInterval = 1000;
    
    if (config.debugMode) {
      console.log('WebSocket connected');
    }

    // Notify listeners about connection
    this.emit('connected', { userId: this.userId, sessionId: this.sessionId });
  }

  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      
      if (config.debugMode) {
        console.log('WebSocket message received:', data);
      }

      // Handle different message types
      switch (data.type) {
        case 'cart_update':
          this.emit('cartUpdate', data);
          break;
        case 'cart_real_time_update':
          this.emit('cartRealTimeUpdate', data);
          break;
        case 'payment_update':
          this.emit('paymentUpdate', data);
          break;
        case 'real_time_notification':
          this.emit('notification', data);
          break;
        case 'order_update':
          this.emit('orderUpdate', data);
          break;
        default:
          this.emit('message', data);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  handleClose(event) {
    this.isConnected = false;
    
    if (config.debugMode) {
      console.log('WebSocket disconnected:', event.code, event.reason);
    }

    this.emit('disconnected', { code: event.code, reason: event.reason });

    // Attempt to reconnect if not a normal closure
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  }

  handleError(error) {
    console.error('WebSocket error:', error);
    this.emit('error', error);
  }

  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.emit('maxReconnectAttemptsReached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    if (config.debugMode) {
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    }

    setTimeout(() => {
      this.connect(this.userId, this.sessionId);
    }, delay);
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  // Event listener management
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in WebSocket event listener:', error);
        }
      });
    }
  }

  // Convenience methods for specific events
  onCartUpdate(callback) {
    this.on('cartUpdate', callback);
  }

  onCartRealTimeUpdate(callback) {
    this.on('cartRealTimeUpdate', callback);
  }

  onPaymentUpdate(callback) {
    this.on('paymentUpdate', callback);
  }

  onNotification(callback) {
    this.on('notification', callback);
  }

  onOrderUpdate(callback) {
    this.on('orderUpdate', callback);
  }

  onConnected(callback) {
    this.on('connected', callback);
  }

  onDisconnected(callback) {
    this.on('disconnected', callback);
  }

  onError(callback) {
    this.on('error', callback);
  }

  // Status methods
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      readyState: this.ws ? this.ws.readyState : WebSocket.CLOSED,
      reconnectAttempts: this.reconnectAttempts,
      userId: this.userId,
      sessionId: this.sessionId
    };
  }
}

// Create singleton instance
const webSocketService = new WebSocketService();

export default webSocketService;