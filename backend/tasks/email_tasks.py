"""
Kafka consumer tasks for sending emails using Mailgun
"""
import logging
from uuid import UUID
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from models.order import Order
from models.user import User
from models.product import ProductVariant
from core.utils.messages.email import send_email_mailgun # Import async version
from services.email import EmailService # Import EmailService to encapsulate logic

logger = logging.getLogger(__name__)


async def send_order_confirmation_email(db: AsyncSession, order_id: str):
    """
    Send order confirmation email based on order_id.
    """
    try:
        email_service = EmailService(db)
        await email_service.send_order_confirmation(UUID(order_id)) # Use existing EmailService method
        logger.info(f"✅ Order confirmation email dispatched for order {order_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send order confirmation email for order {order_id}: {e}")
        raise


async def send_shipping_update_email(db: AsyncSession, order_id: str, carrier_name: str, tracking_number: str):
    """
    Send shipping update email.
    """
    try:
        email_service = EmailService(db)
        await email_service.send_shipping_update(UUID(order_id), carrier_name, tracking_number)
        logger.info(f"✅ Shipping update email dispatched for order {order_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send shipping update email for order {order_id}: {e}")
        raise


async def send_welcome_email(db: AsyncSession, user_id: str):
    """
    Send welcome email to new user.
    """
    try:
        email_service = EmailService(db)
        await email_service.send_welcome(UUID(user_id))
        logger.info(f"✅ Welcome email dispatched for user {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send welcome email for user {user_id}: {e}")
        raise


async def send_password_reset_email(db: AsyncSession, user_id: str, reset_token: str):
    """
    Send password reset email.
    """
    try:
        # Email service already constructs the context
        email_service = EmailService(db)
        await email_service.send_password_reset(UUID(user_id), reset_token)
        logger.info(f"✅ Password reset email dispatched for user {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send password reset email for user {user_id}: {e}")
        raise


async def send_cart_abandonment_emails(db: AsyncSession):
    """
    Periodic task to send cart abandonment emails
    """
    logger.info("🔄 Checking for abandoned carts...")
    # Logic to identify abandoned carts and dispatch individual emails
    # This would involve querying the DB for old carts and then using EmailService
    # Example placeholder:
    # from services.cart import CartService
    # cart_service = CartService(db)
    # abandoned_carts = await cart_service.get_abandoned_carts() # This method would need to exist
    # for cart in abandoned_carts:
    #     await email_service.send_abandoned_cart_reminder(cart.user_id, cart.id)
    pass # Actual implementation needed here


async def send_email_verification(db: AsyncSession, user_id: str, verification_token: str):
    """
    Send email verification link.
    """
    try:
        email_service = EmailService(db)
        await email_service.send_email_verification_link(UUID(user_id), verification_token)
        logger.info(f"✅ Email verification dispatched for user {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send email verification for user {user_id}: {e}")
        raise


async def send_email_change_confirmation(db: AsyncSession, user_id: str, new_email: str, old_email: str, confirmation_token: str):
    """
    Send email change confirmation.
    """
    try:
        email_service = EmailService(db)
        await email_service.send_email_change_confirmation_link(UUID(user_id), new_email, old_email, confirmation_token)
        logger.info(f"✅ Email change confirmation dispatched for user {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send email change confirmation for user {user_id}: {e}")
        raise


async def send_order_delivered_email(db: AsyncSession, order_id: str):
    """
    Send order delivered email.
    """
    try:
        email_service = EmailService(db)
        await email_service.send_order_delivered(UUID(order_id))
        logger.info(f"✅ Order delivered email dispatched for order {order_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send order delivered email for order {order_id}: {e}")
        raise


async def send_return_process_email(db: AsyncSession, order_id: str, return_instructions: str):
    """
    Send return process instructions email.
    """
    try:
        email_service = EmailService(db)
        await email_service.send_return_process_instructions(UUID(order_id), return_instructions)
        logger.info(f"✅ Return process email dispatched for order {order_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send return process email for order {order_id}: {e}")
        raise


async def send_referral_request_email(db: AsyncSession, user_id: str, referral_code: str):
    """
    Send referral request email after positive review or repeat purchase.
    """
    try:
        email_service = EmailService(db)
        await email_service.send_referral_request(UUID(user_id), referral_code)
        logger.info(f"✅ Referral request email dispatched for user {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to send referral request email for user {user_id}: {e}")
        raise


async def send_low_stock_alert_email(db: AsyncSession, recipient_email: str, context: Dict[str, Any]):
    """
    Send low stock alert email to admin/supplier.
    """
    try:
        email_service = EmailService(db)
        # Assuming EmailService has a method to handle the context
        # If not, you'd integrate mailgun directly here as before
        await email_service.send_low_stock_alert(recipient_email, context)
        logger.info(f"✅ Low stock alert email dispatched to {recipient_email}")
    except Exception as e:
        logger.error(f"❌ Failed to send low stock alert email to {recipient_email}: {e}")
        raise


async def send_review_requests(db: AsyncSession):
    """
    Periodic task to send review request emails
    """
    logger.info("🔄 Checking for orders ready for review...")
    # Logic to identify orders ready for review and dispatch individual emails
    # Example placeholder:
    # from services.order import OrderService
    # order_service = OrderService(db)
    # orders_for_review = await order_service.get_orders_for_review() # This method would need to exist
    # for order in orders_for_review:
    #     user = await db.execute(select(User).where(User.id == order.user_id)).scalar_one_or_none()
    #     if user:
    #         await email_service.send_review_request(user.id, order.id)
    pass # Actual implementation needed here
