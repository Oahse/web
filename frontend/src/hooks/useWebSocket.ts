import { useContext, useState, useEffect } from 'react';
import { WebSocketContext } from '../contexts/WebSocketContext';
import { WebSocketStatus, type WebSocketMessage } from '../lib/websocket';

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

// Enhanced hooks for specific WebSocket functionality

export const useOrderTracking = (orderId?: string) => {
  const { subscribeToOrder, isConnected } = useWebSocket();
  const [orderUpdate, setOrderUpdate] = useState<any>(null);
  const [isSubscribed, setIsSubscribed] = useState(false);

  useEffect(() => {
    if (!orderId || !isConnected) {
      setIsSubscribed(false);
      return;
    }

    const unsubscribe = subscribeToOrder(orderId, (update: any) => {
      setOrderUpdate(update);
    });

    setIsSubscribed(true);

    return () => {
      unsubscribe();
      setIsSubscribed(false);
    };
  }, [orderId, isConnected, subscribeToOrder]);

  return {
    orderUpdate,
    isConnected,
    isSubscribed,
  };
};

export const useProductTracking = (productId?: string) => {
  const { subscribeToProduct, isConnected } = useWebSocket();
  const [productUpdate, setProductUpdate] = useState<any>(null);
  const [isSubscribed, setIsSubscribed] = useState(false);

  useEffect(() => {
    if (!productId || !isConnected) {
      setIsSubscribed(false);
      return;
    }

    const unsubscribe = subscribeToProduct(productId, (update: any) => {
      setProductUpdate(update);
    });

    setIsSubscribed(true);

    return () => {
      unsubscribe();
      setIsSubscribed(false);
    };
  }, [productId, isConnected, subscribeToProduct]);

  return {
    productUpdate,
    isConnected,
    isSubscribed,
  };
};

export const useNotificationTracking = () => {
  const { subscribeToNotifications, isConnected } = useWebSocket();
  const [notifications, setNotifications] = useState<any[]>([]);
  const [isSubscribed, setIsSubscribed] = useState(false);

  useEffect(() => {
    if (!isConnected) {
      setIsSubscribed(false);
      return;
    }

    const unsubscribe = subscribeToNotifications((notification: any) => {
      setNotifications(prev => [notification, ...prev.slice(0, 49)]); // Keep last 50
    });

    setIsSubscribed(true);

    return () => {
      unsubscribe();
      setIsSubscribed(false);
    };
  }, [isConnected, subscribeToNotifications]);

  const clearNotifications = () => {
    setNotifications([]);
  };

  return {
    notifications,
    isConnected,
    isSubscribed,
    clearNotifications,
  };
};

export const useCartTracking = () => {
  const { subscribeToCart, isConnected } = useWebSocket();
  const [cartUpdates, setCartUpdates] = useState<any[]>([]);
  const [isSubscribed, setIsSubscribed] = useState(false);

  useEffect(() => {
    if (!isConnected) {
      setIsSubscribed(false);
      return;
    }

    const unsubscribe = subscribeToCart((update: any) => {
      setCartUpdates(prev => [update, ...prev.slice(0, 9)]); // Keep last 10
    });

    setIsSubscribed(true);

    return () => {
      unsubscribe();
      setIsSubscribed(false);
    };
  }, [isConnected, subscribeToCart]);

  const clearCartUpdates = () => {
    setCartUpdates([]);
  };

  return {
    cartUpdates,
    isConnected,
    isSubscribed,
    clearCartUpdates,
  };
};

// Hook for connection statistics and monitoring
export const useWebSocketStats = () => {
  const { stats, status, isConnected } = useWebSocket();
  const [connectionHistory, setConnectionHistory] = useState<Array<{
    status: WebSocketStatus;
    timestamp: Date;
  }>>([]);

  useEffect(() => {
    setConnectionHistory(prev => [
      { status, timestamp: new Date() },
      ...prev.slice(0, 99) // Keep last 100 status changes
    ]);
  }, [status]);

  return {
    stats,
    status,
    isConnected,
    connectionHistory,
  };
};

// Hook for sending custom messages
export const useWebSocketMessaging = () => {
  const { sendMessage, isConnected } = useWebSocket();
  const [messageHistory, setMessageHistory] = useState<Array<{
    message: Partial<WebSocketMessage>;
    sent: boolean;
    timestamp: Date;
  }>>([]);

  const sendCustomMessage = (message: Partial<WebSocketMessage>) => {
    const sent = sendMessage(message);
    
    setMessageHistory(prev => [
      { message, sent, timestamp: new Date() },
      ...prev.slice(0, 49) // Keep last 50 messages
    ]);

    return sent;
  };

  const clearMessageHistory = () => {
    setMessageHistory([]);
  };

  return {
    sendMessage: sendCustomMessage,
    messageHistory,
    isConnected,
    clearMessageHistory,
  };
};