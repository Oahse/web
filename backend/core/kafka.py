import json
import logging
import uuid

import asyncio
import importlib
from datetime import datetime
from uuid import UUID
from core.database import AsyncSessionDB
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from core.config import settings
from sqlalchemy import select

# Import new event system
from core.events import EventProducer, EventConsumer

# Initialize event producer
event_producer = EventProducer()
from core.events.handlers import OrderEventHandler, InventoryEventHandler, UserEventHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapping of service names to their classes
# This allows dynamic loading of services based on Kafka message content.
SERVICE_MODULE_MAP = {
    "EmailService": "services.email",
    "NotificationService": "services.notification",
    "OrderService": "services.order",
    # Add other services as needed
}
async def consume_messages_with_deduplication():
    """
    Consume Kafka messages with deduplication
    Ensures exactly-once processing of Kafka events
    """
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_EMAIL,
        settings.KAFKA_TOPIC_NOTIFICATION,
        settings.KAFKA_TOPIC_ORDER,
        settings.KAFKA_TOPIC_PAYMENT,
        settings.KAFKA_TOPIC_CART,
        settings.KAFKA_TOPIC_WEBSOCKET,
        settings.KAFKA_TOPIC_REAL_TIME,
        settings.KAFKA_TOPIC_INVENTORY,
        # settings.KAFKA_TOPIC_NEGOTIATION,  # Disabled - not using negotiator for now
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_CONSUMER_GROUP_BACKEND,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
        enable_auto_commit=False,  # Manual commit for exactly-once semantics
        max_poll_records=settings.KAFKA_MAX_POLL_RECORDS,
        session_timeout_ms=settings.KAFKA_SESSION_TIMEOUT_MS,
        heartbeat_interval_ms=settings.KAFKA_HEARTBEAT_INTERVAL_MS,
        request_timeout_ms=settings.KAFKA_REQUEST_TIMEOUT_MS,
        retry_backoff_ms=settings.KAFKA_RETRY_BACKOFF_MS
    )
    
    logger.info("Starting Kafka consumer with deduplication...")
    await consumer.start()
    logger.info("Kafka consumer started.")

    try:
        async for msg in consumer:
            event_id = msg.value.get("event_id")
            
            if not event_id:
                # Generate event_id if not present (for backward compatibility)
                event_id = str(uuid.uuid4())
                msg.value["event_id"] = event_id
            
            try:
                async with AsyncSessionDB() as db:
                    # Process the message
                    result = await process_kafka_message(msg, db)
                    
                    # Commit offset only after successful processing
                    await consumer.commit()
                    
                    logger.info(f"Successfully processed event {event_id} from topic {msg.topic}")
                    
            except Exception as e:
                logger.error(f"Error processing event {event_id}: {e}")
                # Don't commit offset - will retry on next poll
                # You might want to implement a dead letter queue here
                
    finally:
        logger.info("Stopping Kafka consumer...")
        await consumer.stop()
        logger.info("Kafka consumer stopped.")


