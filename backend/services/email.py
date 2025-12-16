from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.user import User, Address
from models.order import Order
from models.product import ProductVariant
from tasks.email_tasks import (
    send_order_confirmation_email,
    send_shipping_update_email,
    send_welcome_email,
    send_password_reset_email,
    send_email_verification,
    send_email_change_confirmation,
    send_order_delivered_email,
    send_return_process_email,
    send_referral_request_email,
    send_low_stock_alert_email, # NEW
)
from core.config import settings
from core.exceptions import CustomException # Assuming CustomException is suitable for service layer errors


class EmailService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def _get_user_by_id(self, user_id: UUID) -> User:
        result = await self.db_session.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise CustomException(status_code=404, message="User not found for email operation.")
        return user

    async def _get_order_by_id(self, order_id: UUID) -> Order:
        result = await self.db_session.execute(select(Order).filter(Order.id == order_id))
        order = result.scalars().first()
        if not order:
            raise CustomException(status_code=404, message="Order not found for email operation.")
        return order

    async def _get_address_by_id(self, address_id: UUID) -> Optional[Address]:
        result = await self.db_session.execute(select(Address).filter(Address.id == address_id))
        return result.scalars().first()

    async def _get_product_variant_by_id(self, variant_id: UUID) -> Optional[ProductVariant]:
        result = await self.db_session.execute(select(ProductVariant).filter(ProductVariant.id == variant_id))
        return result.scalars().first()

    async def send_order_confirmation(self, order_id: UUID):
        order = await self._get_order_by_id(order_id)
        user = await self._get_user_by_id(order.user_id)
        shipping_address = await self._get_address_by_id(order.shipping_address_id) if order.shipping_address_id else None

        order_items = []
        for item in order.items:
            variant = await self._get_product_variant_by_id(item.variant_id)
            order_items.append({
                "name": variant.name if variant else "Unknown Item",
                "quantity": item.quantity,
                "price": f"{item.total_price:.2f}" # Format as string here
            })

        context = {
            "customer_name": user.firstname,
            "order_number": str(order.id),
            "order_date": order.created_at.strftime("%B %d, %Y"),
            "order_total": f"{order.total_amount:.2f}",
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
        send_order_confirmation_email.delay(str(order_id), context)

    async def send_shipping_update(self, order_id: UUID, carrier_name: str, tracking_number: str):
        order = await self._get_order_by_id(order_id)
        user = await self._get_user_by_id(order.user_id)
        shipping_address = await self._get_address_by_id(order.shipping_address_id) if order.shipping_address_id else None

        context = {
            "customer_name": user.firstname,
            "order_number": str(order.id),
            "tracking_number": tracking_number,
            "carrier_name": carrier_name,
            "shipping_address": {
                "line1": shipping_address.street,
                "city": shipping_address.city,
            } if shipping_address else {},
            "tracking_url": f"https://www.google.com/search?q={carrier_name}+{tracking_number}",
            "company_name": "Banwee",
        }
        send_shipping_update_email.delay(str(order_id), carrier_name, context)

    async def send_welcome(self, user_id: UUID):
        user = await self._get_user_by_id(user_id)
        context = {
            "user_name": user.firstname,
            "email": user.email,
            "store_url": settings.FRONTEND_URL,
            "company_name": "Banwee",
        }
        send_welcome_email.delay(str(user_id), context)

    async def send_password_reset(self, user_id: UUID, reset_token: str):
        user = await self._get_user_by_id(user_id)
        context = {
            "user_name": user.firstname,
            "reset_link": f"{settings.FRONTEND_URL}/reset-password?token={reset_token}",
            "expiry_time": "1 hour",
            "company_name": "Banwee",
        }
        send_password_reset_email.delay(str(user_id), reset_token, context)

    async def send_email_verification_link(self, user_id: UUID, verification_token: str):
        user = await self._get_user_by_id(user_id)
        context = {
            "user_name": user.firstname,
            "activation_link": f"{settings.FRONTEND_URL}/verify-email?token={verification_token}",
            "company_name": "Banwee",
        }
        send_email_verification.delay(str(user_id), verification_token, context)

    async def send_email_change_confirmation_link(self, user_id: UUID, new_email: str, old_email: str, confirmation_token: str):
        user = await self._get_user_by_id(user_id)
        context = {
            "user_name": user.firstname,
            "old_email": old_email,
            "new_email": new_email,
            "confirmation_link": f"{settings.FRONTEND_URL}/confirm-email?token={confirmation_token}",
            "company_name": "Banwee",
        }
        send_email_change_confirmation.delay(str(user_id), new_email, old_email, confirmation_token, context)

    async def send_order_delivered(self, order_id: UUID):
        order = await self._get_order_by_id(order_id)
        user = await self._get_user_by_id(order.user_id)

        order_items = []
        for item in order.items:
            variant = await self._get_product_variant_by_id(item.variant_id)
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
        send_order_delivered_email.delay(str(order_id), context)

    async def send_return_process_instructions(self, order_id: UUID, return_instructions: str):
        order = await self._get_order_by_id(order_id)
        user = await self._get_user_by_id(order.user_id)

        context = {
            "customer_name": user.firstname,
            "order_number": str(order.id),
            "return_instructions": return_instructions,
            "return_label_url": f"{settings.FRONTEND_URL}/returns/{order.id}/label",
            "company_name": "Banwee",
        }
        send_return_process_email.delay(str(order_id), return_instructions, context)

    async def send_referral_request(self, user_id: UUID, referral_code: str):
        user = await self._get_user_by_id(user_id)
        context = {
            "user_name": user.firstname,
            "referral_link": f"{settings.FRONTEND_URL}/register?ref={referral_code}",
            "referral_code": referral_code,
            "reward_amount": "$10",  # Configure as needed
            "company_name": "Banwee",
        }
        send_referral_request_email.delay(str(user_id), referral_code, context)

    async def send_low_stock_alert(self, recipient_email: str, product_name: str, variant_name: str, location_name: str, current_stock: int, threshold: int):
        """
        Sends an email notification for a low stock alert.
        """
        context = {
            "recipient_email": recipient_email,
            "product_name": product_name,
            "variant_name": variant_name,
            "location_name": location_name,
            "current_stock": current_stock,
            "threshold": threshold,
            "admin_inventory_link": f"{settings.FRONTEND_URL}/admin/inventory", # Link to admin inventory page
            "company_name": "Banwee",
        }
        send_low_stock_alert_email.delay(recipient_email, context)
        print(f"📧 Celery task dispatched to send low stock alert email to {recipient_email}.")