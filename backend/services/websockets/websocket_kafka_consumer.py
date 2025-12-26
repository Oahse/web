"""
WebSocket Kafka Consumer

This service consumes Kafka messages and broadcasts them via WebSocket
to connected clients, providing real-time updates for various events.
"""

import asyncio
import json
import logging
from typing import Dict, Any
from aiokafka import AIOKafkaConsumer

from core.config import settings
from .websocket_integration import websocket_integration

logger = logging.getLogger(__name__)


class WebSocketKafkaConsumer:
    """Kafka consumer that broadcasts messages via WebSocket"""
    
    def __init__(self):
        self.consumer = None
        self.running = False
        self.tasks = []
    
    async def start(self):
        """Start the Kafka consumer"""
        if self.running:
            logger.warning("WebSocket Kafka consumer is already running")
            return
        
        try:
            # Create Kafka consumer
            self.consumer = AIOKafkaConsumer(
                settings.KAFKA_TOPIC_ORDER,
                settings.KAFKA_TOPIC_CART,
                settings.KAFKA_TOPIC_INVENTORY,
                settings.KAFKA_TOPIC_NOTIFICATION,
                settings.KAFKA_TOPIC_WEBSOCKET,
                settings.KAFKA_TOPIC_REAL_TIME,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=f"{settings.KAFKA_CONSUMER_GROUP_BACKEND}_websocket",
                auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
                enable_auto_commit=settings.KAFKA_ENABLE_AUTO_COMMIT,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None
            )
            
            await self.consumer.start()
            self.running = True
            
            logger.info("WebSocket Kafka consumer started")
            
            # Start consuming messages
            self.tasks.append(asyncio.create_task(self.consume_messages()))
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket Kafka consumer: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the Kafka consumer"""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Stop consumer
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None
        
        logger.info("WebSocket Kafka consumer stopped")
    
    async def consume_messages(self):
        """Consume messages from Kafka and broadcast via WebSocket"""
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    await self.handle_message(message.topic, message.value)
                except Exception as e:
                    logger.error(f"Error handling Kafka message from topic {message.topic}: {e}")
                    
        except asyncio.CancelledError:
            logger.info("WebSocket Kafka consumer task cancelled")
        except Exception as e:
            logger.error(f"Error in WebSocket Kafka consumer: {e}")
    
    async def handle_message(self, topic: str, message: Dict[str, Any]):
        """Handle individual Kafka message"""
        if not message:
            return
        
        logger.debug(f"Processing WebSocket message from topic {topic}: {message}")
        
        try:
            if topic == settings.KAFKA_TOPIC_ORDER:
                await self.handle_order_message(message)
            elif topic == settings.KAFKA_TOPIC_CART:
                await self.handle_cart_message(message)
            elif topic == settings.KAFKA_TOPIC_INVENTORY:
                await self.handle_inventory_message(message)
            elif topic == settings.KAFKA_TOPIC_NOTIFICATION:
                await self.handle_notification_message(message)
            elif topic == settings.KAFKA_TOPIC_WEBSOCKET:
                await self.handle_websocket_message(message)
            elif topic == settings.KAFKA_TOPIC_REAL_TIME:
                await self.handle_real_time_message(message)
            else:
                logger.debug(f"Unhandled topic in WebSocket consumer: {topic}")
                
        except Exception as e:
            logger.error(f"Error processing message from topic {topic}: {e}")
    
    async def handle_order_message(self, message: Dict[str, Any]):
        """Handle order-related messages"""
        event_type = message.get("event_type")
        order_data = message.get("data", {})
        user_id = order_data.get("user_id")
        
        if not user_id:
            logger.warning("Order message missing user_id")
            return
        
        # Map event types to user-friendly messages
        event_messages = {
            "order_created": "Your order has been created successfully",
            "order_confirmed": "Your order has been confirmed",
            "order_processing": "Your order is being processed",
            "order_shipped": "Your order has been shipped",
            "order_delivered": "Your order has been delivered",
            "order_cancelled": "Your order has been cancelled"
        }
        
        # Broadcast order update
        await websocket_integration.broadcast_order_update(user_id, {
            "event_type": event_type,
            "message": event_messages.get(event_type, f"Order status updated: {event_type}"),
            **order_data
        })
        
        # Send notification if it's a significant event
        if event_type in ["order_shipped", "order_delivered", "order_cancelled"]:
            await websocket_integration.send_notification(user_id, {
                "title": "Order Update",
                "message": event_messages.get(event_type),
                "type": "info" if event_type != "order_cancelled" else "warning",
                "order_id": order_data.get("order_id"),
                "order_number": order_data.get("order_number")
            })
    
    async def handle_cart_message(self, message: Dict[str, Any]):
        """Handle cart-related messages"""
        event_type = message.get("event_type")
        cart_data = message.get("data", {})
        user_id = cart_data.get("user_id")
        
        if not user_id:
            logger.warning("Cart message missing user_id")
            return
        
        # Broadcast cart update
        await websocket_integration.broadcast_cart_update(user_id, {
            "event_type": event_type,
            **cart_data
        })
    
    async def handle_inventory_message(self, message: Dict[str, Any]):
        """Handle inventory-related messages"""
        event_type = message.get("event_type")
        inventory_data = message.get("data", {})
        
        # Broadcast inventory update to all subscribers
        await websocket_integration.broadcast_inventory_update({
            "event_type": event_type,
            **inventory_data
        })
        
        # Send low stock alerts as notifications to admin users
        if event_type == "low_stock_alert":
            product_name = inventory_data.get("product_name", "Unknown Product")
            current_stock = inventory_data.get("current_stock", 0)
            threshold = inventory_data.get("threshold", 0)
            
            # Broadcast to all admin users (you'd need to implement admin user tracking)
            await websocket_integration.broadcast_admin_message({
                "title": "Low Stock Alert",
                "message": f"{product_name} is running low (Stock: {current_stock}, Threshold: {threshold})",
                "type": "warning",
                "priority": "medium",
                **inventory_data
            })
    
    async def handle_notification_message(self, message: Dict[str, Any]):
        """Handle notification messages"""
        event_type = message.get("event_type")
        notification_data = message.get("data", {})
        user_id = notification_data.get("user_id")
        
        if not user_id:
            logger.warning("Notification message missing user_id")
            return
        
        if event_type == "notification_created":
            # Send notification to specific user
            await websocket_integration.send_notification(user_id, notification_data)
        elif event_type == "notification_broadcast":
            # Broadcast notification to all users
            await websocket_integration.broadcast_admin_message({
                "title": notification_data.get("title", "Notification"),
                "message": notification_data.get("message", ""),
                "type": notification_data.get("type", "info"),
                "priority": notification_data.get("priority", "low")
            })
    
    async def handle_websocket_message(self, message: Dict[str, Any]):
        """Handle WebSocket-specific messages"""
        event_type = message.get("event_type")
        data = message.get("data", {})
        
        if event_type == "broadcast_all":
            # Broadcast to all connected clients
            await websocket_integration.broadcast_admin_message(data)
        elif event_type == "broadcast_user":
            # Broadcast to specific user
            user_id = data.get("user_id")
            if user_id:
                await websocket_integration.send_notification(user_id, data)
        elif event_type == "system_announcement":
            # System-wide announcement
            await websocket_integration.broadcast_admin_message({
                "title": "System Announcement",
                "type": "info",
                "priority": "high",
                **data
            })
    
    async def handle_real_time_message(self, message: Dict[str, Any]):
        """Handle real-time notification messages"""
        event_type = message.get("event_type")
        data = message.get("data", {})
        user_id = data.get("user_id")
        
        if user_id:
            # Send real-time notification to specific user
            await websocket_integration.send_notification(user_id, {
                "title": data.get("title", "Real-time Update"),
                "message": data.get("message", ""),
                "type": data.get("type", "info"),
                "event_type": event_type,
                **data
            })
        else:
            # Broadcast to all users
            await websocket_integration.broadcast_admin_message({
                "title": data.get("title", "Real-time Update"),
                "message": data.get("message", ""),
                "type": data.get("type", "info"),
                "event_type": event_type,
                **data
            })


# Global consumer instance
websocket_kafka_consumer = WebSocketKafkaConsumer()


# Startup and shutdown functions for FastAPI
async def start_websocket_kafka_consumer():
    """Start the WebSocket Kafka consumer"""
    await websocket_kafka_consumer.start()


async def stop_websocket_kafka_consumer():
    """Stop the WebSocket Kafka consumer"""
    await websocket_kafka_consumer.stop()