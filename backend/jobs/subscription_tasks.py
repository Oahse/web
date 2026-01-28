"""
Background tasks for subscription management using Hybrid approach
Handles periodic order placement and subscription lifecycle
Uses ARQ for scheduled processing and FastAPI BackgroundTasks for immediate tasks
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID
from fastapi import BackgroundTasks

from lib.db import get_db
from lib.config import settings
from core.hybrid_tasks import hybrid_task_manager, send_email_hybrid, send_notification_hybrid
from lib.arq_worker import enqueue_subscription_processing, enqueue_subscription_renewal
from services.subscriptions.subscription_scheduler import SubscriptionSchedulerService

logger = logging.getLogger(__name__)


class SubscriptionTaskManager:
    """Manages background tasks for subscription operations using hybrid approach"""
    
    def __init__(self):
        self.is_running = False
        self.check_interval_minutes = 60  # Check every hour
        
    async def start_subscription_scheduler(self):
        """Start the subscription order scheduler using ARQ"""
        if self.is_running:
            logger.warning("Subscription scheduler is already running")
            return
        
        self.is_running = True
        logger.info("Starting subscription order scheduler with ARQ")
        
        while self.is_running:
            try:
                # Use ARQ for scheduled processing
                await enqueue_subscription_processing()
                await asyncio.sleep(self.check_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in subscription scheduler: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    def stop_subscription_scheduler(self):
        """Stop the subscription scheduler"""
        self.is_running = False
        logger.info("Subscription scheduler stopped")
    
    async def process_subscription_renewal_immediate(
        self,
        background_tasks: BackgroundTasks,
        subscription_id: str,
        **kwargs
    ):
        """Process subscription renewal immediately using FastAPI BackgroundTasks"""
        hybrid_task_manager.add_subscription_renewal_task(
            background_tasks,
            subscription_id,
            **kwargs
        )
    
    async def schedule_subscription_renewal(
        self,
        subscription_id: str,
        delay_hours: int = 0,
        **kwargs
    ):
        """Schedule subscription renewal using ARQ"""
        if delay_hours > 0:
            # Use ARQ for delayed processing
            from lib.arq_worker import get_arq_pool
            pool = await get_arq_pool()
            await pool.enqueue_job(
                'process_subscription_renewal_task',
                subscription_id,
                _defer_by=timedelta(hours=delay_hours),
                **kwargs
            )
        else:
            # Use ARQ for immediate processing
            await enqueue_subscription_renewal(subscription_id, **kwargs)
    
    async def send_subscription_notification(
        self,
        background_tasks: Optional[BackgroundTasks],
        user_id: str,
        notification_type: str,
        use_arq: bool = False,
        **kwargs
    ):
        """Send subscription notification using hybrid approach"""
        await send_notification_hybrid(
            background_tasks,
            user_id,
            notification_type,
            use_arq,
            **kwargs
        )
    
    async def send_subscription_email(
        self,
        background_tasks: Optional[BackgroundTasks],
        email_type: str,
        recipient: str,
        use_arq: bool = True,  # Email tasks usually use ARQ for reliability
        **kwargs
    ):
        """Send subscription email using hybrid approach"""
        await send_email_hybrid(
            background_tasks,
            email_type,
            recipient,
            use_arq,
            **kwargs
        )
    
    async def _process_subscription_orders(self):
        """Process subscriptions due for order placement"""
        async for db in get_db():
            try:
                scheduler = SubscriptionSchedulerService(db)
                result = await scheduler.process_due_subscriptions()
                
                logger.info(f"Subscription processing result: {result}")
                
                # Send Kafka notifications for each processed order
                for order_result in result["results"]:
                    if order_result["status"] == "success":
                        await self._send_order_created_notification(order_result)
                    else:
                        await self._send_order_failed_notification(order_result)
                
                # Send summary notification to admin if there were failures
                if result["failed_count"] > 0:
                    await self._send_admin_failure_notification(result)
                
            except Exception as e:
                logger.error(f"Error processing subscription orders: {e}")
            finally:
                await db.close()
    
    async def _send_order_created_notification(self, order_result: Dict[str, Any]):
        """Send order created notification via Kafka"""
        try:
            await self.initialize_kafka()
            
            # Send order event
            await self.producer.send_order_notification(
                user_id=order_result.get("user_id", ""),
                order_id=order_result["order_id"],
                event_type="subscription_order_created",
                order_data={
                    "subscription_id": order_result["subscription_id"],
                    "order_type": "subscription_recurring",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Sent order created notification for order {order_result['order_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send order created notification: {e}")
    
    async def _send_order_failed_notification(self, order_result: Dict[str, Any]):
        """Send order failed notification via Kafka"""
        try:
            await self.initialize_kafka()
            
            # Log failed order (notification system removed)
            logger.error(f"Failed to create subscription order for user {order_result.get('user_id', '')}: {order_result.get('reason', 'Unknown error')}")
            
            await self.producer.send_message(
                topic=settings.KAFKA_TOPIC_NOTIFICATION,
                value=notification_message,
                key=order_result.get("user_id", "")
            )
            
            logger.info(f"Sent order failed notification for subscription {order_result['subscription_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send order failed notification: {e}")
    
    async def _send_admin_failure_notification(self, result: Dict[str, Any]):
        """Send notification to admin about subscription processing failures via Kafka"""
        try:
            await self.initialize_kafka()
            
            # Send email notification to admin
            email_message = {
                "task": "send_admin_notification_email",
                "args": [
                    "Subscription Order Processing Failures",
                    f"Subscription processing had {result['failed_count']} failures out of {result['total_due']} due subscriptions."
                ]
            }
            
            await self.producer.send_message(
                topic=settings.KAFKA_TOPIC_EMAIL,
                value=email_message,
                key="admin_notification"
            )
            
            logger.info(f"Sent admin failure notification: {result['failed_count']} failures")
            
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
    
    async def schedule_order_notifications(self):
        """Schedule order notifications via Kafka"""
        try:
            await self.initialize_kafka()
            
            message = {
                "task": "send_subscription_order_notifications",
                "scheduled_at": datetime.utcnow().isoformat(),
                "event_type": "subscription_order_notifications"
            }
            
            await self.producer.send_message(
                topic=settings.KAFKA_TOPIC_NOTIFICATION,
                value=message,
                key="subscription_order_notifications"
            )
            
            logger.info("Scheduled subscription order notifications via Kafka")
            
        except Exception as e:
            logger.error(f"Failed to schedule order notifications: {e}")
    
    async def process_upcoming_order_notifications(self):
        """Process and send notifications about upcoming orders"""
        async for db in get_db():
            try:
                # Get subscriptions due in next 3 days
                upcoming_orders = await self._get_upcoming_subscription_orders(db, days_ahead=3)
                
                notifications_sent = 0
                
                for order_info in upcoming_orders:
                    days_until = order_info["days_until_order"]
                    
                    # Send notification for subscriptions due in 3 days, 1 day, or today
                    if days_until in [3, 1, 0]:
                        try:
                            await self._send_upcoming_order_notification(order_info, days_until)
                            notifications_sent += 1
                        except Exception as e:
                            logger.error(f"Failed to send notification for subscription {order_info['subscription_id']}: {e}")
                
                logger.info(f"Sent {notifications_sent} upcoming order notifications")
                
                return {
                    "status": "completed",
                    "notifications_sent": notifications_sent,
                    "processed_at": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error processing upcoming order notifications: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "processed_at": datetime.utcnow().isoformat()
                }
            finally:
                await db.close()
    
    async def _get_upcoming_subscription_orders(self, db, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming subscription orders"""
        from sqlalchemy import select, and_
        from sqlalchemy.orm import selectinload
        from models.subscriptions import Subscription
        
        end_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        query = select(Subscription).where(
            and_(
                Subscription.status == "active",
                Subscription.auto_renew == True,
                Subscription.next_billing_date <= end_date
            )
        ).options(selectinload(Subscription.user))
        
        result = await db.execute(query)
        subscriptions = result.scalars().all()
        
        schedule = []
        for subscription in subscriptions:
            schedule.append({
                "subscription_id": str(subscription.id),
                "user_id": str(subscription.user_id),
                "user_email": subscription.user.email if subscription.user else None,
                "plan_id": subscription.plan_id,
                "next_billing_date": subscription.next_billing_date.isoformat(),
                "amount": subscription.price,
                "currency": subscription.currency,
                "billing_cycle": subscription.billing_cycle,
                "days_until_order": (subscription.next_billing_date - datetime.utcnow()).days,
                "product_count": len(subscription.variant_ids or [])
            })
        
        return sorted(schedule, key=lambda x: x["next_billing_date"])
    
    async def _send_upcoming_order_notification(self, order_info: dict, days_until: int):
        """Send upcoming order notification via Kafka"""
        try:
            await self.initialize_kafka()
            
            if days_until == 0:
                message = f"Your subscription order will be placed today! Total: {order_info['amount']} {order_info['currency']} for {order_info['product_count']} item(s)."
                notification_type = "info"
            elif days_until == 1:
                message = f"Your subscription order will be placed tomorrow! Total: {order_info['amount']} {order_info['currency']} for {order_info['product_count']} item(s)."
                notification_type = "info"
            else:  # days_until == 3
                message = f"Your subscription order will be placed in {days_until} days. Total: {order_info['amount']} {order_info['currency']} for {order_info['product_count']} item(s)."
                notification_type = "info"
            
            # Log subscription status (notification system removed)
            logger.info(f"Subscription status for user {order_info['user_id']}: {message}")
            
            await self.producer.send_message(
                topic=settings.KAFKA_TOPIC_NOTIFICATION,
                value=notification_message,
                key=order_info["user_id"]
            )
            
            logger.info(f"Sent upcoming order notification to user {order_info['user_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send upcoming order notification: {e}")


