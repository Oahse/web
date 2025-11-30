"""
Celery tasks for sending emails using Mailgun
"""
from celery_app import celery_app
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from uuid import UUID
from datetime import datetime, timedelta

from core.config import settings
from models.order import Order
from models.user import User, Address
from models.product import ProductVariant
from core.utils.messages.email import send_email


# Create SYNC engine for Celery tasks
# Celery tasks run in separate worker processes and should use sync operations
# to avoid greenlet errors
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
def send_order_confirmation_email(order_id: str):
    """
    Send order confirmation email (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            # Fetch order with related data (SYNC)
            result = db.execute(
                select(Order).where(Order.id == UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                print(f"Order {order_id} not found")
                return
            
            # Fetch user (SYNC)
            user_result = db.execute(
                select(User).where(User.id == order.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                print(f"User not found for order {order_id}")
                return
            
            # Fetch order items (SYNC)
            order_items = []
            for item in order.items:
                variant_result = db.execute(
                    select(ProductVariant).where(ProductVariant.id == item.variant_id)
                )
                variant = variant_result.scalar_one_or_none()
                order_items.append({
                    "name": variant.name if variant else "Unknown Item",
                    "quantity": item.quantity,
                    "price": f"${item.total_price:.2f}"
                })
            
            # Fetch shipping address (SYNC)
            shipping_address = None
            if order.shipping_address_id:
                address_result = db.execute(
                    select(Address).where(Address.id == order.shipping_address_id)
                )
                shipping_address = address_result.scalar_one_or_none()
            
            # Build email context
            context = {
                "customer_name": user.firstname,
                "order_number": str(order.id),
                "order_date": order.created_at.strftime("%B %d, %Y"),
                "order_total": f"${order.total_amount:.2f}",
                "order_items": order_items,
                "shipping_address": {
                    "line1": shipping_address.street,
                    "city": shipping_address.city,
                    "state_zip": f"{shipping_address.state} {shipping_address.post_code}",
                    "country": shipping_address.country
                } if shipping_address else {},
                "order_tracking_url": f"{settings.FRONTEND_URL}/account/orders/{order.id}",
                "company_name": "Banwee",
            }
            
            # Send email via Mailgun
            send_email(
                to_email=user.email,
                from_email="",  # Not used with Mailgun
                from_password="",  # Not used with Mailgun
                mail_type='order_confirmation',
                context=context
            )
            
            print(f"✅ Order confirmation email sent to {user.email}")
            
        except Exception as e:
            print(f"❌ Failed to send order confirmation email: {e}")
            raise


@celery_app.task(name='tasks.email_tasks.send_shipping_update_email')
def send_shipping_update_email(order_id: str, carrier_name: str):
    """
    Send shipping update email (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            # Fetch order (SYNC)
            result = db.execute(
                select(Order).where(Order.id == UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                return
            
            # Fetch user (SYNC)
            user_result = db.execute(
                select(User).where(User.id == order.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return
            
            # Fetch shipping address (SYNC)
            shipping_address = None
            if order.shipping_address_id:
                address_result = db.execute(
                    select(Address).where(Address.id == order.shipping_address_id)
                )
                shipping_address = address_result.scalar_one_or_none()
            
            context = {
                "customer_name": user.firstname,
                "order_number": str(order.id),
                "tracking_number": order.tracking_number,
                "carrier_name": carrier_name,
                "shipping_address": {
                    "line1": shipping_address.street,
                    "city": shipping_address.city,
                } if shipping_address else {},
                "tracking_url": f"https://www.google.com/search?q={carrier_name}+{order.tracking_number}",
                "company_name": "Banwee",
            }
            
            send_email(
                to_email=user.email,
                from_email="",
                from_password="",
                mail_type='shipping_update',
                context=context
            )
            
            print(f"✅ Shipping update email sent to {user.email}")
            
        except Exception as e:
            print(f"❌ Failed to send shipping update email: {e}")
            raise


@celery_app.task(name='tasks.email_tasks.send_welcome_email')
def send_welcome_email(user_id: str):
    """
    Send welcome email to new user (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            user_result = db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return
            
            context = {
                "user_name": user.firstname,
                "email": user.email,
                "store_url": settings.FRONTEND_URL,
                "company_name": "Banwee",
            }
            
            send_email(
                to_email=user.email,
                from_email="",
                from_password="",
                mail_type='welcome',
                context=context
            )
            
            print(f"✅ Welcome email sent to {user.email}")
            
        except Exception as e:
            print(f"❌ Failed to send welcome email: {e}")
            raise


@celery_app.task(name='tasks.email_tasks.send_password_reset_email')
def send_password_reset_email(user_id: str, reset_token: str):
    """
    Send password reset email (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            user_result = db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return
            
            context = {
                "user_name": user.firstname,
                "reset_link": f"{settings.FRONTEND_URL}/reset-password?token={reset_token}",
                "expiry_time": "1 hour",
                "company_name": "Banwee",
            }
            
            send_email(
                to_email=user.email,
                from_email="",
                from_password="",
                mail_type='password_reset',
                context=context
            )
            
            print(f"✅ Password reset email sent to {user.email}")
            
        except Exception as e:
            print(f"❌ Failed to send password reset email: {e}")
            raise


@celery_app.task(name='tasks.email_tasks.send_cart_abandonment_emails')
def send_cart_abandonment_emails():
    """
    Periodic task to send cart abandonment emails
    """
    # TODO: Implement cart abandonment logic
    print("🔄 Checking for abandoned carts...")


@celery_app.task(name='tasks.email_tasks.send_email_verification')
def send_email_verification(user_id: str, verification_token: str):
    """
    Send email verification link (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            user_result = db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return
            
            context = {
                "user_name": user.firstname,
                "activation_link": f"{settings.FRONTEND_URL}/verify-email?token={verification_token}",
                "company_name": "Banwee",
            }
            
            send_email(
                to_email=user.email,
                from_email="",
                from_password="",
                mail_type='activation',
                context=context
            )
            
            print(f"✅ Email verification sent to {user.email}")
            
        except Exception as e:
            print(f"❌ Failed to send email verification: {e}")
            raise


@celery_app.task(name='tasks.email_tasks.send_email_change_confirmation')
def send_email_change_confirmation(user_id: str, new_email: str, old_email: str, confirmation_token: str):
    """
    Send email change confirmation (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            user_result = db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return
            
            context = {
                "user_name": user.firstname,
                "old_email": old_email,
                "new_email": new_email,
                "confirmation_link": f"{settings.FRONTEND_URL}/confirm-email?token={confirmation_token}",
                "company_name": "Banwee",
            }
            
            send_email(
                to_email=new_email,
                from_email="",
                from_password="",
                mail_type='email_change',
                context=context
            )
            
            print(f"✅ Email change confirmation sent to {new_email}")
            
        except Exception as e:
            print(f"❌ Failed to send email change confirmation: {e}")
            raise


@celery_app.task(name='tasks.email_tasks.send_order_delivered_email')
def send_order_delivered_email(order_id: str):
    """
    Send order delivered email (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            result = db.execute(
                select(Order).where(Order.id == UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                return
            
            user_result = db.execute(
                select(User).where(User.id == order.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return
            
            # Fetch order items (SYNC)
            order_items = []
            for item in order.items:
                variant_result = db.execute(
                    select(ProductVariant).where(ProductVariant.id == item.variant_id)
                )
                variant = variant_result.scalar_one_or_none()
                order_items.append({
                    "name": variant.name if variant else "Unknown Item",
                    "quantity": item.quantity,
                })
            
            context = {
                "customer_name": user.firstname,
                "order_number": str(order.id),
                "delivery_date": order.updated_at.strftime("%B %d, %Y"),
                "order_items": order_items,
                "review_link": f"{settings.FRONTEND_URL}/account/orders/{order.id}/review",
                "company_name": "Banwee",
            }
            
            send_email(
                to_email=user.email,
                from_email="",
                from_password="",
                mail_type='order_delivered',
                context=context
            )
            
            print(f"✅ Order delivered email sent to {user.email}")
            
        except Exception as e:
            print(f"❌ Failed to send order delivered email: {e}")
            raise


@celery_app.task(name='tasks.email_tasks.send_return_process_email')
def send_return_process_email(order_id: str, return_instructions: str):
    """
    Send return process instructions email (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            result = db.execute(
                select(Order).where(Order.id == UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                return
            
            user_result = db.execute(
                select(User).where(User.id == order.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return
            
            context = {
                "customer_name": user.firstname,
                "order_number": str(order.id),
                "return_instructions": return_instructions,
                "return_label_url": f"{settings.FRONTEND_URL}/returns/{order.id}/label",
                "company_name": "Banwee",
            }
            
            send_email(
                to_email=user.email,
                from_email="",
                from_password="",
                mail_type='return_process',
                context=context
            )
            
            print(f"✅ Return process email sent to {user.email}")
            
        except Exception as e:
            print(f"❌ Failed to send return process email: {e}")
            raise


@celery_app.task(name='tasks.email_tasks.send_referral_request_email')
def send_referral_request_email(user_id: str, referral_code: str):
    """
    Send referral request email after positive review or repeat purchase (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            user_result = db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return
            
            context = {
                "user_name": user.firstname,
                "referral_link": f"{settings.FRONTEND_URL}/register?ref={referral_code}",
                "referral_code": referral_code,
                "reward_amount": "$10",  # Configure as needed
                "company_name": "Banwee",
            }
            
            send_email(
                to_email=user.email,
                from_email="",
                from_password="",
                mail_type='referral_request',
                context=context
            )
            
            print(f"✅ Referral request email sent to {user.email}")
            
        except Exception as e:
            print(f"❌ Failed to send referral request email: {e}")
            raise


@celery_app.task(name='tasks.email_tasks.send_review_requests')
def send_review_requests():
    """
    Periodic task to send review request emails
    """
    # TODO: Implement review request logic
    print("🔄 Checking for orders ready for review...")
