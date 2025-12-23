"""
Kafka consumer tasks for order processing
"""
import asyncio # ADDED for async operations within tasks
from sqlalchemy import select
from uuid import UUID

from models.order import Order
from core.config import settings # ADDED for Kafka topics
from core.kafka import KafkaProducer, get_kafka_producer_service # ADDED for Kafka dispatch
from services.email import EmailService # Import EmailService to encapsulate logic
from services.notification import NotificationService # Import NotificationService to encapsulate logic
from sqlalchemy.ext.asyncio import AsyncSession # Directly use AsyncSession from consumer


async def process_order_confirmation(db: AsyncSession, order_id: str):
    """
    Process order confirmation - send email and create notification via Kafka
    """
    try:
        # Verify order exists
        result = await db.execute(
            select(Order).where(Order.id == UUID(order_id))
        )
        order = result.scalar_one_or_none()
        
        if not order:
            print(f"Order {order_id} not found")
            return

        # Dispatch email confirmation via Kafka
        producer_service = await get_kafka_producer_service()
        await producer_service.send_message(settings.KAFKA_TOPIC_EMAIL, {
            "service": "EmailService",
            "method": "send_order_confirmation",
            "args": [str(order.id)]
        })
        
        # Dispatch notification via Kafka
        await producer_service.send_message(settings.KAFKA_TOPIC_NOTIFICATION, {
            "service": "NotificationService",
            "method": "create_notification",
            "args": [],
            "kwargs": {
                "user_id": str(order.user_id),
                "message": f"Your order #{order_id[:8]}... has been confirmed!",
                "type": "success",
                "related_id": order_id
            }
        })
        
        print(f"✅ Order confirmation processed via Kafka for {order_id}")
        
    except Exception as e:
        print(f"❌ Failed to process order confirmation via Kafka: {e}")
        raise


async def process_shipping_update(db: AsyncSession, order_id: str, carrier_name: str):
    """
    Process shipping update - send email and create notification via Kafka
    """
    try:
        # Verify order exists
        result = await db.execute(
            select(Order).where(Order.id == UUID(order_id))
        )
        order = result.scalar_one_or_none()
        
        if not order:
            print(f"Order {order_id} not found")
            return
        
        # Dispatch shipping update email via Kafka
        producer_service = await get_kafka_producer_service()
        await producer_service.send_message(settings.KAFKA_TOPIC_EMAIL, {
            "service": "EmailService",
            "method": "send_shipping_update",
            "args": [str(order.id), carrier_name, order.tracking_number] # Need order.tracking_number
        })
        
        # Dispatch notification via Kafka
        await producer_service.send_message(settings.KAFKA_TOPIC_NOTIFICATION, {
            "service": "NotificationService",
            "method": "create_notification",
            "args": [],
            "kwargs": {
                "user_id": str(order.user_id),
                "message": f"Your order #{order_id[:8]}... has been shipped via {carrier_name}!",
                "type": "info",
                "related_id": order_id
            }
        })
        
        print(f"✅ Shipping update processed via Kafka for {order_id}")
        
    except Exception as e:
        print(f"❌ Failed to process shipping update via Kafka: {e}")
        raise


async def process_order_delivered(db: AsyncSession, order_id: str):
    """
    Process order delivered - send email and create notification via Kafka
    """
    try:
        # Verify order exists
        result = await db.execute(
            select(Order).where(Order.id == UUID(order_id))
        )
        order = result.scalar_one_or_none()
        
        if not order:
            print(f"Order {order_id} not found")
            return
        
        # Dispatch delivered email via Kafka
        producer_service = await get_kafka_producer_service()
        await producer_service.send_message(settings.KAFKA_TOPIC_EMAIL, {
            "service": "EmailService",
            "method": "send_order_delivered",
            "args": [str(order.id)]
        })
        
        # Dispatch notification via Kafka
        await producer_service.send_message(settings.KAFKA_TOPIC_NOTIFICATION, {
            "service": "NotificationService",
            "method": "create_notification",
            "args": [],
            "kwargs": {
                "user_id": str(order.user_id),
                "message": f"Your order #{order_id[:8]}... has been delivered!",
                "type": "success",
                "related_id": order_id
                }
            })
        
        print(f"✅ Order delivered processed via Kafka for {order_id}")
        
    except Exception as e:
        print(f"❌ Failed to process order delivered via Kafka: {e}")
        raise