# Global instance
subscription_task_manager = SubscriptionTaskManager()


# Kafka message handlers for subscription tasks
async def handle_subscription_task_message(message_data: dict, db):
    """Handle subscription task messages from Kafka"""
    
    task = message_data.get("task")
    
    if task == "send_subscription_order_notifications":
        return await subscription_task_manager.process_upcoming_order_notifications()
    else:
        logger.warning(f"Unknown subscription task: {task}")
        return {"status": "unknown_task", "task": task}


# Task functions for FastAPI BackgroundTasks (keeping for backward compatibility)
def process_subscription_renewal(
    background_tasks: BackgroundTasks,
    subscription_id: str,
    user_email: str,
    user_name: str
):
    """Process subscription order creation and send confirmation"""
    background_tasks.add_task(_handle_subscription_order_creation, subscription_id, user_email, user_name)


async def _handle_subscription_order_creation(subscription_id: str, user_email: str, user_name: str):
    """Handle subscription order creation process"""
    try:
        async for db in get_db():
            try:
                scheduler = SubscriptionSchedulerService(db)
                # Process specific subscription
                logger.info(f"Processing order creation for subscription {subscription_id}")
                
                # Send order confirmation email via Kafka
                producer = await get_kafka_producer_service()
                
                email_data = {
                    "task": "send_subscription_order_email",
                    "args": [user_email, {
                        "customer_name": user_name,
                        "subscription_id": subscription_id,
                        "order_date": datetime.utcnow(),
                        "company_name": "Banwee",
                        "support_email": "support@banwee.com"
                    }]
                }
                
                await producer.send_message(
                    topic=settings.KAFKA_TOPIC_EMAIL,
                    value=email_data,
                    key=user_email
                )
                
            finally:
                await db.close()
                
    except Exception as e:
        logger.error(f"Failed to process subscription order creation {subscription_id}: {e}")


