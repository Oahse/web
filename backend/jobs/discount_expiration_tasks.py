"""
Background tasks for discount expiration handling
Implements automatic discount expiration checking and cleanup
Requirements: 3.3
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from lib.db import get_db_session
from services.discounts import DiscountEngine
from core.utils.messages.email import send_email
from core.utils.messages.sms import send_sms
from models.subscriptions import Subscription
from models.user import User
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


class DiscountExpirationTaskManager:
    """Manager for discount expiration background tasks"""
    
    def __init__(self):
        self.is_running = False
        self.task_interval = 3600  # Run every hour (3600 seconds)
    
    async def start_expiration_monitor(self):
        """Start the discount expiration monitoring task"""
        if self.is_running:
            logger.warning("Discount expiration monitor is already running")
            return
        
        self.is_running = True
        logger.info("Starting discount expiration monitor")
        
        while self.is_running:
            try:
                await self.check_and_remove_expired_discounts()
                await asyncio.sleep(self.task_interval)
            except Exception as e:
                logger.error(f"Error in discount expiration monitor: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def stop_expiration_monitor(self):
        """Stop the discount expiration monitoring task"""
        self.is_running = False
        logger.info("Stopping discount expiration monitor")
    
    async def check_and_remove_expired_discounts(self) -> Dict[str, Any]:
        """
        Check for expired discounts and remove them from subscriptions
        Requirements: 3.3
        
        Returns:
            Summary of expiration handling results
        """
        async with get_db_session() as db_session:
            try:
                discount_engine = DiscountEngine(db_session)
                
                # Remove expired discounts
                expiration_result = await discount_engine.remove_expired_discounts()
                
                if expiration_result['expired_discounts_count'] > 0:
                    logger.info(f"Processed {expiration_result['expired_discounts_count']} expired discounts")
                    
                    # Send notifications to affected users
                    notification_result = await self._notify_affected_users(
                        db_session,
                        expiration_result
                    )
                    
                    expiration_result.update(notification_result)
                
                return expiration_result
                
            except Exception as e:
                logger.error(f"Error checking expired discounts: {str(e)}")
                return {
                    'expired_discounts_count': 0,
                    'affected_subscriptions': 0,
                    'notifications_sent': 0,
                    'error': str(e)
                }
    
    async def _notify_affected_users(
        self,
        db_session: AsyncSession,
        expiration_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send notifications to users whose discounts have expired
        
        Args:
            db_session: Database session
            expiration_result: Result from discount expiration processing
            
        Returns:
            Notification sending results
        """
        notification_result = {
            'email_notifications_sent': 0,
            'sms_notifications_sent': 0,
            'notification_errors': []
        }
        
        try:
            # Get affected subscription IDs (this would need to be tracked in the expiration result)
            # For now, we'll implement a basic notification system
            
            expired_codes = expiration_result.get('expired_codes', [])
            if not expired_codes:
                return notification_result
            
            # Find users with subscriptions that had these discounts
            # This is a simplified approach - in production, you'd want to track this more precisely
            affected_users_result = await db_session.execute(
                select(User.id, User.email, User.phone_number).distinct()
                .join(Subscription, Subscription.user_id == User.id)
                .where(Subscription.status.in_(['active', 'paused']))
            )
            affected_users = affected_users_result.fetchall()
            
            # Send notifications
            for user_id, email, phone_number in affected_users:
                try:
                    # Send email notification
                    if email:
                        await self._send_expiration_email(
                            email=email,
                            expired_codes=expired_codes
                        )
                        notification_result['email_notifications_sent'] += 1
                    
                    # Send SMS notification if phone number is available
                    if phone_number:
                        await self._send_expiration_sms(
                            phone_number=phone_number,
                            expired_codes=expired_codes
                        )
                        notification_result['sms_notifications_sent'] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to notify user {user_id}: {str(e)}"
                    logger.error(error_msg)
                    notification_result['notification_errors'].append(error_msg)
            
            logger.info(f"Sent {notification_result['email_notifications_sent']} email and {notification_result['sms_notifications_sent']} SMS notifications")
            
        except Exception as e:
            error_msg = f"Error sending notifications: {str(e)}"
            logger.error(error_msg)
            notification_result['notification_errors'].append(error_msg)
        
        return notification_result
    
    async def _send_expiration_email(self, email: str, expired_codes: list):
        """Send email notification about expired discounts"""
        subject = "Your Discount Codes Have Expired"
        
        if len(expired_codes) == 1:
            message = f"""
            Dear Valued Customer,
            
            We wanted to let you know that your discount code "{expired_codes[0]}" has expired and has been removed from your active subscriptions.
            
            Don't worry! We regularly offer new promotions and discounts. Keep an eye on your email for our latest offers.
            
            If you have any questions, please don't hesitate to contact our support team.
            
            Best regards,
            The Subscription Team
            """
        else:
            codes_list = ", ".join(expired_codes)
            message = f"""
            Dear Valued Customer,
            
            We wanted to let you know that the following discount codes have expired and have been removed from your active subscriptions:
            
            {codes_list}
            
            Don't worry! We regularly offer new promotions and discounts. Keep an eye on your email for our latest offers.
            
            If you have any questions, please don't hesitate to contact our support team.
            
            Best regards,
            The Subscription Team
            """
        
        try:
            await send_email(
                to_email=email,
                subject=subject,
                message=message
            )
            logger.info(f"Sent expiration email to {email}")
        except Exception as e:
            logger.error(f"Failed to send expiration email to {email}: {str(e)}")
            raise
    
    async def _send_expiration_sms(self, phone_number: str, expired_codes: list):
        """Send SMS notification about expired discounts"""
        if len(expired_codes) == 1:
            message = f"Your discount code {expired_codes[0]} has expired and was removed from your subscription. Watch for new offers!"
        else:
            message = f"Your discount codes have expired and were removed from your subscription. Watch for new offers!"
        
        try:
            await send_sms(
                phone_number=phone_number,
                message=message
            )
            logger.info(f"Sent expiration SMS to {phone_number}")
        except Exception as e:
            logger.error(f"Failed to send expiration SMS to {phone_number}: {str(e)}")
            raise
    
    async def check_soon_to_expire_discounts(self, days_ahead: int = 7) -> Dict[str, Any]:
        """
        Check for discounts that will expire soon and send warning notifications
        
        Args:
            days_ahead: Number of days ahead to check for expiring discounts
            
        Returns:
            Summary of soon-to-expire discount notifications
        """
        async with get_db_session() as db_session:
            try:
                from models.discounts import Discount, SubscriptionDiscount
                
                # Find discounts expiring in the next N days
                expiry_threshold = datetime.now(timezone.utc) + timedelta(days=days_ahead)
                current_time = datetime.now(timezone.utc)
                
                soon_to_expire_result = await db_session.execute(
                    select(Discount).where(
                        and_(
                            Discount.is_active == True,
                            Discount.valid_until > current_time,
                            Discount.valid_until <= expiry_threshold
                        )
                    )
                )
                soon_to_expire_discounts = soon_to_expire_result.scalars().all()
                
                if not soon_to_expire_discounts:
                    return {
                        'soon_to_expire_count': 0,
                        'warnings_sent': 0
                    }
                
                # Find affected subscriptions
                discount_ids = [d.id for d in soon_to_expire_discounts]
                affected_subscriptions_result = await db_session.execute(
                    select(SubscriptionDiscount.subscription_id, Discount.code, Discount.valid_until)
                    .join(Discount, SubscriptionDiscount.discount_id == Discount.id)
                    .where(SubscriptionDiscount.discount_id.in_(discount_ids))
                )
                affected_subscriptions = affected_subscriptions_result.fetchall()
                
                # Send warning notifications
                warnings_sent = 0
                for subscription_id, discount_code, expiry_date in affected_subscriptions:
                    try:
                        # Get user info for this subscription
                        user_result = await db_session.execute(
                            select(User.email, User.phone_number)
                            .join(Subscription, Subscription.user_id == User.id)
                            .where(Subscription.id == subscription_id)
                        )
                        user_info = user_result.first()
                        
                        if user_info and user_info.email:
                            await self._send_expiry_warning_email(
                                email=user_info.email,
                                discount_code=discount_code,
                                expiry_date=expiry_date
                            )
                            warnings_sent += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to send expiry warning for subscription {subscription_id}: {str(e)}")
                
                logger.info(f"Sent {warnings_sent} expiry warning notifications for {len(soon_to_expire_discounts)} discounts")
                
                return {
                    'soon_to_expire_count': len(soon_to_expire_discounts),
                    'warnings_sent': warnings_sent,
                    'expiring_codes': [d.code for d in soon_to_expire_discounts]
                }
                
            except Exception as e:
                logger.error(f"Error checking soon-to-expire discounts: {str(e)}")
                return {
                    'soon_to_expire_count': 0,
                    'warnings_sent': 0,
                    'error': str(e)
                }
    
    async def _send_expiry_warning_email(self, email: str, discount_code: str, expiry_date: datetime):
        """Send warning email about soon-to-expire discount"""
        days_remaining = (expiry_date - datetime.now(timezone.utc)).days
        
        subject = f"Your Discount Code {discount_code} Expires Soon!"
        message = f"""
        Dear Valued Customer,
        
        This is a friendly reminder that your discount code "{discount_code}" will expire in {days_remaining} day(s) on {expiry_date.strftime('%B %d, %Y')}.
        
        Your subscription will continue normally after the discount expires, but the discount savings will no longer apply to future billing cycles.
        
        Keep an eye out for new promotions and discount codes in your email!
        
        If you have any questions, please contact our support team.
        
        Best regards,
        The Subscription Team
        """
        
        try:
            await send_email(
                to_email=email,
                subject=subject,
                message=message
            )
            logger.info(f"Sent expiry warning email to {email} for discount {discount_code}")
        except Exception as e:
            logger.error(f"Failed to send expiry warning email to {email}: {str(e)}")
            raise


