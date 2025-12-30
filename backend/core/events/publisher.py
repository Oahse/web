"""
Event Publisher Module - Handles publishing events to message broker
"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from aiokafka import AIOKafkaProducer

from core.config import settings
from .simple_event import SimpleEvent

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Event publisher for publishing events to Kafka message broker
    """
    
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self._is_started = False
    
    async def start(self):
        """Start the Kafka producer"""
        if not self._is_started:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                retry_backoff_ms=settings.KAFKA_RETRY_BACKOFF_MS,
                request_timeout_ms=settings.KAFKA_REQUEST_TIMEOUT_MS,
                compression_type=settings.KAFKA_COMPRESSION_TYPE,
                batch_size=settings.KAFKA_BATCH_SIZE,
                linger_ms=settings.KAFKA_LINGER_MS
            )
            await self.producer.start()
            self._is_started = True
            logger.info("Event publisher started successfully")
    
    async def stop(self):
        """Stop the Kafka producer"""
        if self.producer and self._is_started:
            await self.producer.stop()
            self._is_started = False
            logger.info("Event publisher stopped")
    
    async def _publish_event(
        self,
        topic: str,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        key: Optional[str] = None
    ) -> bool:
        """
        Internal method to publish event to Kafka
        """
        try:
            if not self._is_started:
                await self.start()
            
            # Create event object
            event = SimpleEvent(
                event_type=event_type,
                data=data,
                correlation_id=correlation_id,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Publish to Kafka
            await self.producer.send_and_wait(
                topic=topic,
                value=event.to_dict(),
                key=key or correlation_id
            )
            
            logger.info(
                f"Published event: {event_type} to topic: {topic} "
                f"with correlation_id: {correlation_id}"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to publish event {event_type} to {topic}: {e}",
                exc_info=True
            )
            return False
    
    async def publish_payment_event(
        self,
        event_type: str,
        payment_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish payment event to message broker
        
        Args:
            event_type: Type of payment event (e.g., 'payment.created', 'payment.completed')
            payment_data: Payment data to include in event
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        return await self._publish_event(
            topic=settings.KAFKA_TOPIC_PAYMENT,
            event_type=event_type,
            data=payment_data,
            correlation_id=correlation_id,
            key=payment_data.get('payment_id') or payment_data.get('id')
        )
    
    async def publish_order_event(
        self,
        event_type: str,
        order_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish order event to message broker
        
        Args:
            event_type: Type of order event (e.g., 'order.created', 'order.completed')
            order_data: Order data to include in event
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        return await self._publish_event(
            topic=settings.KAFKA_TOPIC_ORDER,
            event_type=event_type,
            data=order_data,
            correlation_id=correlation_id,
            key=order_data.get('order_id') or order_data.get('id')
        )
    
    async def publish_user_event(
        self,
        event_type: str,
        user_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish user event to message broker
        
        Args:
            event_type: Type of user event (e.g., 'user.registered', 'user.verified')
            user_data: User data to include in event
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        return await self._publish_event(
            topic=settings.KAFKA_TOPIC_NOTIFICATION,  # User events go to notification topic
            event_type=event_type,
            data=user_data,
            correlation_id=correlation_id,
            key=user_data.get('user_id') or user_data.get('id')
        )
    
    async def publish_inventory_event(
        self,
        event_type: str,
        inventory_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish inventory event to message broker
        
        Args:
            event_type: Type of inventory event (e.g., 'inventory.updated', 'inventory.low')
            inventory_data: Inventory data to include in event
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        return await self._publish_event(
            topic=settings.KAFKA_TOPIC_INVENTORY,
            event_type=event_type,
            data=inventory_data,
            correlation_id=correlation_id,
            key=inventory_data.get('product_id') or inventory_data.get('variant_id')
        )
    
    async def publish_notification_event(
        self,
        event_type: str,
        notification_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish notification event to message broker
        
        Args:
            event_type: Type of notification event (e.g., 'notification.created', 'notification.sent')
            notification_data: Notification data to include in event
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        return await self._publish_event(
            topic=settings.KAFKA_TOPIC_NOTIFICATION,
            event_type=event_type,
            data=notification_data,
            correlation_id=correlation_id,
            key=notification_data.get('user_id')
        )
    
    async def publish_cart_event(
        self,
        event_type: str,
        cart_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish cart event to message broker
        
        Args:
            event_type: Type of cart event (e.g., 'cart.updated', 'cart.abandoned')
            cart_data: Cart data to include in event
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        return await self._publish_event(
            topic=settings.KAFKA_TOPIC_CART,
            event_type=event_type,
            data=cart_data,
            correlation_id=correlation_id,
            key=cart_data.get('cart_id') or cart_data.get('user_id')
        )
    
    async def publish_negotiation_event(
        self,
        event_type: str,
        negotiation_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish negotiation event to message broker
        
        Args:
            event_type: Type of negotiation event (e.g., 'negotiation.started', 'negotiation.completed')
            negotiation_data: Negotiation data to include in event
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        return await self._publish_event(
            topic=settings.KAFKA_TOPIC_NEGOTIATION,
            event_type=event_type,
            data=negotiation_data,
            correlation_id=correlation_id,
            key=negotiation_data.get('negotiation_id') or negotiation_data.get('id')
        )


# Global event publisher instance
event_publisher = EventPublisher()


# Convenience functions for backward compatibility with message_broker.py
async def publish_payment_event(
    event_type: str,
    payment_data: Dict[str, Any],
    correlation_id: Optional[str] = None
) -> bool:
    """
    Publish payment event to message broker
    
    This function provides backward compatibility with the old message_broker.py
    """
    return await event_publisher.publish_payment_event(
        event_type=event_type,
        payment_data=payment_data,
        correlation_id=correlation_id
    )


async def publish_order_event(
    event_type: str,
    order_data: Dict[str, Any],
    correlation_id: Optional[str] = None
) -> bool:
    """
    Publish order event to message broker
    
    This function provides backward compatibility with the old message_broker.py
    """
    return await event_publisher.publish_order_event(
        event_type=event_type,
        order_data=order_data,
        correlation_id=correlation_id
    )