def send_subscription_shipment_notification(
    background_tasks: BackgroundTasks,
    user_email: str,
    user_name: str,
    order_number: str,
    tracking_number: str = None
):
    """Send shipment notification for subscription order via Kafka"""
    background_tasks.add_task(_send_shipment_notification_kafka, user_email, user_name, order_number, tracking_number)


async def _send_shipment_notification_kafka(user_email: str, user_name: str, order_number: str, tracking_number: str = None):
    """Send shipment notification via Kafka"""
    try:
        producer = await get_kafka_producer_service()
        
        email_data = {
            "task": "send_subscription_shipment_email",
            "args": [user_email, {
                "customer_name": user_name,
                "order_number": order_number,
                "tracking_number": tracking_number,
                "shipment_date": datetime.utcnow(),
                "company_name": "Banwee",
                "support_email": "support@banwee.com"
            }]
        }
        
        await producer.send_message(
            topic=settings.KAFKA_TOPIC_EMAIL,
            value=email_data,
            key=user_email
        )
        
    except Exception as e:
        logger.error(f"Failed to send shipment notification via Kafka: {e}")


def send_subscription_pause_notification(
    background_tasks: BackgroundTasks,
    user_email: str,
    user_name: str,
    subscription_id: str,
    pause_reason: str = None
):
    """Send notification when subscription is paused via Kafka"""
    background_tasks.add_task(_send_pause_notification_kafka, user_email, user_name, subscription_id, pause_reason)


