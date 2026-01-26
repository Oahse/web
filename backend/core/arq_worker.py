"""
ARQ (Async Redis Queue) Worker Configuration
Replaces Kafka for background task processing
"""
import asyncio
import logging
from typing import Dict, Any
from arq import create_pool, Worker
from arq.connections import RedisSettings
from core.config import settings
from core.database import AsyncSessionDB

logger = logging.getLogger(__name__)

# ARQ Redis settings
ARQ_REDIS_SETTINGS = RedisSettings.from_dsn(settings.ARQ_REDIS_URL)

async def startup(ctx: Dict[str, Any]) -> None:
    """Worker startup - initialize database connection"""
    logger.info("ARQ Worker starting up...")
    # Store database session factory in context for tasks to use
    ctx['db_session'] = AsyncSessionDB

async def shutdown(ctx: Dict[str, Any]) -> None:
    """Worker shutdown - cleanup resources"""
    logger.info("ARQ Worker shutting down...")

# Background task functions
async def send_email_task(ctx: Dict[str, Any], email_type: str, recipient: str, **kwargs) -> str:
    """Send email background task"""
    try:
        from services.email import EmailService
        
        async with ctx['db_session']() as db:
            email_service = EmailService(db)
            
            if email_type == "welcome":
                await email_service.send_welcome_email(recipient, kwargs.get('user_name', ''))
            elif email_type == "order_confirmation":
                await email_service.send_order_confirmation_email(
                    recipient, 
                    kwargs.get('order_id'), 
                    kwargs.get('order_details', {})
                )
            elif email_type == "password_reset":
                await email_service.send_password_reset_email(
                    recipient, 
                    kwargs.get('reset_token', ''), 
                    kwargs.get('reset_link', '')
                )
            elif email_type == "low_stock_alert":
                await email_service.send_low_stock_alert(
                    recipient,
                    kwargs.get('product_name', ''),
                    kwargs.get('variant_name', ''),
                    kwargs.get('location_name', ''),
                    kwargs.get('current_stock', 0),
                    kwargs.get('threshold', 0)
                )
            else:
                logger.warning(f"Unknown email type: {email_type}")
                return f"Unknown email type: {email_type}"
        
        logger.info(f"Email sent successfully: {email_type} to {recipient}")
        return f"Email sent: {email_type} to {recipient}"
        
    except Exception as e:
        logger.error(f"Failed to send email {email_type} to {recipient}: {e}")
        raise

async def process_payment_task(ctx: Dict[str, Any], payment_id: str, action: str, **kwargs) -> str:
    """Process payment background task"""
    try:
        from services.payments import PaymentService
        
        async with ctx['db_session']() as db:
            payment_service = PaymentService(db)
            
            if action == "confirm":
                result = await payment_service.confirm_payment(payment_id)
            elif action == "refund":
                result = await payment_service.process_refund(
                    payment_id, 
                    kwargs.get('amount'), 
                    kwargs.get('reason', '')
                )
            elif action == "retry":
                result = await payment_service.retry_failed_payment(payment_id)
            else:
                logger.warning(f"Unknown payment action: {action}")
                return f"Unknown payment action: {action}"
        
        logger.info(f"Payment processed successfully: {action} for {payment_id}")
        return f"Payment {action} completed for {payment_id}"
        
    except Exception as e:
        logger.error(f"Failed to process payment {payment_id} with action {action}: {e}")
        raise

async def update_inventory_task(ctx: Dict[str, Any], variant_id: str, action: str, **kwargs) -> str:
    """Update inventory background task"""
    try:
        from services.inventories import InventoryService
        from uuid import UUID
        
        async with ctx['db_session']() as db:
            inventory_service = InventoryService(db)
            
            if action == "decrement":
                await inventory_service.decrement_stock_on_purchase(
                    UUID(variant_id), 
                    kwargs.get('quantity', 1)
                )
            elif action == "increment":
                await inventory_service.increment_stock_on_cancellation(
                    UUID(variant_id), 
                    kwargs.get('quantity', 1)
                )
            elif action == "check_low_stock":
                # Check if stock is low and send alerts
                inventory = await inventory_service.get_inventory_by_variant_id(UUID(variant_id))
                if inventory and inventory.quantity_available <= inventory.low_stock_threshold:
                    # Queue email alert
                    await send_email_task(
                        ctx,
                        "low_stock_alert",
                        kwargs.get('admin_email', 'admin@banwee.com'),
                        product_name=kwargs.get('product_name', ''),
                        variant_name=kwargs.get('variant_name', ''),
                        location_name=kwargs.get('location_name', ''),
                        current_stock=inventory.quantity_available,
                        threshold=inventory.low_stock_threshold
                    )
            else:
                logger.warning(f"Unknown inventory action: {action}")
                return f"Unknown inventory action: {action}"
        
        logger.info(f"Inventory updated successfully: {action} for {variant_id}")
        return f"Inventory {action} completed for {variant_id}"
        
    except Exception as e:
        logger.error(f"Failed to update inventory {variant_id} with action {action}: {e}")
        raise

