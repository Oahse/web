"""
Background Tasks for Payment Retry Management using Hybrid approach
Handles automatic payment retries and cleanup
Uses ARQ for scheduled retries and FastAPI BackgroundTasks for immediate processing
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio
import logging
from fastapi import BackgroundTasks

from lib.db import get_db
from core.hybrid_tasks import hybrid_task_manager, process_payment_hybrid
from lib.arq_worker import enqueue_payment_retry, enqueue_data_cleanup
from models.payments import PaymentIntent, Transaction
from models.subscriptions import Subscription
from models.orders import Order
from services.payment_failure_handler import PaymentFailureHandler, PaymentFailureReason
from services.payments import PaymentService

logger = logging.getLogger(__name__)


class PaymentRetryTaskManager:
    """Manages background tasks for payment retry operations using hybrid approach"""
    
    def __init__(self):
        self.is_running = False
        self.retry_interval_minutes = 30  # Check every 30 minutes
        
    async def start_retry_scheduler(self):
        """Start the payment retry scheduler using ARQ"""
        if self.is_running:
            logger.warning("Payment retry scheduler is already running")
            return
        
        self.is_running = True
        logger.info("Starting payment retry scheduler with ARQ")
        
        # Use ARQ for scheduled processing
        from lib.arq_worker import get_arq_pool
        pool = await get_arq_pool()
        
        while self.is_running:
            try:
                # Schedule the next processing cycle
                await pool.enqueue_job(
                    'process_payment_retries_task',
                    _defer_by=timedelta(minutes=self.retry_interval_minutes)
                )
                await asyncio.sleep(self.retry_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in payment retry scheduler: {e}")
                await asyncio.sleep(60)
    
    def stop_retry_scheduler(self):
        """Stop the payment retry scheduler"""
        self.is_running = False
        logger.info("Payment retry scheduler stopped")
    
    async def schedule_payment_retry(
        self, 
        payment_id: str, 
        retry_delay_hours: int = 1,
        background_tasks: Optional[BackgroundTasks] = None,
        **kwargs
    ):
        """Schedule a payment retry using hybrid approach"""
        try:
            if retry_delay_hours > 0:
                # Use ARQ for delayed retries
                await enqueue_payment_retry(
                    payment_id, 
                    delay_hours=retry_delay_hours,
                    **kwargs
                )
                logger.info(f"Scheduled payment retry for {payment_id} in {retry_delay_hours} hours")
            else:
                # Use FastAPI BackgroundTasks for immediate retry
                if background_tasks:
                    await process_payment_hybrid(
                        background_tasks,
                        payment_id,
                        "retry",
                        use_arq=False,  # Immediate processing
                        **kwargs
                    )
                else:
                    # Direct processing
                    await hybrid_task_manager.process_payment_task(payment_id, "retry", **kwargs)
                
        except Exception as e:
            logger.error(f"Error scheduling payment retry for {payment_id}: {e}")
    
    async def process_immediate_retry(
        self,
        background_tasks: BackgroundTasks,
        payment_id: str,
        **kwargs
    ):
        """Process immediate payment retry using FastAPI BackgroundTasks"""
        await process_payment_hybrid(
            background_tasks,
            payment_id,
            "retry",
            use_arq=False,
            **kwargs
        )
    
    async def cleanup_expired_retries(self, days_old: int = 30):
        """Schedule cleanup of expired retries using ARQ"""
        await enqueue_data_cleanup("failed_payments", days_old)
        logger.info(f"Scheduled cleanup of failed payments older than {days_old} days")
    
    async def _process_retry_queue(self):
        """Process payments that are due for retry"""
        async for db in get_db():
            try:
                # Find payments due for automatic retry
                retry_candidates = await self._find_retry_candidates(db)
                
                logger.info(f"Found {len(retry_candidates)} payments due for retry")
                
                for payment_intent in retry_candidates:
                    try:
                        await self._attempt_payment_retry(db, payment_intent)
                    except Exception as e:
                        logger.error(f"Error retrying payment {payment_intent.id}: {e}")
                
                # Clean up expired retry windows
                await self._cleanup_expired_retries(db)
                
                # Process subscription grace periods
                await self._process_subscription_grace_periods(db)
                
            except Exception as e:
                logger.error(f"Error processing retry queue: {e}")
            finally:
                await db.close()
    
    async def _find_retry_candidates(self, db: AsyncSession) -> List[PaymentIntent]:
        """Find payment intents that are due for automatic retry"""
        current_time = datetime.utcnow()
        
        # Find failed payments with retry metadata
        result = await db.execute(
            select(PaymentIntent).where(
                and_(
                    PaymentIntent.status == "failed",
                    PaymentIntent.failure_metadata.isnot(None)
                )
            )
        )
        
        failed_payments = result.scalars().all()
        retry_candidates = []
        
        for payment in failed_payments:
            failure_metadata = payment.failure_metadata or {}
            
            # Check if this payment should be retried automatically
            if not self._should_auto_retry(payment, failure_metadata):
                continue
            
            # Check if it's time for the next retry
            last_retry_str = failure_metadata.get("last_retry_at")
            if last_retry_str:
                last_retry = datetime.fromisoformat(last_retry_str.replace('Z', '+00:00'))
            else:
                last_retry = payment.failed_at or current_time
            
            # Determine retry delay based on failure reason
            failure_reason = PaymentFailureReason(payment.failure_reason) if payment.failure_reason else PaymentFailureReason.UNKNOWN
            retry_delay_hours = self._get_retry_delay_hours(failure_reason, failure_metadata.get("retry_count", 0))
            
            next_retry_time = last_retry + timedelta(hours=retry_delay_hours)
            
            if current_time >= next_retry_time:
                retry_candidates.append(payment)
        
        return retry_candidates
    
    def _should_auto_retry(self, payment: PaymentIntent, failure_metadata: Dict) -> bool:
        """Determine if a payment should be automatically retried"""
        failure_reason = PaymentFailureReason(payment.failure_reason) if payment.failure_reason else PaymentFailureReason.UNKNOWN
        
        # Don't auto-retry certain failure types
        no_auto_retry_reasons = [
            PaymentFailureReason.FRAUD_SUSPECTED,
            PaymentFailureReason.INVALID_CARD,
            PaymentFailureReason.EXPIRED_CARD,
            PaymentFailureReason.AUTHENTICATION_REQUIRED
        ]
        
        if failure_reason in no_auto_retry_reasons:
            return False
        
        # Check retry count limits
        retry_count = failure_metadata.get("retry_count", 0)
        max_auto_retries = 2  # Maximum automatic retries
        
        if retry_count >= max_auto_retries:
            return False
        
        # Only auto-retry certain failure types
        auto_retry_reasons = [
            PaymentFailureReason.PROCESSING_ERROR,
            PaymentFailureReason.NETWORK_ERROR,
            PaymentFailureReason.INSUFFICIENT_FUNDS  # For subscriptions only
        ]
        
        if failure_reason not in auto_retry_reasons:
            return False
        
        # For insufficient funds, only auto-retry subscriptions
        if failure_reason == PaymentFailureReason.INSUFFICIENT_FUNDS:
            return payment.subscription_id is not None
        
        return True
    
    def _get_retry_delay_hours(self, failure_reason: PaymentFailureReason, retry_count: int) -> float:
        """Get retry delay in hours based on failure reason and attempt count"""
        delay_schedules = {
            PaymentFailureReason.PROCESSING_ERROR: [0.5, 2, 6],  # 30 min, 2 hours, 6 hours
            PaymentFailureReason.NETWORK_ERROR: [0.25, 1, 4],   # 15 min, 1 hour, 4 hours
            PaymentFailureReason.INSUFFICIENT_FUNDS: [24, 72, 168]  # 1 day, 3 days, 1 week
        }
        
        schedule = delay_schedules.get(failure_reason, [1, 6, 24])  # Default schedule
        return schedule[min(retry_count, len(schedule) - 1)]
    
    async def _attempt_payment_retry(self, db: AsyncSession, payment_intent: PaymentIntent):
        """Attempt to retry a failed payment"""
        try:
            logger.info(f"Attempting automatic retry for payment {payment_intent.id}")
            
            payment_service = PaymentService(db)
            failure_handler = PaymentFailureHandler(db)
            
            # Update retry metadata
            if not payment_intent.failure_metadata:
                payment_intent.failure_metadata = {}
            
            payment_intent.failure_metadata["last_retry_at"] = datetime.utcnow().isoformat()
            payment_intent.failure_metadata["retry_count"] = payment_intent.failure_metadata.get("retry_count", 0) + 1
            payment_intent.failure_metadata["auto_retry"] = True
            
            # Reset payment intent status for retry
            payment_intent.status = "requires_payment_method"
            payment_intent.failed_at = None
            payment_intent.failure_reason = None
            
            # Attempt to process the payment again
            if payment_intent.payment_method_id:
                try:
                    # Confirm the payment intent with existing payment method
                    confirmed_intent = await payment_service.confirm_payment_intent(
                        payment_intent_id=payment_intent.id,
                        payment_method_id=payment_intent.payment_method_id,
                        commit=True
                    )
                    
                    if confirmed_intent.status == "succeeded":
                        logger.info(f"Automatic retry succeeded for payment {payment_intent.id}")
                        
                    elif confirmed_intent.status == "failed":
                        logger.warning(f"Automatic retry failed for payment {payment_intent.id}")
                        
                        # Handle the failure again
                        await failure_handler.handle_payment_failure(
                            payment_intent_id=payment_intent.id,
                            failure_context={"auto_retry_failed": True}
                        )
                        
                except Exception as retry_error:
                    logger.error(f"Error during payment retry: {retry_error}")
                    
                    # Mark as failed and handle the failure
                    payment_intent.status = "failed"
                    payment_intent.failed_at = datetime.utcnow()
                    payment_intent.failure_reason = f"Auto-retry failed: {str(retry_error)}"
                    
                    await db.commit()
            
        except Exception as e:
            logger.error(f"Error in payment retry attempt: {e}")
            await db.rollback()
    
    async def _cleanup_expired_retries(self, db: AsyncSession):
        """Clean up payments that have exceeded their retry window"""
        try:
            current_time = datetime.utcnow()
            
            # Find orders with expired retry windows
            orders_result = await db.execute(
                select(Order).where(
                    Order.status == "payment_failed"
                )
            )
            orders = orders_result.scalars().all()
            
            expired_orders = []
            for order in orders:
                if order.order_metadata and "payment_retry_expires_at" in order.order_metadata:
                    expires_at_str = order.order_metadata["payment_retry_expires_at"]
                    expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                    
                    if current_time > expires_at:
                        expired_orders.append(order)
            
            # Mark expired orders as permanently failed
            for order in expired_orders:
                order.status = "payment_permanently_failed"
                if not order.order_metadata:
                    order.order_metadata = {}
                order.order_metadata["retry_window_expired_at"] = current_time.isoformat()
                
                logger.info(f"Order {order.id} retry window expired, marked as permanently failed")
            
            if expired_orders:
                await db.commit()
                logger.info(f"Cleaned up {len(expired_orders)} expired order retry windows")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired retries: {e}")
    
    async def _process_subscription_grace_periods(self, db: AsyncSession):
        """Process subscriptions in grace period and handle expiry"""
        try:
            current_time = datetime.utcnow()
            
            # Find subscriptions with expired grace periods
            subscriptions_result = await db.execute(
                select(Subscription).where(
                    and_(
                        Subscription.status == "payment_failed",
                        Subscription.grace_period_ends_at.isnot(None),
                        Subscription.grace_period_ends_at < current_time
                    )
                )
            )
            
            expired_subscriptions = subscriptions_result.scalars().all()
            
            for subscription in expired_subscriptions:
                # Cancel subscription due to expired grace period
                subscription.status = "cancelled"
                subscription.cancelled_at = current_time
                subscription.auto_renew = False
                
                if not subscription.subscription_metadata:
                    subscription.subscription_metadata = {}
                
                subscription.subscription_metadata["cancellation_reason"] = "payment_grace_period_expired"
                subscription.subscription_metadata["grace_period_expired_at"] = current_time.isoformat()
                
                logger.info(f"Subscription {subscription.id} cancelled due to expired grace period")
            
            if expired_subscriptions:
                await db.commit()
                logger.info(f"Processed {len(expired_subscriptions)} expired subscription grace periods")
                
        except Exception as e:
            logger.error(f"Error processing subscription grace periods: {e}")


# Global task manager instance
payment_retry_manager = PaymentRetryTaskManager()


async def start_payment_retry_scheduler():
    """Start the payment retry scheduler (called from main app startup)"""
    await payment_retry_manager.start_retry_scheduler()


def stop_payment_retry_scheduler():
    """Stop the payment retry scheduler (called from main app shutdown)"""
    payment_retry_manager.stop_retry_scheduler()


async def manual_retry_failed_payments():
    """Manual task to retry failed payments (can be called from admin interface)"""
    async for db in get_db():
        try:
            manager = PaymentRetryTaskManager()
            await manager._process_retry_queue()
        finally:
            await db.close()


async def cleanup_old_failed_payments(days_old: int = 30):
    """Clean up old failed payments that are no longer retryable"""
    async for db in get_db():
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Find old failed payments
            result = await db.execute(
                select(PaymentIntent).where(
                    and_(
                        PaymentIntent.status.in_(["failed", "abandoned"]),
                        PaymentIntent.failed_at < cutoff_date
                    )
                )
            )
            
            old_payments = result.scalars().all()
            
            for payment in old_payments:
                # Mark as permanently failed
                payment.status = "permanently_failed"
                if not payment.failure_metadata:
                    payment.failure_metadata = {}
                payment.failure_metadata["cleanup_date"] = datetime.utcnow().isoformat()
                payment.failure_metadata["cleanup_reason"] = f"Older than {days_old} days"
            
            await db.commit()
            logger.info(f"Cleaned up {len(old_payments)} old failed payments")
            
        except Exception as e:
            logger.error(f"Error cleaning up old failed payments: {e}")
        finally:
            await db.close()