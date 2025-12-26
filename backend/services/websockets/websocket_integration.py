"""
WebSocket Integration Service

This service integrates WebSocket functionality with business logic,
providing event handlers and broadcasting capabilities for various
application events.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .index import manager, MessageType, WebSocketMessage
from core.database import AsyncSessionDB

logger = logging.getLogger(__name__)


class WebSocketIntegrationService:
    """Service for integrating WebSocket events with business logic"""
    
    def __init__(self):
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Set up event handlers for WebSocket messages"""
        
        # Handle connection events
        manager.add_event_handler(MessageType.CONNECT, self.handle_user_connect)
        manager.add_event_handler(MessageType.DISCONNECT, self.handle_user_disconnect)
        
        # Handle business events
        manager.add_event_handler(MessageType.CART_UPDATE, self.handle_cart_update_request)
        manager.add_event_handler(MessageType.ORDER_UPDATE, self.handle_order_update_request)
    
    async def handle_user_connect(self, connection, data: Dict[str, Any]):
        """Handle user connection event"""
        if connection.user_id:
            logger.info(f"User {connection.user_id} connected via WebSocket")
            
            # Broadcast user online status to other users
            await self.broadcast_user_status(connection.user_id, "online")
            
            # Send any pending notifications
            await self.send_pending_notifications(connection.user_id)
    
    async def handle_user_disconnect(self, connection, data: Dict[str, Any]):
        """Handle user disconnection event"""
        if connection.user_id:
            logger.info(f"User {connection.user_id} disconnected from WebSocket")
            
            # Broadcast user offline status to other users
            await self.broadcast_user_status(connection.user_id, "offline")
    
    async def handle_cart_update_request(self, connection, data: Dict[str, Any]):
        """Handle cart update request from client"""
        if not connection.user_id:
            return
        
        try:
            # Process cart update logic here
            # This would typically involve updating the cart in the database
            # and then broadcasting the update to all user's connections
            
            cart_data = data.get("data", {})
            await self.broadcast_cart_update(connection.user_id, cart_data)
            
        except Exception as e:
            logger.error(f"Error handling cart update for user {connection.user_id}: {e}")
    
    async def handle_order_update_request(self, connection, data: Dict[str, Any]):
        """Handle order update request from client"""
        if not connection.user_id:
            return
        
        try:
            # Process order update logic here
            order_data = data.get("data", {})
            await self.broadcast_order_update(connection.user_id, order_data)
            
        except Exception as e:
            logger.error(f"Error handling order update for user {connection.user_id}: {e}")
    
    # Business event broadcasting methods
    
    async def broadcast_user_status(self, user_id: str, status: str):
        """Broadcast user online/offline status"""
        message = WebSocketMessage(
            type=MessageType.USER_STATUS,
            data={
                "user_id": user_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Broadcast to all authenticated connections except the user themselves
        sent_count = 0
        for connection_id, connection in manager.connections.items():
            if connection.is_authenticated and connection.user_id != user_id:
                if "user_status" in connection.subscriptions:
                    await manager.send_to_connection(connection_id, message)
                    sent_count += 1
        
        logger.debug(f"User status broadcast sent to {sent_count} connections")
    
    async def broadcast_cart_update(self, user_id: str, cart_data: Dict[str, Any]):
        """Broadcast cart update to user's connections"""
        message = WebSocketMessage(
            type=MessageType.CART_UPDATE,
            data={
                **cart_data,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            user_id=user_id
        )
        
        sent_count = await manager.send_to_user(user_id, message)
        logger.debug(f"Cart update sent to {sent_count} connections for user {user_id}")
        
        return sent_count
    
    async def broadcast_order_update(self, user_id: str, order_data: Dict[str, Any]):
        """Broadcast order update to user's connections"""
        message = WebSocketMessage(
            type=MessageType.ORDER_UPDATE,
            data={
                **order_data,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            user_id=user_id
        )
        
        sent_count = await manager.send_to_user(user_id, message)
        logger.debug(f"Order update sent to {sent_count} connections for user {user_id}")
        
        return sent_count
    
    async def broadcast_product_update(self, product_data: Dict[str, Any]):
        """Broadcast product update to all subscribers"""
        message = WebSocketMessage(
            type=MessageType.PRODUCT_UPDATE,
            data={
                **product_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        sent_count = await manager.broadcast_to_subscribers("product_updates", message)
        logger.debug(f"Product update sent to {sent_count} connections")
        
        return sent_count
    
    async def broadcast_inventory_update(self, inventory_data: Dict[str, Any]):
        """Broadcast inventory update to all subscribers"""
        message = WebSocketMessage(
            type=MessageType.INVENTORY_UPDATE,
            data={
                **inventory_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        sent_count = await manager.broadcast_to_subscribers("inventory_updates", message)
        logger.debug(f"Inventory update sent to {sent_count} connections")
        
        return sent_count
    
    async def send_notification(self, user_id: str, notification_data: Dict[str, Any]):
        """Send notification to specific user"""
        message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                **notification_data,
                "timestamp": datetime.utcnow().isoformat()
            },
            user_id=user_id
        )
        
        sent_count = await manager.send_to_user(user_id, message)
        logger.debug(f"Notification sent to {sent_count} connections for user {user_id}")
        
        return sent_count
    
    async def broadcast_admin_message(self, message_data: Dict[str, Any]):
        """Broadcast admin message to all connections"""
        message = WebSocketMessage(
            type=MessageType.ADMIN_BROADCAST,
            data={
                **message_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        sent_count = await manager.broadcast(message)
        logger.info(f"Admin broadcast sent to {sent_count} connections")
        
        return sent_count
    
    async def send_pending_notifications(self, user_id: str):
        """Send any pending notifications to newly connected user"""
        try:
            async with AsyncSessionDB() as session:
                # Import here to avoid circular imports
                from services.notifications import NotificationService
                
                notification_service = NotificationService(session)
                
                # Get unread notifications for the user
                notifications = await notification_service.get_user_notifications(
                    user_id=user_id,
                    is_read=False,
                    limit=10
                )
                
                # Send each notification via WebSocket
                for notification in notifications:
                    await self.send_notification(user_id, {
                        "id": str(notification.id),
                        "title": notification.title,
                        "message": notification.message,
                        "type": notification.type,
                        "is_read": notification.is_read,
                        "created_at": notification.created_at.isoformat(),
                        "link": notification.link
                    })
                
                logger.info(f"Sent {len(notifications)} pending notifications to user {user_id}")
                
        except Exception as e:
            logger.error(f"Error sending pending notifications to user {user_id}: {e}")
    
    # Integration with other services
    
    async def handle_kafka_message(self, topic: str, message: Dict[str, Any]):
        """Handle Kafka messages and broadcast via WebSocket"""
        try:
            if topic == "banwee-order-events":
                await self.handle_order_event(message)
            elif topic == "banwee-cart-events":
                await self.handle_cart_event(message)
            elif topic == "banwee-inventory-events":
                await self.handle_inventory_event(message)
            elif topic == "banwee-user-notifications":
                await self.handle_notification_event(message)
            else:
                logger.debug(f"Unhandled Kafka topic: {topic}")
                
        except Exception as e:
            logger.error(f"Error handling Kafka message from topic {topic}: {e}")
    
    async def handle_order_event(self, message: Dict[str, Any]):
        """Handle order events from Kafka"""
        event_type = message.get("event_type")
        order_data = message.get("data", {})
        user_id = order_data.get("user_id")
        
        if user_id and event_type in ["order_created", "order_updated", "order_shipped", "order_delivered"]:
            await self.broadcast_order_update(user_id, {
                "event_type": event_type,
                **order_data
            })
    
    async def handle_cart_event(self, message: Dict[str, Any]):
        """Handle cart events from Kafka"""
        event_type = message.get("event_type")
        cart_data = message.get("data", {})
        user_id = cart_data.get("user_id")
        
        if user_id and event_type in ["cart_updated", "item_added", "item_removed"]:
            await self.broadcast_cart_update(user_id, {
                "event_type": event_type,
                **cart_data
            })
    
    async def handle_inventory_event(self, message: Dict[str, Any]):
        """Handle inventory events from Kafka"""
        event_type = message.get("event_type")
        inventory_data = message.get("data", {})
        
        if event_type in ["stock_updated", "low_stock_alert", "out_of_stock"]:
            await self.broadcast_inventory_update({
                "event_type": event_type,
                **inventory_data
            })
    
    async def handle_notification_event(self, message: Dict[str, Any]):
        """Handle notification events from Kafka"""
        event_type = message.get("event_type")
        notification_data = message.get("data", {})
        user_id = notification_data.get("user_id")
        
        if user_id and event_type == "notification_created":
            await self.send_notification(user_id, notification_data)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return manager.get_stats()
    
    def get_user_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """Get connections for a specific user"""
        return manager.get_user_connections(user_id)


# Global integration service instance
websocket_integration = WebSocketIntegrationService()