async def send_notification_task(ctx: Dict[str, Any], user_id: str, notification_type: str, **kwargs) -> str:
    """Send notification background task"""
    try:
        from services.notifications import NotificationService
        from uuid import UUID
        
        async with ctx['db_session']() as db:
            notification_service = NotificationService(db)
            
            await notification_service.create_notification(
                user_id=UUID(user_id),
                title=kwargs.get('title', ''),
                message=kwargs.get('message', ''),
                notification_type=notification_type,
                data=kwargs.get('data', {})
            )
        
        logger.info(f"Notification sent successfully: {notification_type} to {user_id}")
        return f"Notification sent: {notification_type} to {user_id}"
        
    except Exception as e:
        logger.error(f"Failed to send notification {notification_type} to {user_id}: {e}")
        raise

async def process_subscription_renewal_task(ctx: Dict[str, Any], subscription_id: str, **kwargs) -> str:
    """Process subscription renewal background task"""
    try:
        from services.subscriptions.subscription_scheduler import SubscriptionSchedulerService
        from uuid import UUID
        
        async with ctx['db_session']() as db:
            scheduler = SubscriptionSchedulerService(db)
            result = await scheduler.process_specific_subscription(UUID(subscription_id))
            
            if result.get('success'):
                # Send confirmation email
                await send_email_task(
                    ctx,
                    "subscription_renewal",
                    kwargs.get('user_email', ''),
                    subscription_id=subscription_id,
                    order_id=result.get('order_id'),
                    **kwargs
                )
                return f"Subscription renewal completed for {subscription_id}"
            else:
                # Send failure notification
                await send_notification_task(
                    ctx,
                    kwargs.get('user_id', ''),
                    "subscription_renewal_failed",
                    title="Subscription Renewal Failed",
                    message=f"Failed to renew subscription: {result.get('error', 'Unknown error')}",
                    data={"subscription_id": subscription_id}
                )
                return f"Subscription renewal failed for {subscription_id}: {result.get('error')}"
                
    except Exception as e:
        logger.error(f"Error processing subscription renewal {subscription_id}: {e}")
        raise

async def retry_failed_payment_task(ctx: Dict[str, Any], payment_id: str, **kwargs) -> str:
    """Retry failed payment background task"""
    try:
        from services.payments import PaymentService
        from uuid import UUID
        
        async with ctx['db_session']() as db:
            payment_service = PaymentService(db)
            
            # Attempt to retry the payment
            result = await payment_service.retry_failed_payment(payment_id)
            
            if result.get('success'):
                # Send success notification
                await send_notification_task(
                    ctx,
                    kwargs.get('user_id', ''),
                    "payment_retry_success",
                    title="Payment Processed",
                    message="Your payment has been processed successfully after retry.",
                    data={"payment_id": payment_id}
                )
                return f"Payment retry succeeded for {payment_id}"
            else:
                # Schedule next retry or mark as permanently failed
                retry_count = kwargs.get('retry_count', 0) + 1
                max_retries = kwargs.get('max_retries', 3)
                
                if retry_count < max_retries:
                    # Schedule next retry with exponential backoff
                    delay_hours = 2 ** retry_count  # 2, 4, 8 hours
                    await ctx['arq_pool'].enqueue_job(
                        'retry_failed_payment_task',
                        payment_id,
                        _defer_by=timedelta(hours=delay_hours),
                        retry_count=retry_count,
                        max_retries=max_retries,
                        **kwargs
                    )
                    return f"Payment retry {retry_count} failed, scheduled next retry in {delay_hours} hours"
                else:
                    # Mark as permanently failed
                    await send_notification_task(
                        ctx,
                        kwargs.get('user_id', ''),
                        "payment_permanently_failed",
                        title="Payment Failed",
                        message="Your payment could not be processed after multiple attempts. Please update your payment method.",
                        data={"payment_id": payment_id}
                    )
                    return f"Payment permanently failed for {payment_id} after {max_retries} retries"
                
    except Exception as e:
        logger.error(f"Error retrying payment {payment_id}: {e}")
        raise