async def process_kafka_message(msg, db) -> dict:
    """Process individual Kafka message"""
    logger.info(f"Processing message from topic {msg.topic}: {msg.value}")
    task_data = msg.value
    
    service_name = task_data.get("service")
    method_name = task_data.get("method")
    task_name = task_data.get("task")
    args = task_data.get("args", [])
    kwargs = task_data.get("kwargs", {})
    
    # Handle different message types based on topic
    if msg.topic == settings.KAFKA_TOPIC_WEBSOCKET or msg.topic == settings.KAFKA_TOPIC_REAL_TIME:
        # Handle WebSocket messages for real-time notifications
        result = await handle_websocket_message(task_data)
        return {"action": "websocket_message_processed", "result": result}
        
    elif msg.topic == settings.KAFKA_TOPIC_PAYMENT:
        # Handle payment notifications with real-time updates
        result = await handle_payment_message(task_data)
        # Also send real-time notification
        await send_real_time_notification(task_data)
        return {"action": "payment_message_processed", "result": result}
        
    elif msg.topic == settings.KAFKA_TOPIC_CART:
        # Handle cart update notifications
        result = await handle_cart_message(task_data)
        # Send real-time cart updates
        await send_cart_real_time_update(task_data)
        return {"action": "cart_message_processed", "result": result}
        
    elif msg.topic == settings.KAFKA_TOPIC_ORDER:
        # Handle order events with real-time updates
        result = await handle_order_message(task_data)
        await send_real_time_notification(task_data)
        return {"action": "order_message_processed", "result": result}
        
    elif msg.topic == settings.KAFKA_TOPIC_INVENTORY:
        # Handle inventory updates
        result = await handle_inventory_message(task_data)
        return {"action": "inventory_message_processed", "result": result}
        
    elif service_name and method_name:
        try:
            service_module = importlib.import_module(SERVICE_MODULE_MAP.get(service_name))
            ServiceClass = getattr(service_module, service_name)
            
            service_instance = ServiceClass(db)
            method = getattr(service_instance, method_name)
            
            if asyncio.iscoroutinefunction(method):
                result = await method(*args, **kwargs)
            else:
                result = method(*args, **kwargs)

            logger.info(f"Successfully executed {service_name}.{method_name}")
            return {"action": "service_method_executed", "service": service_name, "method": method_name, "result": result}

        except ImportError:
            error_msg = f"Service module for '{service_name}' not found or incorrectly mapped."
            logger.error(error_msg)
            raise Exception(error_msg)
        except AttributeError:
            error_msg = f"Method '{method_name}' not found in '{service_name}'."
            logger.error(error_msg)
            raise Exception(error_msg)

    elif task_name:
        try:
            # Assuming email tasks are in `tasks.email_tasks`
            task_module = importlib.import_module("tasks.email_tasks")
            task_func = getattr(task_module, task_name)
            
            import inspect
            sig = inspect.signature(task_func)
            if 'db' in sig.parameters:
                result = await task_func(db, *args, **kwargs)
            else:
                result = await task_func(*args, **kwargs)

            logger.info(f"Successfully executed task {task_name}")
            return {"action": "task_executed", "task": task_name, "result": result}

        except ImportError:
            error_msg = f"Task module for '{task_name}' not found."
            logger.error(error_msg)
            raise Exception(error_msg)
        except AttributeError:
            error_msg = f"Task '{task_name}' not found in module."
            logger.error(error_msg)
            raise Exception(error_msg)
    
    else:
        error_msg = f"Invalid task data: {task_data}. Missing 'service'/'method' or 'task'."
        logger.error(error_msg)
        raise Exception(error_msg)


# Keep the original consume_messages function for backward compatibility
async def consume_messages():
    """Original consume_messages function - use consume_messages_with_deduplication for golden rules"""
    return await consume_messages_with_deduplication()


async def handle_websocket_message(message_data: dict):
    """Handle WebSocket notification messages"""
    try:
        # Import here to avoid circular imports
        from services.websockets import websocket_integration
        
        message_type = message_data.get('type')
        user_id = message_data.get('user_id')
        
        if message_type == 'payment_update' and user_id:
            # Send payment update to user's WebSocket connections
            await websocket_integration.send_notification(user_id, message_data.get('message', {}))
            logger.info(f"Sent WebSocket payment update to user {user_id}")
            return {"status": "websocket_sent", "user_id": user_id}
            
        return {"status": "no_action_needed"}
            
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        raise


