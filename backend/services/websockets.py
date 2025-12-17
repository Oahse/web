# manager.py
from typing import List, Dict, Optional, Set
from fastapi import WebSocket, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
import logging
from datetime import datetime, timedelta
from core.config import settings
from core.utils.auth.jwt_auth import JWTManager
import asyncio
import uuid

# Setup logging
logger = logging.getLogger(__name__)

# Initialize JWT manager
jwt_manager = JWTManager(secret_key=settings.SECRET_KEY,
                         algorithm=settings.ALGORITHM)


class WebSocketConnection:
    """Represents a WebSocket connection with metadata"""

    def __init__(self, websocket: WebSocket, user_id: Optional[str] = None, connection_id: Optional[str] = None):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_id = connection_id or str(uuid.uuid4())
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.is_authenticated = user_id is not None
        self.subscriptions: Set[str] = set()
        self.metadata: Dict = {}

    def update_ping(self):
        """Update last ping timestamp"""
        self.last_ping = datetime.utcnow()

    def is_alive(self, timeout_minutes: int = 5) -> bool:
        """Check if connection is still alive based on last ping"""
        return (datetime.utcnow() - self.last_ping) < timedelta(minutes=timeout_minutes)

    def add_subscription(self, event_type: str):
        """Add event subscription"""
        self.subscriptions.add(event_type)

    def remove_subscription(self, event_type: str):
        """Remove event subscription"""
        self.subscriptions.discard(event_type)

    def to_dict(self) -> Dict:
        """Convert connection info to dictionary"""
        return {
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "connected_at": self.connected_at.isoformat(),
            "last_ping": self.last_ping.isoformat(),
            "is_authenticated": self.is_authenticated,
            "subscriptions": list(self.subscriptions),
            "is_alive": self.is_alive()
        }