async def process_subscription_orders_task(ctx: Dict[str, Any]) -> str:
    """Process all due subscription orders"""
    try:
        from services.subscriptions.subscription_scheduler import SubscriptionSchedulerService
        
        async with ctx['db_session']() as db:
            scheduler = SubscriptionSchedulerService(db)
            result = await scheduler.process_due_subscriptions()
            
            # Send notifications for each result
            for order_result in result.get("results", []):
                if order_result["status"] == "success":
                    await send_email_task(
                        ctx,
                        "order_confirmation",
                        order_result.get("user_email", ""),
                        order_id=order_result["order_id"],
                        subscription_id=order_result["subscription_id"]
                    )
                else:
                    await send_notification_task(
                        ctx,
                        order_result.get("user_id", ""),
                        "subscription_order_failed",
                        title="Subscription Order Failed",
                        message=f"Failed to create your subscription order: {order_result.get('reason', 'Unknown error')}",
                        data={"subscription_id": order_result["subscription_id"]}
                    )
            
            return f"Processed {result.get('total_due', 0)} subscription orders, {result.get('failed_count', 0)} failed"
            
    except Exception as e:
        logger.error(f"Error processing subscription orders: {e}")
        raise

async def cleanup_old_data_task(ctx: Dict[str, Any], data_type: str, days_old: int = 30) -> str:
    """Cleanup old data background task"""
    try:
        if data_type == "expired_carts":
            return await cleanup_expired_carts_task(ctx)
        elif data_type == "old_notifications":
            from services.notifications import NotificationService
            async with ctx['db_session']() as db:
                notification_service = NotificationService(db)
                count = await notification_service.delete_old_notifications(days_old)
                return f"Cleaned up {count} old notifications"
        elif data_type == "failed_payments":
            from tasks.payment_retry_tasks import cleanup_old_failed_payments
            await cleanup_old_failed_payments(days_old)
            return f"Cleaned up failed payments older than {days_old} days"
        else:
            return f"Unknown cleanup data type: {data_type}"
            
    except Exception as e:
        logger.error(f"Error cleaning up {data_type}: {e}")
        raise

# ARQ Worker class configuration
class WorkerSettings:
    """ARQ Worker settings"""
    redis_settings = ARQ_REDIS_SETTINGS
    functions = [
        send_email_task,
        process_payment_task,
        update_inventory_task,
        send_notification_task,
        process_subscription_renewal_task,
        retry_failed_payment_task,
        process_subscription_orders_task,
        cleanup_old_data_task,
    ]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    job_timeout = 300  # 5 minutes
    keep_result = 3600  # Keep results for 1 hour

async def get_arq_pool():
    """Get ARQ Redis pool for enqueueing jobs"""
    return await create_pool(ARQ_REDIS_SETTINGS)

async def cleanup_expired_carts_task(ctx: Dict[str, Any]) -> str:
    """Cleanup expired carts background task"""
    try:
        from core.redis import RedisService
        
        redis_service = RedisService()
        # This would need to be implemented to scan and clean expired cart keys
        # For now, just log that the task ran
        logger.info("Expired carts cleanup task completed")
        return "Expired carts cleanup completed"
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired carts: {e}")
        raise

# Convenience functions for enqueueing tasks
async def enqueue_email(email_type: str, recipient: str, **kwargs):
    """Enqueue email task"""
    pool = await get_arq_pool()
    await pool.enqueue_job('send_email_task', email_type, recipient, **kwargs)

async def enqueue_payment_processing(payment_id: str, action: str, **kwargs):
    """Enqueue payment processing task"""
    pool = await get_arq_pool()
    await pool.enqueue_job('process_payment_task', payment_id, action, **kwargs)

async def enqueue_inventory_update(variant_id: str, action: str, **kwargs):
    """Enqueue inventory update task"""
    pool = await get_arq_pool()
    await pool.enqueue_job('update_inventory_task', variant_id, action, **kwargs)

async def enqueue_notification(user_id: str, notification_type: str, **kwargs):
    """Enqueue notification task"""
    pool = await get_arq_pool()
    await pool.enqueue_job('send_notification_task', user_id, notification_type, **kwargs)

async def enqueue_subscription_renewal(subscription_id: str, **kwargs):
    """Enqueue subscription renewal task"""
    pool = await get_arq_pool()
    await pool.enqueue_job('process_subscription_renewal_task', subscription_id, **kwargs)

async def enqueue_payment_retry(payment_id: str, delay_hours: int = 1, **kwargs):
    """Enqueue payment retry task with delay"""
    pool = await get_arq_pool()
    await pool.enqueue_job(
        'retry_failed_payment_task', 
        payment_id, 
        _defer_by=timedelta(hours=delay_hours),
        **kwargs
    )

async def enqueue_subscription_processing():
    """Enqueue subscription order processing task"""
    pool = await get_arq_pool()
    await pool.enqueue_job('process_subscription_orders_task')

async def enqueue_data_cleanup(data_type: str, days_old: int = 30):
    """Enqueue data cleanup task"""
    pool = await get_arq_pool()
    await pool.enqueue_job('cleanup_old_data_task', data_type, days_old)

async def enqueue_cart_cleanup():
    """Enqueue cart cleanup task"""
    pool = await get_arq_pool()
    await pool.enqueue_job('cleanup_old_data_task', 'expired_carts')