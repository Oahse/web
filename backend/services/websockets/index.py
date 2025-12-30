"""
Enhanced WebSocket Service for Real-time Communication

This service provides comprehensive WebSocket management with:
- User authentication and session management
- Event-based messaging system
- Connection health monitoring
- Automatic reconnection handling
- Message queuing and delivery guarantees
"""

import json
import logging
import asyncio
import uuid
from typing import Dict, List, Optional, Set, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from fastapi import WebSocket, HTTPException, status
from core.config import settings
from core.utils.auth.jwt_auth import JWTManager

logger = logging.getLogger(__name__)
jwt_manager = JWTManager(secret_key=settings.SECRET_KEY, algorithm=settings.ALGORITHM)


class ConnectionStatus(Enum):
    """WebSocket connection status"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MessageType(Enum):
    """WebSocket message types"""
    # System messages
    PING = "ping"
    PONG = "pong"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    
    # Subscription messages
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SUBSCRIPTION_RESPONSE = "subscription_response"
    
    # Business messages
    NOTIFICATION = "notification"
    ORDER_UPDATE = "order_update"
    CART_UPDATE = "cart_update"
    PRODUCT_UPDATE = "product_update"
    INVENTORY_UPDATE = "inventory_update"
    USER_STATUS = "user_status"
    
    # Admin messages
    ADMIN_BROADCAST = "admin_broadcast"
    SYSTEM_ANNOUNCEMENT = "system_announcement"


@dataclass
class WebSocketMessage:
    """Structured WebSocket message"""
    type: MessageType
    data: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    connection_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    message_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps({
            "type": self.type.value,
            "data": self.data,
            "user_id": self.user_id,
            "connection_id": self.connection_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "message_id": self.message_id
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketMessage':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls(
            type=MessageType(data.get("type")),
            data=data.get("data", {}),
            user_id=data.get("user_id"),
            connection_id=data.get("connection_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            message_id=data.get("message_id")
        )


@dataclass
class WebSocketConnection:
    """Enhanced WebSocket connection with metadata"""
    websocket: WebSocket
    connection_id: str
    user_id: Optional[str] = None
    status: ConnectionStatus = ConnectionStatus.CONNECTING
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)
    last_pong: datetime = field(default_factory=datetime.utcnow)
    subscriptions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_queue: List[WebSocketMessage] = field(default_factory=list)
    failed_messages: int = 0
    
    @property
    def is_authenticated(self) -> bool:
        return self.user_id is not None
    
    @property
    def connection_duration(self) -> timedelta:
        return datetime.utcnow() - self.connected_at
    
    def is_alive(self, timeout_seconds: int = 300) -> bool:
        """Check if connection is alive based on last pong"""
        return (datetime.utcnow() - self.last_pong).total_seconds() < timeout_seconds
    
    def update_ping(self):
        """Update last ping timestamp"""
        self.last_ping = datetime.utcnow()
    
    def update_pong(self):
        """Update last pong timestamp"""
        self.last_pong = datetime.utcnow()
    
    def add_subscription(self, event_type: str):
        """Add event subscription"""
        self.subscriptions.add(event_type)
    
    def remove_subscription(self, event_type: str):
        """Remove event subscription"""
        self.subscriptions.discard(event_type)
    
    def queue_message(self, message: WebSocketMessage):
        """Queue message for delivery"""
        self.message_queue.append(message)
        # Limit queue size to prevent memory issues
        if len(self.message_queue) > 100:
            self.message_queue.pop(0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert connection info to dictionary"""
        return {
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "connected_at": self.connected_at.isoformat(),
            "last_ping": self.last_ping.isoformat(),
            "last_pong": self.last_pong.isoformat(),
            "is_authenticated": self.is_authenticated,
            "subscriptions": list(self.subscriptions),
            "is_alive": self.is_alive(),
            "connection_duration_seconds": self.connection_duration.total_seconds(),
            "queued_messages": len(self.message_queue),
            "failed_messages": self.failed_messages,
            "metadata": self.metadata
        }


