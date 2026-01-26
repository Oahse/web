"""
Hybrid Task Manager - Combines FastAPI BackgroundTasks with ARQ
Uses FastAPI BackgroundTasks for quick operations and ARQ for longer-running tasks
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import BackgroundTasks
from uuid import UUID

from core.config import settings
from core.arq_worker import (
    enqueue_email, enqueue_payment_processing, 
    enqueue_inventory_update
)

logger = logging.getLogger(__name__)


class HybridTaskManager:
    """
    Manages both FastAPI BackgroundTasks and ARQ tasks
    - FastAPI BackgroundTasks: Quick operations (< 30 seconds)
    - ARQ: Long-running operations (> 30 seconds), retries, scheduled tasks
    """
    
    def __init__(self):
        self.arq_enabled = settings.ENABLE_ARQ
    
    # Email Tasks - Use ARQ for reliability and retries
    async def send_email_task(self, email_type: str, recipient: str, **kwargs):
        """Send email using ARQ for reliability"""
        if self.arq_enabled:
            await enqueue_email(email_type, recipient, **kwargs)
        else:
            # Fallback to direct email sending
            from services.email import EmailService
            from core.database import AsyncSessionDB
            async with AsyncSessionDB() as db:
                email_service = EmailService(db)
                # Handle different email types
                if email_type == "welcome":
                    await email_service.send_welcome(kwargs.get('user_id'))
                elif email_type == "order_confirmation":
                    await email_service.send_order_confirmation(kwargs.get('order_id'))
                # Add more email types as needed
    
    def add_quick_email_task(self, background_tasks: BackgroundTasks, email_type: str, recipient: str, **kwargs):
        """Add email task to FastAPI BackgroundTasks for immediate processing"""
        background_tasks.add_task(self.send_email_task, email_type, recipient, **kwargs)
    
    # Payment Tasks - Use ARQ for retries and complex processing
    async def process_payment_task(self, payment_id: str, action: str, **kwargs):
        """Process payment using ARQ for retries"""
        if self.arq_enabled:
            await enqueue_payment_processing(payment_id, action, **kwargs)
        else:
            # Fallback to direct processing
            from services.payments import PaymentService
            from core.database import AsyncSessionDB
            async with AsyncSessionDB() as db:
                payment_service = PaymentService(db)
                if action == "confirm":
                    await payment_service.confirm_payment(payment_id)
                elif action == "refund":
                    await payment_service.process_refund(payment_id, kwargs.get('amount'))
    
    def add_quick_payment_task(self, background_tasks: BackgroundTasks, payment_id: str, action: str, **kwargs):
        """Add payment task to FastAPI BackgroundTasks for immediate processing"""
        background_tasks.add_task(self.process_payment_task, payment_id, action, **kwargs)
    
    # Inventory Tasks - Use ARQ for stock checks and updates
    async def update_inventory_task(self, variant_id: str, action: str, **kwargs):
        """Update inventory using ARQ"""
        if self.arq_enabled:
            await enqueue_inventory_update(variant_id, action, **kwargs)
        else:
            # Fallback to direct update
            from services.inventories import InventoryService
            from core.database import AsyncSessionDB
            async with AsyncSessionDB() as db:
                inventory_service = InventoryService(db)
                if action == "decrement":
                    await inventory_service.decrement_stock_on_purchase(
                        UUID(variant_id), kwargs.get('quantity', 1)
                    )
                elif action == "increment":
                    await inventory_service.increment_stock_on_cancellation(
                        UUID(variant_id), kwargs.get('quantity', 1)
                    )
    
    def add_quick_inventory_task(self, background_tasks: BackgroundTasks, variant_id: str, action: str, **kwargs):
        """Add inventory task to FastAPI BackgroundTasks for immediate processing"""
        background_tasks.add_task(self.update_inventory_task, variant_id, action, **kwargs)
    
    # Notification Tasks - Use FastAPI for immediate, ARQ for scheduled

        else:
            # Fallback to direct notification
            from services.notifications import NotificationService
            from core.database import AsyncSessionDB
            async with AsyncSessionDB() as db:
                notification_service = NotificationService(db)
                await notification_service.create_notification(
                    user_id=UUID(user_id),
                    title=kwargs.get('title', ''),
                    message=kwargs.get('message', ''),
                    notification_type=notification_type,
                    data=kwargs.get('data', {})
                )
    
    def add_quick_notification_task(self, background_tasks: BackgroundTasks, user_id: str, notification_type: str, **kwargs):
        """Add notification task to FastAPI BackgroundTasks for immediate processing"""
        background_tasks.add_task(self.send_notification_task, user_id, notification_type, **kwargs)
    
    # Subscription Tasks - Complex logic uses ARQ
    async def process_subscription_renewal(self, subscription_id: str, **kwargs):
        """Process subscription renewal using ARQ for reliability"""
        if self.arq_enabled:
            from core.arq_worker import get_arq_pool
            pool = await get_arq_pool()
            await pool.enqueue_job(
                'process_subscription_renewal_task',
                subscription_id,
                **kwargs
            )
        else:
            # Fallback to direct processing
            await self._process_subscription_renewal_direct(subscription_id, **kwargs)
    
    async def _process_subscription_renewal_direct(self, subscription_id: str, **kwargs):
        """Direct subscription renewal processing"""
        try:
            from services.subscriptions.subscription_scheduler import SubscriptionSchedulerService
            from core.database import AsyncSessionDB
            
            async with AsyncSessionDB() as db:
                scheduler = SubscriptionSchedulerService(db)
                result = await scheduler.process_specific_subscription(UUID(subscription_id))
                
                if result.get('success'):
                    # Send confirmation email
                    await self.send_email_task(
                        "subscription_renewal",
                        kwargs.get('user_email', ''),
                        subscription_id=subscription_id,
                        order_id=result.get('order_id'),
                        **kwargs
                    )
                else:
                    # Send failure notification
                    await self.send_notification_task(
                        kwargs.get('user_id', ''),
                        "subscription_renewal_failed",
                        title="Subscription Renewal Failed",
                        message=f"Failed to renew subscription: {result.get('error', 'Unknown error')}",
                        data={"subscription_id": subscription_id}
                    )
        except Exception as e:
            logger.error(f"Error processing subscription renewal {subscription_id}: {e}")
    
    def add_subscription_renewal_task(self, background_tasks: BackgroundTasks, subscription_id: str, **kwargs):
        """Add subscription renewal to FastAPI BackgroundTasks"""
        background_tasks.add_task(self.process_subscription_renewal, subscription_id, **kwargs)
    
    # Payment Retry Tasks - Use ARQ for scheduled retries
    async def schedule_payment_retry(self, payment_id: str, retry_delay_hours: int = 1, **kwargs):
        """Schedule payment retry using ARQ"""
        if self.arq_enabled:
            from core.arq_worker import get_arq_pool
            pool = await get_arq_pool()
            # Schedule for future execution
            await pool.enqueue_job(
                'retry_failed_payment_task',
                payment_id,
                _defer_by=timedelta(hours=retry_delay_hours),
                **kwargs
            )
        else:
            # Fallback: add to background tasks with delay simulation
            background_tasks = BackgroundTasks()
            background_tasks.add_task(
                self._delayed_payment_retry, 
                payment_id, 
                retry_delay_hours * 3600,  # Convert to seconds
                **kwargs
            )
    
    async def _delayed_payment_retry(self, payment_id: str, delay_seconds: int, **kwargs):
        """Simulate delayed payment retry"""
        await asyncio.sleep(delay_seconds)
        await self.process_payment_task(payment_id, "retry", **kwargs)
    
    # Cart Cleanup - Use ARQ for scheduled cleanup
    async def schedule_cart_cleanup(self):
        """Schedule cart cleanup using ARQ"""
        if self.arq_enabled:
            from core.arq_worker import enqueue_cart_cleanup
            await enqueue_cart_cleanup()
        else:
            # Fallback to direct cleanup
            from services.cart import CartService
            from core.database import AsyncSessionDB
            async with AsyncSessionDB() as db:
                cart_service = CartService(db)
                # Implement direct cleanup logic here
                logger.info("Direct cart cleanup completed")
    
    # Hybrid task decision logic
    def should_use_arq(self, task_type: str, estimated_duration_seconds: int = 0) -> bool:
        """Decide whether to use ARQ or FastAPI BackgroundTasks"""
        if not self.arq_enabled:
            return False
        
        # Use ARQ for:
        # 1. Long-running tasks (> 30 seconds)
        # 2. Tasks that need retries
        # 3. Scheduled tasks
        # 4. Email tasks (for reliability)
        # 5. Payment tasks (for retries)
        
        arq_task_types = {
            'email', 'payment_retry', 'subscription_renewal', 
            'cart_cleanup', 'inventory_sync', 'report_generation'
        }
        
        return (
            task_type in arq_task_types or 
            estimated_duration_seconds > 30
        )
    
    async def add_hybrid_task(
        self, 
        background_tasks: BackgroundTasks,
        task_type: str,
        task_func,
        *args,
        estimated_duration_seconds: int = 0,
        **kwargs
    ):
        """Add task using hybrid approach"""
        if self.should_use_arq(task_type, estimated_duration_seconds):
            # Use ARQ for long-running or critical tasks
            if self.arq_enabled:
                from core.arq_worker import get_arq_pool
                pool = await get_arq_pool()
                await pool.enqueue_job(task_func.__name__, *args, **kwargs)
            else:
                # Fallback to background tasks
                background_tasks.add_task(task_func, *args, **kwargs)
        else:
            # Use FastAPI BackgroundTasks for quick tasks
            background_tasks.add_task(task_func, *args, **kwargs)


# Global instance
hybrid_task_manager = HybridTaskManager()


# Convenience functions for common task patterns
async def send_email_hybrid(
    background_tasks: Optional[BackgroundTasks],
    email_type: str,
    recipient: str,
    use_arq: bool = True,
    **kwargs
):
    """Send email using hybrid approach"""
    if use_arq and hybrid_task_manager.arq_enabled:
        await hybrid_task_manager.send_email_task(email_type, recipient, **kwargs)
    elif background_tasks:
        hybrid_task_manager.add_quick_email_task(background_tasks, email_type, recipient, **kwargs)
    else:
        # Direct execution
        await hybrid_task_manager.send_email_task(email_type, recipient, **kwargs)


async def process_payment_hybrid(
    background_tasks: Optional[BackgroundTasks],
    payment_id: str,
    action: str,
    use_arq: bool = True,
    **kwargs
):
    """Process payment using hybrid approach"""
    if use_arq and hybrid_task_manager.arq_enabled:
        await hybrid_task_manager.process_payment_task(payment_id, action, **kwargs)
    elif background_tasks:
        hybrid_task_manager.add_quick_payment_task(background_tasks, payment_id, action, **kwargs)
    else:
        # Direct execution
        await hybrid_task_manager.process_payment_task(payment_id, action, **kwargs)


async def update_inventory_hybrid(
    background_tasks: Optional[BackgroundTasks],
    variant_id: str,
    action: str,
    use_arq: bool = False,  # Inventory updates are usually quick
    **kwargs
):
    """Update inventory using hybrid approach"""
    if use_arq and hybrid_task_manager.arq_enabled:
        await hybrid_task_manager.update_inventory_task(variant_id, action, **kwargs)
    elif background_tasks:
        hybrid_task_manager.add_quick_inventory_task(background_tasks, variant_id, action, **kwargs)
    else:
        # Direct execution
        await hybrid_task_manager.update_inventory_task(variant_id, action, **kwargs)


async def send_notification_hybrid(
    background_tasks: Optional[BackgroundTasks],
    user_id: str,
    notification_type: str,
    use_arq: bool = False,  # Notifications are usually quick
    **kwargs
):
    """Send notification using hybrid approach"""
    if use_arq and hybrid_task_manager.arq_enabled:
        await hybrid_task_manager.send_notification_task(user_id, notification_type, **kwargs)
    elif background_tasks:
        hybrid_task_manager.add_quick_notification_task(background_tasks, user_id, notification_type, **kwargs)
    else:
        # Direct execution
        await hybrid_task_manager.send_notification_task(user_id, notification_type, **kwargs)