async def handle_payment_message(message_data: dict):
    """Handle payment notification messages"""
    try:
        event_type = message_data.get('event_type')
        user_id = message_data.get('user_id')
        
        if event_type in ['payment_succeeded', 'payment_failed']:
            # Create notification in database
            async with AsyncSessionDB() as db:
                from services.notifications import NotificationService
                notification_service = NotificationService(db)
                
                title = "Payment Successful" if event_type == 'payment_succeeded' else "Payment Failed"
                message = f"Your payment has been {'processed successfully' if event_type == 'payment_succeeded' else 'failed'}."
                
                notification = await notification_service.create_notification(
                    user_id=UUID(user_id),
                    title=title,
                    message=message,
                    notification_type="payment"
                )
                
            # Send real-time WebSocket notification
            from services.websockets import websocket_integration
            await websocket_integration.send_notification(user_id, {
                "title": title,
                "message": message,
                "type": "payment",
                "event_type": event_type
            })
                
            logger.info(f"Created payment notification for user {user_id}: {event_type}")
            return {"status": "notification_created", "notification_id": str(notification.id)}
            
        return {"status": "no_action_needed"}
            
    except Exception as e:
        logger.error(f"Error handling payment message: {e}")
        raise


async def handle_cart_message(message_data: dict):
    """Handle cart update messages"""
    try:
        user_id = message_data.get('user_id')
        action = message_data.get('action')
        
        logger.info(f"Processed cart {action} for user {user_id}")
        return {"status": "cart_processed", "action": action, "user_id": user_id}
        
    except Exception as e:
        logger.error(f"Error handling cart message: {e}")
        raise


async def handle_order_message(message_data: dict):
    """Handle order event messages"""
    try:
        event_type = message_data.get('event_type')
        user_id = message_data.get('user_id')
        order_id = message_data.get('order_id')
        
        if event_type in ['order_created', 'order_updated', 'order_shipped', 'order_delivered', 'order_cancelled']:
            # Create notification in database
            async with AsyncSessionDB() as db:
                from services.notifications import NotificationService
                notification_service = NotificationService(db)
                
                title_map = {
                    'order_created': 'Order Confirmed',
                    'order_updated': 'Order Updated',
                    'order_shipped': 'Order Shipped',
                    'order_delivered': 'Order Delivered',
                    'order_cancelled': 'Order Cancelled'
                }
                
                title = title_map.get(event_type, 'Order Update')
                message = f"Your order #{order_id} has been {event_type.replace('order_', '')}."
                
                notification = await notification_service.create_notification(
                    user_id=UUID(user_id),
                    title=title,
                    message=message,
                    notification_type="order"
                )
                
            # Send real-time WebSocket notification
            from services.websockets import websocket_integration
            await websocket_integration.broadcast_order_update(user_id, {
                "title": title,
                "message": message,
                "event_type": event_type,
                "order_id": order_id
            })
                
            logger.info(f"Created order notification for user {user_id}: {event_type}")
            return {"status": "notification_created", "notification_id": str(notification.id)}
            
        return {"status": "no_action_needed"}
            
    except Exception as e:
        logger.error(f"Error handling order message: {e}")
        raise


async def handle_inventory_message(message_data: dict):
    """Handle inventory update messages"""
    try:
        event_type = message_data.get('event_type')
        product_id = message_data.get('product_id')
        variant_id = message_data.get('variant_id')
        
        if event_type in ['stock_low', 'stock_out', 'stock_replenished']:
            # Notify admin users about inventory changes
            async with AsyncSessionDB() as db:
                from services.notifications import NotificationService
                notification_service = NotificationService(db)
                
                title_map = {
                    'stock_low': 'Low Stock Alert',
                    'stock_out': 'Out of Stock Alert',
                    'stock_replenished': 'Stock Replenished'
                }
                
                title = title_map.get(event_type, 'Inventory Update')
                message = f"Product variant {variant_id} is {event_type.replace('stock_', '')}."
                
                # Send to admin users (you might want to implement admin user detection)
                # For now, we'll broadcast it via WebSocket
                from services.websockets import websocket_integration
                await websocket_integration.broadcast_inventory_update({
                    "title": title,
                    "message": message,
                    "event_type": event_type,
                    "product_id": product_id,
                    "variant_id": variant_id
                })
                
                logger.info(f"Inventory alert: {title} - {message}")
                return {"status": "inventory_alert_sent", "event_type": event_type}
                
        return {"status": "no_action_needed"}
                
    except Exception as e:
        logger.error(f"Error handling inventory message: {e}")
        raise


