import requests
import os
import resend
from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.config import settings

# This is your MailSlurp API key

resend.api_key = settings.RESEND_API_KEY

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)

# Utility to render Jinja2 template with context
def render_email(template_name: str, context: dict) -> str:
    

    try:
        template = env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        print(f"Template rendering error: {e}")
        raise RuntimeError(f"Template rendering error: {e}")

# Central dispatch function
def send_email(
    to_email: str,
    from_email: str,
    from_password: str,
    mail_type: str,
    context: dict = {}
):
    subject_map = {
        # 1. Pre-Purchase / Lead Nurturing
        "store_launch": "Store Launch 🚀",
        "waitlist_notification": "Back in Stock Alert!",
        "product_launch": "New Product Launch 🚀",
        "back_in_stock": "Your Favorite Item is Back!",
        "cart_abandonment": "Forgot Something in Your Cart?",
        "price_drop": "Price Drop Alert!",
        "browse_abandonment": "Still Thinking About This?",
        "wishlist_reminder": "A Wishlist Item is Waiting for You",

        # 2. Purchase Related
        "order_confirmation": "Order Confirmation",
        "payment_receipt": "Payment Receipt",
        "shipping_update": "Shipping Update",
        "order_delivered": "Your Order Has Been Delivered",
        "digital_delivery": "Your Digital Product is Ready",
        "out_for_delivery": "Your Order is Out for Delivery",
        "partial_shipment": "Partial Shipment Notification",

        # 3. Post-Purchase
        "thank_you": "Thank You for Your Purchase!",
        "review_request": "Tell Us What You Think",
        "referral_request": "Refer a Friend & Get Rewards",
        "product_tips": "How to Use Your Product",
        "warranty_reminder": "Register Your Warranty",
        "reorder_reminder": "Time to Reorder?",
        "return_process": "Return Instructions",

        # 4. Account & Engagement
        "welcome": "Welcome to Our Store!",
        "onboarding": "Let’s Get You Started",
        "activation": "Activate Your Account",
        "email_change":'Change Email',
        "password_reset": "Reset Your Password",
        "login_alert": "Login Alert",
        "profile_update": "Profile Update Confirmation",
        "unsubscribe_confirmation": "Unsubscribe Confirmation",

        # 5. Marketing
        "newsletter": "Latest News & Offers",
        "flash_sale": "⚡ Flash Sale - Don’t Miss Out!",
        "holiday_campaign": "Seasonal Special Just for You",
        "loyalty_update": "Your Loyalty Perks",
        "birthday_offer": "Happy Birthday 🎉",
        "cross_sell": "You Might Also Like These",
        "event_invite": "You’re Invited!",

        # 6. Transactional / System
        "payment_failed": "Payment Failed",
        "subscription_update": "Subscription Update",
        "invoice": "Your Invoice",
        "fraud_alert": "Suspicious Activity Detected",
        "maintenance_notice": "Scheduled Maintenance",

        # 7. Legal / Compliance
        "policy_update": "We’ve Updated Our Policies",
        "gdpr_confirmation": "Your GDPR Request",
        "cookie_settings": "Your Cookie Preferences",
    }

    template_map = {
        # Pre-Purchase
        "store_launch": "pre_purchase/store_launch.html",
        "waitlist_notification": "pre_purchase/waitlist_notification.html",
        "product_launch": "pre_purchase/product_launch.html",
        "back_in_stock": "pre_purchase/back_in_stock.html",
        "cart_abandonment": "pre_purchase/cart_abandonment.html",
        "price_drop": "pre_purchase/price_drop.html",
        "browse_abandonment": "pre_purchase/browse_abandonment.html",
        "wishlist_reminder": "pre_purchase/wishlist_reminder.html",

        # Purchase Related
        "order_confirmation": "purchase/order_confirmation.html",
        "payment_receipt": "purchase/payment_receipt.html",
        "shipping_update": "purchase/shipping_update.html",
        "order_delivered": "purchase/order_delivered.html",
        "digital_delivery": "purchase/digital_delivery.html",
        "out_for_delivery": "purchase/out_for_delivery.html",
        "partial_shipment": "purchase/partial_shipment.html",

        # Post-Purchase
        "thank_you": "post_purchase/thank_you.html",
        "review_request": "post_purchase/review_request.html",
        "referral_request": "post_purchase/referral_request.html",
        "product_tips": "post_purchase/product_tips.html",
        "warranty_reminder": "post_purchase/warranty_reminder.html",
        "reorder_reminder": "post_purchase/reorder_reminder.html",
        "return_process": "post_purchase/return_process.html",

        # Account & Engagement
        "welcome": "account/welcome.html",
        "onboarding": "account/onboarding.html",
        "activation": "account/activation.html",
        "email_change": "account/email_change.html",
        "password_reset": "account/password_reset.html",
        "login_alert": "account/login_alert.html",
        "profile_update": "account/profile_update.html",
        "unsubscribe_confirmation": "account/unsubscribe_confirmation.html",

        # Marketing
        "newsletter": "marketing/newsletter.html",
        "flash_sale": "marketing/flash_sale.html",
        "holiday_campaign": "marketing/holiday_campaign.html",
        "loyalty_update": "marketing/loyalty_update.html",
        "birthday_offer": "marketing/birthday_offer.html",
        "cross_sell": "marketing/cross_sell.html",
        "event_invite": "marketing/event_invite.html",

        # Transactional / System
        "payment_failed": "system/payment_failed.html",
        "subscription_update": "system/subscription_update.html",
        "invoice": "system/invoice.html",
        "fraud_alert": "system/fraud_alert.html",
        "maintenance_notice": "system/maintenance_notice.html",

        # Legal / Compliance
        "policy_update": "legal/policy_update.html",
        "gdpr_confirmation": "legal/gdpr_confirmation.html",
        "cookie_settings": "legal/cookie_settings.html",
    }

    subject = subject_map.get(mail_type, "Notification")
    template_name = template_map.get(mail_type)

    if not template_name:
        print(f"No template found for mail_type: {mail_type}")
        return

    try:
        html_body = render_email(template_name, context)
        text_body = context.get("text_body", "This is a plain-text fallback.")
        print('📤 Sending email...')

        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "Banwee <onboarding@resend.dev>",  # Must be verified
                "to": [to_email],
                "subject": subject,
                "html": html_body,
                "text": text_body
            },
            timeout=10
        )

        response.raise_for_status()
        data = response.json()
        print("✅ Email sent successfully:", data)
        return data

    except requests.exceptions.HTTPError as http_err:
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text
        print(f"❌ HTTP error: {http_err}")
        print(f"🔍 Detail: {error_detail}")
        raise

    except requests.exceptions.Timeout:
        print("❌ Request timed out.")
        raise

    except requests.exceptions.ConnectionError as conn_err:
        print(f"❌ Connection error: {conn_err}")
        raise

    except Exception as err:
        print(f"❌ Unexpected error: {err}")
        raise