# Global task manager instance
discount_task_manager = DiscountExpirationTaskManager()


# Task functions for ARQ worker integration
async def check_expired_discounts_task() -> Dict[str, Any]:
    """
    ARQ task function for checking expired discounts
    This can be scheduled to run periodically
    """
    return await discount_task_manager.check_and_remove_expired_discounts()


async def check_soon_to_expire_discounts_task(days_ahead: int = 7) -> Dict[str, Any]:
    """
    ARQ task function for checking soon-to-expire discounts
    This can be scheduled to run daily
    """
    return await discount_task_manager.check_soon_to_expire_discounts(days_ahead)


# Startup function to begin monitoring
async def start_discount_monitoring():
    """Start the discount expiration monitoring background task"""
    asyncio.create_task(discount_task_manager.start_expiration_monitor())
    logger.info("Discount expiration monitoring started")


# Shutdown function
async def stop_discount_monitoring():
    """Stop the discount expiration monitoring background task"""
    discount_task_manager.stop_expiration_monitor()
    logger.info("Discount expiration monitoring stopped")


if __name__ == "__main__":
    # Test the expiration handling
    async def test_expiration_handling():
        manager = DiscountExpirationTaskManager()
        result = await manager.check_and_remove_expired_discounts()
        print(f"Expiration check result: {result}")
        
        warning_result = await manager.check_soon_to_expire_discounts(7)
        print(f"Soon-to-expire check result: {warning_result}")
    
    asyncio.run(test_expiration_handling())