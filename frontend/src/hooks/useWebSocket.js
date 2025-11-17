import { useContext, useState, useEffect } from 'react';
import { WebSocketContext } from '../contexts/WebSocketContext';

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

// Custom hooks for specific WebSocket functionality
export const useOrderTracking = (orderId) => {
  const { subscribeToOrder, isOrderServiceConnected } = useWebSocket();
  const [orderUpdate, setOrderUpdate] = useState(null);

  useEffect(() => {
    if (!orderId || !isOrderServiceConnected) return;

    const unsubscribe = subscribeToOrder(orderId, (update) => {
      setOrderUpdate(update);
    });

    return unsubscribe;
  }, [orderId, isOrderServiceConnected, subscribeToOrder]);

  return {
    orderUpdate,
    isConnected: isOrderServiceConnected,
  };
};

export const useInventoryTracking = (productId) => {
  const { subscribeToProduct, isInventoryServiceConnected } = useWebSocket();
  const [inventoryUpdate, setInventoryUpdate] = useState(null);

  useEffect(() => {
    if (!productId || !isInventoryServiceConnected) return;

    const unsubscribe = subscribeToProduct(productId, (update) => {
      setInventoryUpdate(update);
    });

    return unsubscribe;
  }, [productId, isInventoryServiceConnected, subscribeToProduct]);

  return {
    inventoryUpdate,
    isConnected: isInventoryServiceConnected,
  };
};