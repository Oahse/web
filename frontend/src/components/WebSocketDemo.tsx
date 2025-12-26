import React, { useState, useEffect } from 'react';
import { 
  useWebSocket, 
  useOrderTracking, 
  useProductTracking, 
  useNotificationTracking,
  useCartTracking,
  useWebSocketStats,
  useWebSocketMessaging
} from '../hooks/useWebSocket';
import { WebSocketStatus, MessageType } from '../lib/websocket';

const WebSocketDemo: React.FC = () => {
  const { 
    status, 
    isConnected, 
    connect, 
    disconnect, 
    subscribe, 
    unsubscribe 
  } = useWebSocket();
  
  const { stats, connectionHistory } = useWebSocketStats();
  const { sendMessage, messageHistory } = useWebSocketMessaging();
  
  // Demo state
  const [orderId, setOrderId] = useState('');
  const [productId, setProductId] = useState('');
  const [customMessage, setCustomMessage] = useState('');
  const [subscriptions, setSubscriptions] = useState<string[]>([]);
  
  // Tracking hooks
  const { orderUpdate, isSubscribed: orderSubscribed } = useOrderTracking(orderId);
  const { productUpdate, isSubscribed: productSubscribed } = useProductTracking(productId);
  const { notifications, clearNotifications } = useNotificationTracking();
  const { cartUpdates, clearCartUpdates } = useCartTracking();

  const getStatusColor = (status: WebSocketStatus) => {
    switch (status) {
      case WebSocketStatus.CONNECTED:
        return 'text-green-600';
      case WebSocketStatus.CONNECTING:
      case WebSocketStatus.RECONNECTING:
        return 'text-yellow-600';
      case WebSocketStatus.DISCONNECTED:
        return 'text-gray-600';
      case WebSocketStatus.ERROR:
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const handleSubscribe = () => {
    const events = ['notifications', 'order_updates', 'cart_updates', 'product_updates'];
    subscribe(events);
    setSubscriptions(prev => [...new Set([...prev, ...events])]);
  };

  const handleUnsubscribe = () => {
    const events = ['notifications', 'order_updates', 'cart_updates', 'product_updates'];
    unsubscribe(events);
    setSubscriptions(prev => prev.filter(sub => !events.includes(sub)));
  };

  const handleSendCustomMessage = () => {
    if (customMessage.trim()) {
      sendMessage({
        type: MessageType.NOTIFICATION,
        data: { message: customMessage, custom: true }
      });
      setCustomMessage('');
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">WebSocket Demo</h1>
      
      {/* Connection Status */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Connection Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-600">Status</p>
            <p className={`font-semibold ${getStatusColor(status)}`}>
              {status.toUpperCase()}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Connected</p>
            <p className={`font-semibold ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
              {isConnected ? 'Yes' : 'No'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Reconnect Attempts</p>
            <p className="font-semibold">{stats.reconnectAttempts}</p>
          </div>
        </div>
        
        <div className="mt-4 flex gap-2">
          <button
            onClick={connect}
            disabled={isConnected}
            className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300"
          >
            Connect
          </button>
          <button
            onClick={disconnect}
            disabled={!isConnected}
            className="px-4 py-2 bg-red-500 text-white rounded disabled:bg-gray-300"
          >
            Disconnect
          </button>
        </div>
      </div>

      {/* Statistics */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Statistics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Messages Sent</p>
            <p className="font-semibold">{stats.messagesSent}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Messages Received</p>
            <p className="font-semibold">{stats.messagesReceived}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Queued Messages</p>
            <p className="font-semibold">{stats.queuedMessages}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Connected Since</p>
            <p className="font-semibold">
              {stats.connectedAt ? stats.connectedAt.toLocaleTimeString() : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Subscriptions */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Subscriptions</h2>
        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2">Active Subscriptions:</p>
          <div className="flex flex-wrap gap-2">
            {subscriptions.map(sub => (
              <span key={sub} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                {sub}
              </span>
            ))}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleSubscribe}
            disabled={!isConnected}
            className="px-4 py-2 bg-green-500 text-white rounded disabled:bg-gray-300"
          >
            Subscribe to Events
          </button>
          <button
            onClick={handleUnsubscribe}
            disabled={!isConnected}
            className="px-4 py-2 bg-orange-500 text-white rounded disabled:bg-gray-300"
          >
            Unsubscribe from Events
          </button>
        </div>
      </div>

      {/* Order Tracking */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Order Tracking</h2>
        <div className="mb-4">
          <input
            type="text"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            placeholder="Enter Order ID"
            className="w-full p-2 border rounded"
          />
          <p className="text-sm text-gray-600 mt-2">
            Subscribed: {orderSubscribed ? 'Yes' : 'No'}
          </p>
        </div>
        {orderUpdate && (
          <div className="bg-gray-50 p-4 rounded">
            <h3 className="font-semibold mb-2">Latest Order Update:</h3>
            <pre className="text-sm">{JSON.stringify(orderUpdate, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* Product Tracking */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Product Tracking</h2>
        <div className="mb-4">
          <input
            type="text"
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            placeholder="Enter Product ID"
            className="w-full p-2 border rounded"
          />
          <p className="text-sm text-gray-600 mt-2">
            Subscribed: {productSubscribed ? 'Yes' : 'No'}
          </p>
        </div>
        {productUpdate && (
          <div className="bg-gray-50 p-4 rounded">
            <h3 className="font-semibold mb-2">Latest Product Update:</h3>
            <pre className="text-sm">{JSON.stringify(productUpdate, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* Notifications */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">
          Notifications ({notifications.length})
          <button
            onClick={clearNotifications}
            className="ml-2 px-2 py-1 bg-gray-500 text-white text-sm rounded"
          >
            Clear
          </button>
        </h2>
        <div className="max-h-60 overflow-y-auto">
          {notifications.map((notification, index) => (
            <div key={index} className="bg-gray-50 p-3 rounded mb-2">
              <div className="text-sm text-gray-600">
                {new Date(notification.timestamp).toLocaleTimeString()}
              </div>
              <pre className="text-sm mt-1">{JSON.stringify(notification.data, null, 2)}</pre>
            </div>
          ))}
        </div>
      </div>

      {/* Cart Updates */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">
          Cart Updates ({cartUpdates.length})
          <button
            onClick={clearCartUpdates}
            className="ml-2 px-2 py-1 bg-gray-500 text-white text-sm rounded"
          >
            Clear
          </button>
        </h2>
        <div className="max-h-60 overflow-y-auto">
          {cartUpdates.map((update, index) => (
            <div key={index} className="bg-gray-50 p-3 rounded mb-2">
              <div className="text-sm text-gray-600">
                {new Date(update.timestamp).toLocaleTimeString()}
              </div>
              <pre className="text-sm mt-1">{JSON.stringify(update.data, null, 2)}</pre>
            </div>
          ))}
        </div>
      </div>

      {/* Custom Messages */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Send Custom Message</h2>
        <div className="mb-4">
          <input
            type="text"
            value={customMessage}
            onChange={(e) => setCustomMessage(e.target.value)}
            placeholder="Enter custom message"
            className="w-full p-2 border rounded"
            onKeyPress={(e) => e.key === 'Enter' && handleSendCustomMessage()}
          />
          <button
            onClick={handleSendCustomMessage}
            disabled={!isConnected || !customMessage.trim()}
            className="mt-2 px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300"
          >
            Send Message
          </button>
        </div>
        
        <h3 className="font-semibold mb-2">Message History:</h3>
        <div className="max-h-40 overflow-y-auto">
          {messageHistory.map((msg, index) => (
            <div key={index} className="bg-gray-50 p-2 rounded mb-2 text-sm">
              <span className={`font-semibold ${msg.sent ? 'text-green-600' : 'text-red-600'}`}>
                {msg.sent ? 'Sent' : 'Failed'}
              </span>
              <span className="text-gray-600 ml-2">
                {msg.timestamp.toLocaleTimeString()}
              </span>
              <div className="mt-1">{JSON.stringify(msg.message.data)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Connection History */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Connection History</h2>
        <div className="max-h-40 overflow-y-auto">
          {connectionHistory.map((entry, index) => (
            <div key={index} className="flex justify-between items-center py-2 border-b">
              <span className={`font-semibold ${getStatusColor(entry.status)}`}>
                {entry.status.toUpperCase()}
              </span>
              <span className="text-sm text-gray-600">
                {entry.timestamp.toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default WebSocketDemo;