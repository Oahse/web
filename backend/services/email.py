from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.user import User, Address
from models.orders import Order
from models.product import ProductVariant
from services.templates import JinjaTemplateService
# Email tasks are imported separately where needed
# from tasks.email_tasks import (...)
from lib.config import settings
from core.hybrid_tasks import send_email_hybrid
from lib.errors import APIException # Assuming APIException is suitable for service layer errors



class EmailService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.template_service = JinjaTemplateService(template_dir="core/utils/messages/templates")

    async def _get_user_by_id(self, user_id: UUID) -> User:
        result = await self.db_session.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise APIException(status_code=404, message="User not found for email operation.")
        return user

    async def _get_order_by_id(self, order_id: UUID) -> Order:
        result = await self.db_session.execute(select(Order).filter(Order.id == order_id))
        order = result.scalars().first()
        if not order:
            raise APIException(status_code=404, message="Order not found for email operation.")
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
        from core.hybrid_tasks import send_email_hybrid
        await send_email_hybrid(None, "order_confirmation", user.email, use_arq=True, order_id=str(order_id), **context)

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
        from core.hybrid_tasks import send_email_hybrid
        await send_email_hybrid(None, "shipping_update", user.email, use_arq=True, order_id=str(order_id), carrier_name=carrier_name, **context)

    async def send_welcome(self, user_id: UUID):
        user = await self._get_user_by_id(user_id)
        context = {
            "user_name": user.firstname,
            "email": user.email,
            "store_url": settings.FRONTEND_URL,
            "company_name": "Banwee",
        }
        await send_email_hybrid(None, "welcome", user.email, use_arq=True, user_name=user.firstname or user.email, **context)

    async def send_password_reset(self, user_id: UUID, reset_token: str):
        user = await self._get_user_by_id(user_id)
        context = {
            "user_name": user.firstname,
            "reset_link": f"{settings.FRONTEND_URL}/reset-password?token={reset_token}",
            "expiry_time": "1 hour",
            "company_name": "Banwee",
        }
        await send_email_hybrid(None, "password_reset", user.email, use_arq=True, reset_token=reset_token, **context)

    async def send_email_verification_link(self, user_id: UUID, verification_token: str):
        user = await self._get_user_by_id(user_id)
        context = {
            "user_name": user.firstname,
            "activation_link": f"{settings.FRONTEND_URL}/verify-email?token={verification_token}",
            "company_name": "Banwee",
        }
        await send_email_hybrid(None, "email_verification", user.email, use_arq=True, verification_token=verification_token, **context)

    async def send_email_change_confirmation_link(self, user_id: UUID, new_email: str, old_email: str, confirmation_token: str):
        user = await self._get_user_by_id(user_id)
        context = {
            "user_name": user.firstname,
            "old_email": old_email,
            "new_email": new_email,
            "confirmation_link": f"{settings.FRONTEND_URL}/confirm-email?token={confirmation_token}",
            "company_name": "Banwee",
        }
        await send_email_hybrid(None, "email_change_confirmation", old_email, use_arq=True, new_email=new_email, confirmation_token=confirmation_token, **context)

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
        await send_email_hybrid(None, "order_delivered", user.email, use_arq=True, order_id=str(order_id), **context)

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
        await send_email_hybrid(None, "return_process", user.email, use_arq=True, order_id=str(order_id), return_instructions=return_instructions, **context)

    async def send_referral_request(self, user_id: UUID, referral_code: str):
        user = await self._get_user_by_id(user_id)
        context = {
            "user_name": user.firstname,
            "referral_link": f"{settings.FRONTEND_URL}/register?ref={referral_code}",
            "referral_code": referral_code,
            "reward_amount": "$10",  # Configure as needed
            "company_name": "Banwee",
        }
        await send_email_hybrid(None, "referral_request", user.email, use_arq=True, referral_code=referral_code, **context)

    async def send_low_stock_alert(self, recipient_email: str, product_name: str, variant_name: str, location_name: str, current_stock: int, threshold: int):
        """
        Sends an email alert for a low stock situation.
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
        await send_email_hybrid(None, "low_stock_alert", recipient_email, use_arq=True,
                          product_name=product_name, variant_name=variant_name, 
                          location_name=location_name, current_stock=current_stock, 
                          threshold=threshold, **context)
        print(f"📧 ARQ task queued to send low stock alert email to {recipient_email}.")
        
    async def send_payment_method_expiration_notice(self, user_id: UUID, payment_method_id: UUID):
        """
        Sends an email to a user about their expiring payment method.
        """
        from models.payments import PaymentMethod
        
        user = await self._get_user_by_id(user_id)
        payment_method = await self.db_session.get(PaymentMethod, payment_method_id)
        
        if not user or not payment_method:
            return

        context = {
            "user_name": user.firstname,
            "payment_method_provider": payment_method.provider.title(),
            "payment_method_last_four": payment_method.last_four,
            "expiry_date": f"{payment_method.expiry_month:02d}/{payment_method.expiry_year}",
        "update_payment_url": f"{settings.FRONTEND_URL}/account/payment-methods",
        "company_name": "Banwee",
        }
        await send_email_hybrid(None, "payment_method_expiration", user.email, use_arq=True,
                          payment_method_id=str(payment_method_id), **context)
        print(f"📧 ARQ task queued for payment method expiration notice to {user.email}.")
    
    async def send_subscription_cost_change_email(
        self, 
        user_id: UUID, 
        subscription_id: UUID,
        old_cost: float,
        new_cost: float,
        change_reason: str
    ):
        """
        Send email when subscription cost changes
        """
        user = await self._get_user_by_id(user_id)
        
        context = {
            "user_name": user.firstname,
            "subscription_id": str(subscription_id),
            "old_cost": old_cost,
            "new_cost": new_cost,
            "cost_difference": new_cost - old_cost,
            "change_reason": change_reason,
            "subscription_management_url": f"{settings.FRONTEND_URL}/account/subscriptions/{subscription_id}",
            "company_name": "Banwee",
        }
        
        await send_email_hybrid(None, "subscription_cost_change", user.email, use_arq=True,
                          subscription_id=str(subscription_id), old_cost=old_cost, 
                          new_cost=new_cost, change_reason=change_reason, **context)
        print(f"📧 Subscription cost change email sent to {user.email}")
    
    async def send_payment_confirmation(
        self,
        user_id: UUID,
        subscription_id: UUID,
        payment_amount: float,
        payment_method: str,
        cost_breakdown: Dict[str, Any]
    ):
        """
        Send payment confirmation email with detailed cost breakdown
        """
        user = await self._get_user_by_id(user_id)
        
        context = {
            "user_name": user.firstname,
            "subscription_id": str(subscription_id),
            "payment_amount": payment_amount,
            "payment_method": payment_method,
            "cost_breakdown": cost_breakdown,
            "payment_date": datetime.now().strftime("%B %d, %Y"),
            "subscription_management_url": f"{settings.FRONTEND_URL}/account/subscriptions/{subscription_id}",
            "company_name": "Banwee",
        }
        
        await send_email_hybrid(None, "payment_confirmation", user.email, use_arq=True,
                          subscription_id=str(subscription_id), payment_amount=payment_amount,
                          payment_method=payment_method, cost_breakdown=cost_breakdown, **context)
        print(f"📧 Payment confirmation sent to {user.email}")
    
    async def send_payment_failure_email(
        self,
        user_id: UUID,
        subscription_id: UUID,
        failure_reason: str,
        retry_url: str
    ):
        """
        Send payment failure email with retry instructions
        """
        user = await self._get_user_by_id(user_id)
        
        context = {
            "user_name": user.firstname,
            "subscription_id": str(subscription_id),
            "failure_reason": failure_reason,
            "retry_url": retry_url,
            "subscription_management_url": f"{settings.FRONTEND_URL}/account/subscriptions/{subscription_id}",
            "support_email": "support@banwee.com",
            "company_name": "Banwee",
        }
        
        await send_email_hybrid(None, "payment_failure", user.email, use_arq=True,
                          subscription_id=str(subscription_id), failure_reason=failure_reason,
                          retry_url=retry_url, **context)
        print(f"📧 Payment failure email sent to {user.email}")
    
    async def render_email_with_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render an email using Jinja template
        """
        try:
            rendered = await self.template_service.render_email_template(template_name, context)
            return rendered.content
        except Exception as e:
            print(f"❌ Failed to render email template {template_name}: {e}")
            raise
    