class ConnectionManager:
    def __init__(self):
        # Store connections with metadata
        self.connections: Dict[str, WebSocketConnection] = {}
        # Map user IDs to connection IDs
        self.user_connections: Dict[str, Set[str]] = {}
        # Track connection cleanup tasks
        self.cleanup_tasks: Dict[str, asyncio.Task] = {}
        # Connection statistics
        self.stats = {
            "total_connections": 0,
            "authenticated_connections": 0,
            "anonymous_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "connection_errors": 0
        }

    async def authenticate_connection(self, token: str) -> Optional[str]:
        """Authenticate WebSocket connection using JWT token"""
        try:
            payload = jwt_manager.verify_token(token)
            user_id = payload.get("sub")
            if user_id:
                logger.info(
                    f"WebSocket authentication successful for user: {user_id}")
                return user_id
            else:
                logger.warning(
                    "WebSocket authentication failed: No user ID in token")
                return None
        except Exception as e:
            logger.error(f"WebSocket authentication error: {str(e)}")
            return None

    async def connect(self, websocket: WebSocket, token: Optional[str] = None) -> str:
        """Connect a WebSocket with optional authentication"""
        await websocket.accept()

        # Authenticate if token provided
        user_id = None
        if token:
            user_id = await self.authenticate_connection(token)

        # Create connection object
        connection = WebSocketConnection(websocket, user_id)
        connection_id = connection.connection_id

        # Store connection
        self.connections[connection_id] = connection

        # Update user connections mapping if authenticated
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            self.stats["authenticated_connections"] += 1
        else:
            self.stats["anonymous_connections"] += 1

        self.stats["total_connections"] += 1

        logger.info(
            f"New WebSocket connection: {connection_id}, User: {user_id}, Total: {len(self.connections)}")

        # Send welcome message with connection info
        welcome_message = {
            "type": "connected",
            "message": "Connected to Banwee WebSocket",
            "connection_id": connection_id,
            "authenticated": user_id is not None,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            await websocket.send_text(json.dumps(welcome_message))
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
            await self.disconnect(connection_id)

        # Start connection monitoring
        self._start_connection_monitoring(connection_id)

        return connection_id

    async def disconnect(self, connection_id: str, reason: str = "normal_closure"):
        """Disconnect a WebSocket connection with proper cleanup"""
        if connection_id not in self.connections:
            logger.warning(
                f"Attempted to disconnect non-existent connection: {connection_id}")
            return

        connection = self.connections[connection_id]
        user_id = connection.user_id

        try:
            # Send disconnect notification if connection is still open
            if connection.websocket:
                disconnect_message = {
                    "type": "disconnecting",
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await connection.websocket.send_text(json.dumps(disconnect_message))
        except Exception as e:
            logger.debug(
                f"Could not send disconnect message to {connection_id}: {e}")

        # Clean up user connections mapping
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
            self.stats["authenticated_connections"] -= 1
        else:
            self.stats["anonymous_connections"] -= 1

        # Cancel cleanup task if exists
        if connection_id in self.cleanup_tasks:
            self.cleanup_tasks[connection_id].cancel()
            del self.cleanup_tasks[connection_id]

        # Remove connection
        del self.connections[connection_id]

        # Log connection duration
        duration = datetime.utcnow() - connection.connected_at
        logger.info(
            f"WebSocket disconnected: {connection_id}, User: {user_id}, Duration: {duration}, Reason: {reason}, Remaining: {len(self.connections)}")

        # Broadcast disconnection to other users if authenticated
        if user_id:
            await self._broadcast_user_status(user_id, "offline")

    def _start_connection_monitoring(self, connection_id: str):
        """Start monitoring a connection for health checks"""
        async def monitor_connection():
            while connection_id in self.connections:
                try:
                    connection = self.connections[connection_id]

                    # Check if connection is still alive
                    if not connection.is_alive():
                        logger.warning(
                            f"Connection {connection_id} appears dead, cleaning up")
                        await self.disconnect(connection_id, "timeout")
                        break

                    # Send ping every 30 seconds
                    ping_message = {
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat()
                    }

                    await connection.websocket.send_text(json.dumps(ping_message))
                    await asyncio.sleep(30)  # Wait 30 seconds before next ping

                except Exception as e:
                    logger.error(
                        f"Error monitoring connection {connection_id}: {e}")
                    await self.disconnect(connection_id, "monitoring_error")
                    break

        # Start monitoring task
        task = asyncio.create_task(monitor_connection())
        self.cleanup_tasks[connection_id] = task

    async def _broadcast_user_status(self, user_id: str, status: str):
        """Broadcast user online/offline status to other users"""
        status_message = {
            "type": "user_status",
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Broadcast to all authenticated connections
        await self.broadcast_to_authenticated(json.dumps(status_message))

    async def connect_user(self, websocket: WebSocket, user_id: str, token: Optional[str] = None) -> str:
        """Connect a user-specific WebSocket with authentication"""
        # Verify token if provided
        if token:
            authenticated_user_id = await self.authenticate_connection(token)
            if not authenticated_user_id or authenticated_user_id != user_id:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
                raise HTTPException(
                    status_code=401, detail="Authentication failed")

        # Use the general connect method
        connection_id = await self.connect(websocket, token)

        # Broadcast user online status
        await self._broadcast_user_status(user_id, "online")

        return connection_id

    async def disconnect_user(self, connection_id: str, user_id: str):
        """Disconnect a user-specific WebSocket"""
        await self.disconnect(connection_id, "user_disconnect")

    async def send_to_connection(self, connection_id: str, message: str) -> bool:
        """Send message to a specific connection"""
        if connection_id not in self.connections:
            logger.warning(
                f"Attempted to send message to non-existent connection: {connection_id}")
            return False

        connection = self.connections[connection_id]
        try:
            await connection.websocket.send_text(message)
            self.stats["total_messages_sent"] += 1
            return True
        except Exception as e:
            logger.error(
                f"Error sending message to connection {connection_id}: {e}")
            self.stats["connection_errors"] += 1
            await self.disconnect(connection_id, "send_error")
            return False

    async def send_to_user(self, user_id: str, message: str) -> int:
        """Send message to all connections for a specific user"""
        if user_id not in self.user_connections:
            logger.debug(f"No connections found for user: {user_id}")
            return 0

        sent_count = 0
        # Create copy to avoid modification during iteration
        connection_ids = list(self.user_connections[user_id])

        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1

        return sent_count

    async def broadcast(self, message: str, exclude_connections: Optional[Set[str]] = None) -> int:
        """Broadcast message to all active connections"""
        exclude_connections = exclude_connections or set()
        sent_count = 0

        # Create copy to avoid modification during iteration
        connection_ids = list(self.connections.keys())

        for connection_id in connection_ids:
            if connection_id not in exclude_connections:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1

        return sent_count

    async def broadcast_to_authenticated(self, message: str) -> int:
        """Broadcast message to all authenticated connections"""
        sent_count = 0

        for connection_id, connection in list(self.connections.items()):
            if connection.is_authenticated:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1

        return sent_count

    async def broadcast_to_subscribers(self, event_type: str, message: str) -> int:
        """Broadcast message to connections subscribed to specific event type"""
        sent_count = 0

        for connection_id, connection in list(self.connections.items()):
            if event_type in connection.subscriptions:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1

        return sent_count

    async def handle_ping(self, connection_id: str, timestamp: Optional[str] = None):
        """Handle ping message and update connection status"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.update_ping()

            # Send pong response
            pong_message = {
                "type": "pong",
                "timestamp": timestamp or datetime.utcnow().isoformat(),
                "server_timestamp": datetime.utcnow().isoformat()
            }
            await self.send_to_connection(connection_id, json.dumps(pong_message))

    async def subscribe_to_events(self, connection_id: str, event_types: List[str]) -> bool:
        """Subscribe connection to specific event types"""
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        for event_type in event_types:
            connection.add_subscription(event_type)

        logger.info(
            f"Connection {connection_id} subscribed to events: {event_types}")
        return True

    async def unsubscribe_from_events(self, connection_id: str, event_types: List[str]) -> bool:
        """Unsubscribe connection from specific event types"""
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        for event_type in event_types:
            connection.remove_subscription(event_type)

        logger.info(
            f"Connection {connection_id} unsubscribed from events: {event_types}")
        return True

    async def broadcast_cart_update(self, user_id: str, cart_data: dict):
        """Broadcast cart updates to user's connections"""
        message = json.dumps({
            "type": "cart_update",
            "data": cart_data,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        sent_count = await self.send_to_user(user_id, message)
        logger.debug(
            f"Cart update sent to {sent_count} connections for user {user_id}")

    async def broadcast_order_update(self, user_id: str, order_data: dict):
        """Broadcast order updates to user's connections"""
        message = json.dumps({
            "type": "order_update",
            "data": order_data,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        sent_count = await self.send_to_user(user_id, message)
        logger.debug(
            f"Order update sent to {sent_count} connections for user {user_id}")

    async def broadcast_product_update(self, product_data: dict):
        """Broadcast product updates to all connections"""
        message = json.dumps({
            "type": "product_update",
            "data": product_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        sent_count = await self.broadcast(message)
        logger.debug(f"Product update sent to {sent_count} connections")

    async def broadcast_to_admins(self, message: str) -> int:
        """Broadcast message to admin users (you'd need to track admin roles)"""
        # For now, broadcast to all authenticated users
        # In production, you'd filter by user role
        sent_count = await self.broadcast_to_authenticated(message)
        logger.debug(f"Admin broadcast sent to {sent_count} connections")
        return sent_count

    # Management and monitoring methods
    def get_connection_info(self, connection_id: str) -> Optional[Dict]:
        """Get information about a specific connection"""
        if connection_id in self.connections:
            return self.connections[connection_id].to_dict()
        return None

    def get_user_connections(self, user_id: str) -> List[Dict]:
        """Get all connections for a specific user"""
        if user_id not in self.user_connections:
            return []

        connections = []
        for connection_id in self.user_connections[user_id]:
            if connection_id in self.connections:
                connections.append(self.connections[connection_id].to_dict())

        return connections

    def get_stats(self) -> Dict:
        """Get connection statistics"""
        active_connections = len(self.connections)
        authenticated_count = sum(
            1 for conn in self.connections.values() if conn.is_authenticated)
        anonymous_count = active_connections - authenticated_count

        return {
            **self.stats,
            "active_connections": active_connections,
            "authenticated_connections_current": authenticated_count,
            "anonymous_connections_current": anonymous_count,
            "unique_users": len(self.user_connections),
            "average_connection_duration": self._calculate_average_duration()
        }

    def _calculate_average_duration(self) -> float:
        """Calculate average connection duration in seconds"""
        if not self.connections:
            return 0.0

        total_duration = 0
        for connection in self.connections.values():
            duration = datetime.utcnow() - connection.connected_at
            total_duration += duration.total_seconds()

        return total_duration / len(self.connections)

    async def cleanup_dead_connections(self):
        """Clean up connections that haven't responded to pings"""
        dead_connections = []

        for connection_id, connection in self.connections.items():
            if not connection.is_alive():
                dead_connections.append(connection_id)

        for connection_id in dead_connections:
            await self.disconnect(connection_id, "cleanup_dead")

        if dead_connections:
            logger.info(f"Cleaned up {len(dead_connections)} dead connections")

    async def shutdown(self):
        """Gracefully shutdown all connections"""
        logger.info("Shutting down WebSocket manager...")

        # Cancel all cleanup tasks
        for task in self.cleanup_tasks.values():
            task.cancel()

        # Disconnect all connections
        connection_ids = list(self.connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id, "server_shutdown")

        logger.info("WebSocket manager shutdown complete")

manager = ConnectionManager()