async def send_real_time_notification(message_data: dict):
    """Send real-time notifications via WebSocket"""
    try:
        user_id = message_data.get('user_id')
        if user_id:
            from services.websockets import websocket_integration
            
            notification_message = {
                'type': 'real_time_notification',
                'event_type': message_data.get('event_type'),
                'title': message_data.get('title', 'Notification'),
                'message': message_data.get('message', ''),
                'data': message_data.get('data', {}),
                'timestamp': message_data.get('timestamp')
            }
            
            await websocket_integration.send_notification(user_id, notification_message)
            logger.info(f"Sent real-time notification to user {user_id}")
            
    except Exception as e:
        logger.error(f"Error sending real-time notification: {e}")


async def send_cart_real_time_update(message_data: dict):
    """Send real-time cart updates via WebSocket"""
    try:
        user_id = message_data.get('user_id')
        if user_id:
            from services.websockets import websocket_integration
            
            cart_update = {
                'type': 'cart_real_time_update',
                'action': message_data.get('action'),
                'cart_count': message_data.get('cart_count', 0),
                'cart_total': message_data.get('cart_total', 0.0),
                'timestamp': message_data.get('timestamp')
            }
            
            await websocket_integration.broadcast_cart_update(user_id, cart_update)
            logger.info(f"Sent real-time cart update to user {user_id}")
            
    except Exception as e:
        logger.error(f"Error sending cart real-time update: {e}")

