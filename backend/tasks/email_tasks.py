"""
Email tasks using Hybrid approach (FastAPI BackgroundTasks + ARQ)
Quick email tasks use FastAPI BackgroundTasks, complex/retry tasks use ARQ
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.hybrid_tasks import hybrid_task_manager, send_email_hybrid
from core.utils.messages.email import send_email
from services.jinja_template import JinjaTemplateService

logger = logging.getLogger(__name__)


class EmailTaskService:
    """Service for handling email tasks with hybrid processing"""
    
    def __init__(self):
        self.template_service = JinjaTemplateService(template_dir="core/utils/messages/templates")
    
    async def _send_email_direct(self, email_data: Dict[str, Any]):
        """Send email directly"""
        try:
            await send_email(
                to_email=email_data['to_email'],
                mail_type=email_data['mail_type'],
                context=email_data['context']
            )
            logger.info(f"Email sent directly: {email_data['mail_type']} to {email_data['to_email']}")
        except Exception as e:
            logger.error(f"Failed to send email directly: {e}")
    
    def add_email_task(self, background_tasks: BackgroundTasks, email_data: Dict[str, Any], use_arq: bool = True):
        """Add email task using hybrid approach"""
        if use_arq:
            # Use ARQ for reliability and retries
            background_tasks.add_task(
                send_email_hybrid,
                None,  # No background_tasks for ARQ
                email_data['mail_type'],
                email_data['to_email'],
                True,  # use_arq=True
                **email_data['context']
            )
        else:
            # Use FastAPI BackgroundTasks for immediate processing
            background_tasks.add_task(self._send_email_direct, email_data)


# Global instance
email_task_service = EmailTaskService()


# Email task functions
def send_order_confirmation_email(
    background_tasks: BackgroundTasks,
    to_email: str,
    customer_name: str,
    order_number: str,
    order_date: datetime,
    total_amount: float,
    items: List[Dict[str, Any]] = None,
    shipping_address: Dict[str, Any] = None
):
    """Send order confirmation email"""
    context = {
        "customer_name": customer_name,
        "order_number": order_number,
        "order_date": order_date,
        "total_amount": total_amount,
        "items": items or [],
        "shipping_address": shipping_address,
        "company_name": "Banwee",
        "support_email": "support@banwee.com",
        "current_year": datetime.now().year
    }
    
    email_data = {
        "to_email": to_email,
        "mail_type": "order_confirmation",
        "context": context,
        "template": "purchase/order_confirmation.html"
    }
    
    email_task_service.add_email_task(background_tasks, email_data)


def send_shipping_update_email(
    background_tasks: BackgroundTasks,
    to_email: str,
    customer_name: str,
    order_number: str,
    tracking_number: str,
    carrier: str,
    estimated_delivery: datetime,
    tracking_url: Optional[str] = None
):
    """Send shipping update email"""
    context = {
        "customer_name": customer_name,
        "order_number": order_number,
        "tracking_number": tracking_number,
        "carrier": carrier,
        "estimated_delivery": estimated_delivery,
        "tracking_url": tracking_url,
        "company_name": "Banwee",
        "support_email": "support@banwee.com",
        "current_year": datetime.now().year
    }
    
    email_data = {
        "to_email": to_email,
        "mail_type": "shipping_update",
        "context": context,
        "template": "purchase/shipping_update.html"
    }
    
    email_task_service.add_email_task(background_tasks, email_data)


def send_welcome_email(
    background_tasks: BackgroundTasks,
    to_email: str,
    customer_name: str,
    verification_required: bool = False,
    verification_url: Optional[str] = None
):
    """Send welcome email"""
    context = {
        "customer_name": customer_name,
        "verification_required": verification_required,
        "verification_url": verification_url,
        "company_name": "Banwee",
        "support_email": "support@banwee.com",
        "current_year": datetime.now().year
    }
    
    email_data = {
        "to_email": to_email,
        "mail_type": "welcome",
        "context": context,
        "template": "account/welcome.html"
    }
    
    email_task_service.add_email_task(background_tasks, email_data)


def send_password_reset_email(
    background_tasks: BackgroundTasks,
    to_email: str,
    customer_name: str,
    reset_link: str
):
    """Send password reset email"""
    context = {
        "customer_name": customer_name,
        "reset_link": reset_link,
        "company_name": "Banwee",
        "support_email": "support@banwee.com",
        "current_year": datetime.now().year
    }
    
    email_data = {
        "to_email": to_email,
        "mail_type": "password_reset",
        "context": context,
        "template": "account/password_reset.html"
    }
    
    email_task_service.add_email_task(background_tasks, email_data)


def send_email_verification(
    background_tasks: BackgroundTasks,
    to_email: str,
    customer_name: str,
    verification_url: str
):
    """Send email verification"""
    context = {
        "customer_name": customer_name,
        "verification_url": verification_url,
        "company_name": "Banwee",
        "support_email": "support@banwee.com",
        "current_year": datetime.now().year
    }
    
    email_data = {
        "to_email": to_email,
        "mail_type": "email_verification",
        "context": context,
        "template": "account/activation.html"
    }
    
    email_task_service.add_email_task(background_tasks, email_data)


def send_email_change_confirmation(
    background_tasks: BackgroundTasks,
    to_email: str,
    customer_name: str,
    old_email: str,
    new_email: str,
    confirmation_url: str
):
    """Send email change confirmation"""
    context = {
        "customer_name": customer_name,
        "old_email": old_email,
        "new_email": new_email,
        "confirmation_url": confirmation_url,
        "company_name": "Banwee",
        "support_email": "support@banwee.com",
        "current_year": datetime.now().year
    }
    
    email_data = {
        "to_email": to_email,
        "mail_type": "email_change",
        "context": context,
        "template": "account/email_change.html"
    }
    
    email_task_service.add_email_task(background_tasks, email_data)


def send_order_delivered_email(
    background_tasks: BackgroundTasks,
    to_email: str,
    customer_name: str,
    order_number: str,
    delivery_date: datetime,
    delivery_address: str,
    delivery_notes: Optional[str] = None,
    review_url: Optional[str] = None
):
    """Send order delivered email"""
    context = {
        "customer_name": customer_name,
        "order_number": order_number,
        "delivery_date": delivery_date,
        "delivery_address": delivery_address,
        "delivery_notes": delivery_notes,
        "review_url": review_url,
        "company_name": "Banwee",
        "support_email": "support@banwee.com",
        "current_year": datetime.now().year
    }
    
    email_data = {
        "to_email": to_email,
        "mail_type": "order_delivered",
        "context": context,
        "template": "purchase/order_delivered.html"
    }
    
    email_task_service.add_email_task(background_tasks, email_data)


def send_return_process_email(
    background_tasks: BackgroundTasks,
    to_email: str,
    customer_name: str,
    return_number: str,
    order_number: str,
    return_status: str,
    return_date: datetime,
    return_items: List[Dict[str, Any]] = None,
    refund_amount: Optional[float] = None,
    processing_time: Optional[str] = None
):
    """Send return process email"""
    context = {
        "customer_name": customer_name,
        "return_number": return_number,
        "order_number": order_number,
        "return_status": return_status,
        "return_date": return_date,
        "return_items": return_items or [],
        "refund_amount": refund_amount,
        "processing_time": processing_time,
        "company_name": "Banwee",
        "support_email": "support@banwee.com",
        "current_year": datetime.now().year
    }
    
    email_data = {
        "to_email": to_email,
        "mail_type": "return_process",
        "context": context,
        "template": "post_purchase/return_process.html"
    }
    
    email_task_service.add_email_task(background_tasks, email_data)


def send_referral_request_email(
    background_tasks: BackgroundTasks,
    to_email: str,
    customer_name: str,
    referral_code: str,
    referral_url: Optional[str] = None,
    friend_discount: int = 10,
    referrer_reward: str = "$10",
    current_referrals: Optional[Dict[str, Any]] = None
):
    """Send referral request email"""
    context = {
        "customer_name": customer_name,
        "referral_code": referral_code,
        "referral_url": referral_url,
        "friend_discount": friend_discount,
        "referrer_reward": referrer_reward,
        "current_referrals": current_referrals,
        "company_name": "Banwee",
        "support_email": "support@banwee.com",
        "current_year": datetime.now().year
    }
    
    email_data = {
        "to_email": to_email,
        "mail_type": "referral_request",
        "context": context,
        "template": "post_purchase/referral_request.html"
    }
    
    email_task_service.add_email_task(background_tasks, email_data)


def send_low_stock_alert_email(
    background_tasks: BackgroundTasks,
    to_email: str,
    recipient_name: str,
    low_stock_products: List[Dict[str, Any]],
    alert_date: Optional[datetime] = None
):
    """Send low stock alert email"""
    context = {
        "recipient_name": recipient_name,
        "low_stock_products": low_stock_products,
        "alert_date": alert_date or datetime.now(),
        "company_name": "Banwee",
        "support_email": "support@banwee.com",
        "current_year": datetime.now().year
    }
    
    email_data = {
        "to_email": to_email,
        "mail_type": "low_stock_alert",
        "context": context,
        "template": "system/low_stock_alert.html"  # We'll need to create this template
    }
    
    email_task_service.add_email_task(background_tasks, email_data)


# Kafka consumer for processing email tasks
async def process_email_task(message: Dict[str, Any]):
    """Process email task from Kafka"""
    try:
        await send_email(
            to_email=message['to_email'],
            mail_type=message['mail_type'],
            context=message['context']
        )
        logger.info(f"Processed email task: {message['mail_type']} to {message['to_email']}")
    except Exception as e:
        logger.error(f"Failed to process email task: {e}")
        # Could implement retry logic here