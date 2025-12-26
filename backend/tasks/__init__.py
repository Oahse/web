"""
Tasks package for background processing
"""
from .email_tasks import (
    send_order_confirmation_email,
    send_shipping_update_email,
    send_welcome_email,
    send_password_reset_email,
    send_email_verification,
    send_email_change_confirmation,
    send_order_delivered_email,
    send_return_process_email,
    send_referral_request_email,
    send_low_stock_alert_email,
    EmailTaskService,
    email_task_service,
    process_email_task
)

__all__ = [
    "send_order_confirmation_email",
    "send_shipping_update_email", 
    "send_welcome_email",
    "send_password_reset_email",
    "send_email_verification",
    "send_email_change_confirmation",
    "send_order_delivered_email",
    "send_return_process_email",
    "send_referral_request_email",
    "send_low_stock_alert_email",
    "EmailTaskService",
    "email_task_service",
    "process_email_task"
]