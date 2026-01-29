"""
Mailgun email service for sending emails
"""
import aiohttp
import asyncio
from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.config import settings
import os
from pathlib import Path

# Initialize Jinja environment directly to avoid circular imports
template_dir = Path("templates")
template_dir.mkdir(parents=True, exist_ok=True)

env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)

# Add custom filters
def _format_currency(value: float, currency: str = "USD") -> str:
    """Format currency values"""
    if currency == "USD":
        return f"${value:.2f}"
    return f"{value:.2f} {currency}"

def _format_date(value) -> str:
    """Format date values"""
    if hasattr(value, 'strftime'):
        return value.strftime('%B %d, %Y')
    return str(value)

def _format_datetime(value) -> str:
    """Format datetime values"""
    if hasattr(value, 'strftime'):
        return value.strftime('%B %d, %Y at %I:%M %p')
    return str(value)

env.filters['currency'] = _format_currency
env.filters['date'] = _format_date
env.filters['datetime'] = _format_datetime


async def render_email(template_name: str, context: dict) -> str:
    """Render Jinja2 template with context"""
    try:
        template = env.get_template(template_name)
        
        # Add common email context variables
        email_context = {
            **context,
            'company_name': context.get('company_name', 'Banwee'),
            'support_email': context.get('support_email', 'support@banwee.com'),
            'current_year': context.get('current_year', '2024')
        }
        
        return template.render(**email_context)
    except Exception as e:
        print(f"Template rendering error: {e}")
        raise RuntimeError(f"Template rendering error: {e}")


