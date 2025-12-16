"""
Celery tasks for sending emails using Mailgun
"""
import asyncio
from celery_app import celery_app
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from uuid import UUID
from datetime import datetime, timedelta
from typing import Dict, Any

from core.config import settings
from models.order import Order
from models.user import User, Address
from models.product import ProductVariant
from core.utils.messages.email import send_email_mailgun # Import async version


# Create SYNC engine for Celery tasks - Not strictly needed if tasks are fully async,
# but keeping for other potential sync needs or if a task needs direct DB access.
sync_database_url = str(settings.SQLALCHEMY_DATABASE_URI).replace('+asyncpg', '')
if 'postgresql' in sync_database_url and '+' not in sync_database_url:
    sync_database_url = sync_database_url.replace('postgresql://', 'postgresql+psycopg2://')

sync_engine = create_engine(
    sync_database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False
)


@celery_app.task(name='tasks.email_tasks.send_order_confirmation_email')
def send_order_confirmation_email(user_email: str, context: Dict[str, Any]):
    """
    Send order confirmation email.
    """
    try:
        asyncio.run(send_email_mailgun(
            to_email=user_email,
            mail_type='order_confirmation',
            context=context
        ))
        print(f"✅ Order confirmation email sent to {user_email}")
    except Exception as e:
        print(f"❌ Failed to send order confirmation email: {e}")
        raise


@celery_app.task(name='tasks.email_tasks.send_shipping_update_email')
def send_shipping_update_email(user_email: str, context: Dict[str, Any]):
    """
    Send shipping update email.
    """
    try:
        asyncio.run(send_email_mailgun(
            to_email=user_email,
            mail_type='shipping_update',
            context=context
        ))
        print(f"✅ Shipping update email sent to {user_email}")
    except Exception as e:
        print(f"❌ Failed to send shipping update email: {e}")
        raise


@celery_app.task(name='tasks.email_tasks.send_welcome_email')
def send_welcome_email(user_email: str, context: Dict[str, Any]):
    """
    Send welcome email to new user.
    """
    try:
        asyncio.run(send_email_mailgun(
            to_email=user_email,
            mail_type='welcome',
            context=context
        ))
        print(f"✅ Welcome email sent to {user_email}")
    except Exception as e:
        print(f"❌ Failed to send welcome email: {e}")
        raise


@celery_app.task(name='tasks.email_tasks.send_password_reset_email')
def send_password_reset_email(user_email: str, context: Dict[str, Any]):
    """
    Send password reset email.
    """
    try:
        asyncio.run(send_email_mailgun(
            to_email=user_email,
            mail_type='password_reset',
            context=context
        ))
        print(f"✅ Password reset email sent to {user_email}")
    except Exception as e:
        print(f"❌ Failed to send password reset email: {e}")
        raise


@celery_app.task(name='tasks.email_tasks.send_cart_abandonment_emails')
def send_cart_abandonment_emails():
    """
    Periodic task to send cart abandonment emails
    """
    # Cart abandonment logic to be implemented
    print("🔄 Checking for abandoned carts...")


@celery_app.task(name='tasks.email_tasks.send_email_verification')
def send_email_verification(user_email: str, context: Dict[str, Any]):
    """
    Send email verification link.
    """
    try:
        asyncio.run(send_email_mailgun(
            to_email=user_email,
            mail_type='activation',
            context=context
        ))
        print(f"✅ Email verification sent to {user_email}")
    except Exception as e:
        print(f"❌ Failed to send email verification: {e}")
        raise


@celery_app.task(name='tasks.email_tasks.send_email_change_confirmation')
def send_email_change_confirmation(user_email: str, context: Dict[str, Any]):
    """
    Send email change confirmation.
    """
    try:
        asyncio.run(send_email_mailgun(
            to_email=user_email,
            mail_type='email_change',
            context=context
        ))
        print(f"✅ Email change confirmation sent to {user_email}")
    except Exception as e:
        print(f"❌ Failed to send email change confirmation: {e}")
        raise


@celery_app.task(name='tasks.email_tasks.send_order_delivered_email')
def send_order_delivered_email(user_email: str, context: Dict[str, Any]):
    """
    Send order delivered email.
    """
    try:
        asyncio.run(send_email_mailgun(
            to_email=user_email,
            mail_type='order_delivered',
            context=context
        ))
        print(f"✅ Order delivered email sent to {user_email}")
    except Exception as e:
        print(f"❌ Failed to send order delivered email: {e}")
        raise


@celery_app.task(name='tasks.email_tasks.send_return_process_email')
def send_return_process_email(user_email: str, context: Dict[str, Any]):
    """
    Send return process instructions email.
    """
    try:
        asyncio.run(send_email_mailgun(
            to_email=user_email,
            mail_type='return_process',
            context=context
        ))
        print(f"✅ Return process email sent to {user_email}")
    except Exception as e:
        print(f"❌ Failed to send return process email: {e}")
        raise


@celery_app.task(name='tasks.email_tasks.send_referral_request_email')
def send_referral_request_email(user_email: str, context: Dict[str, Any]):
    """
    Send referral request email after positive review or repeat purchase.
    """
    try:
        asyncio.run(send_email_mailgun(
            to_email=user_email,
            mail_type='referral_request',
            context=context
        ))
        print(f"✅ Referral request email sent to {user_email}")
    except Exception as e:
        print(f"❌ Failed to send referral request email: {e}")
        raise


@celery_app.task(name='tasks.email_tasks.send_low_stock_alert_email')
def send_low_stock_alert_email(recipient_email: str, context: Dict[str, Any]):
    """
    Send low stock alert email to admin/supplier.
    """
    try:
        asyncio.run(send_email_mailgun(
            to_email=recipient_email,
            mail_type='low_stock_alert', # This email template needs to be created
            context=context
        ))
        print(f"✅ Low stock alert email sent to {recipient_email}")
    except Exception as e:
        print(f"❌ Failed to send low stock alert email: {e}")
        raise



@celery_app.task(name='tasks.email_tasks.send_review_requests')
def send_review_requests():
    """
    Periodic task to send review request emails
    """
    # Review request logic to be implemented
    print("🔄 Checking for orders ready for review...")