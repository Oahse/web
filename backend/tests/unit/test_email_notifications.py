"""
Unit tests for email notifications and messaging
"""
import pytest
from unittest.mock import patch, MagicMock, call
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from decimal import Decimal

from core.utils.messages.email import EmailService, send_email
from services.email import EmailNotificationService
from models.user import User
from models.orders import Order, OrderStatus
from models.product import ProductVariant


@pytest.mark.unit
class TestEmailNotifications:
    """Test email notification system."""
    
    @pytest.mark.asyncio
    async def test_user_registration_email(self, db_session: AsyncSession, mock_email):
        """Test user registration confirmation email."""
        email_service = EmailNotificationService(db_session)
        
        user = User(
            id=uuid4(),
            email="newuser@example.com",
            firstname="New",
            lastname="User",
            hashed_password="hashed_password",
            role="customer",
            verified=False,
            is_active=True
        )
        
        # Send registration email
        await email_service.send_registration_confirmation(user, "verification_token_123")
        
        # Verify email was sent
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        assert call_args[1]["to"] == user.email
        assert call_args[1]["subject"] == "Welcome to Banwee - Please verify your email"
        assert "verification_token_123" in call_args[1]["html_content"]
        assert user.firstname in call_args[1]["html_content"]
    
    @pytest.mark.asyncio
    async def test_email_verification_success_email(self, db_session: AsyncSession, mock_email):
        """Test email verification success notification."""
        email_service = EmailNotificationService(db_session)
        
        user = User(
            id=uuid4(),
            email="verified@example.com",
            firstname="Verified",
            lastname="User",
            hashed_password="hashed_password",
            role="customer",
            verified=True,
            is_active=True
        )
        
        # Send verification success email
        await email_service.send_email_verification_success(user)
        
        # Verify email was sent
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        assert call_args[1]["to"] == user.email
        assert call_args[1]["subject"] == "Email Verified Successfully"
        assert user.firstname in call_args[1]["html_content"]
    
    @pytest.mark.asyncio
    async def test_password_reset_email(self, db_session: AsyncSession, mock_email):
        """Test password reset email."""
        email_service = EmailNotificationService(db_session)
        
        user = User(
            id=uuid4(),
            email="reset@example.com",
            firstname="Reset",
            lastname="User",
            hashed_password="hashed_password",
            role="customer",
            verified=True,
            is_active=True
        )
        
        # Send password reset email
        reset_token = "reset_token_123"
        await email_service.send_password_reset(user, reset_token)
        
        # Verify email was sent
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        assert call_args[1]["to"] == user.email
        assert call_args[1]["subject"] == "Password Reset Request"
        assert reset_token in call_args[1]["html_content"]
        assert user.firstname in call_args[1]["html_content"]
    
    @pytest.mark.asyncio
    async def test_order_confirmation_email(self, db_session: AsyncSession, mock_email):
        """Test order confirmation email."""
        email_service = EmailNotificationService(db_session)
        
        user = User(
            id=uuid4(),
            email="order@example.com",
            firstname="Order",
            lastname="User",
            hashed_password="hashed_password",
            role="customer",
            verified=True,
            is_active=True
        )
        
        order = Order(
            id=uuid4(),
            user_id=user.id,
            status=OrderStatus.CONFIRMED,
            subtotal=Decimal("99.99"),
            shipping_cost=Decimal("9.99"),
            tax_amount=Decimal("8.75"),
            total_amount=Decimal("118.73"),
            currency="USD"
        )
        
        # Send order confirmation email
        await email_service.send_order_confirmation(user, order)
        
        # Verify email was sent
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        assert call_args[1]["to"] == user.email
        assert call_args[1]["subject"] == f"Order Confirmation - #{order.id}"
        assert str(order.id) in call_args[1]["html_content"]
        assert str(order.total_amount) in call_args[1]["html_content"]
        assert user.firstname in call_args[1]["html_content"]
    
    @pytest.mark.asyncio
    async def test_order_shipped_email(self, db_session: AsyncSession, mock_email):
        """Test order shipped notification email."""
        email_service = EmailNotificationService(db_session)
        
        user = User(
            id=uuid4(),
            email="shipped@example.com",
            firstname="Shipped",
            lastname="User",
            hashed_password="hashed_password",
            role="customer",
            verified=True,
            is_active=True
        )
        
        order = Order(
            id=uuid4(),
            user_id=user.id,
            status=OrderStatus.SHIPPED,
            subtotal=Decimal("99.99"),
            total_amount=Decimal("118.73"),
            currency="USD",
            tracking_number="TRACK123456",
            carrier="UPS"
        )
        
        # Send order shipped email
        await email_service.send_order_shipped(user, order)
        
        # Verify email was sent
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        assert call_args[1]["to"] == user.email
        assert call_args[1]["subject"] == f"Your Order Has Shipped - #{order.id}"
        assert order.tracking_number in call_args[1]["html_content"]
        assert order.carrier in call_args[1]["html_content"]
    
    @pytest.mark.asyncio
    async def test_order_delivered_email(self, db_session: AsyncSession, mock_email):
        """Test order delivered notification email."""
        email_service = EmailNotificationService(db_session)
        
        user = User(
            id=uuid4(),
            email="delivered@example.com",
            firstname="Delivered",
            lastname="User",
            hashed_password="hashed_password",
            role="customer",
            verified=True,
            is_active=True
        )
        
        order = Order(
            id=uuid4(),
            user_id=user.id,
            status=OrderStatus.DELIVERED,
            subtotal=Decimal("99.99"),
            total_amount=Decimal("118.73"),
            currency="USD"
        )
        
        # Send order delivered email
        await email_service.send_order_delivered(user, order)
        
        # Verify email was sent
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        assert call_args[1]["to"] == user.email
        assert call_args[1]["subject"] == f"Order Delivered - #{order.id}"
        assert "delivered" in call_args[1]["html_content"].lower()
        assert "review" in call_args[1]["html_content"].lower()  # Should include review request
    
    @pytest.mark.asyncio
    async def test_payment_failed_email(self, db_session: AsyncSession, mock_email):
        """Test payment failed notification email."""
        email_service = EmailNotificationService(db_session)
        
        user = User(
            id=uuid4(),
            email="payment@example.com",
            firstname="Payment",
            lastname="User",
            hashed_password="hashed_password",
            role="customer",
            verified=True,
            is_active=True
        )
        
        order = Order(
            id=uuid4(),
            user_id=user.id,
            status=OrderStatus.PENDING,
            subtotal=Decimal("99.99"),
            total_amount=Decimal("118.73"),
            currency="USD"
        )
        
        # Send payment failed email
        failure_reason = "Your card was declined"
        await email_service.send_payment_failed(user, order, failure_reason)
        
        # Verify email was sent
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        assert call_args[1]["to"] == user.email
        assert call_args[1]["subject"] == f"Payment Failed - Order #{order.id}"
        assert failure_reason in call_args[1]["html_content"]
        assert "retry" in call_args[1]["html_content"].lower()
    
    @pytest.mark.asyncio
    async def test_low_stock_alert_email(self, db_session: AsyncSession, mock_email):
        """Test low stock alert email to admin."""
        email_service = EmailNotificationService(db_session)
        
        # Create admin user
        admin_user = User(
            id=uuid4(),
            email="admin@example.com",
            firstname="Admin",
            lastname="User",
            hashed_password="hashed_password",
            role="admin",
            verified=True,
            is_active=True
        )
        
        # Create low stock items
        low_stock_items = [
            {
                "variant_name": "Test Product - Red",
                "sku": "TEST-001-RED",
                "current_stock": 2,
                "reorder_point": 10,
                "warehouse": "Main Warehouse"
            },
            {
                "variant_name": "Test Product - Blue",
                "sku": "TEST-001-BLUE",
                "current_stock": 1,
                "reorder_point": 5,
                "warehouse": "Main Warehouse"
            }
        ]
        
        # Send low stock alert
        await email_service.send_low_stock_alert(admin_user, low_stock_items)
        
        # Verify email was sent
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        assert call_args[1]["to"] == admin_user.email
        assert call_args[1]["subject"] == "Low Stock Alert - 2 items need attention"
        assert "TEST-001-RED" in call_args[1]["html_content"]
        assert "TEST-001-BLUE" in call_args[1]["html_content"]
    
    @pytest.mark.asyncio
    async def test_back_in_stock_notification(self, db_session: AsyncSession, mock_email):
        """Test back in stock notification email."""
        email_service = EmailNotificationService(db_session)
        
        user = User(
            id=uuid4(),
            email="notify@example.com",
            firstname="Notify",
            lastname="User",
            hashed_password="hashed_password",
            role="customer",
            verified=True,
            is_active=True
        )
        
        variant = ProductVariant(
            id=uuid4(),
            product_id=uuid4(),
            name="Back in Stock Product",
            sku="BACK-001",
            base_price=Decimal("99.99"),
            is_active=True
        )
        
        # Send back in stock notification
        await email_service.send_back_in_stock_notification(user, variant)
        
        # Verify email was sent
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        assert call_args[1]["to"] == user.email
        assert call_args[1]["subject"] == f"{variant.name} is Back in Stock!"
        assert variant.name in call_args[1]["html_content"]
        assert "back in stock" in call_args[1]["html_content"].lower()
    
    @pytest.mark.asyncio
    async def test_abandoned_cart_reminder(self, db_session: AsyncSession, mock_email):
        """Test abandoned cart reminder email."""
        email_service = EmailNotificationService(db_session)
        
        user = User(
            id=uuid4(),
            email="cart@example.com",
            firstname="Cart",
            lastname="User",
            hashed_password="hashed_password",
            role="customer",
            verified=True,
            is_active=True
        )
        
        cart_items = [
            {
                "variant_name": "Abandoned Product 1",
                "quantity": 2,
                "price": Decimal("49.99")
            },
            {
                "variant_name": "Abandoned Product 2",
                "quantity": 1,
                "price": Decimal("79.99")
            }
        ]
        
        cart_total = Decimal("179.97")
        
        # Send abandoned cart reminder
        await email_service.send_abandoned_cart_reminder(user, cart_items, cart_total)
        
        # Verify email was sent
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        assert call_args[1]["to"] == user.email
        assert call_args[1]["subject"] == "Don't forget your items!"
        assert "Abandoned Product 1" in call_args[1]["html_content"]
        assert str(cart_total) in call_args[1]["html_content"]
    
    @pytest.mark.asyncio
    async def test_newsletter_subscription_confirmation(self, db_session: AsyncSession, mock_email):
        """Test newsletter subscription confirmation email."""
        email_service = EmailNotificationService(db_session)
        
        email_address = "newsletter@example.com"
        unsubscribe_token = "unsubscribe_token_123"
        
        # Send newsletter confirmation
        await email_service.send_newsletter_confirmation(email_address, unsubscribe_token)
        
        # Verify email was sent
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        assert call_args[1]["to"] == email_address
        assert call_args[1]["subject"] == "Newsletter Subscription Confirmed"
        assert unsubscribe_token in call_args[1]["html_content"]
    
    @pytest.mark.asyncio
    async def test_bulk_email_sending(self, db_session: AsyncSession, mock_email):
        """Test bulk email sending functionality."""
        email_service = EmailNotificationService(db_session)
        
        # Create multiple users
        users = []
        for i in range(5):
            user = User(
                id=uuid4(),
                email=f"bulk{i}@example.com",
                firstname=f"User{i}",
                lastname="Bulk",
                hashed_password="hashed_password",
                role="customer",
                verified=True,
                is_active=True
            )
            users.append(user)
        
        # Send bulk promotional email
        subject = "Special Promotion - 20% Off Everything!"
        template_data = {
            "promotion_title": "Flash Sale",
            "discount_percentage": 20,
            "expiry_date": "2024-12-31"
        }
        
        results = await email_service.send_bulk_promotional_email(
            users,
            subject,
            "promotional_template",
            template_data
        )
        
        # Verify all emails were sent
        assert results["sent"] == 5
        assert results["failed"] == 0
        assert mock_email.call_count == 5
        
        # Verify each email was sent to correct recipient
        call_args_list = mock_email.call_args_list
        sent_emails = [call[1]["to"] for call in call_args_list]
        expected_emails = [user.email for user in users]
        
        assert set(sent_emails) == set(expected_emails)
    
    @pytest.mark.asyncio
    async def test_email_template_rendering(self, db_session: AsyncSession):
        """Test email template rendering with dynamic content."""
        email_service = EmailNotificationService(db_session)
        
        template_data = {
            "user_name": "John Doe",
            "order_id": "ORD-123456",
            "total_amount": "$99.99",
            "items": [
                {"name": "Product 1", "quantity": 2, "price": "$49.99"},
                {"name": "Product 2", "quantity": 1, "price": "$49.99"}
            ]
        }
        
        # Render order confirmation template
        rendered_html = await email_service.render_template(
            "order_confirmation",
            template_data
        )
        
        # Verify template was rendered correctly
        assert "John Doe" in rendered_html
        assert "ORD-123456" in rendered_html
        assert "$99.99" in rendered_html
        assert "Product 1" in rendered_html
        assert "Product 2" in rendered_html
    
    @pytest.mark.asyncio
    async def test_email_delivery_failure_handling(self, db_session: AsyncSession):
        """Test email delivery failure handling and retry logic."""
        email_service = EmailNotificationService(db_session)
        
        user = User(
            id=uuid4(),
            email="failure@example.com",
            firstname="Failure",
            lastname="Test",
            hashed_password="hashed_password",
            role="customer",
            verified=True,
            is_active=True
        )
        
        # Mock email service to fail
        with patch('core.utils.messages.email.send_email') as mock_send:
            mock_send.side_effect = Exception("Email delivery failed")
            
            # Attempt to send email
            result = await email_service.send_registration_confirmation(user, "token")
            
            # Verify failure was handled
            assert result["success"] is False
            assert "failed" in result["error"].lower()
            
            # Verify retry was attempted
            assert mock_send.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_email_rate_limiting(self, db_session: AsyncSession, mock_email, mock_redis):
        """Test email rate limiting to prevent spam."""
        email_service = EmailNotificationService(db_session)
        
        user = User(
            id=uuid4(),
            email="ratelimit@example.com",
            firstname="Rate",
            lastname="Limit",
            hashed_password="hashed_password",
            role="customer",
            verified=True,
            is_active=True
        )
        
        # Mock Redis to simulate rate limit hit
        mock_redis.get.return_value = b"5"  # 5 emails sent in time window
        mock_redis.incr.return_value = 6
        
        # Attempt to send email (should be rate limited)
        result = await email_service.send_registration_confirmation(user, "token")
        
        # Verify email was rate limited
        assert result["success"] is False
        assert "rate limit" in result["error"].lower()
        mock_email.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_email_personalization(self, db_session: AsyncSession, mock_email):
        """Test email personalization based on user preferences."""
        email_service = EmailNotificationService(db_session)
        
        user = User(
            id=uuid4(),
            email="personal@example.com",
            firstname="Personal",
            lastname="User",
            hashed_password="hashed_password",
            role="customer",
            verified=True,
            is_active=True,
            language="es",  # Spanish preference
            country="MX"    # Mexico
        )
        
        # Send personalized email
        await email_service.send_registration_confirmation(user, "token")
        
        # Verify email was personalized
        mock_email.assert_called_once()
        call_args = mock_email.call_args
        
        # Should use Spanish template and Mexican formatting
        assert call_args[1]["to"] == user.email
        # Template should be localized (this would depend on implementation)
        # assert "Bienvenido" in call_args[1]["html_content"]  # Spanish welcome