class ConnectionManager:
    """Enhanced WebSocket connection manager"""
    
    def __init__(self):
        # Core connection storage
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        self.subscription_map: Dict[str, Set[str]] = {}  # event_type -> connection_ids
        
        # Background tasks
        self.cleanup_tasks: Dict[str, asyncio.Task] = {}
        self.health_check_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "authenticated_connections": 0,
            "anonymous_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "connection_errors": 0,
            "failed_authentications": 0,
            "reconnections": 0
        }
        
        # Event handlers
        self.event_handlers: Dict[MessageType, List[Callable]] = {}
        
        # Health check task (will be started lazily)
        self.health_check_task: Optional[asyncio.Task] = None
    
    def add_event_handler(self, message_type: MessageType, handler: Callable):
        """Add event handler for specific message type"""
        if message_type not in self.event_handlers:
            self.event_handlers[message_type] = []
        self.event_handlers[message_type].append(handler)
    
    async def _emit_event(self, message_type: MessageType, connection: WebSocketConnection, data: Dict[str, Any]):
        """Emit event to registered handlers"""
        if message_type in self.event_handlers:
            for handler in self.event_handlers[message_type]:
                try:
                    await handler(connection, data)
                except Exception as e:
                    logger.error(f"Error in event handler for {message_type}: {e}")
    
    async def authenticate_connection(self, token: str) -> Optional[str]:
        """Authenticate WebSocket connection using JWT token"""
        try:
            payload = jwt_manager.verify_token(token)
            user_id = payload.get("sub")
            if user_id:
                logger.info(f"WebSocket authentication successful for user: {user_id}")
                return user_id
            else:
                logger.warning("WebSocket authentication failed: No user ID in token")
                self.stats["failed_authentications"] += 1
                return None
        except Exception as e:
            logger.error(f"WebSocket authentication error: {str(e)}")
            self.stats["failed_authentications"] += 1
            return None
    
    async def connect(self, websocket: WebSocket, token: Optional[str] = None, 
                     connection_id: Optional[str] = None) -> str:
        """Connect a WebSocket with optional authentication"""
        await websocket.accept()
        
        # Start health check if this is the first connection
        if self.health_check_task is None:
            self._start_health_check()
        
        # Generate connection ID if not provided
        if connection_id is None:
            connection_id = str(uuid.uuid4())
        
        # Authenticate if token provided
        user_id = None
        if token:
            user_id = await self.authenticate_connection(token)
        
        # Create connection object
        connection = WebSocketConnection(
            websocket=websocket,
            connection_id=connection_id,
            user_id=user_id,
            status=ConnectionStatus.CONNECTED
        )
        
        # Store connection
        self.connections[connection_id] = connection
        
        # Update user connections mapping
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            self.stats["authenticated_connections"] += 1
        else:
            self.stats["anonymous_connections"] += 1
        
        self.stats["total_connections"] += 1
        
        logger.info(f"WebSocket connected: {connection_id}, User: {user_id}, Total: {len(self.connections)}")
        
        # Send welcome message
        welcome_message = WebSocketMessage(
            type=MessageType.CONNECT,
            data={
                "message": "Connected to Banwee WebSocket",
                "connection_id": connection_id,
                "authenticated": user_id is not None,
                "user_id": user_id,
                "server_time": datetime.utcnow().isoformat()
            },
            connection_id=connection_id,
            user_id=user_id
        )
        
        await self._send_message(connection, welcome_message)
        
        # Emit connection event
        await self._emit_event(MessageType.CONNECT, connection, welcome_message.data)
        
        # Start connection monitoring
        self._start_connection_monitoring(connection_id)
        
        return connection_id
    
    async def disconnect(self, connection_id: str, reason: str = "normal_closure"):
        """Disconnect a WebSocket connection with proper cleanup"""
        if connection_id not in self.connections:
            logger.warning(f"Attempted to disconnect non-existent connection: {connection_id}")
            return
        
        connection = self.connections[connection_id]
        connection.status = ConnectionStatus.DISCONNECTING
        user_id = connection.user_id
        
        try:
            # Send disconnect notification
            disconnect_message = WebSocketMessage(
                type=MessageType.DISCONNECT,
                data={
                    "reason": reason,
                    "connection_duration": connection.connection_duration.total_seconds()
                },
                connection_id=connection_id,
                user_id=user_id
            )
            await self._send_message(connection, disconnect_message)
        except Exception as e:
            logger.debug(f"Could not send disconnect message to {connection_id}: {e}")
        
        # Clean up subscriptions
        for event_type in list(connection.subscriptions):
            self._remove_subscription(connection_id, event_type)
        
        # Clean up user connections mapping
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
            self.stats["authenticated_connections"] -= 1
        else:
            self.stats["anonymous_connections"] -= 1
        
        # Cancel monitoring task
        if connection_id in self.cleanup_tasks:
            self.cleanup_tasks[connection_id].cancel()
            del self.cleanup_tasks[connection_id]
        
        # Remove connection
        connection.status = ConnectionStatus.DISCONNECTED
        del self.connections[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}, User: {user_id}, "
                   f"Duration: {connection.connection_duration}, Reason: {reason}")
        
        # Emit disconnection event
        await self._emit_event(MessageType.DISCONNECT, connection, {"reason": reason})
    
    async def _send_message(self, connection: WebSocketConnection, message: WebSocketMessage) -> bool:
        """Send message to a specific connection"""
        try:
            await connection.websocket.send_text(message.to_json())
            self.stats["total_messages_sent"] += 1
            return True
        except Exception as e:
            logger.error(f"Error sending message to {connection.connection_id}: {e}")
            connection.failed_messages += 1
            self.stats["connection_errors"] += 1
            
            # Queue message for retry if connection is still alive
            if connection.is_alive():
                connection.queue_message(message)
            else:
                await self.disconnect(connection.connection_id, "send_error")
            return False
    
    async def send_to_connection(self, connection_id: str, message: WebSocketMessage) -> bool:
        """Send message to a specific connection by ID"""
        if connection_id not in self.connections:
            logger.warning(f"Attempted to send message to non-existent connection: {connection_id}")
            return False
        
        connection = self.connections[connection_id]
        return await self._send_message(connection, message)
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """Send message to all connections for a specific user"""
        if user_id not in self.user_connections:
            logger.debug(f"No connections found for user: {user_id}")
            return 0
        
        sent_count = 0
        connection_ids = list(self.user_connections[user_id])
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast(self, message: WebSocketMessage, exclude_connections: Optional[Set[str]] = None) -> int:
        """Broadcast message to all active connections"""
        exclude_connections = exclude_connections or set()
        sent_count = 0
        
        connection_ids = list(self.connections.keys())
        for connection_id in connection_ids:
            if connection_id not in exclude_connections:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        
        return sent_count
    
    async def broadcast_to_subscribers(self, event_type: str, message: WebSocketMessage) -> int:
        """Broadcast message to connections subscribed to specific event type"""
        if event_type not in self.subscription_map:
            return 0
        
        sent_count = 0
        connection_ids = list(self.subscription_map[event_type])
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    def _add_subscription(self, connection_id: str, event_type: str):
        """Add subscription mapping"""
        if event_type not in self.subscription_map:
            self.subscription_map[event_type] = set()
        self.subscription_map[event_type].add(connection_id)
    
    def _remove_subscription(self, connection_id: str, event_type: str):
        """Remove subscription mapping"""
        if event_type in self.subscription_map:
            self.subscription_map[event_type].discard(connection_id)
            if not self.subscription_map[event_type]:
                del self.subscription_map[event_type]
    
    async def subscribe_to_events(self, connection_id: str, event_types: List[str]) -> bool:
        """Subscribe connection to specific event types"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        for event_type in event_types:
            connection.add_subscription(event_type)
            self._add_subscription(connection_id, event_type)
        
        logger.info(f"Connection {connection_id} subscribed to events: {event_types}")
        return True
    
    async def unsubscribe_from_events(self, connection_id: str, event_types: List[str]) -> bool:
        """Unsubscribe connection from specific event types"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        for event_type in event_types:
            connection.remove_subscription(event_type)
            self._remove_subscription(connection_id, event_type)
        
        logger.info(f"Connection {connection_id} unsubscribed from events: {event_types}")
        return True
    
    async def handle_message(self, connection_id: str, raw_message: str):
        """Handle incoming WebSocket message"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        self.stats["total_messages_received"] += 1
        
        try:
            # Parse message
            message_data = json.loads(raw_message)
            message_type = MessageType(message_data.get("type", ""))
            
            # Create structured message
            message = WebSocketMessage(
                type=message_type,
                data=message_data.get("data", {}),
                user_id=connection.user_id,
                connection_id=connection_id
            )
            
            # Handle specific message types
            if message_type == MessageType.PING:
                await self._handle_ping(connection, message)
            elif message_type == MessageType.SUBSCRIBE:
                await self._handle_subscribe(connection, message)
            elif message_type == MessageType.UNSUBSCRIBE:
                await self._handle_unsubscribe(connection, message)
            else:
                # Emit to event handlers
                await self._emit_event(message_type, connection, message.data)
        
        except json.JSONDecodeError:
            error_message = WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": "Invalid JSON format", "original_message": raw_message},
                connection_id=connection_id,
                user_id=connection.user_id
            )
            await self._send_message(connection, error_message)
        except ValueError as e:
            error_message = WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": f"Invalid message type: {str(e)}", "original_message": raw_message},
                connection_id=connection_id,
                user_id=connection.user_id
            )
            await self._send_message(connection, error_message)
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            error_message = WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": "Internal server error", "message": str(e)},
                connection_id=connection_id,
                user_id=connection.user_id
            )
            await self._send_message(connection, error_message)
    
    async def _handle_ping(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle ping message"""
        connection.update_ping()
        
        pong_message = WebSocketMessage(
            type=MessageType.PONG,
            data={
                "client_timestamp": message.data.get("timestamp"),
                "server_timestamp": datetime.utcnow().isoformat()
            },
            connection_id=connection.connection_id,
            user_id=connection.user_id
        )
        await self._send_message(connection, pong_message)
    
    async def _handle_subscribe(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle subscription request"""
        event_types = message.data.get("events", [])
        success = await self.subscribe_to_events(connection.connection_id, event_types)
        
        response = WebSocketMessage(
            type=MessageType.SUBSCRIPTION_RESPONSE,
            data={
                "success": success,
                "events": event_types,
                "action": "subscribe"
            },
            connection_id=connection.connection_id,
            user_id=connection.user_id
        )
        await self._send_message(connection, response)
    
    async def _handle_unsubscribe(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle unsubscription request"""
        event_types = message.data.get("events", [])
        success = await self.unsubscribe_from_events(connection.connection_id, event_types)
        
        response = WebSocketMessage(
            type=MessageType.SUBSCRIPTION_RESPONSE,
            data={
                "success": success,
                "events": event_types,
                "action": "unsubscribe"
            },
            connection_id=connection.connection_id,
            user_id=connection.user_id
        )
        await self._send_message(connection, response)
    
    def _start_connection_monitoring(self, connection_id: str):
        """Start monitoring a connection for health checks"""
        async def monitor_connection():
            while connection_id in self.connections:
                try:
                    connection = self.connections[connection_id]
                    
                    # Check if connection is still alive
                    if not connection.is_alive():
                        logger.warning(f"Connection {connection_id} appears dead, cleaning up")
                        await self.disconnect(connection_id, "timeout")
                        break
                    
                    # Process queued messages
                    if connection.message_queue:
                        queued_messages = connection.message_queue.copy()
                        connection.message_queue.clear()
                        
                        for queued_message in queued_messages:
                            await self._send_message(connection, queued_message)
                    
                    # Send ping every 30 seconds
                    ping_message = WebSocketMessage(
                        type=MessageType.PING,
                        data={"timestamp": datetime.utcnow().isoformat()},
                        connection_id=connection_id,
                        user_id=connection.user_id
                    )
                    await self._send_message(connection, ping_message)
                    
                    await asyncio.sleep(30)
                
                except Exception as e:
                    logger.error(f"Error monitoring connection {connection_id}: {e}")
                    await self.disconnect(connection_id, "monitoring_error")
                    break
        
        task = asyncio.create_task(monitor_connection())
        self.cleanup_tasks[connection_id] = task
    
    def _start_health_check(self):
        """Start global health check task"""
        if self.health_check_task is not None:
            return  # Already started
            
        async def health_check():
            while True:
                try:
                    # Clean up dead connections
                    dead_connections = []
                    for connection_id, connection in self.connections.items():
                        if not connection.is_alive():
                            dead_connections.append(connection_id)
                    
                    for connection_id in dead_connections:
                        await self.disconnect(connection_id, "health_check_timeout")
                    
                    if dead_connections:
                        logger.info(f"Health check cleaned up {len(dead_connections)} dead connections")
                    
                    # Wait 5 minutes before next health check
                    await asyncio.sleep(300)
                
                except Exception as e:
                    logger.error(f"Error in health check: {e}")
                    await asyncio.sleep(60)  # Shorter retry on error
        
        try:
            self.health_check_task = asyncio.create_task(health_check())
        except RuntimeError:
            # No event loop running, will start later
            pass
    
    # Business logic methods
    async def notify_user(self, user_id: str, notification_data: Dict[str, Any]):
        """Send notification to user"""
        message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data=notification_data,
            user_id=user_id
        )
        return await self.send_to_user(user_id, message)
    
    async def broadcast_order_update(self, order_data: Dict[str, Any]):
        """Broadcast order update"""
        message = WebSocketMessage(
            type=MessageType.ORDER_UPDATE,
            data=order_data
        )
        return await self.broadcast_to_subscribers("order_updates", message)
    
    async def broadcast_product_update(self, product_data: Dict[str, Any]):
        """Broadcast product update"""
        message = WebSocketMessage(
            type=MessageType.PRODUCT_UPDATE,
            data=product_data
        )
        return await self.broadcast_to_subscribers("product_updates", message)
    
    async def broadcast_inventory_update(self, inventory_data: Dict[str, Any]):
        """Broadcast inventory update"""
        message = WebSocketMessage(
            type=MessageType.INVENTORY_UPDATE,
            data=inventory_data
        )
        return await self.broadcast_to_subscribers("inventory_updates", message)
    
    # Management methods
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection"""
        if connection_id in self.connections:
            return self.connections[connection_id].to_dict()
        return None
    
    def get_user_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all connections for a specific user"""
        if user_id not in self.user_connections:
            return []
        
        connections = []
        for connection_id in self.user_connections[user_id]:
            if connection_id in self.connections:
                connections.append(self.connections[connection_id].to_dict())
        
        return connections
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics"""
        active_connections = len(self.connections)
        authenticated_count = sum(1 for conn in self.connections.values() if conn.is_authenticated)
        
        return {
            **self.stats,
            "active_connections": active_connections,
            "authenticated_connections_current": authenticated_count,
            "anonymous_connections_current": active_connections - authenticated_count,
            "unique_users": len(self.user_connections),
            "subscription_types": len(self.subscription_map),
            "total_subscriptions": sum(len(subs) for subs in self.subscription_map.values()),
            "average_connection_duration": self._calculate_average_duration(),
            "connections_by_status": self._get_connections_by_status()
        }
    
    def _calculate_average_duration(self) -> float:
        """Calculate average connection duration in seconds"""
        if not self.connections:
            return 0.0
        
        total_duration = sum(conn.connection_duration.total_seconds() 
                           for conn in self.connections.values())
        return total_duration / len(self.connections)
    
    def _get_connections_by_status(self) -> Dict[str, int]:
        """Get connection count by status"""
        status_counts = {}
        for connection in self.connections.values():
            status = connection.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        return status_counts
    
    async def shutdown(self):
        """Gracefully shutdown the connection manager"""
        logger.info("Shutting down WebSocket connection manager...")
        
        # Cancel health check task
        if self.health_check_task:
            self.health_check_task.cancel()
        
        # Cancel all monitoring tasks
        for task in self.cleanup_tasks.values():
            task.cancel()
        
        # Disconnect all connections
        connection_ids = list(self.connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id, "server_shutdown")
        
        logger.info("WebSocket connection manager shutdown complete")


# Global connection manager instance
manager = ConnectionManager()