async def _send_pause_notification_kafka(user_email: str, user_name: str, subscription_id: str, pause_reason: str = None):
    """Send pause notification via Kafka"""
    try:
        producer = await get_kafka_producer_service()
        
        email_data = {
            "task": "send_subscription_paused_email",
            "args": [user_email, {
                "customer_name": user_name,
                "subscription_id": subscription_id,
                "pause_reason": pause_reason or "User requested",
                "pause_date": datetime.utcnow(),
                "company_name": "Banwee",
                "support_email": "support@banwee.com"
            }]
        }
        
        await producer.send_message(
            topic=settings.KAFKA_TOPIC_EMAIL,
            value=email_data,
            key=user_email
        )
        
    except Exception as e:
        logger.error(f"Failed to send pause notification via Kafka: {e}")


def send_subscription_resume_notification(
    background_tasks: BackgroundTasks,
    user_email: str,
    user_name: str,
    subscription_id: str,
    next_shipment_date: datetime
):
    """Send notification when subscription is resumed via Kafka"""
    background_tasks.add_task(_send_resume_notification_kafka, user_email, user_name, subscription_id, next_shipment_date)


async def _send_resume_notification_kafka(user_email: str, user_name: str, subscription_id: str, next_shipment_date: datetime):
    """Send resume notification via Kafka"""
    try:
        producer = await get_kafka_producer_service()
        
        email_data = {
            "task": "send_subscription_resumed_email",
            "args": [user_email, {
                "customer_name": user_name,
                "subscription_id": subscription_id,
                "resume_date": datetime.utcnow(),
                "next_shipment_date": next_shipment_date,
                "company_name": "Banwee",
                "support_email": "support@banwee.com"
            }]
        }
        
        await producer.send_message(
            topic=settings.KAFKA_TOPIC_EMAIL,
            value=email_data,
            key=user_email
        )
        
    except Exception as e:
        logger.error(f"Failed to send resume notification via Kafka: {e}")


# Manual trigger functions
async def trigger_subscription_order_processing():
    """Manually trigger subscription order processing"""
    await subscription_task_manager._process_subscription_orders()


async def trigger_order_notifications():
    """Manually trigger order notifications"""
    await subscription_task_manager.schedule_order_notifications()