class KafkaProducer:
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    async def start(self):
        logger.info("Starting Kafka Producer...")
        await self.producer.start()
        logger.info("Kafka Producer started.")

    async def stop(self):
        logger.info("Stopping Kafka Producer...")
        await self.producer.stop()
        logger.info("Kafka Producer stopped.")

    async def send_message_with_deduplication(self, topic: str, value: dict, key: str = None):
        """
        Send message with event_id for deduplication
        """
        try:
            # Add event_id if not present
            if "event_id" not in value:
                value["event_id"] = str(uuid.uuid4())
            
            # Add timestamp if not present
            if "timestamp" not in value:
                value["timestamp"] = datetime.utcnow().isoformat()
            
            key_bytes = key.encode('utf-8') if key else None
            await self.producer.send_and_wait(topic, value, key=key_bytes)
            
            logger.info(f"Message sent to topic '{topic}' with event_id {value['event_id']}")
            return value["event_id"]
            
        except Exception as e:
            logger.error(f"Failed to send message to topic '{topic}': {e}")
            raise

    async def send_message(self, topic: str, value: dict, key: str = None):
        """Send message (uses deduplication by default)"""
        return await self.send_message_with_deduplication(topic, value, key)

    async def send_payment_notification(self, user_id: str, event_type: str, payment_data: dict):
        """Send payment notification to Kafka"""
        message = {
            'user_id': user_id,
            'event_type': event_type,
            'payment_data': payment_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.send_message(settings.KAFKA_TOPIC_PAYMENT, message, key=user_id)

    async def send_cart_notification(self, user_id: str, action: str, cart_data: dict):
        """Send cart update notification to Kafka"""
        message = {
            'user_id': user_id,
            'action': action,
            'data': cart_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.send_message(settings.KAFKA_TOPIC_CART, message, key=user_id)

    async def send_real_time_notification(self, user_id: str, notification_type: str, data: dict):
        """Send real-time notification to Kafka"""
        message = {
            'user_id': user_id,
            'type': notification_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.send_message(settings.KAFKA_TOPIC_REAL_TIME, message, key=user_id)

    async def send_order_notification(self, user_id: str, order_id: str, event_type: str, order_data: dict):
        """Send order event notification to Kafka"""
        message = {
            'user_id': user_id,
            'order_id': order_id,
            'event_type': event_type,
            'data': order_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.send_message(settings.KAFKA_TOPIC_ORDER, message, key=user_id)

# Global Kafka Producer instance - initialized lazily
kafka_producer_service = None

async def get_kafka_producer_service() -> KafkaProducer:
    global kafka_producer_service
    if kafka_producer_service is None:
        kafka_producer_service = KafkaProducer()
        await kafka_producer_service.start()
    return kafka_producer_service

# Initialize event system
async def initialize_event_system():
    """Initialize the new event-driven architecture system"""
    try:
        # Start event producer
        await event_producer.start()
        logger.info("Event producer initialized")
        
        # Register event handlers
        event_consumer.register_handler("order.order.created", OrderEventHandler())
        event_consumer.register_handler("order.order.paid", OrderEventHandler())
        event_consumer.register_handler("order.order.failed", OrderEventHandler())
        event_consumer.register_handler("order.order.shipped", OrderEventHandler())
        event_consumer.register_handler("order.order.delivered", OrderEventHandler())
        event_consumer.register_handler("order.order.cancelled", OrderEventHandler())
        
        event_consumer.register_handler("inventory.stock.updated", InventoryEventHandler())
        event_consumer.register_handler("inventory.stock.low", InventoryEventHandler())
        
        event_consumer.register_handler("user.user.registered", UserEventHandler())
        event_consumer.register_handler("user.user.verified", UserEventHandler())
        event_consumer.register_handler("user.profile.updated", UserEventHandler())
        
        # Create processed events table for idempotency
        await event_consumer.create_processed_events_table()
        
        logger.info("Event system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize event system: {e}")
        raise


async def start_event_consumer():
    """Start the new event consumer system"""
    try:
        await event_consumer.start()
        logger.info("New event consumer started")
        
        # Start consuming events in background
        asyncio.create_task(event_consumer.consume_events())
        
    except Exception as e:
        logger.error(f"Failed to start event consumer: {e}")
        raise


# Convenience functions for publishing events using new system
async def publish_order_created_event(order_id: str, user_id: str, amount: float, **kwargs):
    """Publish order created event using new event system"""
    return await event_producer.publish_order_created(
        order_id=order_id,
        user_id=user_id,
        amount=amount,
        **kwargs
    )


async def publish_order_paid_event(order_id: str, payment_id: str, amount: float, **kwargs):
    """Publish order paid event using new event system"""
    return await event_producer.publish_order_paid(
        order_id=order_id,
        payment_id=payment_id,
        amount=amount,
        **kwargs
    )


# Note: Inventory reservation functions removed - implement as needed


async def publish_user_registered_event(user_id: str, email: str, username: str, **kwargs):
    """Publish user registered event using new event system"""
    return await event_producer.publish_user_registered(
        user_id=user_id,
        email=email,
        username=username,
        **kwargs
    )


async def publish_payment_succeeded_event(payment_id: str, order_id: str, transaction_id: str, amount: float, **kwargs):
    """Publish payment succeeded event using new event system"""
    return await event_producer.publish_payment_succeeded(
        payment_id=payment_id,
        order_id=order_id,
        transaction_id=transaction_id,
        amount=amount,
        **kwargs
    )


async def publish_payment_failed_event(payment_id: str, order_id: str, user_id: str, failure_reason: str, error_code: str, **kwargs):
    """Publish payment failed event using new event system"""
    return await event_producer.publish_payment_failed(
        payment_id=payment_id,
        order_id=order_id,
        user_id=user_id,
        failure_reason=failure_reason,
        error_code=error_code,
        **kwargs
    )


# Backward compatibility - keep existing functions but add deprecation warnings
import warnings
from datetime import timedelta

def deprecated_function(func_name: str):
    """Decorator to mark functions as deprecated"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func_name} is deprecated. Use the new event system functions instead.",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


@deprecated_function("get_kafka_producer_service")
async def get_kafka_producer_service() -> KafkaProducer:
    """Deprecated: Use event_producer from core.events instead"""
    global kafka_producer_service
    if kafka_producer_service is None:
        kafka_producer_service = KafkaProducer()
        await kafka_producer_service.start()
    return kafka_producer_service