async def send_email_mailgun(
    to_email: str,
    subject: str = None,
    template_name: str = None,
    context: dict = {}
):
    """
    Send email using Mailgun API (async)
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        template_name: Template file name (e.g., 'emails/welcome.html')
        context: Template context variables
    """
    
    if not template_name:
        raise ValueError("template_name is required")
    
    if not subject:
        subject = "Notification from Banwee"

    try:
        html_body = await render_email(template_name, context)
        text_body = context.get("text_body", "This is a plain-text fallback.")
        
        print(f'📤 Sending email via Mailgun to {to_email}...')

        # Mailgun API endpoint
        mailgun_url = f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages"
        
        # Prepare form data
        data = {
            "from": settings.MAILGUN_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
            "text": text_body
        }
        
        # Send async request to Mailgun
        async with aiohttp.ClientSession() as session:
            async with session.post(
                mailgun_url,
                auth=aiohttp.BasicAuth("api", settings.MAILGUN_API_KEY),
                data=data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Email sent successfully via Mailgun: {result}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ Mailgun error ({response.status}): {error_text}")
                    raise Exception(f"Mailgun API error: {error_text}")

    except asyncio.TimeoutError:
        print("❌ Request timed out.")
        raise

    except Exception as err:
        print(f"❌ Unexpected error: {err}")
        raise


# Legacy function for backward compatibility with old mail_type system
async def send_email_mailgun_legacy(
    to_email: str,
    mail_type: str,
    context: dict = {}
):
    """
    Legacy function for backward compatibility
    """
    
    subject_map = {
        # Pre-Purchase / Lead Nurturing
        "store_launch": "Store Launch 🚀",
        "waitlist_notification": "Back in Stock Alert!",
        "product_launch": "New Product Launch 🚀",
        "back_in_stock": "Your Favorite Item is Back!",
        "cart_abandonment": "Forgot Something in Your Cart?",
        "price_drop": "Price Drop Alert!",
        "browse_abandonment": "Still Thinking About This?",
        "wishlist_reminder": "A Wishlist Item is Waiting for You",

        # Purchase Related
        "order_confirmation": "Order Confirmation",
        "payment_receipt": "Payment Receipt",
        "shipping_update": "Shipping Update",
        "order_delivered": "Your Order Has Been Delivered",
        "digital_delivery": "Your Digital Product is Ready",
        "out_for_delivery": "Your Order is Out for Delivery",
        "partial_shipment": "Partial Shipment Notification",

        # Post-Purchase
        "thank_you": "Thank You for Your Purchase!",
        "review_request": "Tell Us What You Think",
        "referral_request": "Refer a Friend & Get Rewards",
        "product_tips": "How to Use Your Product",
        "warranty_reminder": "Register Your Warranty",
        "reorder_reminder": "Time to Reorder?",
        "return_process": "Return Instructions",

        # Account & Engagement
        "welcome": "Welcome to Banwee!",
        "onboarding": "Let's Get You Started",
        "activation": "Activate Your Account",
        "email_change": 'Change Email',
        "password_reset": "Reset Your Password",
        "login_alert": "Login Alert",
        "profile_update": "Profile Update Confirmation",
        "unsubscribe_confirmation": "Unsubscribe Confirmation",

        # Marketing
        "newsletter": "Latest News & Offers",
        "flash_sale": "⚡ Flash Sale - Don't Miss Out!",
        "holiday_campaign": "Seasonal Special Just for You",
        "loyalty_update": "Your Loyalty Perks",
        "birthday_offer": "Happy Birthday 🎉",
        "cross_sell": "You Might Also Like These",
        "event_invite": "You're Invited!",

        # Transactional / System
        "payment_failed": "Payment Failed",
        "subscription_update": "Subscription Update",
        "invoice": "Your Invoice",
        "fraud_alert": "Suspicious Activity Detected",
        "maintenance_notice": "Scheduled Maintenance",
        
        # New subscription-related emails
        "subscription_cost_change": "Your Subscription Cost Has Changed",
        "payment_confirmation": "Payment Confirmation - Thank You!",
        "payment_failure": "Payment Issue - Action Required",
        "payment_method_expiring": "Your Payment Method is Expiring Soon",

        # Legal / Compliance
        "policy_update": "We've Updated Our Policies",
        "gdpr_confirmation": "Your GDPR Request",
        "cookie_settings": "Your Cookie Preferences",
    }

    template_map = {
        # Pre-Purchase
        "store_launch": "emails/pre_purchase/store_launch.html",
        "waitlist_notification": "emails/pre_purchase/waitlist_notification.html",
        "product_launch": "emails/pre_purchase/product_launch.html",
        "back_in_stock": "emails/pre_purchase/back_in_stock.html",
        "cart_abandonment": "emails/pre_purchase/cart_abandonment.html",
        "price_drop": "emails/pre_purchase/price_drop.html",
        "browse_abandonment": "emails/pre_purchase/browse_abandonment.html",
        "wishlist_reminder": "emails/pre_purchase/wishlist_reminder.html",

        # Purchase Related
        "order_confirmation": "emails/purchase/order_confirmation.html",
        "payment_receipt": "emails/purchase/payment_receipt.html",
        "shipping_update": "emails/purchase/shipping_update.html",
        "order_delivered": "emails/purchase/order_delivered.html",
        "digital_delivery": "emails/purchase/digital_delivery.html",
        "out_for_delivery": "emails/purchase/out_for_delivery.html",
        "partial_shipment": "emails/purchase/partial_shipment.html",

        # Post-Purchase
        "thank_you": "emails/post_purchase/thank_you.html",
        "review_request": "emails/post_purchase/review_request.html",
        "referral_request": "emails/post_purchase/referral_request.html",
        "product_tips": "emails/post_purchase/product_tips.html",
        "warranty_reminder": "emails/post_purchase/warranty_reminder.html",
        "reorder_reminder": "emails/post_purchase/reorder_reminder.html",
        "return_process": "emails/post_purchase/return_process.html",

        # Account & Engagement
        "welcome": "emails/account/welcome.html",
        "onboarding": "emails/account/onboarding.html",
        "activation": "emails/account/activation.html",
        "email_change": "emails/account/email_change.html",
        "password_reset": "emails/account/password_reset.html",
        "login_alert": "emails/account/login_alert.html",
        "profile_update": "emails/account/profile_update.html",
        "unsubscribe_confirmation": "emails/account/unsubscribe_confirmation.html",

        # Marketing
        "newsletter": "emails/marketing/newsletter.html",
        "flash_sale": "emails/marketing/flash_sale.html",
        "holiday_campaign": "emails/marketing/holiday_campaign.html",
        "loyalty_update": "emails/marketing/loyalty_update.html",
        "birthday_offer": "emails/marketing/birthday_offer.html",
        "cross_sell": "emails/marketing/cross_sell.html",
        "event_invite": "emails/marketing/event_invite.html",

        # Transactional / System
        "payment_failed": "emails/payment_failure.html",
        "subscription_update": "emails/system/subscription_update.html",
        "invoice": "emails/system/invoice.html",
        "fraud_alert": "emails/system/fraud_alert.html",
        "maintenance_notice": "emails/system/maintenance_notice.html",
        
        # New subscription-related emails
        "subscription_cost_change": "emails/subscription_cost_change.html",
        "payment_confirmation": "emails/payment_confirmation.html",
        "payment_failure": "emails/payment_failure.html",
        "payment_method_expiring": "emails/payment_method_expiring.html",

        # Legal / Compliance
        "policy_update": "emails/legal/policy_update.html",
        "gdpr_confirmation": "emails/legal/gdpr_confirmation.html",
        "cookie_settings": "emails/legal/cookie_settings.html",
    }

    subject = subject_map.get(mail_type, "Notification")
    template_name = template_map.get(mail_type)

    if not template_name:
        print(f"No template found for mail_type: {mail_type}")
        return

    return await send_email_mailgun(
        to_email=to_email,
        subject=subject,
        template_name=template_name,
        context=context
    )


# Synchronous wrapper for backward compatibility
def send_email_mailgun_sync(to_email: str, mail_type: str, context: dict = {}):
    """
    Synchronous wrapper for send_email_mailgun_legacy
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            send_email_mailgun_legacy(to_email, mail_type, context)
        )
    finally:
        loop.close()


# Alias for backward compatibility
send_email = send_email_mailgun_sync
